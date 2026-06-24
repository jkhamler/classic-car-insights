from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, UniqueConstraint, func
from app.db.base import Base


class PriceBenchmark(Base):
    __tablename__ = "price_benchmarks"
    __table_args__ = (
        UniqueConstraint("vehicle_id", "period", "currency", name="uq_benchmark_vehicle_period"),
        {"schema": "public"},
    )

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("public.vehicles.id"), nullable=False, index=True)
    period = Column(String(7), nullable=False)  # "YYYY-MM"
    avg_price = Column(Float, nullable=False)
    median_price = Column(Float, nullable=True)
    min_price = Column(Float, nullable=True)
    max_price = Column(Float, nullable=True)
    sample_count = Column(Integer, nullable=False)
    price_trend = Column(Float, nullable=True)
    currency = Column(String(3), default="GBP")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
