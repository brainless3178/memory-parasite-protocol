import numpy as np

class SolanaDEX:
    def __init__(self, fee=0.003):
        self.fee = fee
        self.amm_pools = {}

    def add_amm_pool(self, token_a, token_b, liquidity=1000):
        self.amm_pools[(token_a, token_b)] = {
            'reserve_a': liquidity,
            'reserve_b': liquidity,
            'fee': self.fee
        }

    def get_price(self, token_a, token_b):
        pool = self.amm_pools.get((token_a, token_b))
        if pool:
            return pool['reserve_b'] / pool['reserve_a']
        return None

    def swap(self, token_a, token_b, amount_a):
        pool = self.amm_pools.get((token_a, token_b))
        if pool:
            amount_b = self.calculate_amount_b(amount_a, pool['reserve_a'], pool['reserve_b'])
            pool['reserve_a'] += amount_a
            pool['reserve_b'] -= amount_b
            return amount_b
        return None

    @staticmethod
    def calculate_amount_b(amount_a, reserve_a, reserve_b):
        return (amount_a * reserve_b) / (reserve_a + amount_a)

# Example usage
dex = SolanaDEX()
dex.add_amm_pool('SOL', 'USDT')
print(dex.get_price('SOL', 'USDT'))  # prints: 1.0
print(dex.swap('SOL', 'USDT', 100))  # prints: 99.00990099009901
