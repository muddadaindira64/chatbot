from typing import Any

from langchain_core.messages import (
    HumanMessage,
    SystemMessage,
)


SYSTEM_PROMPT = """
You are a helpful AI assistant.

# Tool Usage
You have access to tools. ALWAYS use them when appropriate:
- `get_datetime`: For current date, time, tomorrow, yesterday, etc.
- `get_weather`: For weather in specific locations.
- `live_search`: For current events, news, sports scores, live information, and current office holders.
- `calculator`: For all mathematical calculations.

When a tool returns data, use it as the source of truth to answer concisely. Do not expose internal tool logic.

# Personal Memory
- The `User Memory` section (if provided) contains the authenticated user's profile and preferences.
- ALWAYS use the name from `User Memory` if the user asks "What is my name?" or "Who am I?". Do NOT guess or use history for this.
- If no name is in `User Memory`, say "I don't have access to your name."

# Response Style
Answer clearly, concisely, and directly.
"""


def build_prompt(
    user_message: str,
    context: str | None = None,
    history: list[dict[str, Any]] | None = None,
    tool: dict[str, Any] | None = None,
) -> str:

    prompt_parts = []

    prompt_parts.append(SYSTEM_PROMPT)

    if context:
        prompt_parts.append(
            f"""
User Memory:

{context}
"""
        )

    if history:
        prompt_parts.append(
            f"""
Conversation History:

{history}
"""
        )

    if tool:
        prompt_parts.append(
            f"""
Tool Result:

Tool Name:
{tool.get("name")}

Tool Output:
{tool.get("output")}

Use this information to answer the user.
"""
        )

    prompt_parts.append(
        f"""
User Question:

{user_message}
"""
    )

    return "\n\n".join(prompt_parts)


def build_messages(
    user_message: str,
    context: str | None = None,
    history: list[dict[str, Any]] | None = None,
    tool_messages=None,
    ai_tool_message=None,
):

    messages = []

    messages.append(
        SystemMessage(
            content=SYSTEM_PROMPT
        )
    )

    if context:
        messages.append(
            SystemMessage(
                content=f"User Memory:\n{context}"
            )
        )

    if history:
        messages.append(
            SystemMessage(
                content=f"Conversation History:\n{history}"
            )
        )

    if ai_tool_message:
        messages.append(ai_tool_message)

    if tool_messages:
        messages.extend(tool_messages)

    messages.append(
        HumanMessage(
            content=user_message
        )
    )

    return messages