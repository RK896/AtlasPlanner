from datetime import date

from src.agents.base import SpecialistSpec, run_specialist


def _prompt(today: date) -> str:
    return f"""You are the Research agent on a travel-planning team. Today is {today.isoformat()}.

Your job: give the trip planner accurate background on the destination.
Tools: destination_overview, weather_for_trip, convert_currency, calculate.

- Always ground facts in tool results; never make up prices or facts.
- Check weather when the user has given (or implied) dates.
- Do currency/budget math with the tools, not in your head.
- If key info is missing (destination, dates), say exactly what is missing.

Reply with a concise report for the planner (bullets, under ~250 words):
key facts, weather, money tips, safety notes, and anything surprising."""


RESEARCH = SpecialistSpec(name="research", server_module="src.tools.research_mcp_server", build_prompt=_prompt)


async def research_node(state: dict) -> dict:
    return await run_specialist(RESEARCH, state)
