from datetime import date
from pydantic import BaseModel
from typing import Optional

class AuctionSaleBase(BaseModel):
    car_name: str
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
        from_attributes = True  # Pydantic V2 replacement for orm_mode
