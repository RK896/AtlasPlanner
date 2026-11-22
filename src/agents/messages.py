"""Turn the shared conversation into what each LLM call should see.

Specialist agents store their findings as AIMessages tagged with their name
(e.g. name="flights"). To the next LLM call those are *inputs*, not things it
said itself, so we hand them over as user-role "report" messages. That also
guarantees every request ends on a user turn (newer Claude models reject
requests that end on an assistant turn).
"""
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

MASTER_NAME = "master"


def is_specialist_report(message: BaseMessage) -> bool:
    return isinstance(message, AIMessage) and bool(message.name) and message.name != MASTER_NAME


def to_llm_messages(messages: list[BaseMessage], task: str | None = None) -> list[BaseMessage]:
    """Convert conversation history into LLM input, optionally ending with a task."""
    converted = [_convert(message) for message in messages if _text_of(message)]
    if task:
        converted = [*converted, HumanMessage(content=f"[Task from the trip planner]\n{task}")]
    return converted


def _convert(message: BaseMessage) -> BaseMessage:
    if is_specialist_report(message):
        return HumanMessage(content=f"[Report from the {message.name} agent]\n{_text_of(message)}")
    if isinstance(message, AIMessage):
        return AIMessage(content=_text_of(message), name=message.name)
    return message


def _text_of(message: BaseMessage) -> str:
    return message.text if isinstance(message.content, list) else str(message.content)
