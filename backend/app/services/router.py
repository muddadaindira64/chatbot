import json
import logging
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class ToolRouter:
    """
    LLM-based tool router.

    The LLM decides which MCP tool should be used.
    This router does not perform keyword-based routing.
    It does not generate the final answer.
    """

    def __init__(self):
        self.llm = LLMService()

        self.router_prompt = """
You are an AI Tool Router.

Your ONLY responsibility is to decide whether the user's request
requires an MCP tool.

You MUST NOT answer the user's question.

You MUST return ONLY valid JSON in this exact format:

{
  "tool": "mcp_search|mcp_calculator|mcp_weather|mcp_time_date|none",
  "input": "appropriate input for the selected tool"
}

AVAILABLE MCP TOOLS:

1. mcp_search

Use this for information that requires internet/current information.

Examples:
- latest news
- current events
- recent updates
- live information
- sports results
- IPL results
- IPL winner
- current political information
- current Prime Minister
- current Chief Minister
- current prices
- elections
- latest technology information
- any question where the answer may have changed recently

IMPORTANT:

If the user asks:

"Who is the winner of IPL?"

Do NOT assume an old year.

Interpret it as:

"Who is the winner of the most recently completed IPL season?"

Return:

{
  "tool": "mcp_search",
  "input": "latest IPL winner"
}

If the user asks:

"Who won IPL 2023?"

Return:

{
  "tool": "mcp_search",
  "input": "IPL 2023 winner"
}

If the user asks:

"Who is the current CM of AP?"

Understand AP as Andhra Pradesh and return:

{
  "tool": "mcp_search",
  "input": "current Chief Minister of Andhra Pradesh"
}

If the user asks:

"Who is the current Prime Minister of India?"

Return:

{
  "tool": "mcp_search",
  "input": "current Prime Minister of India"
}

Do NOT use hardcoded answers.
Do NOT rely on your internal knowledge for current information.

2. mcp_calculator

Use this for mathematical calculations.

Examples:
- 10 + 20
- 25% of 500
- 123 * 45
- 100 / 4
- mathematical expressions
- arithmetic
- percentages

Example:

User:
What is 25 percent of 800?

Return:

{
  "tool": "mcp_calculator",
  "input": "25% of 800"
}

3. mcp_weather

Use this for weather-related requests.

Examples:
- current weather
- temperature
- rain
- rainfall
- humidity
- wind
- weather forecast
- weather tomorrow
- weather today

Example:

User:
What is the weather in Hyderabad?

Return:

{
  "tool": "mcp_weather",
  "input": "Hyderabad"
}

If the user specifies a date, preserve it.

Example:

User:
What will the weather be in Hyderabad tomorrow?

Return:

{
  "tool": "mcp_weather",
  "input": "Hyderabad, tomorrow"
}

4. mcp_time_date

Use this for date and time requests.

Examples:
- today's date
- tomorrow's date
- yesterday's date
- current date
- current time
- what day is today
- what day will tomorrow be
- date questions
- day-of-week questions

Example:

User:
What is today's date?

Return:

{
  "tool": "mcp_time_date",
  "input": "today"
}

Example:

User:
What date is tomorrow?

Return:

{
  "tool": "mcp_time_date",
  "input": "tomorrow"
}

5. none

Use "none" when no MCP tool is required.

Examples:
- hi
- hello
- how are you
- explain what is an agent
- explain MCP
- coding questions
- programming explanations
- writing requests
- general knowledge that does not require current information
- casual conversation

IMPORTANT DECISION RULES:

1. Understand the user's meaning semantically.
2. Do NOT rely on simple keyword matching.
3. Do NOT rewrite every query using fixed keywords.
4. Select the MCP tool based on the intent of the question.
5. For current/latest/recent/live information, use mcp_search.
6. For mathematical calculations, use mcp_calculator.
7. For weather, use mcp_weather.
8. For date/time questions, use mcp_time_date.
9. Otherwise use none.
10. Never answer the user's question yourself.
11. Never invent tool results.
12. Return JSON only.
13. Never add markdown.
14. Never add explanations.

CURRENT INFORMATION RULE:

If there is any reasonable possibility that the requested information
has changed over time, use mcp_search.

For sports competitions such as IPL:

- No year specified -> latest completed season.
- Year specified -> that specific year's result.

For political office holders:

- Use mcp_search.
- Do not rely on model knowledge.
- Understand natural-language variations such as:
  "CM of AP"
  "Andhra Pradesh CM"
  "who runs AP"
  "who is leading Andhra Pradesh"
  when they clearly refer to the current Chief Minister.

The final answer will be generated separately after the selected MCP tool
returns its result.
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
USER QUESTION:

{message}

USER MEMORY:

{memory_context or "None"}

CONVERSATION HISTORY:

{conversation_history or "None"}

Now determine whether an MCP tool is required.

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
                    ),
                ]
            )

            content = getattr(
                response,
                "content",
                response,
            )

            raw_text = str(content).strip()

            logger.info(
                "ROUTER RAW RESPONSE: %s",
                raw_text,
            )

            # Extract JSON if model accidentally adds extra text.
            json_text = raw_text

            if not raw_text.startswith("{"):
                match = re.search(
                    r"\{.*\}",
                    raw_text,
                    re.S,
                )

                if match:
                    json_text = match.group(0)

            decision = json.loads(json_text)

            tool = str(
                decision.get(
                    "tool",
                    "none",
                )
            ).strip()

            tool_input = str(
                decision.get(
                    "input",
                    "",
                )
            ).strip()

            # IMPORTANT:
            # Only MCP tool names are allowed.
            allowed_tools = {
                "mcp_search",
                "mcp_calculator",
                "mcp_weather",
                "mcp_time_date",
                "none",
            }

            if tool not in allowed_tools:
                logger.warning(
                    "Router returned invalid tool: %s",
                    tool,
                )
                tool = "none"
                tool_input = ""

            # If the LLM selected a tool but did not provide input,
            # use the original user message.
            if tool != "none" and not tool_input:
                tool_input = message

            if tool == "none":
                tool_input = ""

            result = {
                "tool": tool,
                "input": tool_input,
                "tool_used": (
                    None
                    if tool == "none"
                    else tool
                ),
                "tool_output": None,
                "requires_tool": tool != "none",
            }

            logger.info(
                "ROUTER DECISION: %s",
                result,
            )

            return result

        except json.JSONDecodeError as exc:

            logger.exception(
                "Router returned invalid JSON: %s",
                exc,
            )

            return {
                "tool": "none",
                "input": "",
                "tool_used": None,
                "tool_output": None,
                "requires_tool": False,
            }

        except Exception as exc:

            logger.exception(
                "Router failed: %s",
                exc,
            )

            return {
                "tool": "none",
                "input": "",
                "tool_used": None,
                "tool_output": None,
                "requires_tool": False,
            }


router = ToolRouter()