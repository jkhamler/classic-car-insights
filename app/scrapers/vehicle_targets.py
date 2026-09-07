"""Single source of truth for which makes/models the platform tracks.

Used by every scraper to build search terms and by BaseScraper.run() to
discard anything that isn't one of these — this is the "tighten to specific
models" filter, applied uniformly regardless of source.

Currently narrowed to a single hunt: Mercedes-Benz R107 (SL-Class roadster,
1971-1989), model years 1986 onwards only. No price or mileage ceiling is
set — no budget was given for this hunt.
"""
import re

# Ceilings applied to discovery listings only (not benchmark sources, which
# need full-range sold prices/mileages to compute an accurate fair-value
# baseline across the whole market, not just what the buyer wants to see).
# None = no ceiling; set to a number to cap discovery listings again.
MAX_DISCOVERY_PRICE_GBP: float | None = None
MAX_DISCOVERY_MILEAGE_MILES: float | None = None

# Order matters: more specific keys must come before substrings they contain.
MAKE_MAP: dict[str, str] = {
    "mercedes-benz": "Mercedes-Benz",
    "mercedes": "Mercedes-Benz",
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

MODEL_PATTERNS_BY_MAKE: dict[str, list[tuple[str, str]]] = {
    "Mercedes-Benz": [
        (r"\br\s*-?\s*107\b", "SL (R107)"),
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
]

# Plain make names for scrapers that can only filter by make (or not at all),
# relying on is_target_vehicle() as the real filter after fetching.
SEARCH_MAKES_ONLY = [
    "Mercedes-Benz",
]
