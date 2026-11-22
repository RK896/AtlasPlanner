from unittest.mock import patch

import pytest

from src.tools.services import wikivoyage

ARTICLE = """Lisbon is the capital of Portugal.

== Understand ==
Hilly city on seven hills.

=== History ===
Old.

== See ==
Belem Tower. Jeronimos Monastery.

== Sleep ==
Hostels from €30.
"""


def _payload(extract=None, missing=False):
    page = {"pageid": 1, "title": "Lisbon"}
    if missing:
        page = {"title": "Nowhere", "missing": ""}
    elif extract is not None:
        page["extract"] = extract
    return {"query": {"pages": {"1": page}}}


def test_split_sections_keeps_intro_and_nests_subsections():
    sections = wikivoyage.split_sections(ARTICLE)

    assert list(sections) == ["Intro", "Understand", "See", "Sleep"]
    assert sections["Intro"] == "Lisbon is the capital of Portugal."
    assert "=== History ===" in sections["Understand"]
    assert sections["Sleep"] == "Hostels from €30."


@patch("src.tools.services.wikivoyage.get_json")
def test_get_sections_formats_requested_sections_only(mock_get_json):
    mock_get_json.return_value = _payload(ARTICLE)

    result = wikivoyage.get_sections("Lisbon", ["Intro", "See", "Eat"])

    assert "## See\nBelem Tower" in result
    assert "Sleep" not in result
    assert "## Eat\n(no section in guide)" in result
    assert "Source: Wikivoyage" in result
    assert mock_get_json.call_args.kwargs["params"]["titles"] == "Lisbon"


@patch("src.tools.services.wikivoyage.get_json")
def test_long_sections_are_truncated_with_marker(mock_get_json):
    long_text = "Intro.\n\n== See ==\n" + "x" * (wikivoyage.MAX_SECTION_CHARS + 500)
    mock_get_json.return_value = _payload(long_text)

    result = wikivoyage.get_sections("Lisbon", ["See"])

    assert "[...truncated]" in result
    assert len(result) < wikivoyage.MAX_SECTION_CHARS + 300


@patch("src.tools.services.wikivoyage.get_json")
def test_missing_article_raises_helpful_error(mock_get_json):
    mock_get_json.return_value = _payload(missing=True)

    with pytest.raises(ValueError, match="No Wikivoyage guide"):
        wikivoyage.get_sections("Nowhere", ["See"])


def test_empty_destination_rejected():
    with pytest.raises(ValueError):
        wikivoyage.get_sections("   ", ["See"])
