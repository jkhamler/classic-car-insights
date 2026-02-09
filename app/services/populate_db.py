from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.crud.auction_sales import create_auction_sale
from app.services.old_cars_api import fetch_auction_sales


def populate_auction_sales(make: str, model: str | None = None, limit: int = 20, db: Session | None = None) -> int:
    """
    Fetch auctions from the API and insert them into the database.
    Returns the count of imported records.
    """
    owns_session = db is None
    if owns_session:
        db = SessionLocal()
    try:
        response = fetch_auction_sales(make=make, model=model, limit=limit)
        auction_items = response["data"]
        count = 0

        for item in auction_items:
            create_auction_sale(
                db,
                sale={
                    "car_name": item["title"],
                    "make": make,
                    "model": model or item.get("model"),
                    "sale_price": item.get("price"),
                    "sale_date": item.get("auction_end_date"),
                    "vin": item.get("vin"),
                    "mileage": item.get("mileage"),
                    "year": item.get("year"),
                    "source": item.get("source"),
                    "url": item.get("url")
                }
            )
            count += 1

        return count
    finally:
        if owns_session:
            db.close()


if __name__ == "__main__":
    imported = populate_auction_sales(make="Porsche")
    print(f"Imported {imported} records")
