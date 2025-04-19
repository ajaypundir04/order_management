from sqlalchemy.orm import Session
from app.dto.order_request import OrderRequest
from app.dto.order_response import OrderResponse
from app.repo.order_repository import OrderRepository
from app.utils.id_generator import IdGenerator
from app.processor.stock_exchange_processor import StockExchangeProcessor
from app.exception.order_exception import OrderException
from app.mapper.order_mapper import OrderMapper
from app.config.database import get_db
from fastapi import Depends
from app.utils.logger import get_logger

logger = get_logger("order_service")

class OrderService:
    def __init__(
        self,
        db: Session,
        mapper: OrderMapper,  
        processor: StockExchangeProcessor,
    ):
        self.db = db
        self.repository = OrderRepository(db)
        self.processor = processor
        self.mapper = mapper  
        logger.info("OrderService initialized")

    def create_order(self, order: OrderRequest) -> OrderResponse:
        logger.info(f"Creating order: {order.dict()}")
        order_id = IdGenerator.generate()
        db_order = self.mapper.to_entity(order, order_id)  
        logger.debug(f"Mapped to entity: {db_order.id}")
        saved_order = self.repository.save(db_order)  
        logger.debug(f"Saved order: {saved_order.id}")
        self.processor.enqueue(saved_order) 
        logger.debug(f"Enqueued order: {saved_order.id}")
        response_dict = self.mapper.to_response(saved_order) 
        self.db.commit() #Commit
        logger.info(f"Order created successfully: {saved_order.id}")
        return OrderResponse(**response_dict)