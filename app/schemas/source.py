from pydantic import BaseModel
from datetime import datetime


class SourceBase(BaseModel):
    name: str
    display_name: str | None = None
    source_type: str  # "benchmark" or "discovery"
    base_url: str | None = None
    scraper_class: str | None = None
    is_active: bool = True
    scrape_frequency_minutes: int = 360


class SourceCreate(SourceBase):
    config_json: dict | None = None


class SourceRead(SourceBase):
    id: int
    last_scraped_at: datetime | None = None
    config_json: dict | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
