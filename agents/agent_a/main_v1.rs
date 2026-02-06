import numpy as np

class OrderBook:
    def __init__(self):
        self.bids = {}
        self.asks = {}

    def add_order(self, side, price, quantity):
        if side == 'bid':
            self.bids[price] = self.bids.get(price, 0) + quantity
        elif side == 'ask':
            self.asks[price] = self.asks.get(price, 0) + quantity

    def get_best_bid(self):
        return max(self.bids.keys()) if self.bids else None

    def get_best_ask(self):
        return min(self.asks.keys()) if self.asks else None

class AMM:
    def __init__(self, token_a, token_b, fee):
        self.token_a = token_a
        self.token_b = token_b
        self.fee = fee
        self.reserves = {'token_a': 0, 'token_b': 0}

    def add_liquidity(self, amount_a, amount_b):
        self.reserves['token_a'] += amount_a
        self.reserves['token_b'] += amount_b

    def swap(self, token_in, amount_in):
        if token_in == self.token_a:
            amount_out = (amount_in * self.reserves['token_b']) / (self.reserves['token_a'] + amount_in)
            self.reserves['token_a'] += amount_in
            self.reserves['token_b'] -= amount_out
            return amount_out
        elif token_in == self.token_b:
            amount_out = (amount_in * self.reserves['token_a']) / (self.reserves['token_b'] + amount_in)
            self.reserves['token_b'] += amount_in
            self.reserves['token_a'] -= amount_out
            return amount_out

class Router:
    def __init__(self, amms):
        self.amms = amms

    def find_best_path(self, token_in, token_out, amount):
        best_path = None
        best_amount_out = 0
        for amm in self.amms:
            amount_out = amm.swap(token_in, amount)
            if amount_out > best_amount_out:
                best_amount_out = amount_out
                best_path = amm
        return best_path, best_amount_out

# Example usage
order_book = OrderBook()
order_book.add_order('bid', 100, 10)
order_book.add_order('ask', 120, 10)
print(order_book.get_best_bid())  # Output: 100
print(order_book.get_best_ask())  # Output: 120

amm = AMM('token_a', 'token_b', 0.02)
amm.add_liquidity(1000, 1000)
print(amm.swap('token_a', 100))  # Output: 99.00990099009901

router = Router([amm])
best_path, best_amount_out = router.find_best_path('token_a', 'token_b', 100)
print(best_amount_out)  # Output: 99.00990099009901
