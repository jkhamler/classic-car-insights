from sqlalchemy import Column, Integer, String, Float, DateTime
from app.db.base import Base

class AuctionSale(Base):
    __tablename__ = "auction_sales"
    __table_args__ = {"schema": "public"}  # force public schema

    id = Column(Integer, primary_key=True)
    car_name = Column(String, nullable=False)
    sale_price = Column(Float)
    sale_date = Column(DateTime)