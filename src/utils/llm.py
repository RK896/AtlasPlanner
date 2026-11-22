"""One place to build the Claude chat model from config.yaml."""
from functools import lru_cache

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
