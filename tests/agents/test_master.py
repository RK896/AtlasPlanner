from datetime import date
from unittest.mock import MagicMock

import anthropic
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from src.agents.master import (
    MAX_SPECIALIST_CALLS_PER_TURN,
    RoutingDecision,
    respond_node,
    router_node,
)
from tests.agents.fakes import FakeChatModel

TODAY = date(2027, 1, 1)


def _state(visited=None, messages=None):
    return {
        "messages": messages or [HumanMessage(content="Plan 4 days in Lisbon from JFK, Mar 3-7")],
        "visited": visited or [],
    }


async def test_router_returns_decision_and_task():
    model = FakeChatModel([RoutingDecision(next_agent="flights", task="JFK→LIS 2027-03-03 to 03-07")])

    update = await router_node(_state(visited=["research"]), model=model, today=TODAY)

    assert update == {"next_agent": "flights", "task": "JFK→LIS 2027-03-03 to 03-07"}
    system_prompt = model.calls[0][0]
    assert isinstance(system_prompt, SystemMessage)
    assert "research" in system_prompt.content  # tells the router who already ran
    assert "2027-01-01" in system_prompt.content


async def test_router_never_repeats_an_agent_in_the_same_turn():
    model = FakeChatModel([RoutingDecision(next_agent="research", task="again")])

    update = await router_node(_state(visited=["research"]), model=model, today=TODAY)

    assert update["next_agent"] == "respond"


async def test_router_stops_after_hop_limit_without_calling_llm():
    model = FakeChatModel([])
    visited = ["research", "flights", "hotels", "activities"][:MAX_SPECIALIST_CALLS_PER_TURN]

    update = await router_node(_state(visited=visited), model=model, today=TODAY)

    assert update["next_agent"] == "respond"
    assert model.calls == []


async def test_router_falls_back_to_respond_on_api_error():
    model = FakeChatModel([anthropic.APIConnectionError(request=MagicMock())])

    update = await router_node(_state(), model=model, today=TODAY)

    assert update["next_agent"] == "respond"


async def test_respond_writes_master_reply_from_reports():
    history = [
        HumanMessage(content="Lisbon trip"),
        AIMessage(content="Flights from $350", name="flights"),
    ]
    model = FakeChatModel([AIMessage(content="# Your Lisbon trip")])

    update = await respond_node({"messages": history, "visited": ["flights"]}, model=model, today=TODAY)

    [reply] = update["messages"]
    assert reply.name == "master"
    assert reply.content == "# Your Lisbon trip"
    sent = model.calls[0]
    assert isinstance(sent[-1], HumanMessage)  # request must end on a user turn
    assert "Flights from $350" in sent[-1].content


async def test_respond_degrades_gracefully_on_api_error():
    model = FakeChatModel([anthropic.APIConnectionError(request=MagicMock())])

    update = await respond_node(_state(), model=model, today=TODAY)

    assert "try again" in update["messages"][0].content.lower()
