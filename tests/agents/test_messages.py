from langchain_core.messages import AIMessage, HumanMessage

from src.agents.messages import is_specialist_report, to_llm_messages


def test_specialist_reports_become_user_role_reports():
    history = [
        HumanMessage(content="Plan Lisbon"),
        AIMessage(content="Flights from $350", name="flights"),
    ]

    result = to_llm_messages(history)

    assert isinstance(result[-1], HumanMessage)
    assert result[-1].content.startswith("[Report from the flights agent]")
    assert "Flights from $350" in result[-1].content


def test_master_replies_stay_assistant_messages():
    history = [HumanMessage(content="hi"), AIMessage(content="Hello!", name="master")]

    result = to_llm_messages(history)

    assert isinstance(result[-1], AIMessage)
    assert result[-1].content == "Hello!"


def test_task_is_appended_as_final_user_message():
    result = to_llm_messages([HumanMessage(content="hi")], task="Find hotels in Lisbon")

    assert isinstance(result[-1], HumanMessage)
    assert "Find hotels in Lisbon" in result[-1].content


def test_drops_empty_messages_and_flattens_block_content():
    history = [
        HumanMessage(content="hi"),
        AIMessage(content=""),
        AIMessage(content=[{"type": "text", "text": "Hello"}, {"type": "tool_use", "id": "1", "name": "x", "input": {}}],
                  name="master"),
    ]

    result = to_llm_messages(history)

    assert len(result) == 2
    assert result[-1].content == "Hello"


def test_does_not_mutate_input_history():
    report = AIMessage(content="data", name="hotels")
    history = [report]

    to_llm_messages(history)

    assert history == [report]
    assert report.content == "data"


def test_is_specialist_report():
    assert is_specialist_report(AIMessage(content="x", name="research"))
    assert not is_specialist_report(AIMessage(content="x", name="master"))
    assert not is_specialist_report(AIMessage(content="x"))
    assert not is_specialist_report(HumanMessage(content="x", name="research"))
