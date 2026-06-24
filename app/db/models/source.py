from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, JSON, func
from app.db.base import Base


class Source(Base):
    __tablename__ = "sources"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    display_name = Column(String(200), nullable=True)
    source_type = Column(String(20), nullable=False)  # "benchmark" or "discovery"
    base_url = Column(String(500), nullable=True)
    scraper_class = Column(String(200), nullable=True)
    is_active = Column(Boolean, default=True)
    scrape_frequency_minutes = Column(Integer, default=360)
    last_scraped_at = Column(DateTime, nullable=True)
    config_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
