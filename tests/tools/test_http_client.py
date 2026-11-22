from unittest.mock import MagicMock, patch

import pytest
import requests

from src.tools.http_client import ExternalServiceError, get_json


def _response(status=200, payload=None, json_error=None):
    response = MagicMock()
    response.status_code = status
    if status >= 400:
        response.raise_for_status.side_effect = requests.HTTPError(response=response)
    if json_error:
        response.json.side_effect = json_error
    else:
        response.json.return_value = payload
    return response


@patch("src.tools.http_client.requests.get")
def test_returns_parsed_json_and_sends_user_agent_and_timeout(mock_get):
    mock_get.return_value = _response(payload={"ok": True})

    result = get_json("https://example.test/api", params={"q": "x"}, headers={"k": "v"})

    assert result == {"ok": True}
    _, kwargs = mock_get.call_args
    assert kwargs["params"] == {"q": "x"}
    assert kwargs["headers"]["k"] == "v"
    assert "AtlasPlanner" in kwargs["headers"]["User-Agent"]
    assert kwargs["timeout"] > 0


@patch("src.tools.http_client.requests.get")
def test_wraps_http_errors(mock_get):
    mock_get.return_value = _response(status=503)

    with pytest.raises(ExternalServiceError, match="503"):
        get_json("https://example.test/api")


@patch("src.tools.http_client.requests.get")
def test_wraps_timeouts(mock_get):
    mock_get.side_effect = requests.Timeout()

    with pytest.raises(ExternalServiceError, match="timed out"):
        get_json("https://example.test/api")


@patch("src.tools.http_client.requests.get")
def test_wraps_invalid_json(mock_get):
    mock_get.return_value = _response(json_error=ValueError("bad json"))

    with pytest.raises(ExternalServiceError, match="invalid JSON"):
        get_json("https://example.test/api")
