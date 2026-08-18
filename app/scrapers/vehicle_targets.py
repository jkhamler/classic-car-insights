"""Single source of truth for which makes/models the platform tracks.

Used by every scraper to build search terms and by BaseScraper.run() to
discard anything that isn't one of these — this is the "tighten to specific
models" filter, applied uniformly regardless of source.
"""
import re

# Ceilings applied to discovery listings only (not benchmark sources, which
# need full-range sold prices/mileages to compute an accurate fair-value
# baseline across the whole market, not just what the buyer wants to see).
MAX_DISCOVERY_PRICE_GBP = 30_000
MAX_DISCOVERY_MILEAGE_MILES = 100_000

# Order matters: more specific keys must come before substrings they contain.
MAKE_MAP: dict[str, str] = {
    "porsche": "Porsche",
    "bmw": "BMW",
    "tvr": "TVR",
    "lotus": "Lotus",
}

# Model patterns are only tried for the make they're keyed under.
MODEL_PATTERNS_BY_MAKE: dict[str, list[tuple[str, str]]] = {
    "Porsche": [
        # Only 996 Turbo — no other 996 trims, no 997 at all.
        (r"(?=.*\b996\b)(?=.*turbo)", "911 996 Turbo"),
    ],
    "BMW": [
        (r"\bz4\s*m\b", "Z4 M"),
    ],
    "TVR": [
        # Both T350C (coupe) and T350T (targa).
        (r"\bt350\s*[ct]?\b", "T350"),
    ],
    "Lotus": [
        (r"\belise\b", "Elise"),
    ],
}


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

    if make == "Porsche" and re.search(r"\b911\b", lowered) and "turbo" in lowered:
        # Many listings (BaT in particular) never state the chassis code,
        # just "911 Turbo" — infer 996 from the year.
        year_match = re.search(r"\b(19[6-9]\d|20[0-2]\d)\b", title)
        if year_match and 1998 <= int(year_match.group(1)) <= 2004:
            return make, "911 996 Turbo"

    return make, None


def is_target_vehicle(title: str | None) -> bool:
    make, model = extract_make_model(title)
    return make is not None and model is not None


# "make+model" style terms for scrapers that search via a query string.
SEARCH_TERMS = [
    "porsche+911+996+turbo",
    "bmw+z4+m",
    "tvr+t350c", "tvr+t350t",
    "lotus+elise",
]

# Plain make names for scrapers that can only filter by make (or not at all),
# relying on is_target_vehicle() as the real filter after fetching.
SEARCH_MAKES_ONLY = [
    "Porsche", "BMW", "TVR", "Lotus",
]
