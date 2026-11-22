"""Currency conversion using open.er-api.com (free, no API key, daily rates)."""
import re

from src.tools.http_client import ExternalServiceError, get_json

RATES_URL = "https://open.er-api.com/v6/latest/{base}"
_CURRENCY_CODE = re.compile(r"^[A-Z]{3}$")


def convert(amount: float, from_currency: str, to_currency: str) -> str:
    """Convert an amount between ISO 4217 currencies, e.g. USD → EUR."""
    source, target = _normalize(from_currency), _normalize(to_currency)
    if amount < 0:
        raise ValueError("Amount must not be negative")

    payload = get_json(RATES_URL.format(base=source))
    if payload.get("result") != "success":
        raise ExternalServiceError(f"Exchange rate lookup failed: {payload.get('error-type', 'unknown error')}")
    rate = payload.get("rates", {}).get(target)
    if rate is None:
        raise ValueError(f"Unknown currency code {target}")

    updated = payload.get("time_last_update_utc", "recently")
    return f"{amount:,.2f} {source} = {amount * rate:,.2f} {target} (rate {rate:.4f}, updated {updated})"


def _normalize(code: str) -> str:
    normalized = code.strip().upper()
    if not _CURRENCY_CODE.match(normalized):
        raise ValueError(f"{code!r} is not a 3-letter currency code (e.g. USD, EUR, JPY)")
    return normalized
