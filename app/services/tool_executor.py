import json
import logging
from typing import Any

from langchain_core.messages import ToolMessage
from langchain_core.tools import BaseTool

from app.tools.registry import AVAILABLE_TOOLS


logger = logging.getLogger(__name__)

# Map tool name -> tool object for fast lookup
_TOOL_MAP: dict[str, BaseTool] = {
    tool.name: tool for tool in AVAILABLE_TOOLS
}


def _serialize_tool_input(tool_input: dict[str, Any]) -> str:
    """Serialize tool input dict to a compact JSON string for the frontend."""
    try:
        return json.dumps(tool_input, ensure_ascii=False)
    except (TypeError, ValueError):
        return str(tool_input)


def execute_tool_call(
    tool_name: str,
    tool_input: dict[str, Any],
    tool_call_id: str,
) -> ToolMessage:
    """
    Execute a single tool call requested by the LLM.

    Args:
        tool_name: Name of the tool the LLM decided to call.
        tool_input: Arguments the LLM provided for the tool.
        tool_call_id: Unique ID of the tool call (used to link ToolMessage).

    Returns:
        A LangChain ToolMessage containing the tool's output.
    """
    tool = _TOOL_MAP.get(tool_name)

    if tool is None:
        logger.warning("Unknown tool requested by LLM: %s", tool_name)
        return ToolMessage(
            content=f"Error: Unknown tool '{tool_name}'.",
            tool_call_id=tool_call_id,
        )

    logger.info("Executing tool '%s' with input: %s", tool_name, tool_input)

    try:
        result = tool.invoke(tool_input)
        content = str(result)
    except Exception as exc:
        logger.exception("Tool '%s' execution failed", tool_name)
        content = f"Error executing tool '{tool_name}': {exc}"

    logger.info("Tool '%s' executed successfully", tool_name)

    return ToolMessage(
        content=content,
        tool_call_id=tool_call_id,
    )


def execute_tool_calls(
    tool_calls: list[dict[str, Any]],
) -> list[ToolMessage]:
    """
    Execute all tool calls requested by the LLM.

    Args:
        tool_calls: List of tool call dicts from an AIMessage.

    Returns:
        List of ToolMessage objects to append to the conversation.
    """
    tool_messages: list[ToolMessage] = []

    for call in tool_calls:
        tool_name = call.get("name", "")
        tool_input = call.get("args", {}) or {}
        tool_call_id = call.get("id", "")

        if not tool_call_id:
            logger.warning("Tool call missing id; generating fallback id")
            tool_call_id = f"call_{tool_name}_{len(tool_messages)}"

        tool_messages.append(
            execute_tool_call(
                tool_name=tool_name,
                tool_input=tool_input,
                tool_call_id=tool_call_id,
            )
        )

    return tool_messages


def build_frontend_tool_payload(
    tool_calls: list[dict[str, Any]],
    tool_messages: list[ToolMessage],
) -> dict[str, Any]:
    """
    Build the frontend tool payload from the first tool call + result.

    Returns:
        {
            "name": "search | calculator | weather | none",
            "input": "...",
            "output": "...",
            "requires_tool": true/false
        }
    """
    if not tool_calls or not tool_messages:
        return {
            "name": None,
            "input": None,
            "output": None,
            "requires_tool": False,
        }

    first_call = tool_calls[0]
    first_message = tool_messages[0]

    tool_name = first_call.get("name", "")
    tool_input = _serialize_tool_input(first_call.get("args", {}) or {})
    tool_output = first_message.content or ""

    # Map internal tool names to the frontend contract names
    frontend_name = {
        "live_search": "search",
        "calculator": "calculator",
        "get_weather": "weather",
    }.get(tool_name, tool_name)

    return {
        "name": frontend_name,
        "input": tool_input,
        "output": tool_output,
        "requires_tool": True,
    }