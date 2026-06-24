from pydantic import BaseModel
from datetime import datetime


class BenchmarkBase(BaseModel):
    vehicle_id: int
    period: str
    avg_price: float
    median_price: float | None = None
    min_price: float | None = None
    max_price: float | None = None
    sample_count: int
    price_trend: float | None = None
    currency: str = "GBP"


class BenchmarkCreate(BenchmarkBase):
    pass


class BenchmarkRead(BenchmarkBase):
    id: int
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class PricePoint(BaseModel):
    period: str
    avg_price: float
    sample_count: int
    price_trend: float | None = None
