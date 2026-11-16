from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.db.models.timeshare import SharedVehicle, CoOwner, VehicleOwner, Booking, Expense
from app.schemas.timeshare import (
    SharedVehicleCreate, CoOwnerCreate, VehicleOwnerCreate, BookingCreate, ExpenseCreate,
    BalanceEntry, VehicleBalance,
)


class BookingConflictError(Exception):
    pass


# Shared vehicles

def list_shared_vehicles(db: Session) -> list[SharedVehicle]:
    return db.query(SharedVehicle).order_by(SharedVehicle.id).all()


def get_shared_vehicle(db: Session, vehicle_id: int) -> SharedVehicle | None:
    return db.query(SharedVehicle).filter(SharedVehicle.id == vehicle_id).first()


def create_shared_vehicle(db: Session, vehicle: SharedVehicleCreate) -> SharedVehicle:
    db_vehicle = SharedVehicle(**vehicle.model_dump())
    db.add(db_vehicle)
    db.commit()
    db.refresh(db_vehicle)
    return db_vehicle


# Co-owners

def list_co_owners(db: Session) -> list[CoOwner]:
    return db.query(CoOwner).order_by(CoOwner.id).all()


def get_co_owner(db: Session, co_owner_id: int) -> CoOwner | None:
    return db.query(CoOwner).filter(CoOwner.id == co_owner_id).first()


def create_co_owner(db: Session, co_owner: CoOwnerCreate) -> CoOwner:
    db_co_owner = CoOwner(**co_owner.model_dump())
    db.add(db_co_owner)
    db.commit()
    db.refresh(db_co_owner)
    return db_co_owner


# Vehicle <-> co-owner links

def list_vehicle_owners(db: Session, vehicle_id: int) -> list[VehicleOwner]:
    return db.query(VehicleOwner).filter(VehicleOwner.shared_vehicle_id == vehicle_id).all()


def link_owner_to_vehicle(db: Session, vehicle_id: int, link: VehicleOwnerCreate) -> VehicleOwner:
    db_link = VehicleOwner(shared_vehicle_id=vehicle_id, co_owner_id=link.co_owner_id)
    db.add(db_link)
    db.commit()
    db.refresh(db_link)
    return db_link


# Bookings

def list_bookings(db: Session, vehicle_id: int) -> list[Booking]:
    return (
        db.query(Booking)
        .filter(Booking.shared_vehicle_id == vehicle_id)
        .order_by(Booking.start_date)
        .all()
    )


def create_booking(db: Session, vehicle_id: int, booking: BookingCreate) -> Booking:
    overlap = (
        db.query(Booking)
        .filter(
            Booking.shared_vehicle_id == vehicle_id,
            Booking.start_date <= booking.end_date,
            Booking.end_date >= booking.start_date,
        )
        .first()
    )
    if overlap:
        raise BookingConflictError(
            f"That date range clashes with an existing booking ({overlap.start_date} to {overlap.end_date})"
        )

    db_booking = Booking(shared_vehicle_id=vehicle_id, **booking.model_dump())
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    return db_booking


def delete_booking(db: Session, booking_id: int) -> bool:
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        return False
    db.delete(booking)
    db.commit()
    return True


# Expenses

def list_expenses(db: Session, vehicle_id: int) -> list[Expense]:
    return (
        db.query(Expense)
        .filter(Expense.shared_vehicle_id == vehicle_id)
        .order_by(desc(Expense.expense_date))
        .all()
    )


def create_expense(db: Session, vehicle_id: int, expense: ExpenseCreate) -> Expense:
    db_expense = Expense(shared_vehicle_id=vehicle_id, **expense.model_dump())
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    return db_expense


def delete_expense(db: Session, expense_id: int) -> bool:
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        return False
    db.delete(expense)
    db.commit()
    return True


# Balance

def get_vehicle_balance(db: Session, vehicle_id: int) -> VehicleBalance:
    owner_links = list_vehicle_owners(db, vehicle_id)
    co_owners = {link.co_owner_id: get_co_owner(db, link.co_owner_id) for link in owner_links}
    expenses = list_expenses(db, vehicle_id)

    currency = expenses[0].currency if expenses else "GBP"
    total_contributed_by_owner = {co_owner_id: 0.0 for co_owner_id in co_owners}
    for expense in expenses:
        total_contributed_by_owner[expense.co_owner_id] = (
            total_contributed_by_owner.get(expense.co_owner_id, 0.0) + expense.amount
        )

    total_expenses = sum(e.amount for e in expenses)
    num_owners = len(co_owners) or 1
    fair_share = total_expenses / num_owners

    entries = [
        BalanceEntry(
            co_owner_id=co_owner_id,
            name=co_owner.name if co_owner else "Unknown",
            total_contributed=total_contributed_by_owner.get(co_owner_id, 0.0),
            fair_share=fair_share,
            net_balance=total_contributed_by_owner.get(co_owner_id, 0.0) - fair_share,
        )
        for co_owner_id, co_owner in co_owners.items()
    ]

    return VehicleBalance(shared_vehicle_id=vehicle_id, currency=currency, entries=entries)
