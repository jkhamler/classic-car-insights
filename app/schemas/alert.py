from pydantic import BaseModel
from datetime import datetime


class AlertCriteria(BaseModel):
    make: str | None = None
    model: str | None = None
    year_min: int | None = None
    year_max: int | None = None
    max_price: float | None = None
    min_score: float | None = None


class AlertBase(BaseModel):
    name: str
    alert_type: str = "new_listing"
    criteria_json: AlertCriteria
    notification_channel: str = "in_app"


class AlertCreate(AlertBase):
    pass


class AlertRead(AlertBase):
    id: int
    user_id: str | None = None
    is_active: bool = True
    last_triggered_at: datetime | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class AlertMatchRead(BaseModel):
    id: int
    alert_id: int
    listing_id: int
    triggered_at: datetime
    was_seen: bool = False

    model_config = {"from_attributes": True}
