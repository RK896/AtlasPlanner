"""MCP server exposing destination research tools to the Research agent."""
from fastmcp import FastMCP

from src.tools import shared_tools
from src.tools.mcp_helpers import friendly_errors
from src.tools.services import wikivoyage

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


shared_tools.register(
    mcp,
    shared_tools.weather_for_trip,
    shared_tools.convert_currency,
    shared_tools.calculate,
)

if __name__ == "__main__":
    mcp.run(show_banner=False)
