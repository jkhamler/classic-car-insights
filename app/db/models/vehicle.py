from sqlalchemy import Column, Integer, String, DateTime, UniqueConstraint, func
from app.db.base import Base


class Vehicle(Base):
    __tablename__ = "vehicles"
    __table_args__ = (
        UniqueConstraint("make", "model", "generation", name="uq_vehicle_identity"),
        {"schema": "public"},
    )

    id = Column(Integer, primary_key=True, index=True)
    make = Column(String(100), nullable=False, index=True)
    model = Column(String(200), nullable=False)
    generation = Column(String(100), nullable=True)
    year_start = Column(Integer, nullable=True)
    year_end = Column(Integer, nullable=True)
    country_of_origin = Column(String(50), nullable=True)
    segment = Column(String(50), nullable=True)
    body_style = Column(String(50), nullable=True)
    engine_type = Column(String(100), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
