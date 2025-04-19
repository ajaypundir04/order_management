from app.dto.order_request import OrderRequest
from app.entity.order import Order
from app.utils.logger import get_logger

logger = get_logger("order_mapper")

class OrderMapper:
    def to_entity(self, order_request: OrderRequest, order_id: str) -> Order:
        """
        Maps an OrderRequest DTO to an Order entity.

        Args:
            order_request: The OrderRequest DTO.
            order_id: The unique ID for the order.

        Returns:
            An Order entity.
        """
        db_order = Order(
            order_id=order_id,  # Use order_id
            type=order_request.type_.value,
            side=order_request.side.value,
            instrument=order_request.instrument,
            limit_price=order_request.limit_price,
            quantity=order_request.quantity,
        )
        logger.debug(f"Mapped OrderRequest to entity: {order_id}")
        return db_order

    def to_response(self, order: Order) -> dict:
        """
        Maps an Order entity to a response dictionary.

        Args:
            order: The Order entity.

        Returns:
            A dictionary representing the order.
        """
        response = {
            "id": order.order_id,  # Use order.order_id
            "created_at": order.created_at.isoformat(),
            "type": order.type,
            "side": order.side,
            "instrument": order.instrument,
            "limit_price": order.limit_price,
            "quantity": order.quantity,
        }
        logger.debug(f"Mapped entity to response: {order.order_id}")
        return response
