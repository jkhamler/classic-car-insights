from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.crud.reports import get_latest_report, get_report_for_listing, get_report_for_vehicle
from app.schemas.report import ReportRead

router = APIRouter()


@router.get("/weekly", response_model=ReportRead | None)
def get_weekly_digest(db: Session = Depends(get_db)):
    report = get_latest_report(db, "weekly_digest")
    if not report:
        return None
    return report


@router.get("/opportunity/{listing_id}", response_model=ReportRead | None)
def get_opportunity_report(listing_id: int, db: Session = Depends(get_db)):
    return get_report_for_listing(db, listing_id)


@router.get("/investment-thesis/{vehicle_id}", response_model=ReportRead | None)
def get_investment_thesis(vehicle_id: int, db: Session = Depends(get_db)):
    return get_report_for_vehicle(db, vehicle_id)
