from sqlalchemy.orm import sessionmaker, Session
from app.utils.logger import get_logger
import threading
import queue
import time
from app.entity.order import Order
from app.entity.order_matching import OrderMatching
from app.repo.order_matching_repository import OrderMatchingRepository
from app.stock_exchange import place_order, OrderPlacementError

logger = get_logger("stock_exchange_processor")

class StockExchangeProcessor:
    def __init__(self, session_factory: sessionmaker, max_retries: int = 3, retry_delay: float = 5.0):
        self.q = queue.Queue()
        self.session_factory = session_factory
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.retry_counts = {}
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()
        logger.info("StockExchangeProcessor thread started")

    def _worker(self):
        while True:
            order_id = self.q.get()
            logger.debug(f"Processing order ID: {order_id}")
            session = self.session_factory()
            order_matching_repo = OrderMatchingRepository(session)
            try:
                order = session.query(Order).get(order_id)
                if not order:
                    logger.debug(f"Order {order_id} not found")
                    session.commit()
                    self.retry_counts.pop(order_id, None)
                    continue

                if order.status not in ("OPEN", "SUBMITTED"):
                    logger.debug(f"Order {order_id} is not open or submitted")
                    session.commit()
                    self.retry_counts.pop(order_id, None)
                    continue

                # Temporarily treat SUBMITTED as OPEN for matching
                if order.status == "SUBMITTED":
                    order.status = "OPEN"
                    session.commit()

                matches = self._find_matches(session, order)
                if not matches:
                    logger.debug(f"No matches for order {order_id}")
                    try:
                        place_order(order)
                        order.status = "SUBMITTED"
                        session.commit()
                        logger.info(f"Order submitted to exchange without match: {order.id}")
                        self.retry_counts.pop(order_id, None)
                    except OrderPlacementError as e:
                        retry_count = self.retry_counts.get(order_id, 0)
                        if retry_count < self.max_retries and "Connection not available" in str(e):
                            self.retry_counts[order_id] = retry_count + 1
                            logger.warning(
                                f"Transient error for order {order_id} (attempt {retry_count + 1}/{self.max_retries}): {str(e)}. "
                                f"Re-enqueuing after {self.retry_delay}s delay."
                            )
                            session.commit()
                            time.sleep(self.retry_delay)
                            self.q.put(order_id)
                            continue
                        else:
                            logger.error(f"Failed to place order {order_id} after {retry_count} retries: {str(e)}")
                            order.status = "FAILED"
                            session.commit()
                            self.retry_counts.pop(order_id, None)
                            continue
                else:
                    remaining_quantity = order.quantity
                    for match in matches:
                        if remaining_quantity <= 0:
                            break

                        matched_quantity = min(remaining_quantity, match.quantity)
                        logger.debug(f"Matched order {order.id} with {match.id}: {matched_quantity} units")

                        # Record match
                        match_record = OrderMatching(
                            order_buy_id=order.id if order.side.lower() == "buy" else match.id,
                            order_sell_id=order.id if order.side.lower() == "sell" else match.id,
                            matched_quantity=matched_quantity,
                            instrument=order.instrument
                        )
                        order_matching_repo.save(match_record)

                        # Update quantities
                        order.quantity -= matched_quantity
                        match.quantity -= matched_quantity
                        order.status = "MATCHED" if order.quantity == 0 else "PARTIAL"
                        match.status = "MATCHED" if match.quantity == 0 else "PARTIAL"
                        remaining_quantity -= matched_quantity

                        logger.info(f"Updated orders: {order.id} ({order.quantity}), {match.id} ({match.quantity})")

                    session.commit()
                    logger.info(f"Order {order_id} processed successfully with matches")
                    self.retry_counts.pop(order_id, None)

            except Exception as e:
                logger.error(f"Failed to process order {order_id}: {str(e)}", exc_info=True)
                session.rollback()
                self.retry_counts.pop(order_id, None)
            finally:
                session.close()
                self.q.task_done()

    def _find_matches(self, session: Session, order: Order):
        opposite_side = "sell" if order.side.lower() == "buy" else "buy"
        query = session.query(Order).filter(
            Order.instrument == order.instrument,
            Order.side == opposite_side,
            Order.status.in_(["OPEN", "SUBMITTED"])  # Include SUBMITTED orders
        )
        if order.type.lower() == "limit":
            if order.side.lower() == "buy":
                query = query.filter(Order.limit_price <= order.limit_price)
            else:
                query = query.filter(Order.limit_price >= order.limit_price)
        query = query.order_by(Order.created_at.asc())
        return query.all()

    def enqueue(self, order: Order):
        logger.info(f"Enqueuing order: {order.id}")
        self.q.put(order.id)