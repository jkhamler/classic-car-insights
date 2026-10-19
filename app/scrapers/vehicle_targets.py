"""Single source of truth for which makes/models the platform tracks.

Used by every scraper to build search terms and by BaseScraper.run() to
discard anything that isn't one of these — this is the "tighten to specific
models" filter, applied uniformly regardless of source.

Two hunts currently tracked, both R231-generation Mercedes-Benz SL, both
under the same £18k / 80k-mile / private-seller / dark-exterior-over-
light-interior / Harman Kardon / AIRSCARF criteria — SL400 was added as a
second badge variant to compare directly against SL350 (the two are cross-
shopped as the "safer long-term bet" question), not as a separate hunt with
its own budget:
- Mercedes-Benz SL350 BlueEFFICIENCY, 2012-2015 only. Matched on "SL" +
  "350" together rather than requiring the literal "BlueEFFICIENCY" badge
  text, since that's an efficiency-package name Mercedes used broadly
  across its range and dealers often drop it from listing titles even when
  the car has it (it was effectively standard on every post-2012 SL350).
  Disambiguated from the visually identical R230-generation SL350
  (2006-2011, same "SL350" badge, older shape) via the 2012-2015 year gate
  instead, same "benefit of the doubt when unknown" pattern as every other
  hunt here.
- Mercedes-Benz SL400, 2015-2019. The facelifted R231's name for the same
  3.0L V6 biturbo slot SL350 occupied pre-facelift — same bodyshell/options
  list, no R230-era "SL400" badge to disambiguate against (unlike SL350),
  so the year gate here is mainly to exclude the later SL450 rebadge
  (2018+ in some markets) rather than a genuine lookalike risk. Treated as
  an open bound (2015-2019) rather than a tight one since UK market badge-
  switch timing varies by source/dealer.

Unlike the enthusiast/collector hunts both of these replaced (DB9, 996
Turbo, Jaguar XK — all dropped per explicit request), this is a mainstream
depreciation-curve car: plentiful supply, no scarcity premium, bought/sold
through ordinary classifieds rather than specialist auction houses. Both
hard-require, via DISCOVERY_REQUIRED_TEXT_GROUPS below: a dark exterior
colour and a light interior — excluded at discovery if the ad text doesn't
mention them, per explicit request. Harman Kardon audio and AIRSCARF were
originally hard-required too, but that produced zero live matches (too few
sellers spell either out in ad text even when fitted), so per explicit
follow-up they're DISCOVERY_BONUS_TEXT_GROUPS instead: still text-matched
the same way, but only add to a matching listing's score (see
scoring.py's FEATURE_BONUS_POINTS) rather than excluding a listing that
doesn't mention them.
"""
import re

# Per-(make, model-label) discovery price ceilings — not applied to
# benchmark sources, which need full-range sold prices to compute an
# accurate fair-value baseline across the whole market, not just what the
# buyer wants to see. Keyed by the exact (make, model) label pair
# extract_make_model() returns below. Omit a vehicle here for no ceiling.
DISCOVERY_PRICE_CEILINGS_GBP: dict[tuple[str, str], float] = {
    ("Mercedes-Benz", "SL350"): 18_000,
    ("Mercedes-Benz", "SL400"): 18_000,
}

# Per-(make, model-label) discovery mileage ceilings, same shape/rationale
# as the price ceilings above. Omit a vehicle here for no ceiling.
DISCOVERY_MILEAGE_CEILINGS_MILES: dict[tuple[str, str], float] = {
    ("Mercedes-Benz", "SL350"): 80_000,
    ("Mercedes-Benz", "SL400"): 80_000,
}

# Per-(make, model-label) required seller type for discovery sources —
# "private" or "trade". Like the ceilings above, this gives a listing the
# benefit of the doubt when the source couldn't determine seller type at
# all (None) rather than excluding it; it only excludes a listing whose
# seller type is positively known and doesn't match.
DISCOVERY_SELLER_TYPE_REQUIRED: dict[tuple[str, str], str] = {
    ("Mercedes-Benz", "SL350"): "private",
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
    # light interior
    [f"{colour} {noun}" for colour in _LIGHT_INTERIOR_COLOURS for noun in _LIGHT_INTERIOR_NOUNS],
]

DISCOVERY_REQUIRED_TEXT_GROUPS: dict[tuple[str, str], list[list[str]]] = {
    ("Mercedes-Benz", "SL350"): _SL_REQUIRED_TEXT_GROUPS,
    ("Mercedes-Benz", "SL400"): _SL_REQUIRED_TEXT_GROUPS,
}

# Desirable-but-not-gating features — each (label, synonyms) pair is
# text-matched the same way as the required groups above, but a listing
# that doesn't mention one is scored, not excluded (see scoring.py's
# FEATURE_BONUS_POINTS). label is the human-readable name shown in a
# listing's score explanation when matched.
_SL_BONUS_TEXT_GROUPS: list[tuple[str, list[str]]] = [
    ("Harman Kardon audio", ["harman kardon", "harman/kardon", "harman-kardon"]),
    ("AIRSCARF", ["airscarf", "air scarf"]),
]

DISCOVERY_BONUS_TEXT_GROUPS: dict[tuple[str, str], list[tuple[str, list[str]]]] = {
    ("Mercedes-Benz", "SL350"): _SL_BONUS_TEXT_GROUPS,
    ("Mercedes-Benz", "SL400"): _SL_BONUS_TEXT_GROUPS,
}


def matched_bonus_features(make: str | None, model: str | None, *texts: str | None) -> list[str]:
    """Labels of bonus feature groups (see DISCOVERY_BONUS_TEXT_GROUPS) found
    in the given texts — used to add a scoring bonus, never to exclude."""
    if not make or not model:
        return []
    groups = DISCOVERY_BONUS_TEXT_GROUPS.get((make, model))
    if not groups:
        return []
    combined = " ".join(t for t in texts if t).lower()
    return [label for label, synonyms in groups if any(s in combined for s in synonyms)]


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

# "SL" and the badge number together, either side of optional whitespace/
# hyphen — not the literal "BlueEFFICIENCY" badge text (see module
# docstring). Word-bounded on both ends so it doesn't match "SL 3500" or a
# stray "350"/"400" elsewhere in the title, and doesn't match other SL
# derivatives (SL55, SL63, SL500, SL350 CDI diesel-era siblings like
# SL250/SL280, SL450/SL500 post-2018 rebadges). Year gate (below) does the
# real generation disambiguation.
MERCEDES_SL350_RE = re.compile(r"\bsl\s*-?\s*350\b")
MERCEDES_SL400_RE = re.compile(r"\bsl\s*-?\s*400\b")

# (regex, label, year_start, year_end) — checked in order; year gate uses
# the same "benefit of the doubt when year unknown" rule as every other
# hunt here.
MERCEDES_SL_MODELS: list[tuple[re.Pattern, str, int, int]] = [
    (MERCEDES_SL350_RE, "SL350", 2012, 2015),
    (MERCEDES_SL400_RE, "SL400", 2015, 2019),
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
                if year is None or year_start <= year <= year_end:
                    return make, label

    return make, None


def is_target_vehicle(title: str | None, year: int | None = None) -> bool:
    make, model = extract_make_model(title, year)
    return make is not None and model is not None


# "make+model" style terms for scrapers that search via a query string.
SEARCH_TERMS = [
    "mercedes-benz+sl350",
    "mercedes-benz+sl400",
]

# Plain make names for scrapers that can only filter by make (or not at all),
# relying on is_target_vehicle() as the real filter after fetching.
SEARCH_MAKES_ONLY = [
    "Mercedes-Benz",
]
