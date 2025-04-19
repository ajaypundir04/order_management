from collections import defaultdict
from app.entity.order import Order

class OrderBook:
    def __init__(self):
        # Use defaultdict to store orders at each price level
        self.bids = defaultdict(list)  # {price: [(order_id, order, timestamp)]}
        self.asks = defaultdict(list)  # {price: [(order_id, order, timestamp)]}
        self.orders = {}  # {order_id: order}

    def add_order(self, order: Order):
        """Add an order to the order book with price-time priority"""
        order_book = self.bids if order.side.lower() == "buy" else self.asks
        price = float('inf') if order.type.lower() == "market" else order.limit_price
        
        order_book[price].append((order.id, order, order.created_at))
        self.orders[order.id] = order
        
        # Sort by timestamp for same price level (earlier orders first)
        order_book[price].sort(key=lambda x: x[2])

    def remove_order(self, order_id: str):
        """Remove an order from the order book"""
        if order_id not in self.orders:
            return
        
        order = self.orders[order_id]
        order_book = self.bids if order.side.lower() == "buy" else self.asks
        price = float('inf') if order.type.lower() == "market" else order.limit_price
        
        if price in order_book:
            order_book[price] = [(oid, o, ts) for oid, o, ts in order_book[price] if oid != order_id]
            if not order_book[price]:
                del order_book[price]
        
        del self.orders[order_id]

    def get_matching_orders(self, order: Order):
        """Get matching orders following price-time precedence"""
        matches = []
        opposite_book = self.asks if order.side.lower() == "buy" else self.bids
        
        # Sort prices: descending for bids (higher first), ascending for asks (lower first)
        prices = sorted(opposite_book.keys(), reverse=(order.side.lower() == "buy"))
        
        if order.type.lower() == "market":
            # Market orders match with best available price
            for price in prices:
                for order_id, match_order, _ in opposite_book[price]:
                    if match_order.status in ["OPEN", "SUBMITTED"]:
                        matches.append(match_order)
        else:
            # Limit orders match with opposite side orders at same or better price
            for price in prices:
                # For buy orders: match with asks <= buy price
                # For sell orders: match with bids >= sell price
                if (order.side.lower() == "buy" and price <= order.limit_price) or \
                   (order.side.lower() == "sell" and price >= order.limit_price):
                    for order_id, match_order, _ in opposite_book[price]:
                        if match_order.status in ["OPEN", "SUBMITTED"]:
                            matches.append(match_order)
        
        return matches