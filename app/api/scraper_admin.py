import asyncio
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.scrapers.registry import get_scraper_class, get_available_scrapers
from app.crud.scrape_runs import get_recent_runs
from app.services.scoring import score_all_active
from app.services.benchmark_calculator import recalculate_benchmarks
from app.services.vehicle_matcher import match_vehicle
from app.db.models.listing import Listing

router = APIRouter()


@router.post("/scrape/{source_name}")
async def trigger_scrape(source_name: str, db: Session = Depends(get_db)):
    cls = get_scraper_class(source_name)
    if not cls:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown scraper: {source_name}. Available: {get_available_scrapers()}",
        )

    scraper = cls(db)
    result = await scraper.run()

    _match_unmatched(db)

    return {
        "source": source_name,
        "listings_found": result.listings_found,
        "listings_new": result.listings_new,
        "listings_updated": result.listings_updated,
        "errors": result.errors[:5],
    }


@router.get("/scrape-runs")
def list_scrape_runs(limit: int = 20, db: Session = Depends(get_db)):
    runs = get_recent_runs(db, limit=limit)
    return [
        {
            "id": r.id,
            "source_id": r.source_id,
            "started_at": r.started_at,
            "completed_at": r.completed_at,
            "status": r.status,
            "listings_found": r.listings_found,
            "listings_new": r.listings_new,
            "listings_updated": r.listings_updated,
            "duration_seconds": r.duration_seconds,
            "error_message": r.error_message,
        }
        for r in runs
    ]


@router.post("/score/refresh")
def refresh_scores(db: Session = Depends(get_db)):
    scored = score_all_active(db)
    return {"scored": scored}


@router.post("/benchmarks/recalculate")
def recalc_benchmarks(db: Session = Depends(get_db)):
    updated = recalculate_benchmarks(db)
    return {"benchmark_periods_updated": updated}


@router.post("/match-vehicles")
def match_unmatched(db: Session = Depends(get_db)):
    matched = _match_unmatched(db)
    return {"matched": matched}


def _match_unmatched(db: Session) -> int:
    unmatched = db.query(Listing).filter(Listing.vehicle_id.is_(None)).all()
    matched = 0
    for listing in unmatched:
        vehicle = match_vehicle(db, listing.make, listing.model, listing.title, listing.year)
        if vehicle:
            listing.vehicle_id = vehicle.id
            matched += 1
    db.commit()
    return matched
