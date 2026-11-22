"""Tools that more than one agent's MCP server exposes."""
from fastmcp import FastMCP

from src.tools.mcp_helpers import friendly_errors
from src.tools.services import calculator, currency, weather


def calculate(expression: str) -> str:
    """Evaluate arithmetic for budget math, e.g. "120 * 5 + 2 * 650".

    Args:
        expression: numbers with + - * / // % ** and parentheses only
    """
    return f"Result: {calculator.evaluate_expression(expression)}"


def convert_currency(amount: float, from_currency: str, to_currency: str) -> str:
    """Convert money between currencies using today's exchange rate.

    Args:
        amount: amount of money to convert
        from_currency: ISO code, e.g. "USD"
        to_currency: ISO code, e.g. "EUR"
    """
    return currency.convert(amount, from_currency, to_currency)


def weather_for_trip(destination: str, start_date: str, end_date: str) -> str:
    """Weather for the trip dates: a live forecast if within ~2 weeks, otherwise typical weather.

    Args:
        destination: "City" or "City, Country", e.g. "Lisbon, Portugal"
        start_date: YYYY-MM-DD
        end_date: YYYY-MM-DD (inclusive, at most 31 days after start)
    """
    return weather.weather_for_trip(destination, start_date, end_date)


def register(mcp: FastMCP, *tools) -> None:
    """Register plain functions as MCP tools with friendly error handling."""
    for tool in tools:
        mcp.tool(friendly_errors(tool))
