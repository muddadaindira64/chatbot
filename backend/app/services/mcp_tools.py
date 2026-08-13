import asyncio
import concurrent.futures
import logging
import re
from langchain_core.tools import StructuredTool

from app.services.mcp.mcp_client import call_mcp_tool

logger = logging.getLogger(__name__)


def _run_mcp_sync(tool_name: str, arguments: dict) -> str:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(
                asyncio.run,
                call_mcp_tool(tool_name, arguments),
            ).result()
    else:
        return asyncio.run(call_mcp_tool(tool_name, arguments))


# =========================================================================
# 1. MCP CALCULATOR
# =========================================================================


def _normalize_calculator_expression(expression: str) -> str:
    if not expression:
        return expression

    text = expression.strip()
    text = text.replace(",", "")
    text = text.rstrip("?").strip()
    lower = text.lower()

    # Normalize natural-language calculation requests into evaluatable expressions.
    lower = re.sub(r"^(calculate|what is|what's|compute|find|evaluate|the value of)\s+", "", lower)
    lower = re.sub(r"\bplus\b", "+", lower)
    lower = re.sub(r"\bminus\b", "-", lower)
    lower = re.sub(r"\b(times|multiplied by)\b", "*", lower)
    lower = re.sub(r"\b(divided by|over)\b", "/", lower)
    lower = re.sub(r"\bpercent\b", "%", lower)
    lower = re.sub(r"\bpercent of\b", "% of", lower)

    percent_match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*%\s*of\s*([0-9]+(?:\.[0-9]+)?)", lower)
    if percent_match:
        return f"{percent_match.group(1)} / 100 * {percent_match.group(2)}"

    rectangle_match = re.search(
        r"area of rectangle.*length\s*([0-9]+(?:\.[0-9]+)?)\s*(?:and|,)\s*width\s*([0-9]+(?:\.[0-9]+)?)",
        lower,
    )
    if rectangle_match:
        return f"{rectangle_match.group(1)} * {rectangle_match.group(2)}"

    triangle_match = re.search(
        r"area of triangle.*base\s*([0-9]+(?:\.[0-9]+)?)\s*(?:and|,)\s*height\s*([0-9]+(?:\.[0-9]+)?)",
        lower,
    )
    if triangle_match:
        return f"({triangle_match.group(1)} * {triangle_match.group(2)}) / 2"

    cube_match = re.search(r"volume of cube.*side\s*([0-9]+(?:\.[0-9]+)?)", lower)
    if cube_match:
        side = cube_match.group(1)
        return f"{side} * {side} * {side}"

    circumference_match = re.search(
        r"circumference of circle.*radius\s*([0-9]+(?:\.[0-9]+)?)",
        lower,
    )
    if circumference_match:
        return f"2 * 3.141592653589793 * {circumference_match.group(1)}"

    diameter_match = re.search(
        r"circumference of circle.*diameter\s*([0-9]+(?:\.[0-9]+)?)",
        lower,
    )
    if diameter_match:
        return f"3.141592653589793 * {diameter_match.group(1)}"

    lower = re.sub(r"\s+", " ", lower).strip()
    return lower


def _mcp_calculator_sync(expression: str) -> str:
    expression = _normalize_calculator_expression(expression)
    return _run_mcp_sync("calculator", {"expression": expression})


async def _mcp_calculator_async(expression: str) -> str:
    """Calculate a mathematical expression using the MCP calculator server."""
    expression = _normalize_calculator_expression(expression)
    return await call_mcp_tool("calculator", {"expression": expression})


mcp_calculator = StructuredTool.from_function(
    func=_mcp_calculator_sync,
    coroutine=_mcp_calculator_async,
    name="mcp_calculator",
    description=(
        "Calculate a valid mathematical expression using the MCP calculator server. "
        "The expression must be an evaluatable arithmetic expression only. "
        "Convert percentage and phrase-based math into symbols before calling, "
        "for example: 25 / 100 * 1840, 20 * 15, (10 * 8) / 2, 2 * 3.141592653589793 * 7."
    ),
)


# =========================================================================
# MCP SEARCH
# =========================================================================

def _mcp_search_sync(query: str) -> str:
    """
    Execute the MCP search tool synchronously.

    The LLM is responsible for understanding the user's intent
    and generating the appropriate search query.
    """
    query = (query or "").strip()

    if not query:
        return "No search query provided."

    logger.info("MCP search query: %s", query)

    return _run_mcp_sync(
        "search",
        {"query": query},
    )


async def _mcp_search_async(query: str) -> str:
    """
    Execute the MCP search tool asynchronously.

    The LLM is responsible for understanding the user's intent
    and generating the appropriate search query.
    """
    query = (query or "").strip()

    if not query:
        return "No search query provided."

    logger.info("MCP search query: %s", query)

    return await call_mcp_tool(
        "search",
        {"query": query},
    )


mcp_search = StructuredTool.from_function(
    func=_mcp_search_sync,
    coroutine=_mcp_search_async,
    name="mcp_search",
    description=(
        "Real-time internet search tool. "
        "Use this tool for current, latest, recent, live, "
        "or time-sensitive information including news, "
        "sports results, current office holders, prices, "
        "elections, and recent events. "
        "The LLM must understand the user's intent and "
        "generate the appropriate natural-language search query. "
        "Do not invent or add a year unless the user explicitly "
        "specifies a year."
    ),
)




# =========================================================================
# 3. MCP WEATHER
# =========================================================================


def _mcp_weather_sync(city: str, date: str = "") -> str:
    return _run_mcp_sync("weather", {"city": city, "date": date})


async def _mcp_weather_async(city: str, date: str = "") -> str:
    """Get current or forecast weather information for a city using the MCP weather server."""
    return await call_mcp_tool("weather", {"city": city, "date": date})


mcp_weather = StructuredTool.from_function(
    func=_mcp_weather_sync,
    coroutine=_mcp_weather_async,
    name="mcp_weather",
    description=(
        "Get weather information for a city. Supports current weather, today, "
        "tomorrow, yesterday, or specific YYYY-MM-DD dates."
    ),
)


# =========================================================================
# 4. MCP TIME / DATE
# =========================================================================


def _mcp_time_date_sync(query: str = "today") -> str:
    return _run_mcp_sync("time_date", {"query": query})


async def _mcp_time_date_async(query: str = "today") -> str:
    """Get current date and time or relative dates using the MCP time_date server."""
    return await call_mcp_tool("time_date", {"query": query})


mcp_time_date = StructuredTool.from_function(
    func=_mcp_time_date_sync,
    coroutine=_mcp_time_date_async,
    name="mcp_time_date",
    description=(
        "Get the current date and time. "
        "IMPORTANT: Always provide the query argument. "
        "For a time question such as 'what time is it' or 'current time', "
        "call with query='time'. "
        "For a date question such as 'what is today's date', "
        "call with query='date'. "
        "For tomorrow, call with query='tomorrow'. "
        "For yesterday, call with query='yesterday'. "
        "When the user asks for the current time, return current time, "
        "date, and day of the week."
    ),
)