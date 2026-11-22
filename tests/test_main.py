from unittest.mock import MagicMock

from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import InMemorySaver

from src import main
from src.agents.master import RoutingDecision
from src.graph import workflow
from tests.agents.fakes import FakeChatModel


def test_show_progress_updates_spinner_for_router_decisions():
    status = MagicMock()

    result = main.show_progress("router", {"next_agent": "flights", "task": "JFK to LIS"}, status)

    assert result is None
    assert "flights agent: JFK to LIS" in status.update.call_args.args[0]


def test_show_progress_returns_final_reply():
    update = {"messages": [AIMessage(content="Your plan", name="master")]}

    assert main.show_progress("respond", update, MagicMock()) == "Your plan"


async def test_run_turn_and_resume_last_reply(monkeypatch):
    model = FakeChatModel([RoutingDecision(next_agent="respond"), AIMessage(content="Plan ready")])
    monkeypatch.setattr("src.agents.master.build_chat_model", lambda: model)
    app = workflow.compile_app(checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "s1"}}

    reply = await main.run_turn(app, config, "Plan Lisbon")
    last_reply, count = await main.last_master_reply(app, config)

    assert reply == "Plan ready"
    assert last_reply == "Plan ready"
    assert count == 2


async def test_last_master_reply_for_new_session_is_empty():
    app = workflow.compile_app(checkpointer=InMemorySaver())

    assert await main.last_master_reply(app, {"configurable": {"thread_id": "new"}}) == ("", 0)


def test_handle_save_writes_file(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "ITINERARY_DIR", tmp_path / "itineraries")
    monkeypatch.setattr(main, "PROJECT_ROOT", tmp_path)

    main.handle_save("lisbon", "# Lisbon plan", "trip-abc")

    [saved] = (tmp_path / "itineraries").iterdir()
    assert saved.name.startswith("lisbon-")


def test_new_session_ids_are_unique():
    assert main.new_session_id() != main.new_session_id()

