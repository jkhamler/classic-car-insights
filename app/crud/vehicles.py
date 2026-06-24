from sqlalchemy.orm import Session
from sqlalchemy import func as sql_func
from app.db.models.vehicle import Vehicle
from app.db.models.listing import Listing
from app.db.models.price_benchmark import PriceBenchmark
from app.schemas.vehicle import VehicleCreate


def get_vehicles(db: Session, skip: int = 0, limit: int = 50) -> list[Vehicle]:
    return db.query(Vehicle).order_by(Vehicle.make, Vehicle.model).offset(skip).limit(limit).all()


def get_vehicle(db: Session, vehicle_id: int) -> Vehicle | None:
    return db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()


def get_vehicle_by_identity(db: Session, make: str, model: str, generation: str | None = None) -> Vehicle | None:
    q = db.query(Vehicle).filter(Vehicle.make == make, Vehicle.model == model)
    if generation:
        q = q.filter(Vehicle.generation == generation)
    return q.first()


def create_vehicle(db: Session, vehicle: VehicleCreate) -> Vehicle:
    db_vehicle = Vehicle(**vehicle.model_dump())
    db.add(db_vehicle)
    db.commit()
    db.refresh(db_vehicle)
    return db_vehicle


def get_vehicle_summaries(db: Session, skip: int = 0, limit: int = 50) -> list[dict]:
    vehicles = get_vehicles(db, skip, limit)
    results = []
    for v in vehicles:
        active_count = db.query(sql_func.count(Listing.id)).filter(
            Listing.vehicle_id == v.id, Listing.status == "active"
        ).scalar()
        latest_benchmark = db.query(PriceBenchmark).filter(
            PriceBenchmark.vehicle_id == v.id
        ).order_by(PriceBenchmark.period.desc()).first()

        results.append({
            "id": v.id,
            "make": v.make,
            "model": v.model,
            "generation": v.generation,
            "year_start": v.year_start,
            "year_end": v.year_end,
            "current_avg_price": latest_benchmark.avg_price if latest_benchmark else None,
            "price_trend": latest_benchmark.price_trend if latest_benchmark else None,
            "active_listings": active_count,
        })
    return results
