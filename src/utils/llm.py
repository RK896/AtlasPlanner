"""One place to build the Claude chat model from config.yaml."""
from functools import lru_cache

import anthropic
from langchain_anthropic import ChatAnthropic

from src.utils.config import API_KEY, MODEL_CONFIG


@lru_cache(maxsize=1)
def build_chat_model() -> ChatAnthropic:
    """Return the shared chat model (created once, reused by every agent)."""
    options = {
        "api_key": API_KEY,
        "model": MODEL_CONFIG["model"],
        "max_tokens": MODEL_CONFIG["max_tokens"],
    }
    # Newer Claude models reject sampling params, so temperature is optional.
    if MODEL_CONFIG.get("temperature") is not None:
        options = {**options, "temperature": MODEL_CONFIG["temperature"]}
    return ChatAnthropic(**options)


def describe_api_error(error: anthropic.APIError) -> str:
    """A short, user-facing explanation of a Claude API failure."""
    if isinstance(error, anthropic.AuthenticationError):
        return "The Claude API rejected the API key. Check ANTHROPIC_API_KEY in your .env file."
    if isinstance(error, anthropic.RateLimitError):
        return "The Claude API is rate-limiting requests. Wait a moment and try again."
    if isinstance(error, anthropic.APIConnectionError):
        return "Couldn't reach the Claude API. Check your internet connection and try again."
    if "credit balance" in str(error).lower():
        return "Your Anthropic account is out of credits. Add credits under Plans & Billing, then try again."
    status = getattr(error, "status_code", "unknown")
    return f"The Claude API returned an error (status {status}). Please try again."
