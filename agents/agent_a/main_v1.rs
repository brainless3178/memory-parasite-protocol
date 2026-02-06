import numpy as np

class SolanaDEX:
    def __init__(self):
        self.amm_pools = {}
        self.concentrated_liquidity = {}

    def add_amm_pool(self, token_pair, liquidity):
        self.amm_pools[token_pair] = liquidity

    def add_concentrated_liquidity(self, token_pair, liquidity):
        self.concentrated_liquidity[token_pair] = liquidity

    def optimal_routing(self, token_in, token_out, amount_in):
        best_path = None
        best_rate = 0

        for token_pair, liquidity in self.amm_pools.items():
            if token_pair[0] == token_in:
                rate = liquidity / (liquidity + amount_in)
                if rate > best_rate:
                    best_rate = rate
                    best_path = token_pair
            elif token_pair[1] == token_in:
                rate = (liquidity + amount_in) / liquidity
                if rate > best_rate:
                    best_rate = rate
                    best_path = token_pair

        for token_pair, liquidity in self.concentrated_liquidity.items():
            if token_pair[0] == token_in:
                rate = liquidity / (liquidity + amount_in)
                if rate > best_rate:
                    best_rate = rate
                    best_path = token_pair
            elif token_pair[1] == token_in:
                rate = (liquidity + amount_in) / liquidity
                if rate > best_rate:
                    best_rate = rate
                    best_path = token_pair

        return best_path

    def execute_trade(self, token_in, token_out, amount_in):
        best_path = self.optimal_routing(token_in, token_out, amount_in)
        if best_path:
            if best_path[0] == token_in:
                return amount_in * self.amm_pools[best_path] / (self.amm_pools[best_path] + amount_in)
            else:
                return amount_in * (self.amm_pools[best_path] + amount_in) / self.amm_pools[best_path]
        else:
            return 0

# Example usage:
dex = SolanaDEX()
dex.add_amm_pool(("SOL", "USDC"), 1000)
dex.add_concentrated_liquidity(("USDC", "ETH"), 500)

print(dex.execute_trade("SOL", "USDC", 100))
