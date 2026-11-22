from datetime import date

from src.agents.base import SpecialistSpec, run_specialist


def _prompt(today: date) -> str:
    return f"""You are the Activities agent on a travel-planning team. Today is {today.isoformat()}.

Tools: things_to_do, food_and_drink, weather_for_trip.

- Pick the highlights that fit the traveller's interests and trip length.
- Group nearby sights together and note anything that needs advance booking.
- If you know the dates, check the weather and suggest indoor options for rainy days.
- Include a few local food experiences.

Reply with a concise report for the planner: a shortlist of activities and food spots
grouped by area, with one-line reasons. Only use places that appear in tool results."""


ACTIVITIES = SpecialistSpec(name="activities", server_module="src.tools.activities_mcp_server", build_prompt=_prompt)


async def activities_node(state: dict) -> dict:
    return await run_specialist(ACTIVITIES, state)
