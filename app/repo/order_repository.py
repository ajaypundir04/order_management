from sqlalchemy.orm import Session

from app.entity.order import Order


class OrderRepository:
    def __init__(self, db: Session):
        self.db = db

    def save(self, order: Order) -> Order:
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)
        return order
