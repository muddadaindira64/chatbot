import logging
from collections.abc import Generator
from typing import Annotated, Any, TypedDict
from app.prompts.chat_prompt import SYSTEM_PROMPT
from langgraph.constants import END, START
from langgraph.graph import StateGraph
from langgraph.prebuilt import tools_condition
from langchain_core.messages import SystemMessage
from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    AIMessage,
)

from langgraph.graph.message import add_messages

from app.database.database import AsyncSessionLocal
from app.graph.personal_memory_node import personal_memory_analyzer
from app.graph.tools_node import tool_execution_node
from app.memory.service import get_memory_context
from app.services.llm_service import LLMService


async def _async_personal_memory_node(state: dict[str, Any]) -> dict[str, Any]:
    return await personal_memory_analyzer(state)

logger = logging.getLogger(__name__)


class WorkflowState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    user_id: int | None
    conversation_id: int | None
    loaded_memory: str


class ChatWorkflow:

    def __init__(self) -> None:
        self.llm_service = LLMService()
        self.graph = self._build_graph()

    @staticmethod
    def build_messages(
        message: str,
        memory_context: str | None = None,
        history: list[dict[str, str]] | None = None,
    ) -> list[BaseMessage]:
        history_messages: list[BaseMessage] = []
        if history:
            for item in history:
                role = item.get("role")
                content = item.get("content") or ""
                if role == "assistant":
                    history_messages.append(AIMessage(content=content))
                elif role == "user":
                    history_messages.append(HumanMessage(content=content))

        messages: list[BaseMessage] = [SystemMessage(content=SYSTEM_PROMPT)]
        if memory_context:
            messages.append(SystemMessage(content=f"User Personal Memory:\n{memory_context}"))
        messages.extend(history_messages)
        messages.append(HumanMessage(content=message))
        return messages

    async def llm_node(
        self,
        state: WorkflowState
    ) -> WorkflowState:
        user_id = state.get("user_id")
        conversation_id = state.get("conversation_id")
        messages = list(state.get("messages", []) or [])
        loaded_memory = ""

        if user_id:
            async with AsyncSessionLocal() as db:
                loaded_memory = await get_memory_context(db, user_id)

        logger.info(
            "user_id=%s conversation_id=%s loaded_memory=%s",
            user_id,
            conversation_id,
            loaded_memory or "",
        )

        if loaded_memory:
            memory_message = SystemMessage(
                content=f"User Personal Memory:\n{loaded_memory}"
            )
            if messages and isinstance(messages[0], SystemMessage):
                messages = [messages[0], memory_message, *messages[1:]]
            else:
                messages = [memory_message, *messages]

        response = await self.llm_service.ainvoke_with_tools(messages)

        print("====================")
        print("AI RESPONSE")
        print(response)
        print("TOOL CALLS")
        print(response.tool_calls)
        print("====================")
        tool_calls = getattr(response, "tool_calls", None) or []
        selected_tool = None
        if tool_calls:
            first_tool_call = tool_calls[0]
            if isinstance(first_tool_call, dict):
                selected_tool = first_tool_call.get("name")
            else:
                selected_tool = getattr(first_tool_call, "name", None)

        logger.info(
            "user_id=%s conversation_id=%s AIMessage.tool_calls=%s selected_tool=%s",
            user_id,
            conversation_id,
            tool_calls,
            selected_tool,
        )

        return {
            "messages": [response],
            "loaded_memory": loaded_memory or "",
        }

    def _build_graph(self):
        workflow = StateGraph(
            WorkflowState
        )
        workflow.add_node(
           "personal_memory_analyzer",
           _async_personal_memory_node
        )
        workflow.add_node(
            "llm_node",
            self.llm_node
        )
        workflow.add_node(
            "tools",
            tool_execution_node
        )
        workflow.add_edge(
            START,
            "personal_memory_analyzer"
        )
        workflow.add_edge(
            "personal_memory_analyzer",
            "llm_node"
        )
        workflow.add_conditional_edges(
            "llm_node",
            tools_condition,
            {
                "tools": "tools",
                "__end__": END
            }
        )
        workflow.add_edge(
            "tools",
            "llm_node"
        )
        return workflow.compile()


    async def run(
        self,
        message: str,
        user_id: int | None = None,
        conversation_id: int | None = None,
        memory_context: str | None = None,
        history: list[dict[str, str]] | None = None,
    ) -> tuple[str, str | None, str | None]:
        result = await self.graph.ainvoke(
            {
                "messages": self.build_messages(
                    message=message,
                    memory_context=memory_context,
                    history=history,
                ),
                "user_id": user_id,
                "conversation_id": conversation_id,
                "loaded_memory": memory_context or "",
            }
        )

        final_answer = result["messages"][-1].content

        # Extract the tool that was actually used (if any)
        tool_name: str | None = None
        tool_output: str | None = None
        for message in reversed(result["messages"]):
            message_type = getattr(message, "type", None)
            if message_type == "tool":
                tool_output = getattr(message, "content", None) or None
            if message_type == "ai" and getattr(message, "tool_calls", None):
                tool_calls = message.tool_calls
                if tool_calls:
                    first_call = tool_calls[0]
                    if isinstance(first_call, dict):
                        tool_name = first_call.get("name")
                    else:
                        tool_name = getattr(first_call, "name", None)
                    break

        return final_answer, tool_name, tool_output



    async def stream(self, message: str, user_id: int | None = None, conversation_id: int | None = None) -> Generator[str, None, None]:
        async for chunk in self.graph.astream(
            {
                "messages": [
                    SystemMessage(
                        content=SYSTEM_PROMPT
                    ),
                    HumanMessage(
                        content=message
                    )
                ],
                "user_id": user_id,
                "conversation_id": conversation_id,
                "loaded_memory": "",
            }
        ):
            if "llm_node" in chunk:
                msg = chunk["llm_node"]["messages"][-1]
                if msg.content:
                    yield msg.content