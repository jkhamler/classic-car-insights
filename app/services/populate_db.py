from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.crud.auction_sales import create_auction_sale
from app.services.old_cars_api import fetch_auction_sales


def populate_auction_sales(limit: int = 20):
    """
    Fetch auctions from the API and insert them into the database.
    """
    db: Session = SessionLocal()
    try:
        response = fetch_auction_sales(make="Porsche", limit=limit)
        auction_items = response["data"]

        for item in auction_items:
            create_auction_sale(
                db,
                sale={
                    "car_name": item["title"],
                    "sale_price": item.get("price"),
                    "sale_date": item.get("auction_end_date"),
                    "vin": item.get("vin"),
                    "mileage": item.get("mileage"),
                    "year": item.get("year"),
                    "source": item.get("source"),
                    "url": item.get("url")
                }
            )
    finally:
        db.close()


if __name__ == "__main__":
    populate_auction_sales()
