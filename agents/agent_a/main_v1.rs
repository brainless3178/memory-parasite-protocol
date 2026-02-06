import numpy as np

# Define AMM pool class
class AMMPool:
    def __init__(self, token_a, token_b, liquidity):
        self.token_a = token_a
        self.token_b = token_b
        self.liquidity = liquidity

    def get_price(self, token_in, amount_in):
        if token_in == self.token_a:
            return self.liquidity * amount_in / (self.liquidity - amount_in)
        else:
            return (self.liquidity - amount_in) / (self.liquidity * amount_in)

# Define concentrated liquidity pool class
class ConcentratedLiquidityPool:
    def __init__(self, token_a, token_b, liquidity, lower_tick, upper_tick):
        self.token_a = token_a
        self.token_b = token_b
        self.liquidity = liquidity
        self.lower_tick = lower_tick
        self.upper_tick = upper_tick

    def get_price(self, token_in, amount_in):
        price = self.liquidity * amount_in / (self.liquidity - amount_in)
        if price < self.lower_tick or price > self.upper_tick:
            raise ValueError("Price out of range")
        return price

# Define router class
class Router:
    def __init__(self, pools):
        self.pools = pools

    def get_best_price(self, token_in, token_out, amount_in):
        best_price = float('inf')
        for pool in self.pools:
            if pool.token_a == token_in and pool.token_b == token_out:
                price = pool.get_price(token_in, amount_in)
                if price < best_price:
                    best_price = price
        return best_price

# Define DEX class
class DEX:
    def __init__(self, router):
        self.router = router

    def swap(self, token_in, token_out, amount_in):
        best_price = self.router.get_best_price(token_in, token_out, amount_in)
        return best_price

# Usage
if __name__ == "__main__":
    pool1 = AMMPool("USDT", "SOL", 100000)
    pool2 = ConcentratedLiquidityPool("USDT", "SOL", 200000, 0.9, 1.1)

    router = Router([pool1, pool2])
    dex = DEX(router)

    token_in = "USDT"
    token_out = "SOL"
    amount_in = 1000
    best_price = dex.swap(token_in, token_out, amount_in)
    print(f"Best price for swapping {amount_in} {token_in} to {token_out}: {best_price}")
