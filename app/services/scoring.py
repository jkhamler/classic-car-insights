"""Undervaluation scoring engine."""
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.db.models.listing import Listing
from app.db.models.source import Source
from app.crud.benchmarks import get_latest_benchmark
from app.crud.listings import count_active_for_vehicle

logger = logging.getLogger(__name__)

WEIGHTS = {
    "price_vs_benchmark": 0.40,
    "mileage_adjustment": 0.15,
    "market_trend": 0.15,
    "scarcity": 0.15,
    "freshness": 0.10,
    "source_quality": 0.05,
}


@dataclass
class ScoreBreakdown:
    price_vs_benchmark: float = 0.0
    mileage_adjustment: float = 0.0
    market_trend: float = 0.0
    scarcity: float = 0.0
    freshness: float = 0.0
    source_quality: float = 0.0
    total: float = 0.0
    explanation: str = ""

    def to_dict(self) -> dict:
        return {
            "price_vs_benchmark": self.price_vs_benchmark,
            "mileage_adjustment": self.mileage_adjustment,
            "market_trend": self.market_trend,
            "scarcity": self.scarcity,
            "freshness": self.freshness,
            "source_quality": self.source_quality,
            "total": self.total,
            "explanation": self.explanation,
        }


def _score_price(listing_price: float, benchmark_avg: float) -> float:
    if benchmark_avg <= 0:
        return 0.0
    ratio = listing_price / benchmark_avg
    return max(0.0, min(100.0, (1 - ratio) * 200))


def _score_mileage(mileage: int | None) -> float:
    if mileage is None:
        return 50.0
    if mileage < 50_000:
        return 80.0
    if mileage < 80_000:
        return 60.0
    if mileage < 120_000:
        return 40.0
    return 20.0


def _score_trend(price_trend: float | None) -> float:
    if price_trend is None:
        return 50.0
    return max(0.0, min(100.0, price_trend * 10 + 50))


def _score_scarcity(active_count: int) -> float:
    if active_count <= 1:
        return 95.0
    if active_count <= 3:
        return 80.0
    if active_count <= 5:
        return 60.0
    if active_count <= 10:
        return 40.0
    return max(0.0, 100 - active_count * 10)


def _score_freshness(scraped_at: datetime | None) -> float:
    if scraped_at is None:
        return 50.0
    age_days = (datetime.utcnow() - scraped_at).days
    if age_days <= 1:
        return 100.0
    if age_days <= 14:
        return max(0.0, 100 - (age_days * (100 / 14)))
    return 0.0


def _score_source(source_type: str) -> float:
    return 100.0 if source_type == "discovery" else 30.0


# Best-effort text scan — catches an explicit admission in the title or
# seller's own description, nothing more. Can't see photos or infer
# condition the seller didn't mention, so a clean score here is not a
# guarantee the car is actually good, only that nothing obvious was
# flagged in the text we have. Confirmed need live: a "40% below
# benchmark" listing turned out to have a broken seat control unit and a
# service coming due, mentioned only in its description, which nothing
# in scoring was reading before.
CONDITION_RED_FLAGS = [
    "spares or repair", "spares/repair", "spares or repairs",
    "non runner", "non-runner", "not running", "doesn't run", "does not run",
    "won't start", "does not start", "no mot", "sold as seen", "sold as spares",
    "project car", "needs work", "requires work", "needs attention",
    "accident damage", "damaged", "write off", "write-off", "salvage",
    "insurance write off", "cat c", "cat d", "cat n", "cat s",
    "head gasket", "engine fault", "gearbox fault", "clutch fault",
    "not working", "stopped working", "needs replacing", "needs reflashing",
]


def _condition_flags(listing: Listing) -> list[str]:
    text = " ".join(filter(None, [listing.title, listing.description])).lower()
    return [kw for kw in CONDITION_RED_FLAGS if kw in text]


def compute_score(db: Session, listing: Listing) -> ScoreBreakdown | None:
    price = listing.price_gbp or listing.asking_price
    if not price or price <= 0:
        return None

    benchmark = None
    if listing.vehicle_id:
        benchmark = get_latest_benchmark(db, listing.vehicle_id)

    if not benchmark:
        return None

    source = db.query(Source).filter(Source.id == listing.source_id).first()
    source_type = source.source_type if source else "discovery"

    active_count = 0
    if listing.vehicle_id:
        active_count = count_active_for_vehicle(db, listing.vehicle_id)

    price_score = _score_price(price, benchmark.avg_price)
    mileage_score = _score_mileage(listing.mileage)
    trend_score = _score_trend(benchmark.price_trend)
    scarcity_score = _score_scarcity(active_count)
    freshness_score = _score_freshness(listing.scraped_at)
    source_score = _score_source(source_type)

    total = (
        price_score * WEIGHTS["price_vs_benchmark"]
        + mileage_score * WEIGHTS["mileage_adjustment"]
        + trend_score * WEIGHTS["market_trend"]
        + scarcity_score * WEIGHTS["scarcity"]
        + freshness_score * WEIGHTS["freshness"]
        + source_score * WEIGHTS["source_quality"]
    )
    total = round(total, 1)

    parts = []
    if price_score > 60:
        discount_pct = round((1 - price / benchmark.avg_price) * 100)
        parts.append(f"{discount_pct}% below benchmark avg of £{benchmark.avg_price:,.0f}")
    if trend_score > 60:
        parts.append(f"model trending up ({benchmark.price_trend:+.1f}%)")
    if scarcity_score > 70:
        parts.append(f"only {active_count} active listing{'s' if active_count != 1 else ''}")
    if mileage_score > 70 and listing.mileage:
        parts.append(f"low mileage ({listing.mileage:,} {listing.mileage_unit})")

    explanation = ". ".join(parts) + "." if parts else "Score based on available data."

    # A cheap price with an explicit fault mentioned in the text is not a
    # bargain — it's priced that way for a reason. Penalize rather than
    # exclude, since a minor mention (e.g. one worn part) shouldn't bury a
    # listing as hard as a genuine "non runner, spares or repair" would.
    flags = _condition_flags(listing)
    if flags:
        penalty = min(60.0, 20.0 * len(flags))
        total = round(max(0.0, total - penalty), 1)
        shown = ", ".join(f'"{f}"' for f in flags[:3])
        explanation = f"⚠ Condition flag in listing text ({shown}) — verify before buying. " + explanation

    return ScoreBreakdown(
        price_vs_benchmark=round(price_score, 1),
        mileage_adjustment=round(mileage_score, 1),
        market_trend=round(trend_score, 1),
        scarcity=round(scarcity_score, 1),
        freshness=round(freshness_score, 1),
        source_quality=round(source_score, 1),
        total=total,
        explanation=explanation,
    )


def score_listing(db: Session, listing: Listing) -> bool:
    breakdown = compute_score(db, listing)
    if not breakdown:
        return False

    listing.undervaluation_score = breakdown.total
    listing.score_details = breakdown.to_dict()
    listing.scored_at = datetime.utcnow()
    db.commit()
    return True


def score_all_active(db: Session) -> int:
    listings = (
        db.query(Listing)
        .filter(Listing.status == "active", Listing.vehicle_id.isnot(None))
        .all()
    )
    scored = 0
    for listing in listings:
        if score_listing(db, listing):
            scored += 1
    logger.info(f"Scored {scored}/{len(listings)} active listings")
    return scored
