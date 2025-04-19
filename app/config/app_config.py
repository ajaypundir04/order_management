import sys
import os
from fastapi import FastAPI, Depends
from app.config.database import SQLALCHEMY_DATABASE_URL, SessionLocal, get_db
from app.service.order_service import OrderService
from app.mapper.order_mapper import OrderMapper
from app.processor.stock_exchange_processor import StockExchangeProcessor
from app.processor.order_book import OrderBook
from app.utils.logger import get_logger
from app.exception.global_handler import register_exception_handlers

# Add project root to sys.path for module resolution
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

logger = get_logger("config")

def get_order_service() -> OrderService:
    """
    Dependency override to return the singleton OrderService.
    """
    if order_service_singleton is None:
        raise Exception("OrderService singleton not initialized")
    return order_service_singleton

class Config:
    @staticmethod
    def configure(app: FastAPI):
        logger.info("Configuring FastAPI application")

        # Register exception handlers
        register_exception_handlers(app)

        # Initialize dependencies
        mapper = OrderMapper()
        order_book = OrderBook()
        max_retries = int(os.getenv("MAX_RETRIES", 3))  # Configurable via environment variable
        retry_delay = float(os.getenv("RETRY_DELAY", 5.0))  # Configurable via environment variable
        processor = StockExchangeProcessor(
            session_factory=SessionLocal,
            order_book=order_book,
            max_retries=max_retries,
            retry_delay=retry_delay
        )

        # Initialize OrderService singleton
        global order_service_singleton
        order_service_singleton = OrderService(db=SessionLocal(), mapper=mapper, processor=processor)

        # Override dependency
        app.dependency_overrides[OrderService] = get_order_service
        logger.info("OrderService singleton initialized and injected")