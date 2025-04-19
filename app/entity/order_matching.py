from sqlalchemy import Column, Integer, BigInteger, DateTime, String, ForeignKey
from app.entity.base import Base
from datetime import datetime

class OrderMatching(Base):
    __tablename__ = "order_matching"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    order_buy_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    order_sell_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    matched_quantity = Column(Integer, nullable=False)
    matched_at = Column(DateTime, default=datetime.now, nullable=False)
    instrument = Column(String(12), nullable=False)