from unittest.mock import MagicMock

import anthropic
import httpx
import pytest

from src.utils.llm import describe_api_error


def _status_error(cls, status, message):
    response = httpx.Response(status, request=httpx.Request("POST", "https://api.anthropic.com"))
    return cls(message, response=response, body=None)


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (_status_error(anthropic.AuthenticationError, 401, "bad key"), "ANTHROPIC_API_KEY"),
        (_status_error(anthropic.RateLimitError, 429, "slow down"), "rate-limiting"),
        (_status_error(anthropic.BadRequestError, 400, "Your credit balance is too low"), "out of credits"),
        (_status_error(anthropic.InternalServerError, 500, "boom"), "status 500"),
        (anthropic.APIConnectionError(request=MagicMock()), "internet connection"),
    ],
)
def test_describes_common_api_failures(error, expected):
    assert expected in describe_api_error(error)
