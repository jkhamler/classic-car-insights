from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.auction_sale import AuctionSaleRead, AuctionSaleCreate
from app.crud import auction_sales as crud
from app.db.session import get_db  # dependency for DB session

router = APIRouter()

# Remove the trailing slash here
@router.get("", response_model=list[AuctionSaleRead])
def read_auction_sales(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_auction_sales(db, skip=skip, limit=limit)

@router.post("", response_model=AuctionSaleRead)
def create_auction_sale(sale: AuctionSaleCreate, db: Session = Depends(get_db)):
    return crud.create_auction_sale(db, sale)