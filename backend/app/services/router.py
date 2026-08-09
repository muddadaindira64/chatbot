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
search, calculator, weather, none.

You MUST NOT answer the user.
You MUST NOT explain anything.

Return ONLY JSON:

{
 "tool": "search|calculator|weather|none",
 "input": "tool input"
}


Choose the tool based on the user's intent.
Do not decide only by keyword matching.
Use the meaning of the question and available location context before selecting a tool.
If the user asks about current or live facts, use search.
If the user wants live weather conditions, rain, temperature now, or current forecast details, use weather.
If the user asks for arithmetic or calculations, use calculator.
If the user is greeting, making a personal statement, or asking for general conversation, use none.

For weather requests:
- Prefer weather for live weather checks, rain, temperature now, outside weather, and current weather conditions.
- Look for location in user memory and conversation history.
- If user location is available from memory or conversation history, use that location as the tool input.
- If location is not available, return an empty string and do not invent a city.

For search requests:
- Use search for latest news, current events, recent updates, leaders, prices, or live information.
- Generate a query that matches exactly what the user wants.
- Do not add historical context or years unless the user requested them.

For calculator requests:
- Use calculator for arithmetic, percentages, equations, compound interest, and other math questions.

For none requests:
- Use none for greetings, introductions, hobbies, writing, explanations, opinions, and normal chat.

Examples:
User: Weather in Hyderabad today
{
 "tool":"weather",
 "input":"Hyderabad"
}
User: Is it raining outside?
{
 "tool":"weather",
 "input":""
}
User: Who is PM of India?
{
 "tool":"search",
 "input":"current Prime Minister of India"
}
User: Latest AI news
{
 "tool":"search",
 "input":"latest AI news"
}
User: Calculate 234567*9876
{
 "tool":"calculator",
 "input":"234567*9876"
}
User: Hi
{
 "tool":"none",
 "input":""
}

==============================
SEARCH TOOL RULES
==============================

Use search for:

- current information
- latest information
- news
- sports results
- IPL winner
- current leaders
- politicians
- companies
- prices
- live information


IMPORTANT SEARCH QUERY RULES:

1. Never invent years.

If user does NOT mention a year,
do NOT add any year.

Example:

User:
Who won IPL?

Wrong:
{
 "tool":"search",
 "input":"IPL winner 2023"
}


Correct:
{
 "tool":"search",
 "input":"latest IPL winner"
}



User:
Who won IPL 2023?

Correct:
{
 "tool":"search",
 "input":"IPL 2023 winner"
}



2. For current people:

User:
Who is PM of India?

Return:

{
 "tool":"search",
 "input":"current Prime Minister of India"
}



3. Search input should represent exactly what user wants.
Do not add historical context.



==============================
WEATHER TOOL
==============================

Use weather only for:

- weather
- temperature
- rain
- forecast
- humidity
- wind
- climate


Input should be only location.

Example:

User:
Weather in Hyderabad today

Return:

{
 "tool":"weather",
 "input":"Hyderabad"
}



==============================
CALCULATOR TOOL
==============================

Use calculator for:

- arithmetic
- percentages
- equations
- mathematics


Example:

User:
25% of 400

Return:

{
 "tool":"calculator",
 "input":"25% of 400"
}



==============================
NONE TOOL
==============================

Use none for:

- greetings
- writing
- coding help
- explanations
- opinions
- discussions



Never add markdown.
Never add explanation.
Return JSON only.
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