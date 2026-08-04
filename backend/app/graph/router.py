from langchain_core.messages import HumanMessage


def tool_router(state):

    message = state["messages"][-1].content.lower()


    # Weather keywords
    weather_words = [
        "weather",
        "temperature",
        "rain",
        "forecast",
        "climate"
    ]


    # Math keywords
    math_words = [
        "calculate",
        "sum",
        "multiply",
        "divide",
        "plus",
        "minus"
    ]


    # Live search keywords
    live_words = [
        "latest",
        "today",
        "current",
        "recent",
        "news",
        "winner",
        "price"
    ]


    if any(word in message for word in weather_words):
        return "weather"


    if any(word in message for word in math_words):
        return "calculator"


    if any(word in message for word in live_words):
        return "live_search"


    return "llm"