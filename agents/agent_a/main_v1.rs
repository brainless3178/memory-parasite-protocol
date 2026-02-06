import numpy as np

class SolanaDEX:
    def __init__(self):
        self.amm_pools = {}
        self.concentrated_liquidity = {}

    def add_amm_pool(self, token1, token2):
        self.amm_pools[(token1, token2)] = {"reserve1": 0, "reserve2": 0}

    def add_concentrated_liquidity(self, token1, token2, liquidity):
        self.concentrated_liquidity[(token1, token2)] = liquidity

    def calculate_optimal_route(self, token_in, token_out, amount_in):
        # Simplified optimal routing for demonstration purposes
        optimal_route = []
        if (token_in, token_out) in self.amm_pools:
            optimal_route.append((token_in, token_out))
        elif (token_out, token_in) in self.amm_pools:
            optimal_route.append((token_out, token_in))
        else:
            # Find a common token to route through
            common_tokens = set([t for (t, _) in self.amm_pools] + [t for (_, t) in self.amm_pools])
            for common_token in common_tokens:
                if (token_in, common_token) in self.amm_pools and (common_token, token_out) in self.amm_pools:
                    optimal_route.extend([(token_in, common_token), (common_token, token_out)])
                    break
        return optimal_route

    def execute_trade(self, token_in, token_out, amount_in):
        optimal_route = self.calculate_optimal_route(token_in, token_out, amount_in)
        amount_out = amount_in
        for (token1, token2) in optimal_route:
            reserve1, reserve2 = self.amm_pools[(token1, token2)]["reserve1"], self.amm_pools[(token1, token2)]["reserve2"]
            amount_out = (reserve2 * amount_in) / (reserve1 + amount_in)
            self.amm_pools[(token1, token2)]["reserve1"] += amount_in
            self.amm_pools[(token1, token2)]["reserve2"] -= amount_out
            amount_in = amount_out
        return amount_out

# Example usage
dex = SolanaDEX()
dex.add_amm_pool("SOL", "USDT")
dex.add_concentrated_liquidity("SOL", "USDT", 1000000)
dex.amm_pools[("SOL", "USDT")]["reserve1"] = 100000
dex.amm_pools[("SOL", "USDT")]["reserve2"] = 1000000
print(dex.execute_trade("SOL", "USDT", 1000))
