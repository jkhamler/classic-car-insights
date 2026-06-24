from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db.session import get_db
from app.db.models.price_benchmark import PriceBenchmark
from app.db.models.vehicle import Vehicle
from app.schemas.dashboard import MarketMover

router = APIRouter()


@router.get("/movers", response_model=list[MarketMover])
def get_market_movers(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    benchmarks = (
        db.query(PriceBenchmark)
        .filter(PriceBenchmark.price_trend.isnot(None))
        .order_by(desc(PriceBenchmark.period))
        .limit(200)
        .all()
    )

    seen: dict[int, PriceBenchmark] = {}
    for b in benchmarks:
        if b.vehicle_id not in seen:
            seen[b.vehicle_id] = b

    sorted_benchmarks = sorted(seen.values(), key=lambda b: abs(b.price_trend or 0), reverse=True)[:limit]

    results = []
    for b in sorted_benchmarks:
        vehicle = db.query(Vehicle).filter(Vehicle.id == b.vehicle_id).first()
        if not vehicle:
            continue
        prev_avg = b.avg_price / (1 + (b.price_trend / 100)) if b.price_trend else b.avg_price
        results.append(MarketMover(
            vehicle_id=vehicle.id,
            make=vehicle.make,
            model=vehicle.model,
            generation=vehicle.generation,
            price_change_pct=b.price_trend or 0,
            current_avg=b.avg_price,
            previous_avg=round(prev_avg, 2),
            period=b.period,
        ))
    return results
