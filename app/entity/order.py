from sqlalchemy import Column, String, Integer, Float, DateTime, UniqueConstraint
from app.entity.base import Base
from datetime import datetime

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String(36), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    type = Column(String(10), nullable=False)
    side = Column(String(10), nullable=False)
    instrument = Column(String(12), nullable=False)
    limit_price = Column(Float, nullable=True)
    quantity = Column(Integer, nullable=False)
    status = Column(String(10), default="OPEN", nullable=False)

    __table_args__ = (UniqueConstraint('order_id', name='uq_order_id'),)