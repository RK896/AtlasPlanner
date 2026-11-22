"""The master agent: a supervisor that routes work and writes the final answer.

router_node  - decides which specialist to call next (structured output, not
               text tags), with guards against loops
respond_node - turns the specialists' reports into the reply the user sees
"""
import logging
from datetime import date
from typing import Literal

import anthropic
from langchain_core.exceptions import OutputParserException
from langchain_core.messages import AIMessage, SystemMessage
from pydantic import BaseModel, Field, ValidationError

from src.agents.messages import MASTER_NAME, to_llm_messages
from src.utils.llm import build_chat_model, describe_api_error

logger = logging.getLogger("atlas.agents")

SPECIALISTS = ("research", "flights", "hotels", "activities")
RESPOND = "respond"
MAX_SPECIALIST_CALLS_PER_TURN = 4


class RoutingDecision(BaseModel):
    """Which agent should act next."""

    next_agent: Literal["research", "flights", "hotels", "activities", "respond"] = Field(
        description="The specialist to call next, or 'respond' to answer the user now."
    )
    task: str = Field(
        default="",
        description="Specific instruction for that specialist, repeating every known trip detail "
                    "(destination, origin, dates, travellers, budget, interests). Empty for 'respond'.",
    )


def _router_prompt(today: date, visited: list[str]) -> str:
    consulted = ", ".join(visited) if visited else "none yet"
    return f"""You are the lead trip planner coordinating a team of specialists. Today is {today.isoformat()}.

Specialists:
- research: destination overview, weather for the dates, currency and budget math
- flights: live flight prices (needs origin, destination and dates)
- hotels: which neighbourhoods to stay in and typical nightly prices
- activities: sights, things to do, food and drink

Already consulted for the user's latest message: {consulted}.

Choose the ONE next step for the user's latest message:
- Call a specialist whose input is still needed and who hasn't been consulted yet.
- For a full trip plan, typical order: research → flights (only if origin and dates are known)
  → hotels → activities → respond.
- For a narrow question, call only the relevant specialist, then respond.
- Choose 'respond' for small talk, when you must ask the user for missing details
  (e.g. no destination), or once you have what you need."""


def _respond_prompt(today: date) -> str:
    return f"""You are AtlasPlanner, a friendly expert travel planner. Today is {today.isoformat()}.

Write the reply to the user using the specialist reports in the conversation.
- Use only prices, flights, places and facts that appear in the reports. If a specialist
  failed or information is missing, say so plainly instead of filling the gap.
- For a full trip request, use Markdown with these sections: Trip overview, Flights,
  Where to stay, Day-by-day itinerary, Estimated budget, Tips.
- For a narrow question, answer it directly and briefly.
- If important details are missing (origin city, dates, budget, interests), end with
  1-3 short follow-up questions."""


async def router_node(state: dict, model=None, today: date | None = None) -> dict:
    visited = state.get("visited", [])
    if len(visited) >= MAX_SPECIALIST_CALLS_PER_TURN:
        return {"next_agent": RESPOND, "task": ""}

    messages = [
        SystemMessage(content=_router_prompt(today or date.today(), visited)),
        *to_llm_messages(state["messages"]),
    ]
    router = (model or build_chat_model()).with_structured_output(RoutingDecision, method="json_schema")
    try:
        decision = await router.ainvoke(messages)
    except (anthropic.APIError, OutputParserException, ValidationError) as error:
        logger.error("Router failed, answering directly: %s", error)
        return {"next_agent": RESPOND, "task": ""}

    next_agent = decision.next_agent
    if next_agent in visited:
        next_agent = RESPOND  # never run the same specialist twice in one turn
    return {"next_agent": next_agent, "task": decision.task}


async def respond_node(state: dict, model=None, today: date | None = None) -> dict:
    messages = [SystemMessage(content=_respond_prompt(today or date.today())), *to_llm_messages(state["messages"])]
    try:
        response = await (model or build_chat_model()).ainvoke(messages)
        reply = response.text
    except anthropic.APIError as error:
        logger.error("Respond step failed: %s", error)
        reply = f"Sorry, I couldn't finish planning: {describe_api_error(error)}"
    return {"messages": [AIMessage(content=reply, name=MASTER_NAME)]}


def route_from_router(state: dict) -> str:
    """Conditional-edge function: read the router's decision from state."""
    next_agent = state.get("next_agent", RESPOND)
    return next_agent if next_agent in SPECIALISTS else RESPOND
