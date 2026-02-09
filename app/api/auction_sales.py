from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.schemas.auction_sale import (
    AuctionSaleRead,
    AuctionSaleCreate,
    PriceTrendResponse,
    PriceTrendSeries,
    FilterOptions,
    ImportResponse,
)
from app.crud import auction_sales as crud
from app.db.session import get_db
from app.services.populate_db import populate_auction_sales

router = APIRouter()


@router.get("", response_model=list[AuctionSaleRead])
def read_auction_sales(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_auction_sales(db, skip=skip, limit=limit)


@router.post("", response_model=AuctionSaleRead)
def create_auction_sale(sale: AuctionSaleCreate, db: Session = Depends(get_db)):
    return crud.create_auction_sale(db, sale)


@router.post("/import", response_model=ImportResponse)
def import_auction_sales(
    make: str = Query(..., description="Car make to import"),
    model: str | None = Query(None, description="Car model to filter"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    count = populate_auction_sales(make=make, model=model, limit=limit, db=db)
    return ImportResponse(imported=count, make=make, model=model)


@router.get("/trends", response_model=PriceTrendResponse)
def get_trends(
    make: list[str] | None = Query(None),
    model: str | None = Query(None),
    year_min: int | None = Query(None),
    year_max: int | None = Query(None),
    db: Session = Depends(get_db),
):
    rows = crud.get_price_trends(db, makes=make, model=model, year_min=year_min, year_max=year_max)

    # Group rows by make into series
    series_map: dict[str, list] = {}
    for row in rows:
        series_map.setdefault(row["make"], []).append(row)

    series = []
    for make_name, points in series_map.items():
        total_count = sum(p["count"] for p in points)
        weighted_sum = sum(p["avg_price"] * p["count"] for p in points)
        avg_price = round(weighted_sum / total_count, 2) if total_count > 0 else 0
        series.append(
            PriceTrendSeries(
                make=make_name,
                data=points,
                avg_price=avg_price,
                total_count=total_count,
            )
        )

    return PriceTrendResponse(series=series)


@router.get("/filters", response_model=FilterOptions)
def get_filters(db: Session = Depends(get_db)):
    return crud.get_filter_options(db)
