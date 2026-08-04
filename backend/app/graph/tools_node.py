from langgraph.prebuilt import ToolNode

from app.tools.registry import AVAILABLE_TOOLS


tool_node = ToolNode(
    AVAILABLE_TOOLS
)