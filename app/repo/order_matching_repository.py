from typing import List  # Import List for type hint

from sqlalchemy.orm import Session

from app.entity.order_matching import OrderMatching


class OrderMatchingRepository:
    def __init__(self, db: Session):
        self.db = db

    def save(self, order_matching: OrderMatching) -> OrderMatching:
        self.db.add(order_matching)
        self.db.commit()
        self.db.refresh(order_matching)
        return order_matching

    def get_by_order_id(self, order_id: int) -> List[OrderMatching]:
        return (
            self.db.query(OrderMatching)
            .filter(
                (OrderMatching.order_buy_id == order_id)
                | (OrderMatching.order_sell_id == order_id)
            )
            .all()
        )
