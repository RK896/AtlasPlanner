"""End-to-end graph runs with a scripted fake LLM (no network, no MCP)."""
import pytest
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.memory import InMemorySaver

from src.agents.master import RoutingDecision
from src.graph import workflow
from tests.agents.fakes import FakeChatModel


@pytest.fixture
def fake_llm(monkeypatch):
    def install(responses):
        model = FakeChatModel(responses)
        monkeypatch.setattr("src.agents.master.build_chat_model", lambda: model)
        monkeypatch.setattr("src.agents.base.build_chat_model", lambda: model)

        async def no_tools(spec):
            return []

        monkeypatch.setattr("src.agents.base.load_tools", no_tools)
        return model

    return install


async def test_multi_agent_turn_runs_specialists_then_responds(fake_llm):
    fake_llm([
        RoutingDecision(next_agent="research", task="Lisbon basics"),
        AIMessage(content="Lisbon is hilly"),
        RoutingDecision(next_agent="hotels", task="Lisbon hotels"),
        AIMessage(content="Stay in Alfama"),
        RoutingDecision(next_agent="respond", task=""),
        AIMessage(content="Here is your plan"),
    ])
    app = workflow.compile_app()

    result = await app.ainvoke({"messages": [HumanMessage(content="Plan Lisbon")], "visited": []})

    names = [m.name for m in result["messages"]]
    assert names == [None, "research", "hotels", "master"]
    assert result["messages"][-1].content == "Here is your plan"
    assert result["visited"] == ["research", "hotels"]


async def test_casual_chat_goes_straight_to_respond(fake_llm):
    model = fake_llm([
        RoutingDecision(next_agent="respond", task=""),
        AIMessage(content="Hi! Where would you like to go?"),
    ])
    app = workflow.compile_app()

    result = await app.ainvoke({"messages": [HumanMessage(content="hello")], "visited": []})

    assert result["messages"][-1].content == "Hi! Where would you like to go?"
    assert len(model.calls) == 2


async def test_checkpointer_remembers_conversation_across_turns(fake_llm):
    model = fake_llm([
        RoutingDecision(next_agent="respond", task=""),
        AIMessage(content="Lisbon is great"),
        RoutingDecision(next_agent="respond", task=""),
        AIMessage(content="Still Lisbon"),
    ])
    app = workflow.compile_app(checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "t1"}}

    await app.ainvoke({"messages": [HumanMessage(content="Lisbon?")], "visited": []}, config)
    result = await app.ainvoke({"messages": [HumanMessage(content="And food?")], "visited": []}, config)

    assert len(result["messages"]) == 4
    last_router_input = model.calls[2]
    assert any("Lisbon?" in str(m.content) for m in last_router_input)


def test_graph_has_expected_nodes():
    nodes = set(workflow.build_graph().nodes)
    assert nodes == {"router", "research", "flights", "hotels", "activities", "respond"}
