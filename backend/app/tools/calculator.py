from langchain_core.tools import tool


@tool
def calculator(expression: str) -> str:
    """
    Calculate mathematical expressions.

    Args:
        expression: Mathematical expression to evaluate.

    Returns:
        Calculated result.
    """

    try:
        result = eval(expression)
        return str(result)

    except Exception as e:
        return f"Error: {str(e)}"