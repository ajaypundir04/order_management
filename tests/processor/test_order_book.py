import pytest
from datetime import datetime, timedelta
from app.entity.order import Order
from app.processor.order_book import OrderBook  

@pytest.fixture
def sample_orders():
    base_time = datetime.utcnow()
    return [
        Order(id="1", side="buy", type="limit", instrument="XYZ", limit_price=100.0, quantity=10, created_at=base_time, status="OPEN"),
        Order(id="2", side="sell", type="limit", instrument="XYZ", limit_price=100.0, quantity=10, created_at=base_time + timedelta(seconds=1), status="OPEN"),
        Order(id="3", side="buy", type="market", instrument="XYZ", limit_price=None, quantity=5, created_at=base_time + timedelta(seconds=2), status="OPEN"),
        Order(id="4", side="sell", type="market", instrument="XYZ", limit_price=None, quantity=5, created_at=base_time + timedelta(seconds=3), status="OPEN"),
    ]

def test_add_order_limit(sample_orders):
    ob = OrderBook()
    ob.add_order(sample_orders[0])  # Buy limit order
    assert sample_orders[0].id in ob.orders
    assert 100.0 in ob.bids
    assert len(ob.bids[100.0]) == 1

def test_add_order_market(sample_orders):
    ob = OrderBook()
    ob.add_order(sample_orders[2])  # Buy market order
    assert sample_orders[2].id in ob.orders
    assert float("inf") in ob.bids
    assert len(ob.bids[float("inf")]) == 1

def test_remove_order(sample_orders):
    ob = OrderBook()
    ob.add_order(sample_orders[0])
    ob.remove_order("1")
    assert "1" not in ob.orders
    assert 100.0 not in ob.bids or len(ob.bids[100.0]) == 0

def test_get_matching_orders_limit_buy(sample_orders):
    ob = OrderBook()
    ob.add_order(sample_orders[1])  # Existing sell order at 100
    match = ob.get_matching_orders(sample_orders[0])  # New buy limit order at 100
    assert len(match) == 1
    assert match[0].id == "2"

def test_get_matching_orders_market_buy(sample_orders):
    ob = OrderBook()
    ob.add_order(sample_orders[1])  # Existing sell order
    match = ob.get_matching_orders(sample_orders[2])  # Market buy order
    assert len(match) == 1
    assert match[0].id == "2"

def test_get_matching_orders_market_sell(sample_orders):
    ob = OrderBook()
    ob.add_order(sample_orders[0])  # Existing buy order
    match = ob.get_matching_orders(sample_orders[3])  # Market sell order
    assert len(match) == 1
    assert match[0].id == "1"

def test_get_matching_orders_ignore_closed_orders(sample_orders):
    ob = OrderBook()
    closed_order = Order(
        id="5", side="sell", type="limit", instrument="XYZ", limit_price=100.0,
        quantity=10, created_at=datetime.utcnow(), status="CANCELLED"
    )
    ob.add_order(closed_order)
    match = ob.get_matching_orders(sample_orders[0])  # Buy limit
    assert len(match) == 0
