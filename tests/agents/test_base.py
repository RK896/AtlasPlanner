from datetime import date
from unittest.mock import MagicMock

import anthropic
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool

from src.agents.base import MAX_TOOL_ROUNDS, SpecialistSpec, execute_tool_calls, run_specialist
from tests.agents.fakes import FakeChatModel, tool_call

SPEC = SpecialistSpec(name="hotels", server_module="unused", build_prompt=lambda today: f"Today is {today}")
TODAY = date(2027, 1, 1)


@tool
def where_to_stay(destination: str) -> str:
    """Lodging advice."""
    return f"Stay in Alfama, {destination}"


@tool
def broken(destination: str) -> str:
    """Always fails."""
    raise RuntimeError("server exploded")


def _state(task=None):
    return {"messages": [HumanMessage(content="Hotels in Lisbon?")], "visited": ["research"], "task": task}


async def test_runs_tools_then_returns_single_named_report():
    model = FakeChatModel([
        tool_call("where_to_stay", {"destination": "Lisbon"}),
        AIMessage(content="Best area: Alfama, ~€90/night"),
    ])

    update = await run_specialist(SPEC, _state(), model=model, tools=[where_to_stay], today=TODAY)

    [report] = update["messages"]
    assert report.name == "hotels"
    assert report.content == "Best area: Alfama, ~€90/night"
    assert update["visited"] == ["research", "hotels"]
    second_call = model.calls[1]
    assert isinstance(second_call[-1], ToolMessage)
    assert second_call[-1].content == "Stay in Alfama, Lisbon"


async def test_prompt_includes_date_and_task():
    model = FakeChatModel([AIMessage(content="done")])

    await run_specialist(SPEC, _state(task="Find mid-range hotels"), model=model, tools=[], today=TODAY)

    first_call = model.calls[0]
    assert isinstance(first_call[0], SystemMessage)
    assert "2027-01-01" in first_call[0].content
    assert "Find mid-range hotels" in first_call[-1].content


async def test_stops_after_max_tool_rounds():
    looping = [tool_call("where_to_stay", {"destination": "Lisbon"}, f"c{i}") for i in range(MAX_TOOL_ROUNDS + 1)]
    model = FakeChatModel(looping)

    update = await run_specialist(SPEC, _state(), model=model, tools=[where_to_stay], today=TODAY)

    assert len(model.calls) == MAX_TOOL_ROUNDS + 1
    assert "found nothing useful" in update["messages"][0].content


async def test_api_errors_become_honest_report_instead_of_crash():
    error = anthropic.APIConnectionError(request=MagicMock())
    model = FakeChatModel([error])

    update = await run_specialist(SPEC, _state(), model=model, tools=[], today=TODAY)

    assert "could not complete" in update["messages"][0].content
    assert "Do not invent" in update["messages"][0].content
    assert update["visited"] == ["research", "hotels"]


async def test_tool_exceptions_and_unknown_tools_become_error_tool_messages():
    calls = [
        {"name": "broken", "args": {"destination": "x"}, "id": "a"},
        {"name": "nope", "args": {}, "id": "b"},
        {"name": "where_to_stay", "args": {"destination": "Porto"}, "id": "c"},
    ]

    results = await execute_tool_calls(calls, {"broken": broken, "where_to_stay": where_to_stay})

    assert [r.tool_call_id for r in results] == ["a", "b", "c"]
    assert results[0].status == "error" and "server exploded" in results[0].content
    assert results[1].status == "error" and "unknown tool" in results[1].content
    assert results[2].content == "Stay in Alfama, Porto"


async def test_flattens_mcp_content_blocks():
    @tool
    def mcp_style(destination: str) -> list:
        """Returns MCP-style blocks."""
        return [{"type": "text", "text": "line 1", "id": "x"}, {"type": "text", "text": "line 2"}]

    [result] = await execute_tool_calls([{"name": "mcp_style", "args": {"destination": "x"}, "id": "a"}],
                                        {"mcp_style": mcp_style})

    assert result.content == "line 1\nline 2"
