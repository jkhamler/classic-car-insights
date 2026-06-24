from pydantic import BaseModel
from app.schemas.listing import ListingSummary


class DashboardStats(BaseModel):
    total_listings: int = 0
    total_vehicles: int = 0
    opportunities_this_week: int = 0
    active_alerts: int = 0


class DashboardResponse(BaseModel):
    stats: DashboardStats
    top_opportunities: list[ListingSummary] = []


class MarketMover(BaseModel):
    vehicle_id: int
    make: str
    model: str
    generation: str | None = None
    price_change_pct: float
    current_avg: float
    previous_avg: float
    period: str
