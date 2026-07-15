"""Single source of truth for which makes/models the platform tracks.

Used by every scraper to build search terms and by BaseScraper.run() to
discard anything that isn't one of these — this is the "tighten to specific
models" filter, applied uniformly regardless of source.
"""
import re

# Ceiling applied to discovery listings only (not benchmark sources, which
# need full-range sold prices to compute an accurate fair-value baseline).
MAX_DISCOVERY_PRICE_GBP = 30_000

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
}

# Model patterns are only tried for the make they're keyed under, since
# tokens like "b3"/"d3" are too generic to safely match against any title.
MODEL_PATTERNS_BY_MAKE: dict[str, list[tuple[str, str]]] = {
    "Porsche": [
        (r"996\s*turbo", "911 996 Turbo"),
        (r"997\s*turbo", "911 997 Turbo"),
        (r"\b996\b", "911 996"),
        (r"\b997\b", "911 997"),
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
        (r"\bdb7\b", "DB7"),
        (r"\bdb9\b", "DB9"),
        (r"v8\s*vantage", "V8 Vantage"),
        (r"\bvanquish\b", "Vanquish"),
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

    return make, None


def is_target_vehicle(title: str | None) -> bool:
    make, model = extract_make_model(title)
    return make is not None and model is not None


# "make+model" style terms for scrapers that search via a query string.
SEARCH_TERMS = [
    "porsche+911+996", "porsche+911+996+turbo",
    "porsche+911+997", "porsche+911+997+turbo",
    "audi+rs4", "audi+rs6",
    "alpina+b3", "alpina+b5", "alpina+b6", "alpina+b10", "alpina+d3",
    "bmw+z3+m", "bmw+z4+m",
    "aston+martin+db7", "aston+martin+db9",
    "aston+martin+v8+vantage", "aston+martin+vanquish",
    "volvo+850+t5r", "volvo+s60+r", "volvo+v70+r",
    "mercedes+e55+amg",
]

# Plain make names for scrapers that can only filter by make (or not at all),
# relying on is_target_vehicle() as the real filter after fetching.
SEARCH_MAKES_ONLY = [
    "Porsche", "Audi", "Alpina", "BMW", "Aston Martin", "Volvo", "Mercedes-Benz",
]
