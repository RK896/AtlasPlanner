"""Destination guides from Wikivoyage (free, no API key, CC BY-SA).

Wikivoyage city articles follow a standard layout ("Understand", "Get around",
"See", "Do", "Eat", "Sleep", "Stay safe", ...), which lets each agent pull just
the sections it cares about.
"""
import re

from src.tools.http_client import get_json

WIKIVOYAGE_API = "https://en.wikivoyage.org/w/api.php"
MAX_SECTION_CHARS = 3500
INTRO_SECTION = "Intro"
_TOP_LEVEL_HEADING = re.compile(r"^== (.+?) ==\s*$", re.MULTILINE)


def get_sections(destination: str, section_names: list[str]) -> str:
    """Fetch a destination guide and return the requested sections as text."""
    sections = split_sections(fetch_article(destination))
    parts = [_format_section(name, sections.get(name)) for name in section_names]
    source = f"Source: Wikivoyage, https://en.wikivoyage.org/wiki/{destination.strip().replace(' ', '_')}"
    return "\n\n".join([*parts, source])


def fetch_article(destination: str) -> str:
    """Return the plain-text Wikivoyage article for a destination."""
    title = destination.strip()
    if not title:
        raise ValueError("Destination must not be empty")
    payload = get_json(WIKIVOYAGE_API, params={
        "action": "query",
        "prop": "extracts",
        "explaintext": 1,
        "titles": title,
        "redirects": 1,
        "format": "json",
    })
    pages = payload.get("query", {}).get("pages", {})
    page = next(iter(pages.values()), {})
    if "missing" in page or not page.get("extract"):
        raise ValueError(
            f"No Wikivoyage guide found for {title!r}. Use the English city name, e.g. 'Kyoto'."
        )
    return page["extract"]


def split_sections(article: str) -> dict[str, str]:
    """Split an article on top-level "== Heading ==" lines.

    Text before the first heading is returned under "Intro". Sub-headings
    ("=== ... ===") stay inside their parent section.
    """
    headings = list(_TOP_LEVEL_HEADING.finditer(article))
    intro_end = headings[0].start() if headings else len(article)
    sections = {INTRO_SECTION: article[:intro_end].strip()}
    for index, match in enumerate(headings):
        body_end = headings[index + 1].start() if index + 1 < len(headings) else len(article)
        sections = {**sections, match.group(1).strip(): article[match.end():body_end].strip()}
    return sections


def _format_section(name: str, body: str | None) -> str:
    if not body:
        return f"## {name}\n(no section in guide)"
    if len(body) > MAX_SECTION_CHARS:
        body = body[:MAX_SECTION_CHARS].rsplit(" ", 1)[0] + " [...truncated]"
    return f"## {name}\n{body}"
