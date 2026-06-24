from pydantic import BaseModel
from datetime import datetime


class ReportRead(BaseModel):
    id: int
    report_type: str
    title: str | None = None
    content: str
    vehicle_id: int | None = None
    listing_id: int | None = None
    generated_at: datetime
    expires_at: datetime | None = None

    model_config = {"from_attributes": True}
