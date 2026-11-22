"""Test doubles for LLMs so agent logic can be tested without API calls."""
from langchain_core.messages import AIMessage


class FakeChatModel:
    """Returns scripted responses in order and records every call."""

    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []
        self.bound_tools = None

    def bind_tools(self, tools):
        self.bound_tools = tools
        return self

    def with_structured_output(self, schema, **_):
        return self

    async def ainvoke(self, messages):
        self.calls.append(messages)
        response = self._responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def tool_call(name, args, call_id="call_1"):
    return AIMessage(content="", tool_calls=[{"name": name, "args": args, "id": call_id}])
