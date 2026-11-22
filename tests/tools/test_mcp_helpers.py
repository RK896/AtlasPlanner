from src.tools.http_client import ExternalServiceError
from src.tools.mcp_helpers import friendly_errors


def test_passes_through_successful_results():
    @friendly_errors
    def tool(x: int) -> str:
        return f"got {x}"

    assert tool(3) == "got 3"


def test_converts_expected_failures_to_error_strings():
    @friendly_errors
    def bad_input() -> str:
        raise ValueError("date must be YYYY-MM-DD")

    @friendly_errors
    def api_down() -> str:
        raise ExternalServiceError("upstream timed out")

    assert bad_input() == "Error: date must be YYYY-MM-DD"
    assert api_down() == "Error: upstream timed out"


def test_preserves_signature_for_mcp_schema_generation():
    @friendly_errors
    def tool(origin: str, days: int) -> str:
        """Docstring."""
        return ""

    assert tool.__name__ == "tool"
    assert tool.__doc__ == "Docstring."
    assert tool.__annotations__ == {"origin": str, "days": int, "return": str}
