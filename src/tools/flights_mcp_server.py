"""MCP server exposing flight search tools to the Flights agent."""
from dotenv import load_dotenv
from fastmcp import FastMCP

from src.tools.mcp_helpers import friendly_errors
from src.tools.services import flights
from src.utils.config import ENV_PATH

load_dotenv(ENV_PATH)
mcp = FastMCP("flights")


@mcp.tool
@friendly_errors
def search_roundtrip(origin: str, destination: str, departure_date: str, return_date: str) -> str:
    """Search round-trip flights and return the cheapest options.

    Args:
        origin: 3-letter IATA airport code, e.g. "JFK"
        destination: 3-letter IATA airport code, e.g. "LIS"
        departure_date: outbound date, YYYY-MM-DD
        return_date: return date, YYYY-MM-DD
    """
    return flights.search_roundtrip(origin, destination, departure_date, return_date)


@mcp.tool
@friendly_errors
def search_oneway(origin: str, destination: str, departure_date: str) -> str:
    """Search one-way flights and return the cheapest options.

    Args:
        origin: 3-letter IATA airport code, e.g. "JFK"
        destination: 3-letter IATA airport code, e.g. "LIS"
        departure_date: date, YYYY-MM-DD
    """
    return flights.search_oneway(origin, destination, departure_date)


if __name__ == "__main__":
    mcp.run(show_banner=False)
