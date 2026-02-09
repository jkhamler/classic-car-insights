from typing import Union
from sqlalchemy import func, extract
from sqlalchemy.orm import Session
from app.db.models.auction_sale import AuctionSale
from app.schemas.auction_sale import AuctionSaleCreate


def get_auction_sales(db: Session, skip: int = 0, limit: int = 100):
    """
    Retrieve a list of auction sales from the database with pagination.

    Args:
        db (Session): SQLAlchemy session
        skip (int): Number of records to skip
        limit (int): Maximum number of records to return

    Returns:
        List[AuctionSale]: List of AuctionSale objects
    """
    return db.query(AuctionSale).offset(skip).limit(limit).all()


def create_auction_sale(db: Session, sale: Union[AuctionSaleCreate, dict]):
    """
    Create a new auction sale record in the database.
    Accepts either a Pydantic model or a plain dict from the API.

    Args:
        db (Session): SQLAlchemy session
        sale (Union[AuctionSaleCreate, dict]): Sale data

    Returns:
        AuctionSale: The created AuctionSale object
    """
    if isinstance(sale, dict):
        db_sale = AuctionSale(**sale)
    else:  # Pydantic model
        db_sale = AuctionSale(**sale.dict())

    db.add(db_sale)
    db.commit()
    db.refresh(db_sale)
    return db_sale


def get_price_trends(
    db: Session,
    makes: list[str] | None = None,
    model: str | None = None,
    year_min: int | None = None,
    year_max: int | None = None,
) -> list[dict]:
    """
    Aggregate average/min/max sale price grouped by make and year-month.
    Returns a list of dicts with keys: make, period, avg_price, min_price, max_price, count.
    """
    year_col = extract("year", AuctionSale.sale_date)
    month_col = extract("month", AuctionSale.sale_date)

    query = db.query(
        AuctionSale.make,
        year_col.label("yr"),
        month_col.label("mo"),
        func.avg(AuctionSale.sale_price).label("avg_price"),
        func.min(AuctionSale.sale_price).label("min_price"),
        func.max(AuctionSale.sale_price).label("max_price"),
        func.count().label("cnt"),
    ).filter(
        AuctionSale.sale_price.isnot(None),
        AuctionSale.sale_date.isnot(None),
        AuctionSale.make.isnot(None),
    )

    if makes:
        query = query.filter(AuctionSale.make.in_(makes))
    if model:
        query = query.filter(AuctionSale.model == model)
    if year_min is not None:
        query = query.filter(AuctionSale.year >= year_min)
    if year_max is not None:
        query = query.filter(AuctionSale.year <= year_max)

    rows = (
        query.group_by(AuctionSale.make, year_col, month_col)
        .order_by(year_col, month_col)
        .all()
    )

    return [
        {
            "make": r.make,
            "period": f"{int(r.yr)}-{int(r.mo):02d}",
            "avg_price": round(float(r.avg_price), 2),
            "min_price": round(float(r.min_price), 2),
            "max_price": round(float(r.max_price), 2),
            "count": r.cnt,
        }
        for r in rows
    ]


def get_filter_options(db: Session) -> dict:
    """
    Return distinct makes, models, and years available in the database.
    """
    makes = [
        r[0]
        for r in db.query(AuctionSale.make)
        .filter(AuctionSale.make.isnot(None))
        .distinct()
        .order_by(AuctionSale.make)
        .all()
    ]
    models = [
        r[0]
        for r in db.query(AuctionSale.model)
        .filter(AuctionSale.model.isnot(None))
        .distinct()
        .order_by(AuctionSale.model)
        .all()
    ]
    years = [
        r[0]
        for r in db.query(AuctionSale.year)
        .filter(AuctionSale.year.isnot(None))
        .distinct()
        .order_by(AuctionSale.year)
        .all()
    ]
    return {"makes": makes, "models": models, "years": years}
