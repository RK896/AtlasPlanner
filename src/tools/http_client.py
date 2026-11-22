"""Shared HTTP helper: timeouts, a polite User-Agent, and one error type."""
import requests

DEFAULT_TIMEOUT_SECONDS = 20
USER_AGENT = "AtlasPlanner/1.0 (educational multi-agent travel planner)"


class ExternalServiceError(Exception):
    """An external API could not be reached or returned something unusable."""


def get_json(
    url: str,
    params: dict | None = None,
    headers: dict | None = None,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> dict:
    """GET a URL and return the decoded JSON body.

    Raises:
        ExternalServiceError: on timeouts, connection errors, HTTP errors or bad JSON.
    """
    merged_headers = {"User-Agent": USER_AGENT, **(headers or {})}
    try:
        response = requests.get(url, params=params, headers=merged_headers, timeout=timeout)
        response.raise_for_status()
    except requests.Timeout as error:
        raise ExternalServiceError(f"Request to {url} timed out") from error
    except requests.HTTPError as error:
        status = error.response.status_code if error.response is not None else "?"
        raise ExternalServiceError(f"{url} returned HTTP {status}") from error
    except requests.RequestException as error:
        raise ExternalServiceError(f"Request to {url} failed: {error}") from error

    try:
        return response.json()
    except ValueError as error:
        raise ExternalServiceError(f"{url} returned invalid JSON") from error
