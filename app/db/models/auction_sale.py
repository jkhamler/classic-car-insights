from sqlalchemy import Column, Integer, String, Float, Date, Text
from app.db.base import Base

class AuctionSale(Base):
    __tablename__ = "auction_sales"
    __table_args__ = {"schema": "public"}  # force public schema

    id = Column(Integer, primary_key=True, index=True)
    car_name = Column(String, nullable=False)
    make = Column(String(100), nullable=True, index=True)
    model = Column(String(200), nullable=True)
    sale_price = Column(Float, nullable=True)
    sale_date = Column(Date, nullable=True)
    vin = Column(String, nullable=True)
    mileage = Column(Integer, nullable=True)
    year = Column(Integer, nullable=True)
    source = Column(String, nullable=True)
    url = Column(Text, nullable=True)