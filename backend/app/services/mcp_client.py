import asyncio
from app.services.mcp.mcp_client import (
    MCP_PYTHON,
    MCP_SERVER,
    PROJECT_ROOT,
    call_mcp_tool,
    main,
)

__all__ = [
    "PROJECT_ROOT",
    "MCP_PYTHON",
    "MCP_SERVER",
    "call_mcp_tool",
    "main",
]


if __name__ == "__main__":
    asyncio.run(main())