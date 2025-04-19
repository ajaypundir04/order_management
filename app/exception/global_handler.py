from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.exception.order_exception import OrderException
from app.utils.logger import get_logger

logger = get_logger("global_handler")


async def order_exception_handler(
    request: Request, exc: OrderException
) -> JSONResponse:
    logger.error(f"OrderException: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": {"message": str(exc)}},
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": {"message": "Unexpected server error"}},
    )


def register_exception_handlers(app):
    app.add_exception_handler(OrderException, order_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
