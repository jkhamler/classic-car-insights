from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.crud.timeshare import (
    list_shared_vehicles, get_shared_vehicle, create_shared_vehicle,
    list_co_owners, create_co_owner,
    list_vehicle_owners, link_owner_to_vehicle,
    list_bookings, create_booking, delete_booking, BookingConflictError,
    list_expenses, create_expense, delete_expense,
    get_vehicle_balance,
)
from app.schemas.timeshare import (
    SharedVehicleCreate, SharedVehicleRead,
    CoOwnerCreate, CoOwnerRead,
    VehicleOwnerCreate, VehicleOwnerRead,
    BookingCreate, BookingRead,
    ExpenseCreate, ExpenseRead,
    VehicleBalance,
)

router = APIRouter()


def _require_vehicle(db: Session, vehicle_id: int):
    vehicle = get_shared_vehicle(db, vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Shared vehicle not found")
    return vehicle


@router.get("/vehicles", response_model=list[SharedVehicleRead])
def list_vehicles(db: Session = Depends(get_db)):
    return list_shared_vehicles(db)


@router.post("/vehicles", response_model=SharedVehicleRead)
def create_vehicle(vehicle: SharedVehicleCreate, db: Session = Depends(get_db)):
    return create_shared_vehicle(db, vehicle)


@router.get("/co-owners", response_model=list[CoOwnerRead])
def list_owners(db: Session = Depends(get_db)):
    return list_co_owners(db)


@router.post("/co-owners", response_model=CoOwnerRead)
def create_owner(co_owner: CoOwnerCreate, db: Session = Depends(get_db)):
    return create_co_owner(db, co_owner)


@router.get("/vehicles/{vehicle_id}/owners", response_model=list[VehicleOwnerRead])
def list_owners_for_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    _require_vehicle(db, vehicle_id)
    return list_vehicle_owners(db, vehicle_id)


@router.post("/vehicles/{vehicle_id}/owners", response_model=VehicleOwnerRead)
def add_owner_to_vehicle(vehicle_id: int, link: VehicleOwnerCreate, db: Session = Depends(get_db)):
    _require_vehicle(db, vehicle_id)
    return link_owner_to_vehicle(db, vehicle_id, link)


@router.get("/vehicles/{vehicle_id}/bookings", response_model=list[BookingRead])
def list_vehicle_bookings(vehicle_id: int, db: Session = Depends(get_db)):
    _require_vehicle(db, vehicle_id)
    return list_bookings(db, vehicle_id)


@router.post("/vehicles/{vehicle_id}/bookings", response_model=BookingRead)
def create_vehicle_booking(vehicle_id: int, booking: BookingCreate, db: Session = Depends(get_db)):
    _require_vehicle(db, vehicle_id)
    try:
        return create_booking(db, vehicle_id, booking)
    except BookingConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.delete("/bookings/{booking_id}")
def delete_vehicle_booking(booking_id: int, db: Session = Depends(get_db)):
    if not delete_booking(db, booking_id):
        raise HTTPException(status_code=404, detail="Booking not found")
    return {"ok": True}


@router.get("/vehicles/{vehicle_id}/expenses", response_model=list[ExpenseRead])
def list_vehicle_expenses(vehicle_id: int, db: Session = Depends(get_db)):
    _require_vehicle(db, vehicle_id)
    return list_expenses(db, vehicle_id)


@router.post("/vehicles/{vehicle_id}/expenses", response_model=ExpenseRead)
def create_vehicle_expense(vehicle_id: int, expense: ExpenseCreate, db: Session = Depends(get_db)):
    _require_vehicle(db, vehicle_id)
    return create_expense(db, vehicle_id, expense)


@router.delete("/expenses/{expense_id}")
def delete_vehicle_expense(expense_id: int, db: Session = Depends(get_db)):
    if not delete_expense(db, expense_id):
        raise HTTPException(status_code=404, detail="Expense not found")
    return {"ok": True}


@router.get("/vehicles/{vehicle_id}/balance", response_model=VehicleBalance)
def get_balance(vehicle_id: int, db: Session = Depends(get_db)):
    _require_vehicle(db, vehicle_id)
    return get_vehicle_balance(db, vehicle_id)
