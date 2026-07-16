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

# Order matters: more specific keys must come before substrings they contain
# (e.g. "alpina" before "bmw", since Alpina titles often also say "BMW").
MAKE_MAP: dict[str, str] = {
    "alpina": "Alpina",
    "aston martin": "Aston Martin",
    "porsche": "Porsche",
    "audi": "Audi",
    "bmw": "BMW",
    "volvo": "Volvo",
    "mercedes-benz": "Mercedes-Benz",
    "mercedes": "Mercedes-Benz",
    "tvr": "TVR",
}

# Model patterns are only tried for the make they're keyed under, since
# tokens like "b3"/"d3" are too generic to safely match against any title.
MODEL_PATTERNS_BY_MAKE: dict[str, list[tuple[str, str]]] = {
    "Porsche": [
        # Only 996 Turbo and 996 Carrera 4S — no other 996 trims, no 997 at all.
        (r"(?=.*\b996\b)(?=.*turbo)", "911 996 Turbo"),
        (r"(?=.*\b996\b)(?=.*(carrera\s*4s|c4s\b))", "911 996 Carrera 4S"),
    ],
    "Audi": [
        (r"\brs\s*4\b", "RS4"),
        (r"\brs\s*6\b", "RS6"),
    ],
    "Alpina": [
        (r"\bb3\b", "B3"),
        (r"\bb5\b", "B5"),
        (r"\bb6\b", "B6"),
        (r"\bb10\b", "B10"),
        (r"\bd3\b", "D3"),
    ],
    "BMW": [
        (r"\bz3\s*m\b", "Z3 M"),
        (r"\bz4\s*m\b", "Z4 M"),
    ],
    "Aston Martin": [
        # Only the DB7 Volante (convertible) — no DB7 coupe, DB9, V8 Vantage, Vanquish.
        (r"(?=.*\bdb7\b)(?=.*volante)", "DB7 Volante"),
    ],
    "Volvo": [
        (r"850\s*t5-?r", "850 T5-R"),
        (r"\b850r\b", "850R"),
        (r"\bs60\s*r\b", "S60 R"),
        (r"\bv70\s*r\b", "V70 R"),
    ],
    "Mercedes-Benz": [
        (r"e\s*55\s*amg", "E55 AMG"),
    ],
    "TVR": [
        (r"\bt350[ct]?\b", "T350"),
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

    return make, None


def is_target_vehicle(title: str | None) -> bool:
    make, model = extract_make_model(title)
    return make is not None and model is not None


# "make+model" style terms for scrapers that search via a query string.
SEARCH_TERMS = [
    "porsche+911+996+turbo", "porsche+911+996+carrera+4s",
    "audi+rs4", "audi+rs6",
    "alpina+b3", "alpina+b5", "alpina+b6", "alpina+b10", "alpina+d3",
    "bmw+z3+m", "bmw+z4+m",
    "aston+martin+db7+volante",
    "volvo+850+t5r", "volvo+s60+r", "volvo+v70+r",
    "mercedes+e55+amg",
    "tvr+t350",
]

# Plain make names for scrapers that can only filter by make (or not at all),
# relying on is_target_vehicle() as the real filter after fetching.
SEARCH_MAKES_ONLY = [
    "Porsche", "Audi", "Alpina", "BMW", "Aston Martin", "Volvo", "Mercedes-Benz", "TVR",
]
