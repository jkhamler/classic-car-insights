"""Single source of truth for which makes/models the platform tracks.

Used by every scraper to build search terms and by BaseScraper.run() to
discard anything that isn't one of these — this is the "tighten to specific
models" filter, applied uniformly regardless of source.

Three hunts currently tracked:
  - Mercedes-Benz R107 (SL-Class roadster, 1971-1989), model years 1986
    onwards only. No budget given — uncapped.
  - Aston Martin DB9 (2004-2016), all model years — coupe and Volante.
    DB9 is the current top search, capped at £35k discovery price.
  - Aston Martin V8 Vantage Roadster, 4.3L or 4.7L (2005-2017ish, covers
    the first-generation V8 Vantage and V8 Vantage S; excludes the V12
    Vantage and the second-generation 2018+ "Vantage" nameplate). No
    budget given — uncapped.
"""
import re

# Per-(make, model-label) discovery price ceilings — not applied to
# benchmark sources, which need full-range sold prices to compute an
# accurate fair-value baseline across the whole market, not just what the
# buyer wants to see. Keyed by the exact (make, model) label pair
# extract_make_model() returns below. Omit a vehicle here for no ceiling.
DISCOVERY_PRICE_CEILINGS_GBP: dict[tuple[str, str], float] = {
    ("Aston Martin", "DB9"): 35000,
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
    "mercedes-benz": "Mercedes-Benz",
    "mercedes": "Mercedes-Benz",
    "aston martin": "Aston Martin",
    "aston-martin": "Aston Martin",
}

# R107 badges in "<number>SL" order (500SL, 560SL, ...) — the R129/R230/R231
# successors badge the other way round ("SL500"), so this word order alone
# disambiguates without needing the chassis code in the title. Only badges
# that were still in production for at least part of 1986+ are tracked:
#   300SL   1985-1989 (Europe, replaced 280SL)      — always qualifies
#   420SL   1985-1989                                — gated to be safe
#   500SL   1980-1989                                — gated, spans the cutoff
#   560SL   1986-1989 (US/export)                    — always qualifies
# 280SL/350SL/380SL/450SL all ended production before 1986 and are excluded
# outright rather than tracked-and-gated.
R107_BADGE_RE = re.compile(r"\b(300|420|500|560)\s*sl\b")

# "V8" and "Vantage" and "Roadster" all present, any order (titles vary:
# "V8 Vantage Roadster" vs "Vantage V8 Roadster"). Requiring "v8" excludes
# the V12 Vantage outright. Doesn't gate on displacement text (4.3L
# 2005-2008 / 4.7L 2008+, including V8 Vantage S) since listings often
# omit it — instead gated by year below, since the second-generation
# 2018+ "Vantage" also carries a V8 (AMG-sourced) and got its own Roadster
# from 2020, and would otherwise false-match on this same keyword set.
V8_VANTAGE_ROADSTER_RE = re.compile(r"(?=.*\bv8\b)(?=.*\bvantage\b)(?=.*\broadster\b)")

MODEL_PATTERNS_BY_MAKE: dict[str, list[tuple[str, str]]] = {
    "Mercedes-Benz": [
        (r"\br\s*-?\s*107\b", "SL (R107)"),
    ],
    "Aston Martin": [
        # Matches "DB9" and "DB9 Volante"/"DB9 GT" alike.
        (r"\bdb\s*-?\s*9\b", "DB9"),
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

    if make == "Mercedes-Benz":
        badge_match = R107_BADGE_RE.search(lowered)
        if badge_match:
            badge = badge_match.group(1)
            year_match = re.search(r"\b(19[6-9]\d|20[0-2]\d)\b", title)
            year = int(year_match.group(1)) if year_match else None
            if badge in ("300", "560"):
                # Only ever built 1985/1986-1989 — no year gate needed.
                return make, "SL (R107)"
            # 420SL/500SL span the 1986 cutoff — require the year when it's
            # present; give an undated listing the benefit of the doubt
            # rather than silently dropping it.
            if year is None or 1986 <= year <= 1989:
                return make, "SL (R107)"

    if make == "Aston Martin":
        if V8_VANTAGE_ROADSTER_RE.search(lowered):
            # Confirmed live on PistonHeads: modern 4.0-litre twin-turbo
            # Vantage Roadsters ("Euro 6", "510 ps"/"665 ps") show up with
            # no year in the title at all, which would otherwise slip past
            # the year gate below via its benefit-of-the-doubt fallback —
            # "4.0" is an unambiguous signal for the second-gen car (the
            # classic V8 is only ever 4.3 or 4.7), so exclude on it first.
            if re.search(r"\b4\.0\b", lowered):
                return make, None
            year_match = re.search(r"\b(19[6-9]\d|20[0-2]\d)\b", title)
            year = int(year_match.group(1)) if year_match else None
            # Second-gen 2018+ "Vantage" (and its 2020+ Roadster) would
            # otherwise false-match the same v8/vantage/roadster keywords —
            # give an undated listing the benefit of the doubt, same as R107.
            if year is None or year <= 2017:
                return make, "V8 Vantage Roadster"

    return make, None


def is_target_vehicle(title: str | None) -> bool:
    make, model = extract_make_model(title)
    return make is not None and model is not None


# "make+model" style terms for scrapers that search via a query string.
SEARCH_TERMS = [
    "mercedes+300sl",
    "mercedes+420sl",
    "mercedes+500sl",
    "mercedes+560sl",
    "mercedes+r107",
    "aston+martin+db9",
    "aston+martin+v8+vantage+roadster",
]

# Plain make names for scrapers that can only filter by make (or not at all),
# relying on is_target_vehicle() as the real filter after fetching.
SEARCH_MAKES_ONLY = [
    "Mercedes-Benz",
    "Aston Martin",
]
