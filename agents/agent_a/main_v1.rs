import hashlib
from typing import List

class SolanaDEX:
    def __init__(self):
        self.amm_pools = {}
        self.concentrated_liquidity = {}

    def add_liquidity(self, token1: str, token2: str, amount1: float, amount2: float):
        pool_key = self.get_pool_key(token1, token2)
        if pool_key not in self.amm_pools:
            self.amm_pools[pool_key] = {'token1': token1, 'token2': token2, 'reserves': [0, 0]}
        self.amm_pools[pool_key]['reserves'][0] += amount1
        self.amm_pools[pool_key]['reserves'][1] += amount2

    def get_pool_key(self, token1: str, token2: str):
        return hashlib.sha256((token1 + token2).encode()).hexdigest()

    def get_optimal_route(self, token_in: str, token_out: str, amount_in: float):
        best_route = None
        best_price = 0
        for pool in self.amm_pools.values():
            if pool['token1'] == token_in or pool['token2'] == token_in:
                price = self.get_price(pool, token_in, amount_in)
                if price > best_price:
                    best_price = price
                    best_route = pool
        return best_route

    def get_price(self, pool: dict, token_in: str, amount_in: float):
        if pool['token1'] == token_in:
            return amount_in / pool['reserves'][0] * pool['reserves'][1]
        else:
            return amount_in / pool['reserves'][1] * pool['reserves'][0]

dex = SolanaDEX()
dex.add_liquidity('SOL', 'USDC', 1000, 10000)
print(dex.get_optimal_route('SOL', 'USDC', 10))
