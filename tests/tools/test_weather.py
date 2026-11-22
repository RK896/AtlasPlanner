from datetime import date
from unittest.mock import patch

import pytest

from src.tools.services import weather

TODAY = date(2026, 11, 22)

GEOCODE = {
    "results": [
        {"name": "Lisbon", "country": "United States", "latitude": 1.0, "longitude": 2.0},
        {"name": "Lisbon", "country": "Portugal", "latitude": 38.7, "longitude": -9.1},
    ]
}


def _daily(dates, highs, lows, extra_key, extra_values):
    return {"daily": {
        "time": dates,
        "temperature_2m_max": highs,
        "temperature_2m_min": lows,
        extra_key: extra_values,
    }}


def _fake_get_json(forecast=None, archive=None):
    def fake(url, params=None, **_):
        if "geocoding" in url:
            return GEOCODE
        if "archive" in url:
            return archive
        return forecast
    return fake


def test_geocode_prefers_country_hint():
    with patch("src.tools.services.weather.get_json", side_effect=_fake_get_json()) as mock:
        place = weather.geocode("Lisbon, Portugal")

    assert place.country == "Portugal"
    assert mock.call_args.kwargs["params"]["name"] == "Lisbon"


def test_near_term_trip_uses_live_forecast():
    forecast = _daily(["2026-11-24", "2026-11-25"], [17.9, 16.0], [11.6, 11.5],
                      "precipitation_probability_max", [85, 3])
    forecast["daily"]["weather_code"] = [63, 3]
    fake = _fake_get_json(forecast=forecast)

    with patch("src.tools.services.weather.get_json", side_effect=fake) as mock:
        result = weather.weather_for_trip("Lisbon, Portugal", "2026-11-24", "2026-11-25", today=TODAY)

    assert "forecast" in result.lower()
    assert "2026-11-24: 12–18°C, rain, 85% chance of precipitation" in result
    assert "overcast" in result
    assert "forecast" in mock.call_args.args[0]


def test_far_future_trip_uses_last_years_weather_as_typical():
    archive = _daily(["2026-05-10", "2026-05-11"], [18.5, 20.5], [12.0, 11.0],
                     "precipitation_sum", [0.7, 0.0])
    fake = _fake_get_json(archive=archive)

    with patch("src.tools.services.weather.get_json", side_effect=fake) as mock:
        result = weather.weather_for_trip("Lisbon", "2027-05-10", "2027-05-11", today=TODAY)

    params = mock.call_args.kwargs["params"]
    assert params["start_date"] == "2026-05-10"
    assert params["end_date"] == "2026-05-11"
    assert "typical" in result.lower()
    assert "avg high 20°C" in result
    assert "1 day(s) with rain" in result


@pytest.mark.parametrize(
    ("start", "end", "message"),
    [
        ("2026-12-10", "2026-12-01", "after"),
        ("2026-12-01", "2027-03-01", "at most"),
        ("Dec 1", "2026-12-05", "YYYY-MM-DD"),
    ],
)
def test_rejects_bad_date_ranges(start, end, message):
    with pytest.raises(ValueError, match=message):
        weather.weather_for_trip("Lisbon", start, end, today=TODAY)


def test_unknown_place_raises():
    with patch("src.tools.services.weather.get_json", return_value={}):
        with pytest.raises(ValueError, match="Could not find"):
            weather.geocode("Atlantis")


def test_shift_year_handles_leap_day():
    assert weather.shift_back_years(date(2028, 2, 29), 1) == date(2027, 2, 28)
