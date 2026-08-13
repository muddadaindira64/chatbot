import asyncio

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


server_params = StdioServerParameters(
    command="python",
    args=["server.py"],
)


async def main():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:

            await session.initialize()

            tools = await session.list_tools()

            print("Available MCP tools:")

            for tool in tools.tools:
                print("-", tool.name)

            # Call calculator tool
            print("\nCalling calculator...")

            result = await session.call_tool(
                "calculator",
                arguments={
                    "expression": "25 * 40"
                }
            )

            print("Result:", result)


if __name__ == "__main__":
    asyncio.run(main())