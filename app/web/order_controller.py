from fastapi import APIRouter, Depends
from app.config.app_config import get_order_service
from app.dto.order_request import OrderRequest
from app.dto.order_response import OrderResponse
from app.service.order_service import OrderService
from app.utils.logger import get_logger

logger = get_logger("order_controller")

router = APIRouter()

@router.post(
    "",
    status_code=201,
    response_model=OrderResponse,
    response_model_by_alias=True,
)
async def create_order(model: OrderRequest, service: OrderService = Depends(get_order_service)):
    logger.info(f"Received order request: {model.dict()}")
    response = service.create_order(model)
    logger.info(f"Created order with ID: {response.id}")
    return response