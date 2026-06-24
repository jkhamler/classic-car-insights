from pydantic import BaseModel
from datetime import datetime


class VehicleBase(BaseModel):
    make: str
    model: str
    generation: str | None = None
    year_start: int | None = None
    year_end: int | None = None
    country_of_origin: str | None = None
    segment: str | None = None
    body_style: str | None = None
    engine_type: str | None = None


class VehicleCreate(VehicleBase):
    pass


class VehicleRead(VehicleBase):
    id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class VehicleSummary(BaseModel):
    id: int
    make: str
    model: str
    generation: str | None = None
    year_start: int | None = None
    year_end: int | None = None
    current_avg_price: float | None = None
    price_trend: float | None = None
    active_listings: int = 0

    model_config = {"from_attributes": True}
