from pydantic import BaseModel
from datetime import datetime


class ScoreBreakdown(BaseModel):
    price_vs_benchmark: float = 0
    mileage_adjustment: float = 0
    market_trend: float = 0
    scarcity: float = 0
    freshness: float = 0
    source_quality: float = 0
    total: float = 0
    explanation: str = ""


class ListingBase(BaseModel):
    title: str
    listing_url: str
    listing_type: str = "classified"
    make: str | None = None
    model: str | None = None
    year: int | None = None
    asking_price: float | None = None
    sale_price: float | None = None
    currency: str = "GBP"
    mileage: int | None = None
    transmission: str | None = None
    location: str | None = None


class ListingCreate(ListingBase):
    source_id: int
    external_id: str
    price_gbp: float | None = None
    mileage_unit: str = "miles"
    vin: str | None = None
    color: str | None = None
    description: str | None = None
    image_urls: list[str] | None = None
    listed_at: datetime | None = None
    auction_end_at: datetime | None = None


class ListingRead(ListingBase):
    id: int
    vehicle_id: int | None = None
    source_id: int
    external_id: str
    status: str
    price_gbp: float | None = None
    mileage_unit: str = "miles"
    vin: str | None = None
    color: str | None = None
    description: str | None = None
    image_urls: list[str] | None = None
    listed_at: datetime | None = None
    auction_end_at: datetime | None = None
    sold_at: datetime | None = None
    scraped_at: datetime | None = None
    undervaluation_score: float | None = None
    score_details: ScoreBreakdown | None = None
    scored_at: datetime | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class ListingSummary(BaseModel):
    id: int
    title: str
    listing_url: str
    make: str | None = None
    model: str | None = None
    year: int | None = None
    asking_price: float | None = None
    price_gbp: float | None = None
    currency: str = "GBP"
    location: str | None = None
    source_name: str | None = None
    undervaluation_score: float | None = None
    status: str = "active"
    scraped_at: datetime | None = None
    image_url: str | None = None

    model_config = {"from_attributes": True}
