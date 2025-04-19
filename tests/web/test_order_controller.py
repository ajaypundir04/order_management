import pytest
from unittest.mock import Mock
from datetime import datetime
from fastapi.testclient import TestClient
from app.dto.order_response import OrderResponse
from app.service.order_service import OrderService
from app.config import app_config
from decimal import Decimal


# Mock fixture for OrderService
@pytest.fixture
def mock_order_service(monkeypatch):
    mock_service = Mock(spec=OrderService)
    monkeypatch.setattr(app_config, "get_order_service", lambda: mock_service)
    return mock_service

# Test case for order creation success
def test_create_order_success(client: TestClient, mock_order_service):
    order_data = {
        "type": "market",  # This will be converted to 'type_' due to alias
        "side": "buy",
        "instrument": "DE0001234567",
        "quantity": 100
    }

    mock_order_service.create_order.return_value = OrderResponse(
        id="1",
        created_at=datetime.utcnow().isoformat(),
        type="market",  # Correct field `type_` here
        side="buy",
        instrument="DE0001234567",
        limit_price=None,
        quantity=100
    )

    response = client.post("/orders/", json=order_data)

    assert response.status_code == 201
    assert response.json()["type"] == "market"


def test_create_limit_order_success(client: TestClient, mock_order_service):
    order_data = {
        "type": "limit",
        "side": "sell",
        "instrument": "DE0009876543",
        "limit_price": "123.45",
        "quantity": 10
    }

    mock_order_service.create_order.return_value = OrderResponse(
        id="2",
        created_at=datetime.utcnow().isoformat(),
        type="limit",
        side="sell",
        instrument="DE0009876543",
        limit_price=Decimal("123.45"),
        quantity=10
    )

    response = client.post("/orders/", json=order_data)
    assert response.status_code == 201
    assert response.json()["type"] == "limit"
    assert response.json()["limit_price"] == 123.45


def test_market_order_with_limit_price_should_fail(client: TestClient):
    order_data = {
        "type": "market",
        "side": "buy",
        "instrument": "DE0001234567",
        "limit_price": "100.00",  # Invalid for market
        "quantity": 50
    }

    response = client.post("/orders/", json=order_data)
    assert response.status_code == 422
    assert "limit_price" in response.text


def test_limit_order_without_limit_price_should_fail(client: TestClient):
    order_data = {
        "type": "limit",
        "side": "sell",
        "instrument": "DE0001234567",
        "quantity": 50  # Missing limit_price
    }

    response = client.post("/orders/", json=order_data)
    assert response.status_code == 422
    assert "limit_price" in response.text


def test_invalid_instrument_length_should_fail(client: TestClient):
    order_data = {
        "type": "market",
        "side": "buy",
        "instrument": "SHORTCODE",  # Invalid length
        "quantity": 100
    }

    response = client.post("/orders/", json=order_data)
    assert response.status_code == 422
    assert "instrument" in response.text


def test_invalid_quantity_should_fail(client: TestClient):
    order_data = {
        "type": "market",
        "side": "buy",
        "instrument": "DE0001234567",
        "quantity": 0  # Invalid (must be > 0)
    }

    response = client.post("/orders/", json=order_data)
    assert response.status_code == 422
    assert "quantity" in response.text


def test_invalid_order_type_should_fail(client: TestClient):
    order_data = {
        "type": "invalidtype",  # Not 'market' or 'limit'
        "side": "buy",
        "instrument": "DE0001234567",
        "quantity": 100
    }

    response = client.post("/orders/", json=order_data)
    assert response.status_code == 422
    assert "type" in response.text


def test_invalid_order_side_should_fail(client: TestClient):
    order_data = {
        "type": "market",
        "side": "hold",  # Not 'buy' or 'sell'
        "instrument": "DE0001234567",
        "quantity": 100
    }

    response = client.post("/orders/", json=order_data)
    assert response.status_code == 422
    assert "side" in response.text   