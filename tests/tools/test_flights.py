from datetime import date
from unittest.mock import patch

import pytest

from src.tools.http_client import ExternalServiceError
from src.tools.services import flights

TODAY = date(2027, 1, 1)


def _segment(dep, arr, airline, number, dep_time="10:00", arr_time="18:00"):
    return {
        "departureAirportCode": dep,
        "arrivalAirportCode": arr,
        "departureTime": dep_time,
        "arrivalTime": arr_time,
        "airline": {"airlineName": airline, "flightNumber": number},
    }


def _flight(price, segments, duration=425, dep_date="2027-01-15", arr_date="2027-01-16"):
    return {
        "price": price,
        "duration": duration,
        "departureDate": dep_date,
        "arrivalDate": arr_date,
        "airlineNames": sorted({s["airline"]["airlineName"] for s in segments}),
        "segments": segments,
        "detailToken": "x" * 500,  # big opaque blobs like this must not reach the LLM
    }


SAMPLE_PAYLOAD = {
    "status": True,
    "data": {
        "topFlights": [
            _flight(404, [_segment("JFK", "LIS", "TAP Air Portugal", "210", "22:00", "10:05")]),
        ],
        "otherFlights": [
            _flight("502", [
                _segment("JFK", "KEF", "Icelandair", "614"),
                _segment("KEF", "LIS", "Icelandair", "550"),
            ], duration=900),
            _flight(350, [
                _segment("JFK", "DUB", "Aer Lingus", "106"),
                _segment("DUB", "LIS", "Aer Lingus", "480"),
            ], duration=730),
            _flight(None, [_segment("JFK", "LIS", "Mystery Air", "1")]),
        ],
        "priceHistory": [[1, 2]] * 60,
    },
}


def test_summary_sorts_by_price_and_drops_unpriced_options():
    summary = flights.summarize_flights(SAMPLE_PAYLOAD, limit=5)

    lines = [line for line in summary.splitlines() if line.startswith("- $")]
    assert [line.split()[1] for line in lines] == ["$350", "$404", "$502"]
    assert "Mystery Air" not in summary


def test_summary_shows_route_stops_and_duration():
    summary = flights.summarize_flights(SAMPLE_PAYLOAD, limit=5)

    assert "Aer Lingus EI" not in summary  # we don't invent airline codes
    assert "1 stop via DUB" in summary
    assert "nonstop" in summary
    assert "7h05m" in summary
    assert "TAP Air Portugal 210" in summary


def test_summary_respects_limit_and_is_compact():
    summary = flights.summarize_flights(SAMPLE_PAYLOAD, limit=1)

    assert summary.count("- $") == 1
    assert "xxxxx" not in summary
    assert len(summary) < 1000


def test_summary_handles_no_results():
    payload = {"status": True, "data": {"topFlights": [], "otherFlights": []}}
    assert "No flights found" in flights.summarize_flights(payload, limit=5)


def test_api_level_errors_raise():
    payload = {"status": False, "data": None, "errors": {"arrivalDate": "arrivalDate is required"}}
    with pytest.raises(ExternalServiceError, match="arrivalDate"):
        flights.summarize_flights(payload, limit=5)


@pytest.mark.parametrize(
    ("origin", "destination", "departure", "return_date", "message"),
    [
        ("JF", "LIS", "2027-01-15", None, "IATA"),
        ("JFK", "lisbon", "2027-01-15", None, "IATA"),
        ("JFK", "LIS", "15/01/2027", None, "YYYY-MM-DD"),
        ("JFK", "LIS", "2026-12-01", None, "past"),
        ("JFK", "LIS", "2027-01-15", "2027-01-10", "after"),
        ("JFK", "JFK", "2027-01-15", None, "different"),
    ],
)
def test_validates_search_inputs(origin, destination, departure, return_date, message):
    with pytest.raises(ValueError, match=message):
        flights.validate_search(origin, destination, departure, return_date, today=TODAY)


def test_validation_normalizes_airport_codes():
    assert flights.validate_search("jfk", " lis ", "2027-01-15", None, today=TODAY) == ("JFK", "LIS")


@patch.dict("os.environ", {"RAPIDAPI_KEY": "k", "RAPIDAPI_HOST": "h"})
@patch("src.tools.services.flights.get_json", return_value=SAMPLE_PAYLOAD)
def test_roundtrip_sends_arrival_date_param(mock_get_json):
    result = flights.search_roundtrip("JFK", "LIS", "2099-01-15", "2099-01-22")

    _, kwargs = mock_get_json.call_args
    assert kwargs["params"] == {
        "departureId": "JFK",
        "arrivalId": "LIS",
        "departureDate": "2099-01-15",
        "arrivalDate": "2099-01-22",
    }
    assert kwargs["headers"] == {"x-rapidapi-key": "k", "x-rapidapi-host": "h"}
    assert "round-trip" in result


@patch.dict("os.environ", {"RAPIDAPI_KEY": "k", "RAPIDAPI_HOST": "h"})
@patch("src.tools.services.flights.get_json", return_value=SAMPLE_PAYLOAD)
def test_oneway_calls_one_way_endpoint(mock_get_json):
    flights.search_oneway("JFK", "LIS", "2099-01-15")

    url = mock_get_json.call_args.args[0]
    assert url.endswith("/search-one-way")


@patch.dict("os.environ", {"RAPIDAPI_KEY": "", "RAPIDAPI_HOST": ""}, clear=False)
def test_missing_credentials_raise_clear_error():
    with pytest.raises(ExternalServiceError, match="RAPIDAPI_KEY"):
        flights.search_oneway("JFK", "LIS", "2099-01-15")
