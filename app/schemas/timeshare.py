from pydantic import BaseModel
from datetime import date, datetime


class SharedVehicleBase(BaseModel):
    name: str
    make: str | None = None
    model: str | None = None
    year: int | None = None
    registration_plate: str | None = None
    notes: str | None = None


class SharedVehicleCreate(SharedVehicleBase):
    pass


class SharedVehicleRead(SharedVehicleBase):
    id: int
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class CoOwnerBase(BaseModel):
    name: str
    email: str | None = None


class CoOwnerCreate(CoOwnerBase):
    pass


class CoOwnerRead(CoOwnerBase):
    id: int
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class VehicleOwnerBase(BaseModel):
    co_owner_id: int


class VehicleOwnerCreate(VehicleOwnerBase):
    pass


class VehicleOwnerRead(VehicleOwnerBase):
    id: int
    shared_vehicle_id: int
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class BookingBase(BaseModel):
    co_owner_id: int
    start_date: date
    end_date: date
    notes: str | None = None


class BookingCreate(BookingBase):
    pass


class BookingRead(BookingBase):
    id: int
    shared_vehicle_id: int
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class ExpenseBase(BaseModel):
    co_owner_id: int
    contribution_type: str = "cash"
    category: str = "other"
    amount: float
    currency: str = "GBP"
    expense_date: date
    description: str | None = None


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseRead(ExpenseBase):
    id: int
    shared_vehicle_id: int
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class BalanceEntry(BaseModel):
    co_owner_id: int
    name: str
    total_contributed: float
    fair_share: float
    net_balance: float


class VehicleBalance(BaseModel):
    shared_vehicle_id: int
    currency: str
    entries: list[BalanceEntry]
