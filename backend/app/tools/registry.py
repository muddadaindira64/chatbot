from app.tools.calculator import calculator
from app.tools.live_search import live_search
from app.tools.weather import get_weather
from app.tools.datetime import get_datetime

from app.services.mcp_tools import (
    mcp_calculator,
    mcp_search,
    mcp_weather,
    mcp_time_date,
)

# Preserve existing local tools and also expose MCP tools.
# Order local tools first so the model can prefer them when appropriate.
AVAILABLE_TOOLS = [
    calculator,
    live_search,
    get_weather,
    get_datetime,
    # MCP-wrapped tools (available but do not replace local tools)
    mcp_calculator,
    mcp_search,
    mcp_weather,
    mcp_time_date,
]