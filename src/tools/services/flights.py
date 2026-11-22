"""Flight search via the RapidAPI "Google Flights" API.

The raw API response is ~200KB of JSON per search. We validate inputs,
call the API, and condense the result to a few lines per option so the LLM
gets just what it needs.
"""
import os
import re
from datetime import date

from src.tools.http_client import ExternalServiceError, get_json

FLIGHTS_BASE_URL = "https://google-flights4.p.rapidapi.com/flights"
DEFAULT_RESULT_LIMIT = 6
_IATA_PATTERN = re.compile(r"^[A-Z]{3}$")


def search_oneway(origin: str, destination: str, departure_date: str,
                  limit: int = DEFAULT_RESULT_LIMIT) -> str:
    origin, destination = validate_search(origin, destination, departure_date, None)
    payload = get_json(
        f"{FLIGHTS_BASE_URL}/search-one-way",
        params={"departureId": origin, "arrivalId": destination, "departureDate": departure_date},
        headers=_auth_headers(),
    )
    header = f"One-way flights {origin} → {destination} on {departure_date}:"
    return f"{header}\n{summarize_flights(payload, limit)}"


def search_roundtrip(origin: str, destination: str, departure_date: str, return_date: str,
                     limit: int = DEFAULT_RESULT_LIMIT) -> str:
    origin, destination = validate_search(origin, destination, departure_date, return_date)
    payload = get_json(
        f"{FLIGHTS_BASE_URL}/search-roundtrip",
        params={
            "departureId": origin,
            "arrivalId": destination,
            "departureDate": departure_date,
            # The API names the return leg's date "arrivalDate".
            "arrivalDate": return_date,
        },
        headers=_auth_headers(),
    )
    header = (f"round-trip flights {origin} ⇄ {destination}, out {departure_date}, "
              f"back {return_date}. Prices are the round-trip total; legs shown are outbound:")
    return f"{header}\n{summarize_flights(payload, limit)}"


def validate_search(origin: str, destination: str, departure_date: str,
                    return_date: str | None, today: date | None = None) -> tuple[str, str]:
    """Validate and normalize search inputs. Returns (origin, destination) codes."""
    origin_code = origin.strip().upper()
    destination_code = destination.strip().upper()
    for code in (origin_code, destination_code):
        if not _IATA_PATTERN.match(code):
            raise ValueError(f"{code!r} is not a 3-letter IATA airport code (e.g. JFK, LIS)")
    if origin_code == destination_code:
        raise ValueError("Origin and destination must be different airports")

    current_day = today or date.today()
    departure = _parse_date(departure_date)
    if departure < current_day:
        raise ValueError(f"Departure date {departure_date} is in the past")
    if return_date is not None and _parse_date(return_date) < departure:
        raise ValueError("Return date must be on or after the departure date")
    return origin_code, destination_code


def summarize_flights(payload: dict, limit: int) -> str:
    """Condense an API payload into the cheapest `limit` options, one line each."""
    if not payload.get("status") or payload.get("data") is None:
        details = payload.get("errors") or payload.get("message") or "unknown error"
        raise ExternalServiceError(f"Flight API error: {details}")

    data = payload["data"]
    candidates = [*(data.get("topFlights") or []), *(data.get("otherFlights") or [])]
    priced = [f for f in candidates if _price_of(f) is not None]
    if not priced:
        return "No flights found for this route and date."

    cheapest = sorted(priced, key=_price_of)[:limit]
    lines = [_format_option(flight) for flight in cheapest]
    return "\n".join([*lines, f"({len(priced)} priced options found; showing {len(lines)} cheapest)"])


def _format_option(flight: dict) -> str:
    segments = flight.get("segments") or []
    stops = max(len(segments) - 1, 0)
    if stops == 0:
        stop_text = "nonstop"
    else:
        via = ", ".join(s.get("arrivalAirportCode", "?") for s in segments[:-1])
        stop_text = f"{stops} stop{'s' if stops > 1 else ''} via {via}"
    first, last = (segments[0], segments[-1]) if segments else ({}, {})
    flight_numbers = ", ".join(
        f"{s.get('airline', {}).get('airlineName', '?')} {s.get('airline', {}).get('flightNumber', '')}".strip()
        for s in segments
    )
    return (
        f"- ${_price_of(flight)} | {flight_numbers} | "
        f"{first.get('departureAirportCode', '?')} {first.get('departureTime', '?')} "
        f"({flight.get('departureDate', '?')}) → {last.get('arrivalAirportCode', '?')} "
        f"{last.get('arrivalTime', '?')} ({flight.get('arrivalDate', '?')}) | "
        f"{_format_duration(flight.get('duration'))} | {stop_text}"
    )


def _price_of(flight: dict) -> int | None:
    try:
        return int(flight.get("price"))
    except (TypeError, ValueError):
        return None


def _format_duration(minutes) -> str:
    try:
        hours, mins = divmod(int(minutes), 60)
    except (TypeError, ValueError):
        return "duration unknown"
    return f"{hours}h{mins:02d}m"


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise ValueError(f"Date {value!r} must be in YYYY-MM-DD format") from error


def _auth_headers() -> dict:
    key = os.getenv("RAPIDAPI_KEY")
    host = os.getenv("RAPIDAPI_HOST")
    if not key or not host:
        raise ExternalServiceError("RAPIDAPI_KEY and RAPIDAPI_HOST must be set in .env for flight search")
    return {"x-rapidapi-key": key, "x-rapidapi-host": host}
