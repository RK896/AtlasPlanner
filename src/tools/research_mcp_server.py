from fastmcp import FastMCP

mcp = FastMCP("travel-research")

@mcp.tool()
def calculate(expression: str) -> str:
    """
    Evaluate a mathematical expression for budget calculations.

    Args:
        expression: A math expression like "100 * 7 + 50"

    Returns:
        The calculated result
    """
    try:
        # Safe eval for simple math
        result = eval(expression, {"__builtins__": {}}, {})
        return f"Result: {result}"
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
def search_destination_info(destination: str) -> str:
    """
    Search for travel information about a destination.
    Args:
        destination: Name of the destination (city or country)

    Returns:
        Travel infomation about this destination
    """
    # This is a placeholder - in reality, you'd call a real search API
    return f"""
    Travel Info for {destination}:
    - Best time to visit: Spring/Fall
    - Average daily budget: $80-150 USD
    - Top attractions: Historic sites, local markets, museums
    - Local currency: Check current exchange rates
    - Language tip: Learn basic greetings

    (Note: This is simulated data. Use real search APIs in production.)
    """