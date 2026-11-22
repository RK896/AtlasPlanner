"""MCP server exposing destination research tools to the Research agent."""
from fastmcp import FastMCP

from src.tools.mcp_helpers import friendly_errors
from src.tools.services import calculator, currency, weather, wikivoyage

mcp = FastMCP("travel-research")

OVERVIEW_SECTIONS = ["Intro", "Understand", "Get around", "Stay safe"]


@mcp.tool
@friendly_errors
def destination_overview(destination: str) -> str:
    """Get a real travel-guide overview of a city: what it's like, getting around, safety.

    Args:
        destination: English city name, e.g. "Lisbon" or "Kyoto"
    """
    return wikivoyage.get_sections(destination, OVERVIEW_SECTIONS)


@mcp.tool
@friendly_errors
def weather_for_trip(destination: str, start_date: str, end_date: str) -> str:
    """Weather for the trip dates: a live forecast if within ~2 weeks, otherwise typical weather.

    Args:
        destination: "City" or "City, Country", e.g. "Lisbon, Portugal"
        start_date: YYYY-MM-DD
        end_date: YYYY-MM-DD (inclusive, at most 31 days after start)
    """
    return weather.weather_for_trip(destination, start_date, end_date)


@mcp.tool
@friendly_errors
def convert_currency(amount: float, from_currency: str, to_currency: str) -> str:
    """Convert money between currencies using today's exchange rate.

    Args:
        amount: amount of money to convert
        from_currency: ISO code, e.g. "USD"
        to_currency: ISO code, e.g. "EUR"
    """
    return currency.convert(amount, from_currency, to_currency)


@mcp.tool
@friendly_errors
def calculate(expression: str) -> str:
    """Evaluate arithmetic for budget math, e.g. "120 * 5 + 2 * 650".

    Args:
        expression: numbers with + - * / // % ** and parentheses only
    """
    return f"Result: {calculator.evaluate_expression(expression)}"


if __name__ == "__main__":
    mcp.run(show_banner=False)
