"""MCP server exposing accommodation tools to the Hotels agent."""
from fastmcp import FastMCP

from src.tools import shared_tools
from src.tools.mcp_helpers import friendly_errors
from src.tools.services import wikivoyage

mcp = FastMCP("hotels")

LODGING_SECTIONS = ["Districts", "Sleep"]


@mcp.tool
@friendly_errors
def where_to_stay(destination: str) -> str:
    """Neighbourhoods and accommodation advice for a city, with typical price levels.

    Comes from the city's travel guide (districts + "Sleep" section). Not live
    availability or booking prices.

    Args:
        destination: English city name, e.g. "Lisbon"
    """
    return wikivoyage.get_sections(destination, LODGING_SECTIONS)


shared_tools.register(mcp, shared_tools.calculate, shared_tools.convert_currency)

if __name__ == "__main__":
    mcp.run(show_banner=False)
