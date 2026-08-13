import asyncio
import os
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Ensure UTF-8 console output for Windows terminal
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def get_project_root() -> Path:
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        if (parent / "mcp_server" / "server.py").is_file():
            return parent
    return current.parents[4]


PROJECT_ROOT = get_project_root()

MCP_PYTHON = (
    PROJECT_ROOT
    / "mcp_server"
    / ".venv"
    / "Scripts"
    / "python.exe"
)

MCP_SERVER = (
    PROJECT_ROOT
    / "mcp_server"
    / "server.py"
)


async def call_mcp_tool(
    tool_name: str,
    arguments: dict,
) -> str:
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"

    server_params = StdioServerParameters(
        command=str(MCP_PYTHON),
        args=[str(MCP_SERVER)],
        env=env,
    )

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments)

                if hasattr(result, "content") and result.content:
                    text_parts = [
                        c.text for c in result.content if hasattr(c, "text")
                    ]
                    return "".join(text_parts).strip()
                return str(result).strip()
    except Exception as e:
        return f"Error executing MCP tool '{tool_name}': {str(e)}"


async def main():
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"

    server_params = StdioServerParameters(
        command=str(MCP_PYTHON),
        args=[str(MCP_SERVER)],
        env=env,
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools_response = await session.list_tools()
            print("Available MCP tools:\n")
            for tool in tools_response.tools:
                print(f"* {tool.name}")
            print()

    print("--- Calculator Test ---")
    calc_res = await call_mcp_tool("calculator", {"expression": "25 * 40"})
    print(calc_res)

    print("\n--- Search Test ---")
    search_res = await call_mcp_tool("search", {"query": "Who is the latest winner of IPL?"})
    print(search_res[:500] if search_res else "No output")

    print("\n--- Weather Test ---")
    weather_res = await call_mcp_tool("weather", {"city": "Hyderabad"})
    print(weather_res[:200] if weather_res else "No output")

    print("\n--- Time/Date Test ---")
    time_res = await call_mcp_tool("time_date", {"query": "today"})
    print(time_res)


if __name__ == "__main__":
    asyncio.run(main())