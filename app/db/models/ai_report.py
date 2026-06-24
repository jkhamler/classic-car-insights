from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey, func
from app.db.base import Base


class AIReport(Base):
    __tablename__ = "ai_reports"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True, index=True)
    report_type = Column(String(30), nullable=False, index=True)
    title = Column(String(500), nullable=True)
    content = Column(Text, nullable=False)
    vehicle_id = Column(Integer, ForeignKey("public.vehicles.id"), nullable=True)
    listing_id = Column(Integer, ForeignKey("public.listings.id"), nullable=True)
    metadata_json = Column(JSON, nullable=True)
    generated_at = Column(DateTime, nullable=False, server_default=func.now())
    expires_at = Column(DateTime, nullable=True)
