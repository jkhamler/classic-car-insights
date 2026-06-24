from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models.source import Source
from app.crud.listings import get_listings, get_listing, get_comparables
from app.schemas.listing import ListingRead, ListingSummary
from app.schemas.common import PaginatedResponse

router = APIRouter()


@router.get("", response_model=PaginatedResponse[ListingSummary])
def search_listings(
    make: str | None = None,
    model: str | None = None,
    year_min: int | None = None,
    year_max: int | None = None,
    price_min: float | None = None,
    price_max: float | None = None,
    min_score: float | None = None,
    source: str | None = None,
    status: str = "active",
    sort_by: str = "score",
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    items, total = get_listings(
        db, make=make, model=model, year_min=year_min, year_max=year_max,
        price_min=price_min, price_max=price_max, min_score=min_score,
        source_name=source, status=status, sort_by=sort_by,
        page=page, per_page=per_page,
    )
    summaries = []
    for l in items:
        src = db.query(Source).filter(Source.id == l.source_id).first()
        image_url = l.image_urls[0] if l.image_urls else None
        summaries.append(ListingSummary(
            id=l.id, title=l.title, listing_url=l.listing_url,
            make=l.make, model=l.model, year=l.year,
            asking_price=l.asking_price, price_gbp=l.price_gbp,
            currency=l.currency, location=l.location,
            source_name=src.display_name if src else None,
            undervaluation_score=l.undervaluation_score,
            status=l.status, scraped_at=l.scraped_at, image_url=image_url,
        ))

    return PaginatedResponse(
        items=summaries, total=total, page=page,
        per_page=per_page, has_next=(page * per_page < total),
    )


@router.get("/{listing_id}", response_model=ListingRead)
def get_listing_detail(listing_id: int, db: Session = Depends(get_db)):
    listing = get_listing(db, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing


@router.get("/{listing_id}/comparables", response_model=list[ListingSummary])
def get_listing_comparables(listing_id: int, limit: int = 10, db: Session = Depends(get_db)):
    listing = get_listing(db, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    comps = get_comparables(db, listing, limit=limit)
    results = []
    for l in comps:
        src = db.query(Source).filter(Source.id == l.source_id).first()
        image_url = l.image_urls[0] if l.image_urls else None
        results.append(ListingSummary(
            id=l.id, title=l.title, listing_url=l.listing_url,
            make=l.make, model=l.model, year=l.year,
            asking_price=l.asking_price, price_gbp=l.price_gbp,
            currency=l.currency, location=l.location,
            source_name=src.display_name if src else None,
            undervaluation_score=l.undervaluation_score,
            status=l.status, scraped_at=l.scraped_at, image_url=image_url,
        ))
    return results
