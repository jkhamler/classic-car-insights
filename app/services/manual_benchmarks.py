"""Seed benchmark data from known market prices for key models.
These are approximate averages from publicly available sold data (BaT, Hagerty, etc.)
Used to bootstrap the scoring engine until automated scraping fills in real data.
"""
from sqlalchemy.orm import Session
from app.crud.benchmarks import upsert_benchmark
from app.crud.vehicles import get_vehicle_by_identity
from app.schemas.benchmark import BenchmarkCreate

MANUAL_BENCHMARKS = [
    # (make, model, generation, avg_gbp, sample_est, trend_pct)
    ("Porsche", "911", "996", 35000, 45, 8.5),
    ("Lotus", "Elise", "S1", 25000, 15, 8.0),
    ("Lotus", "Elise", "S2", 20000, 20, 5.0),
]


def seed_manual_benchmarks(db: Session) -> int:
    created = 0
    period = "2026-06"

    for make, model, gen, avg_gbp, sample, trend in MANUAL_BENCHMARKS:
        vehicle = get_vehicle_by_identity(db, make, model, gen)
        if not vehicle:
            continue

        upsert_benchmark(db, BenchmarkCreate(
            vehicle_id=vehicle.id,
            period=period,
            avg_price=float(avg_gbp),
            median_price=float(avg_gbp) * 0.95,
            min_price=float(avg_gbp) * 0.6,
            max_price=float(avg_gbp) * 1.5,
            sample_count=sample,
            price_trend=trend,
            currency="GBP",
        ))
        created += 1

    return created
