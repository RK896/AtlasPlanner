"""Helpers shared by the MCP servers."""
import functools
import logging
from collections.abc import Callable

from src.tools.http_client import ExternalServiceError

logger = logging.getLogger("atlas.tools")


def friendly_errors(func: Callable[..., str]) -> Callable[..., str]:
    """Turn expected failures into a short message the LLM can act on.

    Bad input (ValueError) and API outages (ExternalServiceError) become a
    tool result like "Error: ..." so the agent can fix its arguments or
    tell the user, instead of the whole graph crashing.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> str:
        try:
            return func(*args, **kwargs)
        except (ValueError, ExternalServiceError) as error:
            logger.info("Tool %s failed: %s", func.__name__, error)
            return f"Error: {error}"

    return wrapper
