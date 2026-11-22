"""Shared engine for specialist agents (research, flights, hotels, activities).

Every specialist does the same thing:
  1. load its tools from its own MCP server
  2. let Claude call tools (possibly several rounds, in parallel)
  3. write ONE concise report back into the shared conversation

Only the final report goes into graph state. The raw tool calls/results
stay local, which keeps the shared context small and readable.
"""
import asyncio
import logging
import os
import sys
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date

import anthropic
from langchain_core.messages import AIMessage, BaseMessage, SystemMessage, ToolMessage
from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient

from src.agents.messages import to_llm_messages
from src.utils.config import PROJECT_ROOT
from src.utils.llm import build_chat_model, describe_api_error

logger = logging.getLogger("atlas.agents")

MAX_TOOL_ROUNDS = 5

_tool_cache: dict[str, list[BaseTool]] = {}


class ToolLoadError(Exception):
    """A specialist's MCP server could not be started or listed."""


@dataclass(frozen=True)
class SpecialistSpec:
    name: str
    server_module: str
    build_prompt: Callable[[date], str]


async def load_tools(spec: SpecialistSpec) -> list[BaseTool]:
    """Start the specialist's MCP server and fetch its tools (cached per agent)."""
    if spec.name in _tool_cache:
        return _tool_cache[spec.name]
    client = MultiServerMCPClient({
        spec.name: {
            "transport": "stdio",
            "command": sys.executable,  # same venv interpreter as the app
            "args": ["-m", spec.server_module],
            "cwd": str(PROJECT_ROOT),
            "env": {**os.environ, "FASTMCP_LOG_LEVEL": "WARNING"},
        }
    })
    try:
        tools = await client.get_tools()
    except Exception as error:  # boundary: subprocess / protocol failures vary widely
        raise ToolLoadError(f"Could not start the {spec.name} tool server: {error}") from error
    _tool_cache[spec.name] = tools
    return tools


async def run_specialist(spec: SpecialistSpec, state: dict, model=None,
                         tools: list[BaseTool] | None = None, today: date | None = None) -> dict:
    """Run one specialist turn and return a state update with its report."""
    try:
        available_tools = tools if tools is not None else await load_tools(spec)
        report = await _research(spec, state, model or build_chat_model(), available_tools,
                                 today or date.today())
    except (ToolLoadError, anthropic.APIError) as error:
        logger.error("%s agent failed: %s", spec.name, error)
        reason = describe_api_error(error) if isinstance(error, anthropic.APIError) else str(error)
        report = f"The {spec.name} agent could not complete its task: {reason} Do not invent its results."

    return {
        "messages": [AIMessage(content=report, name=spec.name)],
        "visited": [*state.get("visited", []), spec.name],
    }


async def _research(spec: SpecialistSpec, state: dict, model, tools: list[BaseTool], today: date) -> str:
    llm = model.bind_tools(tools)
    tools_by_name = {tool.name: tool for tool in tools}
    messages: list[BaseMessage] = [
        SystemMessage(content=spec.build_prompt(today)),
        *to_llm_messages(state["messages"], state.get("task")),
    ]

    response = await llm.ainvoke(messages)
    for _ in range(MAX_TOOL_ROUNDS):
        if not response.tool_calls:
            break
        tool_messages = await execute_tool_calls(response.tool_calls, tools_by_name)
        messages = [*messages, response, *tool_messages]
        response = await llm.ainvoke(messages)

    if response.tool_calls:
        logger.warning("%s agent hit the %d tool-round limit", spec.name, MAX_TOOL_ROUNDS)
    return response.text or f"The {spec.name} agent found nothing useful."


async def execute_tool_calls(tool_calls: list[dict], tools_by_name: dict[str, BaseTool]) -> list[ToolMessage]:
    """Run all tool calls from one response concurrently."""
    return list(await asyncio.gather(*(_run_tool(call, tools_by_name) for call in tool_calls)))


async def _run_tool(call: dict, tools_by_name: dict[str, BaseTool]) -> ToolMessage:
    tool = tools_by_name.get(call["name"])
    if tool is None:
        return ToolMessage(content=f"Error: unknown tool {call['name']}", tool_call_id=call["id"], status="error")
    try:
        result = await tool.ainvoke(call["args"])
    except Exception as error:  # boundary: tool failures must go back to the model, not crash the graph
        logger.warning("Tool %s raised: %s", call["name"], error)
        return ToolMessage(content=f"Error: {error}", tool_call_id=call["id"], status="error")
    return ToolMessage(content=_result_text(result), tool_call_id=call["id"])


def _result_text(result) -> str:
    """MCP tools return a list of content blocks; plain tools return a string."""
    if isinstance(result, list):
        return "\n".join(block.get("text", "") for block in result if isinstance(block, dict))
    return str(result)
