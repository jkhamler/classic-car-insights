from datetime import date
from pydantic import BaseModel
from typing import Optional


class AuctionSaleBase(BaseModel):
    car_name: str
    make: Optional[str] = None
    model: Optional[str] = None
    sale_price: Optional[float] = None
    sale_date: Optional[date] = None
    vin: Optional[str] = None
    mileage: Optional[int] = None
    year: Optional[int] = None
    source: Optional[str] = None
    url: Optional[str] = None

class AuctionSaleCreate(AuctionSaleBase):
    pass

class AuctionSaleRead(AuctionSaleBase):
    id: int

    class Config:
        from_attributes = True


class PriceTrendPoint(BaseModel):
    period: str
    avg_price: float
    min_price: float
    max_price: float
    count: int


class PriceTrendSeries(BaseModel):
    make: str
    data: list[PriceTrendPoint]
    avg_price: float
    total_count: int


class PriceTrendResponse(BaseModel):
    series: list[PriceTrendSeries]


class FilterOptions(BaseModel):
    makes: list[str]
    models: list[str]
    years: list[int]


class ImportResponse(BaseModel):
    imported: int
    make: str
    model: Optional[str] = None
