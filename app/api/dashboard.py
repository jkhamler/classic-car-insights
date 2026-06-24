from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func as sql_func
from datetime import datetime, timedelta

from app.db.session import get_db
from app.db.models.listing import Listing
from app.db.models.vehicle import Vehicle
from app.db.models.source import Source
from app.crud.listings import get_top_opportunities
from app.crud.alerts import count_active_alerts
from app.schemas.dashboard import DashboardStats, DashboardResponse, MarketMover
from app.schemas.listing import ListingSummary

router = APIRouter()


def _listing_to_summary(listing: Listing, db: Session) -> ListingSummary:
    source = db.query(Source).filter(Source.id == listing.source_id).first()
    image_url = listing.image_urls[0] if listing.image_urls else None
    return ListingSummary(
        id=listing.id,
        title=listing.title,
        listing_url=listing.listing_url,
        make=listing.make,
        model=listing.model,
        year=listing.year,
        asking_price=listing.asking_price,
        price_gbp=listing.price_gbp,
        currency=listing.currency,
        location=listing.location,
        source_name=source.display_name if source else None,
        undervaluation_score=listing.undervaluation_score,
        status=listing.status,
        scraped_at=listing.scraped_at,
        image_url=image_url,
    )


@router.get("/top-opportunities", response_model=list[ListingSummary])
def top_opportunities(
    limit: int = Query(20, ge=1, le=100),
    make: str | None = None,
    db: Session = Depends(get_db),
):
    listings = get_top_opportunities(db, limit=limit, make=make)
    return [_listing_to_summary(l, db) for l in listings]


@router.get("/stats", response_model=DashboardStats)
def dashboard_stats(db: Session = Depends(get_db)):
    total_listings = db.query(sql_func.count(Listing.id)).filter(Listing.status == "active").scalar()
    total_vehicles = db.query(sql_func.count(Vehicle.id)).scalar()

    week_ago = datetime.utcnow() - timedelta(days=7)
    opportunities = db.query(sql_func.count(Listing.id)).filter(
        Listing.undervaluation_score >= 60,
        Listing.scraped_at >= week_ago,
        Listing.status == "active",
    ).scalar()

    active_alerts = count_active_alerts(db)

    return DashboardStats(
        total_listings=total_listings or 0,
        total_vehicles=total_vehicles or 0,
        opportunities_this_week=opportunities or 0,
        active_alerts=active_alerts,
    )
