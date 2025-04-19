import queue
import threading
import time

from sqlalchemy.orm import Session, sessionmaker

from app.entity.order import Order
from app.entity.order_matching import OrderMatching
from app.repo.order_matching_repository import OrderMatchingRepository
from app.stock_exchange import OrderPlacementError, place_order
from app.utils.logger import get_logger

from .order_book import OrderBook

logger = get_logger("stock_exchange_processor")


class StockExchangeProcessor:
    def __init__(
        self,
        session_factory: sessionmaker,
        order_book: OrderBook,
        max_retries: int = 3,
        retry_delay: float = 5.0,
    ):
        self.q = queue.Queue()
        self.session_factory = session_factory
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.retry_counts = {}
        self.order_book = order_book
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
                    self.order_book.remove_order(order_id)
                    continue

                if order.status not in ("OPEN", "SUBMITTED"):
                    logger.debug(f"Order {order_id} is not open or submitted")
                    session.commit()
                    self.retry_counts.pop(order_id, None)
                    self.order_book.remove_order(order_id)
                    continue

                # Add order to order book
                self.order_book.add_order(order)

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
                        logger.info(
                            f"Order submitted to exchange without match: {order.id}"
                        )
                        self.retry_counts.pop(order_id, None)
                    except OrderPlacementError as e:
                        retry_count = self.retry_counts.get(order_id, 0)
                        if (
                            retry_count < self.max_retries
                            and "Connection not available" in str(e)
                        ):
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
                            logger.error(
                                f"Failed to place order {order_id} after {retry_count} retries: {str(e)}"
                            )
                            order.status = "FAILED"
                            session.commit()
                            self.retry_counts.pop(order_id, None)
                            self.order_book.remove_order(order_id)
                            continue
                else:
                    remaining_quantity = order.quantity
                    for match in matches:
                        if remaining_quantity <= 0:
                            break

                        matched_quantity = min(remaining_quantity, match.quantity)
                        logger.debug(
                            f"Matched order {order.id} with {match.id}: {matched_quantity} units"
                        )

                        # Record match
                        match_record = OrderMatching(
                            order_buy_id=(
                                order.id if order.side.lower() == "buy" else match.id
                            ),
                            order_sell_id=(
                                order.id if order.side.lower() == "sell" else match.id
                            ),
                            matched_quantity=matched_quantity,
                            instrument=order.instrument,
                        )
                        order_matching_repo.save(match_record)

                        # Update quantities
                        order.quantity -= matched_quantity
                        match.quantity -= matched_quantity
                        order.status = "MATCHED" if order.quantity == 0 else "PARTIAL"
                        match.status = "MATCHED" if match.quantity == 0 else "PARTIAL"
                        remaining_quantity -= matched_quantity

                        # Update order book
                        if order.quantity == 0:
                            self.order_book.remove_order(order.id)
                        if match.quantity == 0:
                            self.order_book.remove_order(match.id)

                        logger.info(
                            f"Updated orders: {order.id} ({order.quantity}), {match.id} ({match.quantity})"
                        )

                    session.commit()
                    logger.info(f"Order {order_id} processed successfully with matches")
                    self.retry_counts.pop(order_id, None)

            except Exception as e:
                logger.error(
                    f"Failed to process order {order_id}: {str(e)}", exc_info=True
                )
                session.rollback()
                self.retry_counts.pop(order_id, None)
                self.order_book.remove_order(order_id)
            finally:
                session.close()
                self.q.task_done()

    def _find_matches(self, session: Session, order: Order):
        """Find matching orders using the order book, ensuring orders are bound to the session"""
        # Merge the order into the current session to ensure it's attached
        order = session.merge(order, load=True)
        matches = self.order_book.get_matching_orders(order)
        # Merge matching orders into the current session
        matches = [session.merge(match, load=True) for match in matches]
        return matches

    def enqueue(self, order: Order):
        logger.info(f"Enqueuing order: {order.id}")
        self.q.put(order.id)
