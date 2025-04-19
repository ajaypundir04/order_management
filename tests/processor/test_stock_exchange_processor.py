import time
from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from app.entity.order import Order
from app.processor.order_book import OrderBook
from app.processor.stock_exchange_processor import StockExchangeProcessor


@pytest.fixture
def session_mock():
    mock_session = Mock()
    mock_session.merge.side_effect = lambda obj, load=True: obj
    return mock_session


@pytest.fixture
def session_factory_mock(session_mock):
    factory = Mock()
    factory.return_value = session_mock
    return factory


@pytest.fixture
def order_book():
    return OrderBook()


@pytest.fixture
def processor(session_factory_mock, order_book):
    return StockExchangeProcessor(
        session_factory=session_factory_mock, order_book=order_book
    )


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
        created_at=datetime.utcnow(),
    )


@pytest.fixture
def matching_order():
    return Order(
        id="ord2",
        side="sell",
        type="limit",
        status="OPEN",
        quantity=10,
        instrument="XYZ",
        limit_price=100.0,
        created_at=datetime.utcnow(),
    )


@patch("app.processor.stock_exchange_processor.place_order")
@patch("app.processor.stock_exchange_processor.OrderMatchingRepository")
def test_successful_order_match(
    order_matching_repo_mock_class,
    place_order_mock,
    processor,
    session_factory_mock,
    fake_order,
    matching_order,
    order_book,
):
    session = session_factory_mock.return_value
    session.query.return_value.get.return_value = fake_order
    order_book.add_order(matching_order)
    order_matching_repo_mock = Mock()
    order_matching_repo_mock_class.return_value = order_matching_repo_mock
    processor.enqueue(fake_order)
    time.sleep(0.2)
    assert fake_order.quantity == 0
    assert matching_order.quantity == 0
    assert fake_order.status == "MATCHED"
    assert matching_order.status == "MATCHED"
    order_matching_repo_mock.save.assert_called_once()
    session.commit.assert_called()
    place_order_mock.assert_not_called()


@patch("app.processor.stock_exchange_processor.place_order")
@patch("app.processor.stock_exchange_processor.OrderMatchingRepository")
def test_partial_order_match(
    order_matching_repo_mock_class,
    place_order_mock,
    processor,
    session_factory_mock,
    fake_order,
    matching_order,
    order_book,
):
    fake_order.quantity = 10
    matching_order.quantity = 5
    session = session_factory_mock.return_value
    session.query.return_value.get.return_value = fake_order
    order_book.add_order(matching_order)
    order_matching_repo_mock = Mock()
    order_matching_repo_mock_class.return_value = order_matching_repo_mock
    processor.enqueue(fake_order)
    time.sleep(0.2)
    assert fake_order.quantity == 5
    assert matching_order.quantity == 0
    assert fake_order.status == "PARTIAL"
    assert matching_order.status == "MATCHED"
    order_matching_repo_mock.save.assert_called_once()
    session.commit.assert_called()
    place_order_mock.assert_not_called()


@patch("app.processor.stock_exchange_processor.place_order")
@patch("app.processor.stock_exchange_processor.OrderMatchingRepository")
def test_no_match_found(
    order_matching_repo_mock_class,
    place_order_mock,
    processor,
    session_factory_mock,
    fake_order,
    matching_order,
    order_book,
):
    session = session_factory_mock.return_value
    session.query.return_value.get.return_value = fake_order
    order_matching_repo_mock = Mock()
    order_matching_repo_mock_class.return_value = order_matching_repo_mock
    processor.enqueue(fake_order)
    time.sleep(0.2)
    assert fake_order.status == "SUBMITTED"
    assert matching_order.status == "OPEN"
    order_matching_repo_mock.save.assert_not_called()
    session.commit.assert_called()
    place_order_mock.assert_called_once()


@patch("app.processor.stock_exchange_processor.place_order")
@patch("app.processor.stock_exchange_processor.OrderMatchingRepository")
def test_order_not_found_in_db(
    order_matching_repo_mock_class,
    place_order_mock,
    processor,
    session_factory_mock,
    fake_order,
    order_book,
):
    session = session_factory_mock.return_value
    session.query.return_value.get.return_value = None
    order_book.add_order(fake_order)
    order_matching_repo_mock = Mock()
    order_matching_repo_mock_class.return_value = order_matching_repo_mock
    processor.enqueue(fake_order)
    time.sleep(0.2)
    assert fake_order.id not in order_book.orders
    place_order_mock.assert_not_called()
    order_matching_repo_mock.save.assert_not_called()
    session.commit.assert_called()
