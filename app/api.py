from fastapi import FastAPI

from app.config.app_config import Config  # Updated import
from app.utils.logger import get_logger
from app.web.order_controller import router as order_router

logger = get_logger("main")

# Initialize FastAPI app
app = FastAPI(title="Lemon Markets Orders API")

# Configure app with dependencies and handlers
Config.configure(app)

# Include routers
app.include_router(order_router, prefix="/orders")

logger.info("FastAPI application initialized")


def get_app() -> FastAPI:
    logger.debug("Providing FastAPI app dependency")
    return app
