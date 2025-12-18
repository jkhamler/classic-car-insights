from datetime import datetime
from pydantic import BaseModel

class AuctionSaleBase(BaseModel):
    car_name: str
    sale_price: float | None = None
    sale_date: datetime | None = None

class AuctionSaleCreate(AuctionSaleBase):
    pass

class AuctionSaleRead(AuctionSaleBase):
    id: int

    class Config:
        orm_mode = True
