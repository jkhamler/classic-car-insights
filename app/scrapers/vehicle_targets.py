"""Single source of truth for which makes/models the platform tracks.

Used by every scraper to build search terms and by BaseScraper.run() to
discard anything that isn't one of these — this is the "tighten to specific
models" filter, applied uniformly regardless of source.

Three hunts currently tracked:
- Aston Martin DB9, UK "55 plate" only (registered Sept 2005-Feb 2006),
  under £30k. Any body style — coupe or Volante, per explicit request to
  stop restricting to Volante only. Later years and the DB9 GT/facelift
  are still excluded via the year gate.
- Porsche 911 (996) Turbo, under £30k. Matched on "911"+"turbo" rather
  than requiring the literal "996" chassis code in the title — classified
  ad titles (AutoTrader etc.) routinely omit it — and disambiguated from
  every other 911 Turbo generation (930/964/993/997/991/992) via the
  2000-2005 year gate instead, same "benefit of the doubt when unknown"
  pattern as DB9.
- Jaguar XK, 2005-2006 only, under £10k and under 70k miles ("really
  good condition" proxied by a mileage ceiling — the one hunt so far
  that needs one). Covers XK8, XKR and the plain-"XK" X150 facelift
  (AutoTrader's own taxonomy splits these into three separate model
  values) as one pooled "XK" label.
"""
import re

# Per-(make, model-label) discovery price ceilings — not applied to
# benchmark sources, which need full-range sold prices to compute an
# accurate fair-value baseline across the whole market, not just what the
# buyer wants to see. Keyed by the exact (make, model) label pair
# extract_make_model() returns below. Omit a vehicle here for no ceiling.
DISCOVERY_PRICE_CEILINGS_GBP: dict[tuple[str, str], float] = {
    ("Porsche", "996 Turbo"): 30_000,
    ("Aston Martin", "DB9"): 30_000,
    ("Jaguar", "XK"): 10_000,
}

# Per-(make, model-label) discovery mileage ceilings, same shape/rationale
# as the price ceilings above. Omit a vehicle here for no ceiling.
DISCOVERY_MILEAGE_CEILINGS_MILES: dict[tuple[str, str], float] = {
    ("Jaguar", "XK"): 70_000,
}


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
    "aston martin": "Aston Martin",
    "aston-martin": "Aston Martin",
    "porsche": "Porsche",
    "jaguar": "Jaguar",
}

# Any DB9 — coupe or Volante. Year gate applied separately below (can't
# express "AND year in range" as a single independent tuple entry the way
# MODEL_PATTERNS_BY_MAKE works, since that needs post-match logic) — see
# extract_make_model().
DB9_RE = re.compile(r"\bdb\s*-?\s*9\b")

# "911" and "turbo" anywhere in the title, either order — not "996" itself,
# since classified titles often drop the chassis code. Year gate (below)
# does the real generation disambiguation.
PORSCHE_911_TURBO_RE = re.compile(r"(?=.*\b911\b)(?=.*\bturbo\b)")

# "XK", "XK8" or "XKR" as a whole word — not "XKE" (an old colloquial
# name for the E-Type, which must not match).
JAGUAR_XK_RE = re.compile(r"\bxk(?:8|r)?\b")

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

    if make == "Aston Martin":
        if DB9_RE.search(lowered):
            if year is None:
                title_year_match = re.search(r"\b(19[6-9]\d|20[0-2]\d)\b", title)
                year = int(title_year_match.group(1)) if title_year_match else None
            # "55 plate" = registered Sept 2005-Feb 2006. Listings almost
            # never state the plate age code directly, so year (2005 or
            # 2006) is the best available proxy — give an undated listing
            # the benefit of the doubt rather than silently dropping it,
            # same pattern used for every other year-gated model here.
            if year is None or 2005 <= year <= 2006:
                return make, "DB9"

    if make == "Porsche":
        if PORSCHE_911_TURBO_RE.search(lowered):
            if year is None:
                title_year_match = re.search(r"\b(19[6-9]\d|20[0-2]\d)\b", title)
                year = int(title_year_match.group(1)) if title_year_match else None
            # 996 generation ran 2000-2005; this is what actually tells a
            # 996 Turbo apart from a 993/997/991/992 Turbo, since the title
            # text often doesn't say "996" at all.
            if year is None or 2000 <= year <= 2005:
                return make, "996 Turbo"

    if make == "Jaguar":
        if JAGUAR_XK_RE.search(lowered):
            if year is None:
                title_year_match = re.search(r"\b(19[6-9]\d|20[0-2]\d)\b", title)
                year = int(title_year_match.group(1)) if title_year_match else None
            if year is None or 2005 <= year <= 2006:
                return make, "XK"

    return make, None


def is_target_vehicle(title: str | None, year: int | None = None) -> bool:
    make, model = extract_make_model(title, year)
    return make is not None and model is not None


# "make+model" style terms for scrapers that search via a query string.
SEARCH_TERMS = [
    "aston+martin+db9",
    "porsche+911+turbo",
    "jaguar+xk",
]

# Plain make names for scrapers that can only filter by make (or not at all),
# relying on is_target_vehicle() as the real filter after fetching.
SEARCH_MAKES_ONLY = [
    "Aston Martin",
    "Porsche",
    "Jaguar",
]
