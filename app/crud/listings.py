from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.db.models.listing import Listing
from app.db.models.source import Source
from app.schemas.listing import ListingCreate


def get_listings(
    db: Session,
    *,
    make: str | None = None,
    model: str | None = None,
    year_min: int | None = None,
    year_max: int | None = None,
    price_min: float | None = None,
    price_max: float | None = None,
    min_score: float | None = None,
    source_name: str | None = None,
    status: str = "active",
    sort_by: str = "score",
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[Listing], int]:
    q = db.query(Listing)

    if status:
        q = q.filter(Listing.status == status)
    if make:
        q = q.filter(Listing.make.ilike(f"%{make}%"))
    if model:
        q = q.filter(Listing.model.ilike(f"%{model}%"))
    if year_min:
        q = q.filter(Listing.year >= year_min)
    if year_max:
        q = q.filter(Listing.year <= year_max)
    if price_min:
        q = q.filter(Listing.price_gbp >= price_min)
    if price_max:
        q = q.filter(Listing.price_gbp <= price_max)
    if min_score:
        q = q.filter(Listing.undervaluation_score >= min_score)
    if source_name:
        q = q.join(Source).filter(Source.name == source_name)

    total = q.count()

    if sort_by == "score":
        q = q.order_by(desc(Listing.undervaluation_score).nulls_last())
    elif sort_by == "price_asc":
        q = q.order_by(Listing.price_gbp.asc().nulls_last())
    elif sort_by == "price_desc":
        q = q.order_by(Listing.price_gbp.desc().nulls_last())
    elif sort_by == "date":
        q = q.order_by(desc(Listing.scraped_at))
    else:
        q = q.order_by(desc(Listing.undervaluation_score).nulls_last())

    items = q.offset((page - 1) * per_page).limit(per_page).all()
    return items, total


def get_listing(db: Session, listing_id: int) -> Listing | None:
    return db.query(Listing).filter(Listing.id == listing_id).first()


def get_listing_by_source(db: Session, source_id: int, external_id: str) -> Listing | None:
    return db.query(Listing).filter(
        Listing.source_id == source_id,
        Listing.external_id == external_id,
    ).first()


def upsert_listing(db: Session, data: ListingCreate) -> tuple[Listing, bool]:
    existing = get_listing_by_source(db, data.source_id, data.external_id)
    if existing:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing, False

    new_listing = Listing(**data.model_dump())
    db.add(new_listing)
    db.commit()
    db.refresh(new_listing)
    return new_listing, True


def get_comparables(db: Session, listing: Listing, limit: int = 10) -> list[Listing]:
    q = db.query(Listing).filter(
        Listing.id != listing.id,
        Listing.make == listing.make,
    )
    if listing.model:
        q = q.filter(Listing.model == listing.model)
    return q.order_by(desc(Listing.scraped_at)).limit(limit).all()


def get_top_opportunities(db: Session, limit: int = 20, make: str | None = None) -> list[Listing]:
    q = db.query(Listing).filter(
        Listing.status == "active",
        Listing.undervaluation_score.isnot(None),
    )
    if make:
        q = q.filter(Listing.make.ilike(f"%{make}%"))
    return q.order_by(desc(Listing.undervaluation_score)).limit(limit).all()


def count_active_for_vehicle(db: Session, vehicle_id: int) -> int:
    return db.query(Listing).filter(
        Listing.vehicle_id == vehicle_id,
        Listing.status == "active",
    ).count()
