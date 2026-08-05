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
    "mercedes-benz": "Mercedes-Benz",
    "mercedes": "Mercedes-Benz",
    "tvr": "TVR",
}

# Model patterns are only tried for the make they're keyed under.
MODEL_PATTERNS_BY_MAKE: dict[str, list[tuple[str, str]]] = {
    "Porsche": [
        # Only 996 Turbo and 996 Carrera 4S — no other 996 trims, no 997 at all.
        (r"(?=.*\b996\b)(?=.*turbo)", "911 996 Turbo"),
        (r"(?=.*\b996\b)(?=.*(carrera\s*4s|c4s\b))", "911 996 Carrera 4S"),
    ],
    "BMW": [
        (r"\bz3\s*m\b", "Z3 M"),
        (r"\bz4\s*m\b", "Z4 M"),
    ],
    "TVR": [
        # Only the T350C (coupe) — excludes the T350T (targa).
        (r"\bt350\s*c\b", "T350C"),
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

    if make == "Porsche" and re.search(r"\b911\b", lowered):
        # Many listings (BaT in particular) never state the chassis code,
        # just "911 Turbo"/"911 Carrera 4S" — infer 996 from the year, but
        # only for the two trims we actually track.
        year_match = re.search(r"\b(19[6-9]\d|20[0-2]\d)\b", title)
        if year_match:
            year = int(year_match.group(1))
            if 1998 <= year <= 2004:
                if "turbo" in lowered:
                    return make, "911 996 Turbo"
                if re.search(r"carrera\s*4s|c4s\b", lowered):
                    return make, "911 996 Carrera 4S"

    if make == "Mercedes-Benz" and re.search(r"\b(280|300|320)\s*sl\b|\bsl\s*(280|300|320)\b", lowered):
        # R107 (1971-89) and R129 (1989-2001) 6-cylinder badges only —
        # 280SL/300SL/320SL. Deliberately excludes V8 badges (350/380/420/
        # 450/500/560/600) and, critically, requires a year in the R107/R129
        # window so this can't false-positive on the unrelated W198 "300SL"
        # Gullwing/Roadster (1954-63), which shares the same badge number.
        year_match = re.search(r"\b(19[6-9]\d|20[0-2]\d)\b", title)
        if year_match and 1971 <= int(year_match.group(1)) <= 2001:
            return make, "SL"

    if make == "Mercedes-Benz" and re.search(r"\bsl\s*350\b|\b350\s*sl\b", lowered):
        # R230 SL350 (3.7L/3.5L V6), 2006 or earlier only. The "350" badge
        # is also used by the unrelated R107 350SL (a 3.5L V8, 1971-80), so
        # year-gate to the R230 window to avoid matching that car.
        year_match = re.search(r"\b(19[6-9]\d|20[0-2]\d)\b", title)
        if year_match and 2001 <= int(year_match.group(1)) <= 2006:
            return make, "SL"

    return make, None


def is_target_vehicle(title: str | None) -> bool:
    make, model = extract_make_model(title)
    return make is not None and model is not None


# "make+model" style terms for scrapers that search via a query string.
SEARCH_TERMS = [
    "porsche+911+996+turbo", "porsche+911+996+carrera+4s",
    "bmw+z3+m", "bmw+z4+m",
    "mercedes+280sl", "mercedes+300sl", "mercedes+320sl", "mercedes+sl350",
    "tvr+t350c",
]

# Plain make names for scrapers that can only filter by make (or not at all),
# relying on is_target_vehicle() as the real filter after fetching.
SEARCH_MAKES_ONLY = [
    "Porsche", "BMW", "Mercedes-Benz", "TVR",
]
