from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.crud.vehicles import get_vehicle, get_vehicle_summaries
from app.crud.benchmarks import get_benchmarks_for_vehicle
from app.schemas.vehicle import VehicleRead, VehicleSummary
from app.schemas.benchmark import BenchmarkRead, PricePoint

router = APIRouter()


@router.get("", response_model=list[VehicleSummary])
def list_vehicles(
    skip: int = 0,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    return get_vehicle_summaries(db, skip=skip, limit=limit)


@router.get("/{vehicle_id}", response_model=VehicleRead)
def get_vehicle_detail(vehicle_id: int, db: Session = Depends(get_db)):
    vehicle = get_vehicle(db, vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return vehicle


@router.get("/{vehicle_id}/price-history", response_model=list[PricePoint])
def get_price_history(
    vehicle_id: int,
    limit: int = Query(24, ge=1, le=120),
    db: Session = Depends(get_db),
):
    vehicle = get_vehicle(db, vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    benchmarks = get_benchmarks_for_vehicle(db, vehicle_id, limit=limit)
    return [
        PricePoint(
            period=b.period,
            avg_price=b.avg_price,
            sample_count=b.sample_count,
            price_trend=b.price_trend,
        )
        for b in reversed(benchmarks)
    ]
