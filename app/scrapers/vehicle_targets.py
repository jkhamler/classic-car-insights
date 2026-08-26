"""Single source of truth for which makes/models the platform tracks.

Used by every scraper to build search terms and by BaseScraper.run() to
discard anything that isn't one of these — this is the "tighten to specific
models" filter, applied uniformly regardless of source.

Currently narrowed to a single hunt: Japanese-import Volvo V70 / XC70,
preferably the 2.5T five-cylinder, under £10k. Japanese-market cars are
RHD (same as the UK) and are commonly resold here explicitly labelled as
imports, so "Japanese import" is enforced as a title/description keyword
match rather than inferred from spec.
"""
import re

# Ceilings applied to discovery listings only (not benchmark sources, which
# need full-range sold prices/mileages to compute an accurate fair-value
# baseline across the whole market, not just what the buyer wants to see).
MAX_DISCOVERY_PRICE_GBP = 10_000
MAX_DISCOVERY_MILEAGE_MILES = 100_000

# Order matters: more specific keys must come before substrings they contain.
MAKE_MAP: dict[str, str] = {
    "volvo": "Volvo",
}

# Model patterns are only tried for the make they're keyed under.
# XC70 must be checked before V70 — "xc70" listings otherwise still contain
# neither pattern for the other, so order here is just for clarity.
MODEL_PATTERNS_BY_MAKE: dict[str, list[tuple[str, str]]] = {
    "Volvo": [
        (r"\bxc\s*-?\s*70\b", "XC70"),
        (r"\bv\s*-?\s*70\b", "V70"),
    ],
}

# Keywords that flag a listing as a Japanese-market grey import — the whole
# point of this hunt. Matched against title (and description, where a
# scraper has it) case-insensitively.
JAPANESE_IMPORT_KEYWORDS = [
    "japanese import", "jap import", "japan import", "imported from japan",
    "jdm import", "jdm", "grey import", "grey-import",
]


def extract_make_model(title: str | None) -> tuple[str | None, str | None]:
    if not title:
        return None, None
    lowered = title.lower()

    make = None
    for key, canonical in MAKE_MAP.items():
        if key in lowered:
            make = canonical
            break
    if not make:
        return None, None

    for pattern, label in MODEL_PATTERNS_BY_MAKE.get(make, []):
        if re.search(pattern, lowered):
            return make, label

    return make, None


def is_japanese_import(text: str | None) -> bool:
    if not text:
        return False
    lowered = text.lower()
    return any(kw in lowered for kw in JAPANESE_IMPORT_KEYWORDS)


def is_target_vehicle(title: str | None, description: str | None = None) -> bool:
    make, model = extract_make_model(title)
    if make is None or model is None:
        return False
    return is_japanese_import(title) or is_japanese_import(description)


def is_preferred_engine(text: str | None) -> bool:
    """2.5T is a soft preference, not a filter — used for search-term
    ordering / surfacing, never to exclude a matching listing."""
    if not text:
        return False
    lowered = text.lower()
    return "2.5t" in lowered.replace(" ", "") or "2.5 t5" in lowered


# "make+model" style terms for scrapers that search via a query string. Kept
# broad (just make+model) rather than adding "japanese import" or "2.5t" into
# the query text itself — free-text search engines match literally, and
# sellers phrase imports/engine differently ("grey import", "JDM", "T5T"
# instead of "2.5T"). is_target_vehicle() applies the real Japanese-import
# gate against the fetched title after the fact.
SEARCH_TERMS = [
    "volvo+v70",
    "volvo+xc70",
]

# Plain make names for scrapers that can only filter by make (or not at all),
# relying on is_target_vehicle() as the real filter after fetching.
SEARCH_MAKES_ONLY = [
    "Volvo",
]
