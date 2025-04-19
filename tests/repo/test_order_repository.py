import pytest
from unittest.mock import MagicMock
from app.entity.order import Order
from app.repo.order_repository import OrderRepository
from sqlalchemy.orm import Session

@pytest.fixture
def mock_db():
    return MagicMock(spec=Session)

@pytest.fixture
def order_repository(mock_db):
    return OrderRepository(db=mock_db)

@pytest.fixture
def fake_order():
    return Order(
        id="ord1",
        side="buy",
        type="limit",
        status="OPEN",
        quantity=10,
        instrument="XYZ",
        limit_price=100.0,
        created_at="2025-04-19T00:00:00Z"
    )

def test_save_order(order_repository, mock_db, fake_order):
    mock_db.add = MagicMock()
    mock_db.commit = MagicMock()
    mock_db.refresh = MagicMock()
    
    saved_order = order_repository.save(fake_order)
    
    mock_db.add.assert_called_once_with(fake_order)
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(fake_order)
    
    assert saved_order == fake_order
