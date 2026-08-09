import logging
from typing import Any

from langgraph.prebuilt import ToolNode

from app.tools.registry import AVAILABLE_TOOLS

logger = logging.getLogger(__name__)


def tool_execution_node(state: dict[str, Any]) -> dict[str, Any]:
    messages = state.get("messages", []) or []
    if not messages:
        return {"messages": []}

    last_message = messages[-1]
    tool_calls = getattr(last_message, "tool_calls", None) or []
    if not tool_calls:
        return {"messages": []}

    logger.info("selected_tool=%s", tool_calls)
    tool_node = ToolNode(AVAILABLE_TOOLS)
    result = tool_node.invoke({"messages": [last_message]})
    tool_result_messages = result.get("messages", []) if isinstance(result, dict) else []
    for tool_message in tool_result_messages:
        logger.info("tool_result=%s", getattr(tool_message, "content", None))

    return {"messages": tool_result_messages}