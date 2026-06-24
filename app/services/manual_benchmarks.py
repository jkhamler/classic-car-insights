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
    ("Porsche", "911", "997", 52000, 60, 6.2),
    ("Porsche", "Boxster", "986", 12000, 30, 5.0),
    ("Porsche", "Cayman", "987", 22000, 25, 7.0),
    ("Porsche", "944", "944", 15000, 20, 12.0),
    ("BMW", "M3", "E36", 22000, 35, 15.0),
    ("BMW", "M3", "E46", 28000, 50, 10.0),
    ("BMW", "M3", "E90/E92", 32000, 40, 5.5),
    ("BMW", "M5", "E39", 18000, 20, 8.0),
    ("BMW", "M5", "E60", 20000, 15, 3.0),
    ("Mercedes-Benz", "C63 AMG", "W204", 25000, 20, 4.0),
    ("Mercedes-Benz", "SL", "R129", 18000, 25, 6.0),
    ("Nissan", "Skyline GT-R", "R32", 55000, 15, 12.0),
    ("Nissan", "Skyline GT-R", "R33", 50000, 12, 10.0),
    ("Nissan", "Skyline GT-R", "R34", 120000, 10, 8.0),
    ("Nissan", "350Z", "Z33", 8000, 30, 4.0),
    ("Toyota", "Supra", "A80", 85000, 15, 5.0),
    ("Toyota", "MR2", "SW20", 12000, 20, 15.0),
    ("Honda", "NSX", "NA1/NA2", 75000, 12, 6.0),
    ("Honda", "S2000", "AP1/AP2", 25000, 25, 10.0),
    ("Honda", "Integra Type R", "DC2", 35000, 15, 12.0),
    ("Mazda", "RX-7", "FD", 40000, 10, 8.0),
    ("Mazda", "MX-5", "NA", 8000, 40, 10.0),
    ("Mazda", "MX-5", "NB", 5000, 35, 8.0),
    ("Mitsubishi", "Lancer Evolution", "VI", 45000, 10, 10.0),
    ("Mitsubishi", "Lancer Evolution", "VII-IX", 25000, 15, 8.0),
    ("Subaru", "Impreza WRX STI", "GD", 18000, 20, 6.0),
    ("Lotus", "Elise", "S1", 25000, 15, 8.0),
    ("Lotus", "Elise", "S2", 20000, 20, 5.0),
    ("Lotus", "Exige", "S2", 30000, 12, 7.0),
    ("Alfa Romeo", "GTV", "916", 8000, 15, 5.0),
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
