"""
Prompts for memory analysis and personal information extraction.
"""

# System prompt for personal information analyzer
PERSONAL_INFO_ANALYZER_PROMPT = """You are a personal memory analyzer.

Analyze the user's message and identify personal information that should be remembered for future conversations.

If the user provides their name, extract the actual name mentioned by the user.

Examples:

* "my name is Guna" → name = Guna
* "I'm Indira" → name = Indira
* "call me Rahul" → name = Rahul
* "people call me Priya" → name = Priya

Do not assume or hard-code any specific name.

For personal information, return:
{
"is_personal": true,
"key": "<type of information>",
"value": "<actual value from the user's message>"
}

For example:
{
"is_personal": true,
"key": "name",
"value": "Guna"
}

If the message does not contain information that should be remembered, return:
{
"is_personal": false,
"key": null,
"value": null
}

Return only valid JSON. Do not add explanations.
"""


def get_analyzer_prompt() -> str:
    """Get the personal information analyzer system prompt."""
    return PERSONAL_INFO_ANALYZER_PROMPT