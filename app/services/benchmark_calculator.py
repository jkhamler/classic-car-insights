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
