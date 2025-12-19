from typing import Union
from sqlalchemy.orm import Session
from app.db.models.auction_sale import AuctionSale
from app.schemas.auction_sale import AuctionSaleCreate

def get_auction_sales(db: Session, skip: int = 0, limit: int = 100):
    """
    Retrieve a list of auction sales from the database with pagination.

    Args:
        db (Session): SQLAlchemy session
        skip (int): Number of records to skip
        limit (int): Maximum number of records to return

    Returns:
        List[AuctionSale]: List of AuctionSale objects
    """
    return db.query(AuctionSale).offset(skip).limit(limit).all()


def create_auction_sale(db: Session, sale: Union[AuctionSaleCreate, dict]):
    """
    Create a new auction sale record in the database.
    Accepts either a Pydantic model or a plain dict from the API.

    Args:
        db (Session): SQLAlchemy session
        sale (Union[AuctionSaleCreate, dict]): Sale data

    Returns:
        AuctionSale: The created AuctionSale object
    """
    if isinstance(sale, dict):
        db_sale = AuctionSale(**sale)
    else:  # Pydantic model
        db_sale = AuctionSale(**sale.dict())

    db.add(db_sale)
    db.commit()
    db.refresh(db_sale)
    return db_sale
