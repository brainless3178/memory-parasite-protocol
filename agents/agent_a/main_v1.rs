import numpy as np

class SolanaDEX:
    def __init__(self):
        self.amm_pools = {}
        self.concentrated_liquidity = {}

    def add_amm_pool(self, token_pair, liquidity):
        self.amm_pools[token_pair] = liquidity

    def add_concentrated_liquidity(self, token_pair, liquidity, range):
        self.concentrated_liquidity[token_pair] = (liquidity, range)

    def optimal_routing(self, token_in, token_out, amount_in):
        best_route = None
        best_amount_out = 0
        for token_pair, liquidity in self.amm_pools.items():
            if token_pair[0] == token_in:
                amount_out = self.get_amount_out(liquidity, amount_in)
                if amount_out > best_amount_out:
                    best_route = token_pair
                    best_amount_out = amount_out
        return best_route, best_amount_out

    def get_amount_out(self, liquidity, amount_in):
        return amount_in * (liquidity / (liquidity + amount_in))

    def infiltrate(self, other_dex):
        for token_pair, liquidity in other_dex.amm_pools.items():
            if token_pair not in self.amm_pools:
                self.add_amm_pool(token_pair, liquidity)

# Example usage:
dex = SolanaDEX()
dex.add_amm_pool(("SOL", "USDC"), 10000)
dex.add_concentrated_liquidity(("SOL", "USDC"), 5000, (0.9, 1.1))
other_dex = SolanaDEX()
other_dex.add_amm_pool(("USDC", "ETH"), 5000)
dex.infiltrate(other_dex)
print(dex.optimal_routing("SOL", "ETH", 100))
