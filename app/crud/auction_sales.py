from sqlalchemy.orm import Session
from app.db.models.auction_sale import AuctionSale
from app.schemas.auction_sale import AuctionSaleCreate

def get_auction_sales(db: Session, skip: int = 0, limit: int = 100):
    return db.query(AuctionSale).offset(skip).limit(limit).all()

def create_auction_sale(db: Session, sale: AuctionSaleCreate):
    db_sale = AuctionSale(**sale.dict())
    db.add(db_sale)
    db.commit()
    db.refresh(db_sale)
    return db_sale
