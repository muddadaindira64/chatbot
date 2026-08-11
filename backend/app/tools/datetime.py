from datetime import datetime, timedelta

from langchain_core.tools import tool


@tool
def get_datetime(query: str = "today") -> str:
    """
    Get the current date and time.

    Use this tool for:
    - today's date
    - tomorrow's date
    - yesterday's date
    - current day
    - current time
    - relative date questions
    """

    now = datetime.now()
    query_lower = query.lower()

    if "tomorrow" in query_lower:
        target = now + timedelta(days=1)
        label = "Tomorrow"
    elif "yesterday" in query_lower:
        target = now - timedelta(days=1)
        label = "Yesterday"
    else:
        target = now
        label = "Today"

    return (
        f"{label}: {target.strftime('%B %d, %Y')}, "
        f"{target.strftime('%A')}"
    )