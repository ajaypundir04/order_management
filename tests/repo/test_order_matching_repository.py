from typing import List
from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from app.entity.order_matching import OrderMatching
from app.repo.order_matching_repository import OrderMatchingRepository


@pytest.fixture
def mock_db():
    return MagicMock(spec=Session)


@pytest.fixture
def order_matching_repository(mock_db):
    return OrderMatchingRepository(db=mock_db)


@pytest.fixture
def fake_order_matching():
    return OrderMatching(
        order_buy_id="ord1", order_sell_id="ord2", matched_quantity=10, instrument="XYZ"
    )


def test_save_order_matching(order_matching_repository, mock_db, fake_order_matching):
    mock_db.add = MagicMock()
    mock_db.commit = MagicMock()
    mock_db.refresh = MagicMock()

    saved_order_matching = order_matching_repository.save(fake_order_matching)

    mock_db.add.assert_called_once_with(fake_order_matching)
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(fake_order_matching)

    assert saved_order_matching == fake_order_matching


def test_get_by_order_id(order_matching_repository, mock_db, fake_order_matching):
    mock_db.query.return_value.filter.return_value.all.return_value = [
        fake_order_matching
    ]

    result: List[OrderMatching] = order_matching_repository.get_by_order_id("ord1")

    mock_db.query.assert_called_once_with(OrderMatching)
    mock_db.query.return_value.filter.assert_called_once()
    mock_db.query.return_value.filter.return_value.all.assert_called_once()

    assert result == [fake_order_matching]
