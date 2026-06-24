from sqlalchemy import (
    Column, Integer, String, Float, Text, Boolean, DateTime, Date,
    JSON, ForeignKey, UniqueConstraint, Index, func,
)
from app.db.base import Base


class Listing(Base):
    __tablename__ = "listings"
    __table_args__ = (
        UniqueConstraint("source_id", "external_id", name="uq_source_external"),
        Index("ix_listings_make_model_year", "make", "model", "year"),
        Index("ix_listings_score", "undervaluation_score", postgresql_nulls_not_distinct=False),
        {"schema": "public"},
    )

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("public.vehicles.id"), nullable=True, index=True)
    source_id = Column(Integer, ForeignKey("public.sources.id"), nullable=False, index=True)
    external_id = Column(String(500), nullable=False)
    title = Column(String(500), nullable=False)
    listing_url = Column(Text, nullable=False)
    listing_type = Column(String(20), nullable=False, default="classified")
    status = Column(String(20), nullable=False, default="active", index=True)

    asking_price = Column(Float, nullable=True)
    sale_price = Column(Float, nullable=True)
    currency = Column(String(3), default="GBP")
    price_gbp = Column(Float, nullable=True)

    make = Column(String(100), nullable=True)
    model = Column(String(200), nullable=True)
    year = Column(Integer, nullable=True)
    mileage = Column(Integer, nullable=True)
    mileage_unit = Column(String(10), default="miles")
    vin = Column(String(50), nullable=True)
    color = Column(String(100), nullable=True)
    transmission = Column(String(50), nullable=True)
    location = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    image_urls = Column(JSON, nullable=True)

    listed_at = Column(DateTime, nullable=True)
    auction_end_at = Column(DateTime, nullable=True)
    sold_at = Column(DateTime, nullable=True)
    scraped_at = Column(DateTime, nullable=False, server_default=func.now())

    undervaluation_score = Column(Float, nullable=True)
    score_details = Column(JSON, nullable=True)
    scored_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
