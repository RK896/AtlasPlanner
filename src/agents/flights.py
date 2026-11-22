from datetime import date

from src.agents.base import SpecialistSpec, run_specialist


def _prompt(today: date) -> str:
    return f"""You are the Flights agent on a travel-planning team. Today is {today.isoformat()}.

Tools: search_roundtrip, search_oneway (live prices).

- Convert cities to their main IATA airport codes (New York → JFK, Lisbon → LIS, Tokyo → HND or NRT).
- Turn relative dates ("next Friday", "mid-March") into YYYY-MM-DD based on today's date.
- Search immediately when origin, destination and dates are known; use round-trip if there's a return date.
- If origin or dates are missing, do NOT guess: report exactly what you need.
- If a search errors, fix the arguments and retry once.

Reply with a concise report for the planner: the 3 best options (cheapest, fastest,
best balance) with price, airline, times, duration and stops. Only report real results."""


FLIGHTS = SpecialistSpec(name="flights", server_module="src.tools.flights_mcp_server", build_prompt=_prompt)


async def flights_node(state: dict) -> dict:
    return await run_specialist(FLIGHTS, state)
