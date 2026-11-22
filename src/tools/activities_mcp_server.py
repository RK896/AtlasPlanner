"""MCP server exposing sightseeing and food tools to the Activities agent."""
from fastmcp import FastMCP

from src.tools import shared_tools
from src.tools.mcp_helpers import friendly_errors
from src.tools.services import wikivoyage

mcp = FastMCP("activities")


@mcp.tool
@friendly_errors
def things_to_do(destination: str) -> str:
    """Sights, attractions and activities in a city from its travel guide.

    Args:
        destination: English city name, e.g. "Kyoto"
    """
    return wikivoyage.get_sections(destination, ["See", "Do"])


@mcp.tool
@friendly_errors
def food_and_drink(destination: str) -> str:
    """Local food, restaurants and nightlife in a city from its travel guide.

    Args:
        destination: English city name, e.g. "Kyoto"
    """
    return wikivoyage.get_sections(destination, ["Eat", "Drink"])


shared_tools.register(mcp, shared_tools.weather_for_trip)

if __name__ == "__main__":
    mcp.run(show_banner=False)
