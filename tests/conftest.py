from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api import get_app
from app.config.database import get_db
from app.service.order_service import OrderService

# In-memory DB
TEST_DB_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def mock_order_service():
    return Mock(spec=OrderService)


@pytest.fixture
def client(mock_order_service):
    app = get_app()

    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.rollback()
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    from app.config import app_config

    app_config.get_order_service = lambda: mock_order_service

    return TestClient(app)
