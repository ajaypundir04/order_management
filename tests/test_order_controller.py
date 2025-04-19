import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from unittest.mock import MagicMock
from app.web.order_controller import router
from app.config.database import get_db
from app.entity.base import Base
from app.entity.order import Order
from app.service.order_service import OrderService
from app.mapper.order_mapper import OrderMapper
from app.processor.stock_exchange_processor import StockExchangeProcessor
from app.dto.order_response import OrderResponse

# Test DB setup (SQLite)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

# FastAPI app with router
app = FastAPI()
app.include_router(router)  # Prefix set in router, no need to repeat

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        TestingSessionLocal.remove()

@pytest.fixture
def mock_order_service():
    db = TestingSessionLocal()
    mapper = OrderMapper()
    processor = MagicMock(spec=StockExchangeProcessor)
    service = OrderService(db=db, mapper=mapper, processor=processor)
    yield service
    db.close()
    TestingSessionLocal.remove()

def override_get_order_service(mock_order_service):
    return mock_order_service

@pytest.fixture
def client(mock_order_service):
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[OrderService] = lambda: override_get_order_service(mock_order_service)
    Base.metadata.create_all(bind=engine)
    yield TestClient(app)
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()

@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        TestingSessionLocal.remove()

@pytest.fixture
def clean_db(db_session):
    db_session.query(Order).delete()
    db_session.commit()

def test_create_order_success(client, clean_db, mock_order_service):
    order_data = {
        "type": "market",
        "side": "buy",
        "instrument": "DE0001234567",
        "quantity": 100
    }
    mock_order_service.create_order.return_value = OrderResponse(
        id=1,
        type="market",
        side="buy",
        instrument="DE0001234567",
        quantity=100,
        limit_price=None
    )
    response = client.post("/orders", json=order_data)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 1
    assert data["type"] == "market"
    assert data["side"] == "buy"
    assert data["instrument"] == "DE0001234567"
    assert data["quantity"] == 100
    assert data["limit_price"] is None

def test_create_order_db_storage(client, db_session, clean_db, mock_order_service):
    order_data = {
        "type": "limit",
        "side": "sell",
        "instrument": "DE0001234567",
        "limit_price": 99.99,
        "quantity": 50
    }
    mock_order_service.create_order.return_value = OrderResponse(
        id=1,
        type="limit",
        side="sell",
        instrument="DE0001234567",
        quantity=50,
        limit_price=99.99
    )
    response = client.post("/orders", json=order_data)
    assert response.status_code == 201
    order = db_session.query(Order).filter(Order.id == 1).first()
    assert order
    assert order.type == "limit"
    assert order.side == "sell"
    assert order.instrument == "DE0001234567"
    assert order.quantity == 50
    assert order.limit_price == 99.99

def test_create_order_error(client, clean_db, mock_order_service):
    order_data = {
        "type": "market",
        "side": "buy",
        "instrument": "DE0001234567",
        "quantity": 10
    }
    mock_order_service.create_order.side_effect = Exception("Service error")
    response = client.post("/orders", json=order_data)
    assert response.status_code == 500
    assert response.json() == {"message": "Internal server error while placing the order"}