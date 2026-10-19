"""Single source of truth for which makes/models the platform tracks.

Used by every scraper to build search terms and by BaseScraper.run() to
discard anything that isn't one of these — this is the "tighten to specific
models" filter, applied uniformly regardless of source.

One hunt currently tracked:
- Mercedes-Benz SL350 BlueEFFICIENCY (R231 generation), 2012-2015 only,
  under £18k. Unlike the enthusiast/collector hunts this replaced (DB9,
  996 Turbo, Jaguar XK — all dropped per explicit request), this is a
  mainstream depreciation-curve car: plentiful supply, no scarcity premium,
  bought/sold through ordinary classifieds rather than specialist auction
  houses. Matched on "SL" + "350" together rather than requiring the
  literal "BlueEFFICIENCY" badge text, since that's an efficiency-package
  name Mercedes used broadly across its range and dealers often drop it
  from listing titles even when the car has it (it was effectively
  standard on every post-2012 SL350). Disambiguated from the visually
  identical R230-generation SL350 (2006-2011, same "SL350" badge, older
  shape) via the 2012-2015 year gate instead, same "benefit of the doubt
  when unknown" pattern as every other hunt here.
"""
import re

# Per-(make, model-label) discovery price ceilings — not applied to
# benchmark sources, which need full-range sold prices to compute an
# accurate fair-value baseline across the whole market, not just what the
# buyer wants to see. Keyed by the exact (make, model) label pair
# extract_make_model() returns below. Omit a vehicle here for no ceiling.
DISCOVERY_PRICE_CEILINGS_GBP: dict[tuple[str, str], float] = {
    ("Mercedes-Benz", "SL350"): 18_000,
}

# Per-(make, model-label) discovery mileage ceilings, same shape/rationale
# as the price ceilings above. Omit a vehicle here for no ceiling.
DISCOVERY_MILEAGE_CEILINGS_MILES: dict[tuple[str, str], float] = {}


def discovery_price_ceiling(make: str | None, model: str | None) -> float | None:
    if not make or not model:
        return None
    return DISCOVERY_PRICE_CEILINGS_GBP.get((make, model))


def discovery_mileage_ceiling(make: str | None, model: str | None) -> float | None:
    if not make or not model:
        return None
    return DISCOVERY_MILEAGE_CEILINGS_MILES.get((make, model))

# Order matters: more specific keys must come before substrings they contain.
MAKE_MAP: dict[str, str] = {
    "mercedes-benz": "Mercedes-Benz",
    "mercedes benz": "Mercedes-Benz",
    "mercedes": "Mercedes-Benz",
}

# "SL" and "350" together, either side of optional whitespace/hyphen — not
# the literal "BlueEFFICIENCY" badge text (see module docstring). Word-
# bounded on both ends so it doesn't match "SL 3500" or a stray "350"
# elsewhere in the title, and doesn't match other SL derivatives (SL55,
# SL63, SL500, SL400, SL350 CDI diesel-era siblings like SL250/SL280).
# Year gate (below) does the real generation disambiguation.
MERCEDES_SL350_RE = re.compile(r"\bsl\s*-?\s*350\b")

MODEL_PATTERNS_BY_MAKE: dict[str, list[tuple[str, str]]] = {}


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

    if make == "Mercedes-Benz":
        if MERCEDES_SL350_RE.search(lowered):
            if year is None:
                title_year_match = re.search(r"\b(19[6-9]\d|20[0-2]\d)\b", title)
                year = int(title_year_match.group(1)) if title_year_match else None
            # R231 generation ran 2012-2015 under the SL350 badge (later
            # renamed SL400); this is what tells it apart from the
            # visually-similar R230-generation SL350 (2006-2011), since
            # the badge text alone is identical across both.
            if year is None or 2012 <= year <= 2015:
                return make, "SL350"

    return make, None


def is_target_vehicle(title: str | None, year: int | None = None) -> bool:
    make, model = extract_make_model(title, year)
    return make is not None and model is not None


# "make+model" style terms for scrapers that search via a query string.
SEARCH_TERMS = [
    "mercedes-benz+sl350",
]

# Plain make names for scrapers that can only filter by make (or not at all),
# relying on is_target_vehicle() as the real filter after fetching.
SEARCH_MAKES_ONLY = [
    "Mercedes-Benz",
]
