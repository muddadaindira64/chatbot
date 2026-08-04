from collections.abc import Generator
from typing import Annotated, TypedDict

from langgraph.constants import END, START
from langgraph.graph import StateGraph
from langgraph.prebuilt import tools_condition
from langchain_core.messages import SystemMessage
from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
)

from langgraph.graph.message import add_messages

from app.graph.tools_node import tool_node
from app.services.llm_service import LLMService


class WorkflowState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


class ChatWorkflow:

    def __init__(self) -> None:
        self.llm_service = LLMService()
        self.graph = self._build_graph()


    def llm_node(
        self,
        state: WorkflowState
    ) -> WorkflowState:

        response = self.llm_service.invoke(
            state["messages"]
        )

        return {
            "messages": [
                response
            ]
        }


    def _build_graph(self):

        workflow = StateGraph(
            WorkflowState
        )


        # Nodes
        workflow.add_node(
            "llm_node",
            self.llm_node
        )

        workflow.add_node(
            "tools",
            tool_node
        )


        # Start
        workflow.add_edge(
            START,
            "llm_node"
        )


        # Tool decision
        workflow.add_conditional_edges(
            "llm_node",
            tools_condition,
            {
                "tools": "tools",
                "__end__": END
            }
        )


        # Tool result back to LLM
        workflow.add_edge(
            "tools",
            "llm_node"
        )


        return workflow.compile()



    def run(
        self,
        message: str
    ) -> str:


        result = self.graph.invoke(
            {
                "messages": [
                    SystemMessage(
                        content="""
You are an AI agent.

Rules:
- Weather questions MUST use get_weather tool.
- Math questions MUST use calculator tool.
- Latest information MUST use live_search tool.
"""
                ),
                    HumanMessage(
                        content=message
                    )
                ]
            }
        )


        return result["messages"][-1].content



    def stream(self,message: str) -> Generator[str, None, None]:
        for chunk in self.graph.stream(
            {
                "messages": [

                SystemMessage(
                    content="""
You are an AI agent.

Rules:
- Weather questions MUST use get_weather tool.
- Math questions MUST use calculator tool.
- Latest information MUST use live_search tool.
"""
                ),

                HumanMessage(
                    content=message
                )
            ]
        }
    ):
            if "llm_node" in chunk:
                msg = chunk["llm_node"]["messages"][-1]
                if msg.content:
                    yield msg.content