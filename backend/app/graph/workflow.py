import logging
from collections.abc import AsyncGenerator
from typing import Annotated, Any, TypedDict

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
)
from langgraph.constants import END, START
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import tools_condition

from app.database.database import AsyncSessionLocal
from app.graph.personal_memory_node import personal_memory_analyzer
from app.graph.tools_node import tool_execution_node
from app.memory.context import build_user_context
from app.prompts.chat_prompt import SYSTEM_PROMPT
from app.services.llm_service import LLMService


logger = logging.getLogger(__name__)


async def _async_personal_memory_node(
    state: dict[str, Any],
) -> dict[str, Any]:
    return await personal_memory_analyzer(state)


class WorkflowState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    user_id: int | None
    conversation_id: int | None
    loaded_memory: str


class ChatWorkflow:

    def __init__(self) -> None:
        self.llm_service = LLMService()
        self.graph = self._build_graph()

    # =========================================================
    # BUILD MESSAGES
    # =========================================================

    @staticmethod
    def build_messages(
        message: str,
        memory_context: str | None = None,
        history: list[dict[str, str]] | None = None,
    ) -> list[BaseMessage]:

        history_messages: list[BaseMessage] = []

        # Current conversation history only
        if history:
            MAX_HISTORY_MESSAGES = 4
            history = history[-MAX_HISTORY_MESSAGES:]

            for item in history:

                role = item.get("role")
                content = item.get("content") or ""

                if role == "assistant":

                    history_messages.append(
                        AIMessage(
                            content=content
                        )
                    )

                elif role == "user":

                    history_messages.append(
                        HumanMessage(
                            content=content
                        )
                    )

        # Base system prompt
        messages: list[BaseMessage] = [
            SystemMessage(
                content=SYSTEM_PROMPT
            )
        ]

        # =====================================================
        # CURRENT CONVERSATION HISTORY
        # =====================================================

        messages.extend(history_messages)

        # =====================================================
        # CURRENT USER MESSAGE
        # =====================================================

        messages.append(
            HumanMessage(
                content=message
            )
        )

        return messages

    # =========================================================
    # LLM NODE
    # =========================================================

    async def llm_node(
        self,
        state: WorkflowState,
    ) -> WorkflowState:

        user_id = state.get(
            "user_id"
        )

        conversation_id = state.get(
            "conversation_id"
        )

        messages = list(
            state.get(
                "messages",
                [],
            )
            or []
        )

        # Use memory from state if available
        loaded_memory = state.get("loaded_memory", "")
        has_tool_messages = any(msg.type == "tool" for msg in messages)

        # =====================================================
        # LOAD USER-SPECIFIC PERSONAL MEMORY
        # =====================================================

        if user_id is not None and not loaded_memory and not has_tool_messages:

            logger.info(
                "========== MEMORY RETRIEVE START =========="
            )

            logger.info(
                "MEMORY RETRIEVE user_id=%s conversation_id=%s",
                user_id,
                conversation_id,
            )

            try:

                async with AsyncSessionLocal() as db:

                    loaded_memory = (
                        await build_user_context(
                            db=db,
                            user_id=user_id,
                        )
                    )

                logger.info(
                    "MEMORY RETRIEVE RESULT "
                    "user_id=%s memory=%r",
                    user_id,
                    loaded_memory,
                )

            except Exception:

                logger.exception(
                    "MEMORY RETRIEVE FAILED "
                    "user_id=%s",
                    user_id,
                )

                loaded_memory = ""

            logger.info(
                "========== MEMORY RETRIEVE END =========="
            )

        else:

            logger.warning(
                "MEMORY RETRIEVE SKIPPED: user_id=None"
            )

        # =====================================================
        # INJECT MEMORY INTO LLM PROMPT
        # =====================================================

        if loaded_memory:

            logger.info(
                "MEMORY INJECTING INTO LLM "
                "user_id=%s",
                user_id,
            )

            memory_message = SystemMessage(
                content=(
                    "IMPORTANT USER INFORMATION:\n"
                    f"{loaded_memory}\n\n"
                    "Use this information when answering "
                    "questions about the user."
                )
            )

            if (
                messages
                and isinstance(
                    messages[0],
                    SystemMessage,
                )
            ):

                messages = [
                    messages[0],
                    memory_message,
                    *messages[1:],
                ]

            else:

                messages = [
                    memory_message,
                    *messages,
                ]

        else:

            logger.info(
                "NO PERSONAL MEMORY AVAILABLE "
                "FOR user_id=%s",
                user_id,
            )

        # =====================================================
        # CALL LLM
        # =====================================================

        response = (
            await self.llm_service.ainvoke_with_tools(
                messages
            )
        )

        # =====================================================
        # TOOL CALLS
        # =====================================================

        tool_calls = (
            getattr(
                response,
                "tool_calls",
                None,
            )
            or []
        )

        selected_tool = None

        if tool_calls:

            first_tool_call = tool_calls[0]

            if isinstance(
                first_tool_call,
                dict,
            ):

                selected_tool = (
                    first_tool_call.get(
                        "name"
                    )
                )

            else:

                selected_tool = getattr(
                    first_tool_call,
                    "name",
                    None,
                )

        logger.info(
            "user_id=%s conversation_id=%s "
            "AIMessage.tool_calls=%s "
            "selected_tool=%s",
            user_id,
            conversation_id,
            tool_calls,
            selected_tool,
        )

        return {
            "messages": [response],
            "loaded_memory": loaded_memory,
            "user_id": user_id,
            "conversation_id": conversation_id,
        }

    # =========================================================
    # BUILD GRAPH
    # =========================================================

    def _build_graph(self):

        workflow = StateGraph(
            WorkflowState
        )

        # Personal memory analyzer
        workflow.add_node(
            "personal_memory_analyzer",
            _async_personal_memory_node,
        )

        # LLM
        workflow.add_node(
            "llm_node",
            self.llm_node,
        )

        # Tools
        workflow.add_node(
            "tools",
            tool_execution_node,
        )

        # =====================================================
        # GRAPH FLOW
        # =====================================================

        workflow.add_edge(
            START,
            "personal_memory_analyzer",
        )

        workflow.add_edge(
            "personal_memory_analyzer",
            "llm_node",
        )

        workflow.add_conditional_edges(
            "llm_node",
            tools_condition,
            {
                "tools": "tools",
                "__end__": END,
            },
        )

        workflow.add_edge(
            "tools",
            "llm_node",
        )

        return workflow.compile()

    # =========================================================
    # RUN
    # =========================================================

    async def run(
        self,
        message: str,
        user_id: int | None = None,
        conversation_id: int | None = None,
        memory_context: str | None = None,
        history: list[dict[str, str]] | None = None,
    ) -> tuple[str, str | None, str | None]:

        logger.info(
            "WORKFLOW RUN "
            "user_id=%s conversation_id=%s",
            user_id,
            conversation_id,
        )

        # =====================================================
        # BUILD INITIAL MESSAGES
        # =====================================================

        initial_messages = self.build_messages(
            message=message,
            memory_context=memory_context,
            history=history,
        )

        # =====================================================
        # RUN LANGGRAPH
        # =====================================================

        result = await self.graph.ainvoke(
            {
                "messages": initial_messages,

                "user_id": user_id,

                "conversation_id": conversation_id,

                "loaded_memory": (
                    memory_context or ""
                ),
            }
        )

        # =====================================================
        # FINAL ANSWER
        # =====================================================

        final_message = (
            result["messages"][-1]
        )

        final_answer = (
            getattr(
                final_message,
                "content",
                None,
            )
            or ""
        )

        # =====================================================
        # EXTRACT TOOL INFORMATION
        # =====================================================

        tool_name: str | None = None
        tool_output: str | None = None

        for msg in reversed(
            result["messages"]
        ):

            message_type = getattr(
                msg,
                "type",
                None,
            )

            # Tool output
            if message_type == "tool":

                tool_output = (
                    getattr(
                        msg,
                        "content",
                        None,
                    )
                    or None
                )

            # Tool call
            if (
                message_type == "ai"
                and getattr(
                    msg,
                    "tool_calls",
                    None,
                )
            ):

                tool_calls = msg.tool_calls

                if tool_calls:

                    first_call = tool_calls[0]

                    if isinstance(
                        first_call,
                        dict,
                    ):

                        tool_name = (
                            first_call.get(
                                "name"
                            )
                        )

                    else:

                        tool_name = getattr(
                            first_call,
                            "name",
                            None,
                        )

                    break

        logger.info(
            "WORKFLOW COMPLETE "
            "user_id=%s conversation_id=%s "
            "tool=%s",
            user_id,
            conversation_id,
            tool_name,
        )

        return (
            final_answer,
            tool_name,
            tool_output,
        )

    # =========================================================
    # STREAM
    # =========================================================

    async def stream(
        self,
        message: str,
        user_id: int | None = None,
        conversation_id: int | None = None,
    ) -> AsyncGenerator[str, None]:

        logger.info(
            "STREAM START "
            "user_id=%s conversation_id=%s",
            user_id,
            conversation_id,
        )

        async for chunk in self.graph.astream(
            {
                "messages": [
                    SystemMessage(
                        content=SYSTEM_PROMPT
                    ),
                    HumanMessage(
                        content=message
                    ),
                ],

                "user_id": user_id,

                "conversation_id": conversation_id,

                "loaded_memory": "",
            }
        ):

            if "llm_node" not in chunk:
                continue

            messages = (
                chunk["llm_node"].get(
                    "messages",
                    [],
                )
            )

            if not messages:
                continue

            msg = messages[-1]

            # Do not stream tool-call messages
            if getattr(
                msg,
                "tool_calls",
                None,
            ):
                continue

            content = getattr(
                msg,
                "content",
                None,
            )

            if content:

                yield content