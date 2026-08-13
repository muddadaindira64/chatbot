import sys
print("Python:", sys.version)
print("Testing imports...")

try:
    from app.graph.workflow import ChatWorkflow
    print("Workflow imports OK")
except Exception as e:
    print(f"Workflow import FAILED: {e}")

try:
    from app.graph.tools_node import atool_execution_node, tool_execution_node
    print("Tools node imports OK")
except Exception as e:
    print(f"Tools node import FAILED: {e}")

try:
    from app.services.mcp_tools import mcp_calculator, mcp_search, mcp_weather, mcp_time_date
    print("MCP tools imports OK")
except Exception as e:
    print(f"MCP tools import FAILED: {e}")

try:
    from app.tools.registry import AVAILABLE_TOOLS
    print(f"Registry imports OK - {len(AVAILABLE_TOOLS)} tools: {[t.name for t in AVAILABLE_TOOLS]}")
except Exception as e:
    print(f"Registry import FAILED: {e}")

try:
    from app.services.llm_service import LLMService
    print("LLM service imports OK")
except Exception as e:
    print(f"LLM service import FAILED: {e}")

try:
    from app.prompts.chat_prompt import SYSTEM_PROMPT
    print("Chat prompt imports OK")
except Exception as e:
    print(f"Chat prompt import FAILED: {e}")

print("All import tests complete")