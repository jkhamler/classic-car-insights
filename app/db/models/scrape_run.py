from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, func
from app.db.base import Base


class ScrapeRun(Base):
    __tablename__ = "scrape_runs"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("public.sources.id"), nullable=False, index=True)
    started_at = Column(DateTime, nullable=False, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(20), nullable=False, default="running")
    listings_found = Column(Integer, default=0)
    listings_new = Column(Integer, default=0)
    listings_updated = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    duration_seconds = Column(Float, nullable=True)
