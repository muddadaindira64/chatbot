from langchain_core.tools import tool
from tavily import TavilyClient

from app.core.config import settings


# Tavily client
client = TavilyClient(
    api_key=settings.tavily_api_key
)


@tool
def live_search(query: str) -> str:
    """
    Real-time internet search tool.

    Use this tool for information that changes over time.

    MUST use for:
    - latest news
    - today's news
    - current events
    - recent updates
    - IPL winner
    - sports results
    - stock prices
    - current Prime Minister / President
    - elections
    - latest technology updates
    - live information

     Location rules:
    - AP in India context means Andhra Pradesh.
    - Do not assume AP means Associated Press.

    Never answer these questions from memory.
    """

    try:

        print("\n========== TAVILY SEARCH ==========")
        print("QUERY:", query)


        response = client.search(
            query=query,
            search_depth="advanced",
            max_results=5,
            include_answer=True
        )


        # Debug complete response
        print(f"🔎 Searching: {query}")
        results = response.get(
            "results",
            []
        )


        if not results:
            return (
                "No relevant search results found "
                "for this query."
            )


        output = ""


        # Tavily answer if available
        if response.get("answer"):

            output += (
                "Tavily Summary:\n"
                f"{response['answer']}\n\n"
            )


        output += "Search Results:\n\n"


        for index, item in enumerate(
            results,
            start=1
        ):

            title = item.get(
                "title",
                ""
            )

            content = item.get(
                "content",
                ""
            )

            url = item.get(
                "url",
                ""
            )


            output += (
                f"Result {index}\n"
                f"Title: {title}\n"
                f"Content: {content}\n"
                f"Source: {url}\n\n"
            )


        return output.strip()


    except Exception as e:

        print(
            "TAVILY ERROR:",
            str(e)
        )

        return (
            f"Live search failed: {str(e)}"
        )