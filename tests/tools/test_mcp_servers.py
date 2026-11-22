"""Each agent's MCP server exposes the expected tools with usable schemas."""
import importlib

import pytest

EXPECTED_TOOLS = {
    "src.tools.research_mcp_server": {"destination_overview", "weather_for_trip", "convert_currency", "calculate"},
    "src.tools.flights_mcp_server": {"search_roundtrip", "search_oneway"},
    "src.tools.hotels_mcp_server": {"where_to_stay", "calculate", "convert_currency"},
    "src.tools.activities_mcp_server": {"things_to_do", "food_and_drink", "weather_for_trip"},
}


@pytest.mark.parametrize(("module_name", "expected"), EXPECTED_TOOLS.items())
async def test_server_registers_expected_tools(module_name, expected):
    server = importlib.import_module(module_name).mcp

    tools = await server.get_tools()

    assert set(tools) == expected
    for tool in tools.values():
        assert tool.description, f"{tool.name} needs a description for the LLM"
        assert tool.parameters["properties"], f"{tool.name} lost its parameter schema"


async def test_shared_calculate_tool_returns_errors_as_text():
    from src.tools.research_mcp_server import mcp

    tool = (await mcp.get_tools())["calculate"]
    result = await tool.run({"expression": "__import__('os')"})

    assert "Error" in result.content[0].text
