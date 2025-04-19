from unittest.mock import Mock, patch

import pytest

from app.dto.order_request import CreateOrderModel
from app.dto.order_response import OrderResponse
from app.entity.order import Order  # Assuming your DB entity is `Order`
from app.service.order_service import OrderService


@pytest.fixture
def mock_dependencies():
    db = Mock()
    mapper = Mock()
    processor = Mock()
    return db, mapper, processor


@patch("app.service.order_service.OrderRepository")
@patch("app.service.order_service.IdGenerator.generate", return_value="test-id-123")
def test_create_order_success(mock_id_gen, mock_repo_class, mock_dependencies):
    db, mapper, processor = mock_dependencies
    mock_repo = Mock()
    mock_repo.save.return_value = Mock(id="test-id-123")  # Simulated DB Order entity
    mock_repo_class.return_value = mock_repo

    # Arrange
    service = OrderService(db=db, mapper=mapper, processor=processor)

    order_input = CreateOrderModel(
        type="market",
        side="buy",
        instrument="DE0001234567",
        limit_price=None,
        quantity=100,
    )

    fake_entity = Mock(id="test-id-123")
    mapper.to_entity.return_value = fake_entity
    mapper.to_response.return_value = {
        "id": "test-id-123",
        "created_at": "2023-01-01T00:00:00",
        "type": "market",
        "side": "buy",
        "instrument": "DE0001234567",
        "limit_price": None,
        "quantity": 100,
    }

    # Act
    response = service.create_order(order_input)

    # Assert
    mock_id_gen.assert_called_once()
    mapper.to_entity.assert_called_once_with(order_input, "test-id-123")
    mock_repo.save.assert_called_once_with(fake_entity)
    processor.enqueue.assert_called_once_with(mock_repo.save.return_value)
    mapper.to_response.assert_called_once_with(mock_repo.save.return_value)
    db.commit.assert_called_once()

    assert isinstance(response, OrderResponse)
    assert response.id == "test-id-123"
    assert response.type_ == "market"
    assert response.instrument == "DE0001234567"
    assert response.quantity == 100
