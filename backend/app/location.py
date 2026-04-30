"""
Location normalizer and gate functions.
Pure Python — no external dependencies, fully testable without Groq.
"""
import re

# ─── City alias table ─────────────────────────────────────────────────────────

CITY_ALIASES: dict[str, str] = {
    # Ottawa and surroundings
    "ottawa":    "Ottawa",
    "gatineau":  "Ottawa",
    "kanata":    "Ottawa",
    "nepean":    "Ottawa",
    "hull":      "Ottawa",
    "orléans":   "Ottawa",
    "orleans":   "Ottawa",
    "gloucester":"Ottawa",
    # Montreal and surroundings
    "montreal":  "Montreal",
    "montréal":  "Montreal",
    "laval":     "Montreal",
    "longueuil": "Montreal",
}

REMOTE_PATTERNS = re.compile(
    r'\b(remote|work from home|wfh|fully remote|100% remote|télétravail)\b',
    re.IGNORECASE
)

HYBRID_PATTERN = re.compile(r'\bhybrid\b', re.IGNORECASE)


def _find_city_in_text(text: str) -> str | None:
    """Scan text for a known city alias. Returns canonical name or None."""
    text_lower = text.lower()
    # Sort by length descending so longer aliases match before shorter substrings
    for alias in sorted(CITY_ALIASES, key=len, reverse=True):
        if alias in text_lower:
            return CITY_ALIASES[alias]
    return None


def extract_city(location_field: str, description: str) -> str:
    """
    Normalize a job's location to a canonical city name.

    Priority order:
    1. Remote signals in location field
    2. Known city in location field
    3. Hybrid in location field with no known city → scan description → fallback Remote
    4. Remote signals in first 600 chars of description
    5. Known city in first 600 chars of description
    6. "Unknown" if nothing matched

    Returns one of: "Remote", "Ottawa", "Montreal", "Unknown"
    """
    loc = location_field.strip()
    desc_head = description[:600] if description else ""

    # 1. Remote in location field
    if REMOTE_PATTERNS.search(loc):
        return "Remote"

    # 2. Known city in location field
    city = _find_city_in_text(loc)
    if city:
        return city

    # 3. Hybrid in location field — scan description for city, else Remote
    if HYBRID_PATTERN.search(loc):
        city = _find_city_in_text(desc_head)
        if city:
            return city
        return "Remote"

    # 4. Remote signals in description
    if REMOTE_PATTERNS.search(desc_head):
        return "Remote"

    # 5. Known city in description
    city = _find_city_in_text(desc_head)
    if city:
        return city

    return "Unknown"


def is_preferred(city: str) -> bool:
    """Ottawa and Remote are preferred."""
    return city in ("Ottawa", "Remote")


def is_acceptable(city: str) -> bool:
    """Montreal is acceptable."""
    return city == "Montreal"


def is_excluded(city: str) -> bool:
    """Anything not preferred or acceptable is hard-excluded."""
    return not is_preferred(city) and not is_acceptable(city)
