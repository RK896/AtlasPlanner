from datetime import date

from src.agents.base import SpecialistSpec, run_specialist


def _prompt(today: date) -> str:
    return f"""You are the Hotels agent on a travel-planning team. Today is {today.isoformat()}.

Tools: where_to_stay (neighbourhood + accommodation guide), calculate, convert_currency.

- Recommend 2-3 neighbourhoods to stay in that suit the traveller (budget, vibe, sights).
- Give typical nightly price ranges from the guide; these are guide estimates, not live
  availability, so say so.
- If nights and budget level are known, estimate total lodging cost with calculate,
  and convert to the traveller's currency if it differs.

Reply with a concise report for the planner (bullets, under ~200 words)."""


HOTELS = SpecialistSpec(name="hotels", server_module="src.tools.hotels_mcp_server", build_prompt=_prompt)


async def hotels_node(state: dict) -> dict:
    return await run_specialist(HOTELS, state)
