from unittest.mock import patch

import pytest

from src.tools.http_client import ExternalServiceError
from src.tools.services import currency

RATES = {"result": "success", "time_last_update_utc": "Sun, 22 Nov 2026", "rates": {"USD": 1, "EUR": 0.9}}


@patch("src.tools.services.currency.get_json", return_value=RATES)
def test_converts_amount_using_live_rate(mock_get_json):
    result = currency.convert(100, "usd", "eur")

    assert "100.00 USD = 90.00 EUR" in result
    assert mock_get_json.call_args.args[0].endswith("/USD")


@patch("src.tools.services.currency.get_json", return_value=RATES)
def test_unknown_target_currency_raises(mock_get_json):
    with pytest.raises(ValueError, match="XYZ"):
        currency.convert(10, "USD", "XYZ")


@patch("src.tools.services.currency.get_json", return_value={"result": "error", "error-type": "unsupported-code"})
def test_api_error_raises(mock_get_json):
    with pytest.raises(ExternalServiceError, match="unsupported-code"):
        currency.convert(10, "QQQ", "USD")


@pytest.mark.parametrize(("amount", "source"), [(-1, "USD"), (10, "DOLLARS")])
def test_validates_inputs(amount, source):
    with pytest.raises(ValueError):
        currency.convert(amount, source, "EUR")
