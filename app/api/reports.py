from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.crud.reports import get_latest_report, get_report_for_listing, get_report_for_vehicle
from app.crud.listings import get_listing
from app.crud.vehicles import get_vehicle
from app.services.ai_analysis import generate_opportunity_explanation, generate_investment_thesis, generate_weekly_digest
from app.schemas.report import ReportRead

router = APIRouter()


@router.get("/weekly", response_model=ReportRead | None)
def get_weekly_digest_report(db: Session = Depends(get_db)):
    report = get_latest_report(db, "weekly_digest")
    if not report:
        content = generate_weekly_digest(db)
        if content:
            report = get_latest_report(db, "weekly_digest")
    return report


@router.get("/opportunity/{listing_id}", response_model=ReportRead | None)
def get_opportunity_report(listing_id: int, db: Session = Depends(get_db)):
    report = get_report_for_listing(db, listing_id)
    if report:
        return report

    listing = get_listing(db, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if not listing.vehicle_id or not listing.undervaluation_score:
        return None

    content = generate_opportunity_explanation(db, listing)
    if content:
        return get_report_for_listing(db, listing_id)
    return None


@router.get("/investment-thesis/{vehicle_id}", response_model=ReportRead | None)
def get_investment_thesis_report(vehicle_id: int, db: Session = Depends(get_db)):
    report = get_report_for_vehicle(db, vehicle_id)
    if report:
        return report

    vehicle = get_vehicle(db, vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    content = generate_investment_thesis(db, vehicle)
    if content:
        return get_report_for_vehicle(db, vehicle_id)
    return None
