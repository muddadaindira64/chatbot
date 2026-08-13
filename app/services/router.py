import json
import logging
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.services.llm_service import LLMService


logger = logging.getLogger(__name__)


class ToolRouter:
    """
    Production Tool Router.

    Uses LLM only for tool selection.
    It never generates final answers.
    """

    def __init__(self):
        self.llm = LLMService()

        self.router_prompt = """
You are an AI Tool Router.

Your ONLY task is selecting exactly one tool:
mcp_search, mcp_calculator, mcp_weather, mcp_time_date, none.

You MUST NOT answer the user.
You MUST NOT explain anything.

Return ONLY JSON:

{
  "tool": "mcp_search|mcp_calculator|mcp_weather|mcp_time_date|none",
  "input": "tool input"
}

IMPORTANT:
Use ONLY MCP tools for tool-based requests.
Never select search, calculator, weather, or any non-MCP tool.

TOOL SELECTION RULES:

1. mcp_search
Use mcp_search for:
- current information
- latest information
- news
- current events
- sports results
- IPL winner
- current Prime Minister / Chief Minister
- current politicians
- current prices
- live information
- recent updates

If the user asks "Who won IPL?" without a year:
- interpret it as the latest completed IPL season
- return:
{
  "tool": "mcp_search",
  "input": "latest IPL winner"
}

If the user specifies a year:
"Who won IPL 2023?"
return:
{
  "tool": "mcp_search",
  "input": "IPL 2023 winner"
}

Never change an unspecified IPL query to an old year such as 2023.

For current office holders:

"Who is PM of India?"
→ "current Prime Minister of India"

"Who is CM of AP?"
→ "current Chief Minister of Andhra Pradesh"

"Who is CM of Telangana?"
→ "current Chief Minister of Telangana"

"Who is CM of Tamil Nadu?"
→ "current Chief Minister of Tamil Nadu"


2. mcp_calculator

Use mcp_calculator for:
- arithmetic
- percentages
- equations
- mathematical calculations

Example:

User:
Calculate 2 plus 9 into 4

Return:

{
  "tool": "mcp_calculator",
  "input": "2 + 9 * 4"
}


3. mcp_weather

Use mcp_weather for:
- current weather
- temperature
- rain
- forecast
- humidity
- wind

If location is available in memory or conversation history, use it.

Example:

{
  "tool": "mcp_weather",
  "input": "Hyderabad"
}


4. mcp_time_date

Use mcp_time_date for:
- current date
- current time
- today
- tomorrow
- yesterday
- day/date questions

Example:

User:
What is today's date?

Return:

{
  "tool": "mcp_time_date",
  "input": "today"
}


5. none

Use none for:
- greetings
- normal conversation
- explanations
- writing
- coding help
- opinions
- questions that do not require a tool

IMPORTANT CURRENT INFORMATION RULE:

Whenever the user asks for current/latest/recent/today/now information,
prefer the appropriate MCP tool.

For sports questions without a year, interpret the question as asking
for the latest completed season.

Never use old cached knowledge when MCP search is available.

Return JSON only.
Never add markdown.
Never add explanations.
"""
    async def classify(
        self,
        message: str,
        memory_context: str | None = None,
        history: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:

        conversation_history = ""
        if history:
            conversation_history = "\n".join(
                f"{msg['role']}: {msg['content']}"
                for msg in history
            )

        prompt = f"""
User question:

{message}

User memory:
{memory_context or 'None'}

Conversation history:
{conversation_history or 'None'}

Return JSON only.
"""

        try:

            response = self.llm.invoke(
                [
                    SystemMessage(
                        content=self.router_prompt
                    ),
                    HumanMessage(
                        content=prompt
                    )
                ]
            )

            content = getattr(
                response,
                "content",
                response
            )
            raw_text = str(content).strip()

            logger.info(
                "Router response: %s",
                raw_text
            )

            json_text = raw_text
            if not raw_text.startswith("{"):
                match = re.search(r"(\{.*\})", raw_text, re.S)
                if match:
                    json_text = match.group(1)

            decision = json.loads(json_text)


            tool = decision.get(
                "tool",
                "none"
            )

            tool_input = decision.get(
                "input",
                ""
            )


            if tool not in [
                "search",
                "calculator",
                "weather",
                "none"
            ]:
                tool = "none"


            if tool == "weather" and not tool_input:
                tool_input = ""
            elif tool != "none" and not tool_input:
                tool_input = message


            if tool == "none":
                tool_input = ""


            return {

                "tool": tool,

                "input": tool_input,

                "tool_used":
                    None
                    if tool == "none"
                    else tool,

                "tool_output": None,

                "requires_tool":
                    tool != "none"
            }


        except Exception as exc:

            logger.exception(
                "Router failed: %s",
                exc
            )

            return {

                "tool": "none",

                "input": "",

                "tool_used": None,

                "tool_output": None,

                "requires_tool": False
            }



router = ToolRouter()