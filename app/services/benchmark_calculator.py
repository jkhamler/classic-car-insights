"""Calculate price benchmarks from sold auction data."""
import logging
from datetime import datetime
from statistics import median

from sqlalchemy.orm import Session
from sqlalchemy import func as sql_func

from app.db.models.listing import Listing
from app.db.models.source import Source
from app.db.models.vehicle import Vehicle
from app.db.models.price_benchmark import PriceBenchmark
from app.crud.benchmarks import upsert_benchmark, get_latest_benchmark
from app.schemas.benchmark import BenchmarkCreate

logger = logging.getLogger(__name__)


MIN_FALLBACK_SAMPLE = 3


def recalculate_benchmarks(db: Session) -> int:
    vehicles = db.query(Vehicle).all()
    updated = 0

    for vehicle in vehicles:
        sold = (
            db.query(Listing)
            .join(Source)
            .filter(
                Listing.vehicle_id == vehicle.id,
                Listing.sale_price.isnot(None),
                Listing.price_gbp.isnot(None),
                Source.source_type == "benchmark",
            )
            .all()
        )

        if not sold:
            # No true sold-comp data yet — bring_a_trailer only scrapes
            # currently-live auctions, and hasn't turned up a match for
            # this vehicle. Fall back to the going asking-price rate
            # across every currently-active listing we know of (any
            # source, any seller type — this is about estimating the
            # real market rate, not about what gets shown as a buying
            # opportunity), so scoring — and therefore "which of these
            # is actually a bargain" — isn't permanently blank.
            if _recalculate_fallback_benchmark(db, vehicle.id):
                updated += 1
            continue

        by_period: dict[str, list[float]] = {}
        for listing in sold:
            date = listing.sold_at or listing.scraped_at
            if date:
                period = date.strftime("%Y-%m")
            else:
                period = datetime.utcnow().strftime("%Y-%m")
            by_period.setdefault(period, []).append(listing.price_gbp)

        sorted_periods = sorted(by_period.keys())
        prev_avg = None

        for period in sorted_periods:
            prices = by_period[period]
            avg_price = round(sum(prices) / len(prices), 2)
            med_price = round(median(prices), 2)
            trend = None
            if prev_avg and prev_avg > 0:
                trend = round(((avg_price - prev_avg) / prev_avg) * 100, 2)

            upsert_benchmark(db, BenchmarkCreate(
                vehicle_id=vehicle.id,
                period=period,
                avg_price=avg_price,
                median_price=med_price,
                min_price=min(prices),
                max_price=max(prices),
                sample_count=len(prices),
                price_trend=trend,
                currency="GBP",
            ))
            prev_avg = avg_price
            updated += 1

    logger.info(f"Recalculated {updated} benchmark periods")
    return updated


def _recalculate_fallback_benchmark(db: Session, vehicle_id: int) -> bool:
    listings = (
        db.query(Listing)
        .filter(
            Listing.vehicle_id == vehicle_id,
            Listing.status == "active",
            Listing.price_gbp.isnot(None),
        )
        .all()
    )
    if len(listings) < MIN_FALLBACK_SAMPLE:
        # Too few data points for a median to mean anything — a "market
        # rate" of one or two listings is just those listings' own price.
        return False

    prices = [listing.price_gbp for listing in listings]
    avg_price = round(sum(prices) / len(prices), 2)
    med_price = round(median(prices), 2)

    upsert_benchmark(db, BenchmarkCreate(
        vehicle_id=vehicle_id,
        period=datetime.utcnow().strftime("%Y-%m"),
        avg_price=avg_price,
        median_price=med_price,
        min_price=min(prices),
        max_price=max(prices),
        sample_count=len(prices),
        price_trend=None,  # single snapshot, not a time series — no trend yet
        currency="GBP",
    ))
    return True
