from fastapi import FastAPI, Depends
from app.config.database import SQLALCHEMY_DATABASE_URL, SessionLocal, get_db
from app.service.order_service import OrderService
from app.mapper.order_mapper import OrderMapper
from app.processor.stock_exchange_processor import StockExchangeProcessor
from app.utils.logger import get_logger
from app.exception.global_handler import register_exception_handlers
import os 
from sqlalchemy.orm import Session


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

        register_exception_handlers(app)

        mapper = OrderMapper()
        processor = StockExchangeProcessor(SessionLocal)  # Pass the factory, not a session instance
        global order_service_singleton
        order_service_singleton = OrderService(db=SessionLocal(), mapper=mapper, processor=processor)

        app.dependency_overrides[OrderService] = get_order_service
        logger.info("OrderService singleton initialized and injected")