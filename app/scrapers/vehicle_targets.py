"""Single source of truth for which makes/models the platform tracks.

Used by every scraper to build search terms and by BaseScraper.run() to
discard anything that isn't one of these — this is the "tighten to specific
models" filter, applied uniformly regardless of source.

Two hunts:
  - Aston Martin DB9 Volante, late 2005 or early 2006 build only (UK "55
    plate" territory — the first model year the RHD Volante was actually
    delivered in). Coupes, later Volantes, and the DB9 GT/facelift are all
    excluded. No budget given — uncapped.
  - Aston Martin DB11 (2016-2023, DB9's successor) — any body style/year
    within that run, capped at £65k discovery price.
"""
import re

# Per-(make, model-label) discovery price ceilings — not applied to
# benchmark sources, which need full-range sold prices to compute an
# accurate fair-value baseline across the whole market, not just what the
# buyer wants to see. Keyed by the exact (make, model) label pair
# extract_make_model() returns below. Omit a vehicle here for no ceiling.
DISCOVERY_PRICE_CEILINGS_GBP: dict[tuple[str, str], float] = {
    ("Aston Martin", "DB11"): 65000,
}

# Mileage ceiling — global (not per-vehicle, unlike price) since no hunt
# has needed one differentiated by vehicle yet. None = no ceiling.
MAX_DISCOVERY_MILEAGE_MILES: float | None = None


def discovery_price_ceiling(make: str | None, model: str | None) -> float | None:
    if not make or not model:
        return None
    return DISCOVERY_PRICE_CEILINGS_GBP.get((make, model))

# Order matters: more specific keys must come before substrings they contain.
MAKE_MAP: dict[str, str] = {
    "aston martin": "Aston Martin",
    "aston-martin": "Aston Martin",
}

# "db9" and "volante" both present, any order. Year gate applied separately
# below (can't express "AND year in range" as a single independent tuple
# entry the way MODEL_PATTERNS_BY_MAKE works, since that needs post-match
# logic) — see extract_make_model().
DB9_VOLANTE_RE = re.compile(r"(?=.*\bdb\s*-?\s*9\b)(?=.*\bvolante\b)")

MODEL_PATTERNS_BY_MAKE: dict[str, list[tuple[str, str]]] = {
    "Aston Martin": [
        # "db11" never matches the db9 pattern above (digit sequence is
        # "11" not "9") — no collision, order doesn't matter between them.
        (r"\bdb\s*-?\s*11\b", "DB11"),
    ],
}


def extract_make_model(title: str | None, year: int | None = None) -> tuple[str | None, str | None]:
    """`year`: pass the listing's own structured year field when the caller
    has one. Several sources (AutoTrader confirmed live) never embed a year
    in the title text at all — it only lives in a separate field — so
    relying on regex-scraping the title alone silently defeats every
    year-gate below via its "benefit of the doubt" fallback, letting
    completely wrong model years through. Falls back to scanning the title
    only when no structured year is supplied.
    """
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

    if make == "Aston Martin":
        if DB9_VOLANTE_RE.search(lowered):
            if year is None:
                title_year_match = re.search(r"\b(19[6-9]\d|20[0-2]\d)\b", title)
                year = int(title_year_match.group(1)) if title_year_match else None
            # Late-2005/early-2006 build only — give an undated listing the
            # benefit of the doubt rather than silently dropping it, same
            # pattern used for every other year-gated model here before.
            if year is None or 2005 <= year <= 2006:
                return make, "DB9 Volante"

    return make, None


def is_target_vehicle(title: str | None, year: int | None = None) -> bool:
    make, model = extract_make_model(title, year)
    return make is not None and model is not None


# "make+model" style terms for scrapers that search via a query string.
SEARCH_TERMS = [
    "aston+martin+db9+volante",
    "aston+martin+db11",
]

# Plain make names for scrapers that can only filter by make (or not at all),
# relying on is_target_vehicle() as the real filter after fetching.
SEARCH_MAKES_ONLY = [
    "Aston Martin",
]
