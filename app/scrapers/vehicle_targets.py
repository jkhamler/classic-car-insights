"""Single source of truth for which makes/models the platform tracks.

Used by every scraper to build search terms and by BaseScraper.run() to
discard anything that isn't one of these — this is the "tighten to specific
models" filter, applied uniformly regardless of source.

One hunt currently tracked, per explicit request (replacing the earlier
Aston Martin modern-classics hunt and its cleared vehicle/listing data):
Mercedes-Benz S500 Coupe (C217 generation), 2015 onwards — open-ended, no
upper year bound, mirroring how the SL400 hunt before it was scoped.

The C217 generation's "S500" badge is reused elsewhere — most notably the
contemporary W222 S-Class SALOON also carries an "S500" badge — so title
matching requires both "S500" (or "S 500") AND "coupe" to appear, not just
the badge alone. The badge itself was also retired at the C217 facelift
(renamed S560 from ~2018), so requiring "S500" naturally scopes this to
the pre-facelift C217 cars rather than needing a closed year range.

No hard discovery-time gates (price, mileage, seller type, text) and no
scoring bonuses yet — no budget or feature preference has been stated for
this hunt, so none should be invented. Undervaluation is left entirely to
scoring.py's benchmark-vs-asking-price comparison. Add entries to the
dicts below once real preferences emerge, following the same per-(make,
model-label) shape used throughout this module.
"""
import re

# Per-(make, model-label) discovery price ceilings — not applied to
# benchmark sources, which need full-range sold prices to compute an
# accurate fair-value baseline across the whole market, not just what the
# buyer wants to see. Keyed by the exact (make, model) label pair
# extract_make_model() returns below. Omit a vehicle here for no ceiling.
# Empty — no budget stated yet.
DISCOVERY_PRICE_CEILINGS_GBP: dict[tuple[str, str], float] = {}

# Per-(make, model-label) discovery mileage ceilings, same shape/rationale
# as the price ceilings above. Omit a vehicle here for no ceiling.
DISCOVERY_MILEAGE_CEILINGS_MILES: dict[tuple[str, str], float] = {}

# Per-(make, model-label) required seller type for discovery sources —
# "private" or "trade". A listing whose source couldn't determine seller
# type at all (None) always gets the benefit of the doubt; this only
# excludes a listing whose seller type is positively known and doesn't
# match. Empty — no preference stated.
DISCOVERY_SELLER_TYPE_REQUIRED: dict[tuple[str, str], str] = {}

# Per-(make, model-label) preferred seller type: (label, seller_type,
# points) — a listing whose structured seller_type field matches gets
# `points` added to its score the same way a DISCOVERY_BONUS_TEXT_GROUPS
# match does (see scoring.py's compute_score). Empty — no preference
# stated.
DISCOVERY_SELLER_TYPE_BONUS: dict[tuple[str, str], tuple[str, str, float]] = {}


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


def seller_type_bonus_feature(make: str | None, model: str | None, seller_type: str | None) -> tuple[str, float] | None:
    """(label, points) if this listing's seller_type matches the preferred
    one in DISCOVERY_SELLER_TYPE_BONUS — used to add a scoring bonus, never
    to exclude."""
    if not make or not model or not seller_type:
        return None
    entry = DISCOVERY_SELLER_TYPE_BONUS.get((make, model))
    if not entry:
        return None
    label, preferred_type, points = entry
    return (label, points) if seller_type == preferred_type else None


# Desirable-but-not-gating features — each (label, synonyms, points,
# exclude_near) is text-matched (title + description, where fetched — see
# each scraper's module docstring for what text it actually captures), but
# a listing that doesn't mention one is scored, not excluded (see
# scoring.py's compute_score, which sums `points` for every matched
# group). label is the human-readable name shown in a listing's score
# explanation when matched. exclude_near works the same as in
# meets_required_text — a synonym occurrence doesn't count if an
# exclude_near word follows before the next " with " (see
# _synonym_matches_outside_context). Empty — no feature preference stated
# yet.
DISCOVERY_REQUIRED_TEXT_GROUPS: dict[tuple[str, str], list[tuple[list[str], list[str]]]] = {}

DISCOVERY_BONUS_TEXT_GROUPS: dict[tuple[str, str], list[tuple[str, list[str], float, list[str]]]] = {}


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
    return [
        (label, points)
        for label, synonyms, points, exclude_near in groups
        if any(_synonym_matches_outside_context(combined, s, exclude_near) for s in synonyms)
    ]


def discovery_required_text_groups(make: str | None, model: str | None) -> list[tuple[list[str], list[str]]] | None:
    if not make or not model:
        return None
    return DISCOVERY_REQUIRED_TEXT_GROUPS.get((make, model))


def _synonym_matches_outside_context(combined: str, synonym: str, exclude_near: list[str]) -> bool:
    """True if `synonym` occurs in `combined` at least once without one of
    exclude_near appearing before the next " with " — guards against e.g.
    "white leather interior" counting as a white EXTERIOR mention when a
    future bonus/required text group cares about exterior colour."""
    window = 40
    start = 0
    while True:
        idx = combined.find(synonym, start)
        if idx == -1:
            return False
        after = combined[idx + len(synonym):idx + len(synonym) + window]
        exclude_idx = min((after.find(w) for w in exclude_near if w in after), default=-1)
        with_idx = after.find(" with ")
        if exclude_idx == -1 or (with_idx != -1 and with_idx < exclude_idx):
            return True
        start = idx + len(synonym)


def meets_required_text(make: str | None, model: str | None, *texts: str | None) -> bool:
    groups = discovery_required_text_groups(make, model)
    if not groups:
        return True
    combined = " ".join(t for t in texts if t).lower()
    return all(
        any(_synonym_matches_outside_context(combined, synonym, exclude_near) for synonym in synonyms)
        for synonyms, exclude_near in groups
    )

# Order matters: more specific keys must come before substrings they contain.
MAKE_MAP: dict[str, str] = {
    "mercedes-benz": "Mercedes-Benz",
    "mercedes benz": "Mercedes-Benz",
    "mercedes": "Mercedes-Benz",
}

# "S500" (or "S 500") word-bounded so it doesn't match "S5000" or a stray
# "500" elsewhere in the title. "Coupe"/"coupé" must also appear — the
# badge alone is ambiguous with the W222 S-Class SALOON, which was sold
# alongside it under the same "S500" name. Year gate (open-ended from
# 2015) uses the same "benefit of the doubt when year unknown" rule as
# every other hunt here; it's not load-bearing for generation
# disambiguation the way it was for SL400/Vantage/DBS, since the "S500"
# badge itself was retired at the C217 facelift (renamed S560), but it's
# kept for consistency and to exclude any pre-2015 badge reuse.
MERCEDES_S500_RE = re.compile(r"\bs\s?500\b")
MERCEDES_COUPE_RE = re.compile(r"\bcoup[eé]\b")

# (regex, label, year_start, year_end) — checked in order; year_end=None
# means open-ended (no upper bound).
MERCEDES_S_CLASS_MODELS: list[tuple[re.Pattern, str, int, int | None]] = [
    (MERCEDES_S500_RE, "S500 Coupe", 2015, None),
]

MODEL_PATTERNS_BY_MAKE: dict[str, list[tuple[str, str]]] = {}


def extract_make_model(title: str | None, year: int | None = None) -> tuple[str | None, str | None]:
    """`year`: pass the listing's own structured year field when the caller
    has one. Several sources (AutoTrader confirmed live, for the earlier
    SL400 hunt) never embed a year in the title text at all — it only
    lives in a separate field — so relying on regex-scraping the title
    alone silently defeats every year-gate below via its "benefit of the
    doubt" fallback, letting completely wrong model years through. Falls
    back to scanning the title only when no structured year is supplied.
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
        if not MERCEDES_COUPE_RE.search(lowered):
            return make, None
        for pattern, label, year_start, year_end in MERCEDES_S_CLASS_MODELS:
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
    "mercedes-benz+s500+coupe",
]

# Plain make names for scrapers that can only filter by make (or not at all),
# relying on is_target_vehicle() as the real filter after fetching.
SEARCH_MAKES_ONLY = [
    "Mercedes-Benz",
]
