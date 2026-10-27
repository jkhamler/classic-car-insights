"""Single source of truth for which makes/models the platform tracks.

Used by every scraper to build search terms and by BaseScraper.run() to
discard anything that isn't one of these — this is the "tighten to specific
models" filter, applied uniformly regardless of source.

One hunt currently tracked: Mercedes-Benz SL400 (R231 generation), 2015
onwards, open-ended — no upper year bound, per explicit request, so a
later facelift year doesn't silently age out of the hunt the way a closed
range would. SL350 (the pre-facelift badge for the same 3.0L-era V6 slot)
was tracked alongside SL400 earlier for a direct cross-shop comparison,
but was dropped per explicit follow-up once the user settled on SL400 as
the only model of interest.

Under £24k (raised from £18k once live AutoTrader/Gumtree/PistonHeads data
showed every real SL400 currently for sale asks £19k-£35k — the original
£18k ceiling was below the entire live market, not just the cheap end of
it), 80k miles, private-seller-only. Mainstream depreciation-curve car:
plentiful supply, no scarcity premium, bought/sold through ordinary
classifieds rather than specialist auction houses — hence the mainstream-
classifieds-only source list in seed.py, not niche/enthusiast sources.

Hard-requires, via DISCOVERY_REQUIRED_TEXT_GROUPS below, only a dark
exterior colour — excluded at discovery if the ad text doesn't mention
it. Light interior, Harman Kardon audio, and AIRSCARF are all
DISCOVERY_BONUS_TEXT_GROUPS instead (text-matched the same way, but only
add to a matching listing's score via scoring.py's compute_score, never
exclude a listing that doesn't mention them) — light interior was
originally hard-required alongside dark exterior, but moved here per
explicit request and given a much larger points value (20, vs 5 each for
Harman Kardon/AIRSCARF) since it matters far more to the user than those
two. Harman Kardon/AIRSCARF were moved here earlier for the same reason
dark-exterior-and-light-interior-both-required produced zero live
matches at the time (too few sellers spell any of these out in ad text
even when fitted).
"""
import re

# Per-(make, model-label) discovery price ceilings — not applied to
# benchmark sources, which need full-range sold prices to compute an
# accurate fair-value baseline across the whole market, not just what the
# buyer wants to see. Keyed by the exact (make, model) label pair
# extract_make_model() returns below. Omit a vehicle here for no ceiling.
DISCOVERY_PRICE_CEILINGS_GBP: dict[tuple[str, str], float] = {
    ("Mercedes-Benz", "SL400"): 24_000,
}

# Per-(make, model-label) discovery mileage ceilings, same shape/rationale
# as the price ceilings above. Omit a vehicle here for no ceiling.
DISCOVERY_MILEAGE_CEILINGS_MILES: dict[tuple[str, str], float] = {
    ("Mercedes-Benz", "SL400"): 80_000,
}

# Per-(make, model-label) required seller type for discovery sources —
# "private" or "trade". Like the ceilings above, this gives a listing the
# benefit of the doubt when the source couldn't determine seller type at
# all (None) rather than excluding it; it only excludes a listing whose
# seller type is positively known and doesn't match.
DISCOVERY_SELLER_TYPE_REQUIRED: dict[tuple[str, str], str] = {
    ("Mercedes-Benz", "SL400"): "private",
}


def discovery_price_ceiling(make: str | None, model: str | None) -> float | None:
    if not make or not model:
        return None
    return DISCOVERY_PRICE_CEILINGS_GBP.get((make, model))


def discovery_mileage_ceiling(make: str | None, model: str | None) -> float | None:
    if not make or not model:
        return None
    return DISCOVERY_MILEAGE_CEILINGS_MILES.get((make, model))


def discovery_seller_type_required(make: str | None, model: str | None) -> str | None:
    if not make or not model:
        return None
    return DISCOVERY_SELLER_TYPE_REQUIRED.get((make, model))


# Light-interior phrasing is generated from colour x furnishing-noun
# combinations rather than hand-listing every phrase, since sellers
# describe the same interior as "cream leather", "cream interior" or
# "cream upholstery" interchangeably.
_LIGHT_INTERIOR_COLOURS = [
    "cream", "beige", "tan", "sand", "almond", "ivory", "porcelain",
    "stone", "light grey", "light gray", "two-tone", "two tone",
]
_LIGHT_INTERIOR_NOUNS = ["interior", "leather", "upholstery", "trim"]

# Required-feature/condition text groups — every group must have at least
# one synonym present somewhere in the listing's available text (title +
# description, where fetched — see each scraper's module docstring for
# what text it actually captures) for a listing to qualify. Unlike the
# price/mileage ceilings above, this can only be checked against free
# text: none of the three sources expose exterior colour, interior
# colour, or factory options as structured fields consistently enough to
# filter on directly (PistonHeads exposes exterior colour structurally;
# AutoTrader and Gumtree don't at all). A listing whose seller simply
# didn't mention one of these in the ad text gets excluded even if the
# car genuinely qualifies — a real coverage gap, not a design choice;
# there's no more reliable signal available from any of these sources
# short of OCR'ing photos. Omit a vehicle here for no text requirement.
_SL_REQUIRED_TEXT_GROUPS = [
    # dark exterior
    [
        "black", "obsidian", "anthracite", "graphite", "tenorite",
        "selenite grey", "selenite gray", "dark grey", "dark gray",
        "charcoal",
    ],
]

DISCOVERY_REQUIRED_TEXT_GROUPS: dict[tuple[str, str], list[list[str]]] = {
    ("Mercedes-Benz", "SL400"): _SL_REQUIRED_TEXT_GROUPS,
}

# Desirable-but-not-gating features — each (label, synonyms, points) is
# text-matched the same way as the required groups above, but a listing
# that doesn't mention one is scored, not excluded (see scoring.py's
# compute_score, which sums `points` for every matched group). label is
# the human-readable name shown in a listing's score explanation when
# matched. Light interior was moved here from DISCOVERY_REQUIRED_TEXT_GROUPS
# (dropped as a hard gate, per explicit request) and given a much larger
# points value than Harman Kardon/AIRSCARF to reflect it mattering far
# more than those two.
_SL_BONUS_TEXT_GROUPS: list[tuple[str, list[str], float]] = [
    ("Light interior", [f"{colour} {noun}" for colour in _LIGHT_INTERIOR_COLOURS for noun in _LIGHT_INTERIOR_NOUNS], 20.0),
    ("Harman Kardon audio", ["harman kardon", "harman/kardon", "harman-kardon"], 5.0),
    ("AIRSCARF", ["airscarf", "air scarf"], 5.0),
]

DISCOVERY_BONUS_TEXT_GROUPS: dict[tuple[str, str], list[tuple[str, list[str], float]]] = {
    ("Mercedes-Benz", "SL400"): _SL_BONUS_TEXT_GROUPS,
}


def matched_bonus_features(make: str | None, model: str | None, *texts: str | None) -> list[tuple[str, float]]:
    """(label, points) for every bonus feature group (see
    DISCOVERY_BONUS_TEXT_GROUPS) found in the given texts — used to add a
    scoring bonus, never to exclude."""
    if not make or not model:
        return []
    groups = DISCOVERY_BONUS_TEXT_GROUPS.get((make, model))
    if not groups:
        return []
    combined = " ".join(t for t in texts if t).lower()
    return [(label, points) for label, synonyms, points in groups if any(s in combined for s in synonyms)]


def discovery_required_text_groups(make: str | None, model: str | None) -> list[list[str]] | None:
    if not make or not model:
        return None
    return DISCOVERY_REQUIRED_TEXT_GROUPS.get((make, model))


def meets_required_text(make: str | None, model: str | None, *texts: str | None) -> bool:
    groups = discovery_required_text_groups(make, model)
    if not groups:
        return True
    combined = " ".join(t for t in texts if t).lower()
    return all(any(synonym in combined for synonym in group) for group in groups)

# Order matters: more specific keys must come before substrings they contain.
MAKE_MAP: dict[str, str] = {
    "mercedes-benz": "Mercedes-Benz",
    "mercedes benz": "Mercedes-Benz",
    "mercedes": "Mercedes-Benz",
}

# "SL" and "400" together, either side of optional whitespace/hyphen.
# Word-bounded on both ends so it doesn't match "SL 4000" or a stray "400"
# elsewhere in the title, and doesn't match other SL derivatives (SL55,
# SL63, SL500, SL350). Year gate (below) does the real generation
# disambiguation.
MERCEDES_SL400_RE = re.compile(r"\bsl\s*-?\s*400\b")

# (regex, label, year_start, year_end) — checked in order; year_end=None
# means open-ended (no upper bound). year gate uses the same "benefit of
# the doubt when year unknown" rule as every other hunt here.
MERCEDES_SL_MODELS: list[tuple[re.Pattern, str, int, int | None]] = [
    (MERCEDES_SL400_RE, "SL400", 2015, None),
]

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
        for pattern, label, year_start, year_end in MERCEDES_SL_MODELS:
            if pattern.search(lowered):
                if year is None:
                    title_year_match = re.search(r"\b(19[6-9]\d|20[0-2]\d)\b", title)
                    year = int(title_year_match.group(1)) if title_year_match else None
                if year is None or (year >= year_start and (year_end is None or year <= year_end)):
                    return make, label

    return make, None


def is_target_vehicle(title: str | None, year: int | None = None) -> bool:
    make, model = extract_make_model(title, year)
    return make is not None and model is not None


# "make+model" style terms for scrapers that search via a query string.
SEARCH_TERMS = [
    "mercedes-benz+sl400",
]

# Plain make names for scrapers that can only filter by make (or not at all),
# relying on is_target_vehicle() as the real filter after fetching.
SEARCH_MAKES_ONLY = [
    "Mercedes-Benz",
]
