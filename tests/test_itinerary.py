from datetime import datetime

import pytest

from src.utils.itinerary import save_itinerary, slugify


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("My Lisbon Trip!", "my-lisbon-trip"),
        ("../../etc/passwd", "etc-passwd"),
        ("   ", "trip"),
        ("a" * 100, "a" * 40),
    ],
)
def test_slugify_produces_safe_filenames(text, expected):
    assert slugify(text) == expected


def test_save_itinerary_writes_markdown(tmp_path):
    path = save_itinerary("# Lisbon\nDay 1", tmp_path / "out", "Lisbon Trip", now=datetime(2027, 3, 1, 9, 30))

    assert path == tmp_path / "out" / "lisbon-trip-20270301-093000.md"
    assert path.read_text().endswith("# Lisbon\nDay 1")


def test_save_itinerary_rejects_empty_content(tmp_path):
    with pytest.raises(ValueError, match="Nothing to save"):
        save_itinerary("  ", tmp_path, "x")
