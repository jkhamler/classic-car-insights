from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.db.models.price_benchmark import PriceBenchmark
from app.schemas.benchmark import BenchmarkCreate


def get_benchmarks_for_vehicle(
    db: Session, vehicle_id: int, limit: int = 24
) -> list[PriceBenchmark]:
    return (
        db.query(PriceBenchmark)
        .filter(PriceBenchmark.vehicle_id == vehicle_id)
        .order_by(desc(PriceBenchmark.period))
        .limit(limit)
        .all()
    )


def get_latest_benchmark(db: Session, vehicle_id: int) -> PriceBenchmark | None:
    return (
        db.query(PriceBenchmark)
        .filter(PriceBenchmark.vehicle_id == vehicle_id)
        .order_by(desc(PriceBenchmark.period))
        .first()
    )


def upsert_benchmark(db: Session, data: BenchmarkCreate) -> PriceBenchmark:
    existing = (
        db.query(PriceBenchmark)
        .filter(
            PriceBenchmark.vehicle_id == data.vehicle_id,
            PriceBenchmark.period == data.period,
            PriceBenchmark.currency == data.currency,
        )
        .first()
    )
    if existing:
        for key, value in data.model_dump().items():
            setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing

    benchmark = PriceBenchmark(**data.model_dump())
    db.add(benchmark)
    db.commit()
    db.refresh(benchmark)
    return benchmark
