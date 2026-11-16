from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, UniqueConstraint, func
from app.db.base import Base


class SharedVehicle(Base):
    __tablename__ = "timeshare_vehicles"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    make = Column(String(50), nullable=True)
    model = Column(String(50), nullable=True)
    year = Column(Integer, nullable=True)
    registration_plate = Column(String(20), nullable=True)
    notes = Column(String(1000), nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class CoOwner(Base):
    __tablename__ = "timeshare_co_owners"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class VehicleOwner(Base):
    __tablename__ = "timeshare_vehicle_owners"
    __table_args__ = (
        UniqueConstraint("shared_vehicle_id", "co_owner_id", name="uq_vehicle_owner"),
        {"schema": "public"},
    )

    id = Column(Integer, primary_key=True, index=True)
    shared_vehicle_id = Column(Integer, ForeignKey("public.timeshare_vehicles.id"), nullable=False, index=True)
    co_owner_id = Column(Integer, ForeignKey("public.timeshare_co_owners.id"), nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now())


class Booking(Base):
    __tablename__ = "timeshare_bookings"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True, index=True)
    shared_vehicle_id = Column(Integer, ForeignKey("public.timeshare_vehicles.id"), nullable=False, index=True)
    co_owner_id = Column(Integer, ForeignKey("public.timeshare_co_owners.id"), nullable=False, index=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    notes = Column(String(500), nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class Expense(Base):
    __tablename__ = "timeshare_expenses"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True, index=True)
    shared_vehicle_id = Column(Integer, ForeignKey("public.timeshare_vehicles.id"), nullable=False, index=True)
    co_owner_id = Column(Integer, ForeignKey("public.timeshare_co_owners.id"), nullable=False, index=True)
    contribution_type = Column(String(10), nullable=False, default="cash")  # "cash" | "labour"
    category = Column(String(30), nullable=False, default="other")  # "insurance" | "servicing" | "fuel" | "other"
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="GBP")
    expense_date = Column(Date, nullable=False)
    description = Column(String(500), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
