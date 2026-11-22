"""Trip weather from Open-Meteo (free, no API key).

Trips within the forecast window get a live daily forecast. Trips further out
get the same calendar dates from the most recent past year as a
"what it's typically like" guide.
"""
from dataclasses import dataclass
from datetime import date, timedelta

from src.tools.http_client import get_json

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
FORECAST_HORIZON_DAYS = 15
MAX_TRIP_DAYS = 31
RAIN_THRESHOLD_MM = 0.5
GEOCODE_CANDIDATES = 5

# Subset of WMO weather codes, grouped into plain-English buckets.
_WEATHER_CODES = {
    0: "clear", 1: "mostly clear", 2: "partly cloudy", 3: "overcast",
    45: "fog", 48: "fog",
    51: "drizzle", 53: "drizzle", 55: "drizzle",
    61: "light rain", 63: "rain", 65: "heavy rain",
    71: "light snow", 73: "snow", 75: "heavy snow",
    80: "showers", 81: "showers", 82: "heavy showers",
    95: "thunderstorms", 96: "thunderstorms", 99: "thunderstorms",
}


@dataclass(frozen=True)
class Place:
    name: str
    country: str
    latitude: float
    longitude: float


def weather_for_trip(destination: str, start_date: str, end_date: str,
                     today: date | None = None) -> str:
    """Describe the weather for a destination between two dates (inclusive)."""
    start, end = _parse_date(start_date), _parse_date(end_date)
    if end < start:
        raise ValueError("End date must be on or after the start date")
    if (end - start).days + 1 > MAX_TRIP_DAYS:
        raise ValueError(f"Date range can cover at most {MAX_TRIP_DAYS} days")

    current_day = today or date.today()
    place = geocode(destination)
    if start >= current_day and end <= current_day + timedelta(days=FORECAST_HORIZON_DAYS):
        return _live_forecast(place, start, end)
    return _typical_weather(place, start, end, current_day)


def geocode(destination: str) -> Place:
    """Resolve "City" or "City, Country" to coordinates."""
    city, _, country_hint = destination.partition(",")
    payload = get_json(GEOCODE_URL, params={"name": city.strip(), "count": GEOCODE_CANDIDATES})
    results = payload.get("results") or []
    if not results:
        raise ValueError(f"Could not find a place called {destination!r}")
    hint = country_hint.strip().lower()
    match = next((r for r in results if hint and r.get("country", "").lower() == hint), results[0])
    return Place(match["name"], match.get("country", ""), match["latitude"], match["longitude"])


def shift_back_years(day: date, years: int) -> date:
    """Same calendar date `years` earlier (Feb 29 falls back to Feb 28)."""
    try:
        return day.replace(year=day.year - years)
    except ValueError:
        return day.replace(year=day.year - years, day=28)


def _live_forecast(place: Place, start: date, end: date) -> str:
    daily = get_json(FORECAST_URL, params={
        **_coordinates(place),
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,weather_code",
        "timezone": "auto",
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
    })["daily"]
    lines = [
        f"- {day}: {round(low)}–{round(high)}°C, {_WEATHER_CODES.get(code, 'mixed')}, "
        f"{rain}% chance of precipitation"
        for day, high, low, rain, code in zip(
            daily["time"], daily["temperature_2m_max"], daily["temperature_2m_min"],
            daily["precipitation_probability_max"], daily["weather_code"],
        )
    ]
    return "\n".join([f"Live forecast for {place.name}, {place.country}:", *lines])


def _typical_weather(place: Place, start: date, end: date, today: date) -> str:
    years_back = 1
    while shift_back_years(end, years_back) >= today:
        years_back += 1
    past_start, past_end = shift_back_years(start, years_back), shift_back_years(end, years_back)

    daily = get_json(ARCHIVE_URL, params={
        **_coordinates(place),
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "timezone": "auto",
        "start_date": past_start.isoformat(),
        "end_date": past_end.isoformat(),
    })["daily"]
    highs = [v for v in daily["temperature_2m_max"] if v is not None]
    lows = [v for v in daily["temperature_2m_min"] if v is not None]
    rain_days = sum(1 for mm in daily["precipitation_sum"] if mm is not None and mm >= RAIN_THRESHOLD_MM)
    if not highs or not lows:
        raise ValueError(f"No historical weather data available for {place.name}")
    return (
        f"Typical weather for {place.name}, {place.country} on these dates "
        f"(based on {past_start.year}; too far ahead for a live forecast): "
        f"avg high {round(sum(highs) / len(highs))}°C, avg low {round(sum(lows) / len(lows))}°C, "
        f"{rain_days} day(s) with rain out of {len(highs)}."
    )


def _coordinates(place: Place) -> dict:
    return {"latitude": place.latitude, "longitude": place.longitude}


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise ValueError(f"Date {value!r} must be in YYYY-MM-DD format") from error
