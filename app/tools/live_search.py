import logging
from typing import Any

import httpx
from langchain_core.tools import tool

from app.core.config import settings


logger = logging.getLogger(__name__)
TAVILY_SEARCH_URL = "https://api.tavily.com/search"
TAVILY_TIMEOUT = httpx.Timeout(
    timeout=15.0,
    connect=5.0,
    read=15.0,
    write=15.0,
    pool=5.0,
)


def _format_results(payload: dict[str, Any]) -> str:
    results = payload.get("results") or []
    answer = str(payload.get("answer") or "").strip()

    if not results and not answer:
        return "No relevant search results found for this query."

    sections: list[str] = []

    if answer:
        sections.append(f"Tavily Summary:\n{answer}")

    if results:
        result_lines: list[str] = ["Search Results:"]
        for index, item in enumerate(results[:3], start=1):
            title = str(item.get("title", "")).strip()
            content = str(item.get("content", "")).strip()
            url = str(item.get("url", "")).strip()

            if len(content) > 280:
                content = content[:280].rstrip() + "..."

            result_lines.extend(
                [
                    f"Result {index}",
                    f"Title: {title}",
                    f"Content: {content}",
                    f"Source: {url}",
                    "",
                ]
            )

        sections.append("\n".join(result_lines).strip())

    return "\n\n".join(section for section in sections if section).strip()


@tool
def live_search(query: str) -> str:
    """
    Real-time internet search tool.

    Use this tool for information that changes over time.

    MUST use for:
    - current date
    - today's date
    - tomorrow's date
    - yesterday's date
    - current day of the week
    - tomorrow's day of the week
    - yesterday's day of the week
    - current time
    - current time in another location
    - latest news
    - today's news
    - current events
    - recent updates
    - current office holders
    - political positions
    - IPL winner
    - sports results
    - stock prices
    - elections
    - latest technology updates
    - live information
    - current weather when get_weather is not available
    - breaking news

    Date questions:
    - Always use this tool for current or relative date questions.
    - When the user asks for a date, search for BOTH the exact date
      and the corresponding day of the week.
    - For example, "tomorrow date" must return tomorrow's date AND
      its weekday.
    - Do not rely on the model's internal knowledge for current dates.

    Location rules:
    - AP in India context means Andhra Pradesh.
    - Do not assume AP means Associated Press.

    Never answer current or latest information from memory.
    """
   

    cleaned_query = (query or "").strip()
    if not cleaned_query:
        return "No search query provided."

    if not settings.tavily_api_key:
        logger.error("Tavily API key is missing")
        return "Sorry, I couldn't access the search service right now. Please try again later."

    logger.info("Search started: %s", cleaned_query)

    payload = {
        "api_key": settings.tavily_api_key,
        "query": f"{cleaned_query}. Provide the current latest status as of today.",
        "search_depth": "advanced",
        "max_results": 3,
        "include_answer": True
    }

    try:
        logger.info("Request sent to Tavily")
        with httpx.Client(timeout=TAVILY_TIMEOUT) as client:
            response = client.post(TAVILY_SEARCH_URL, json=payload)
            response.raise_for_status()
            data = response.json()
        logger.info("Response received from Tavily")
    except httpx.TimeoutException:
        logger.exception("Tavily search timed out")
        return "Sorry, I couldn't access the search service right now. Please try again later."
    except httpx.HTTPStatusError as exc:
        logger.exception(
            "Tavily search returned HTTP %s",
            exc.response.status_code if exc.response is not None else "unknown",
        )
        return "Sorry, I couldn't access the search service right now. Please try again later."
    except httpx.RequestError:
        logger.exception("Tavily network request failed")
        return "Sorry, I couldn't access the search service right now. Please try again later."
    except Exception:
        logger.exception("Unexpected Tavily search failure")
        return "Sorry, I couldn't access the search service right now. Please try again later."

    logger.info("Search completed")
    logger.info("Search response formatted")
    return _format_results(data)
