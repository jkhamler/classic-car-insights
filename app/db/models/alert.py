from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, ForeignKey, func
from app.db.base import Base


class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), nullable=True)
    name = Column(String(200), nullable=False)
    alert_type = Column(String(30), nullable=False, default="new_listing")
    criteria_json = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True)
    notification_channel = Column(String(20), default="in_app")
    last_triggered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class AlertMatch(Base):
    __tablename__ = "alert_matches"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("public.alerts.id"), nullable=False, index=True)
    listing_id = Column(Integer, ForeignKey("public.listings.id"), nullable=False, index=True)
    triggered_at = Column(DateTime, nullable=False, server_default=func.now())
    was_seen = Column(Boolean, default=False)
