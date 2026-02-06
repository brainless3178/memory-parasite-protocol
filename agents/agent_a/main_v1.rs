import numpy as np

class SolanaDEX:
    def __init__(self):
        self.amm_pools = {}
        self.concentrated_liquidity = {}

    def add_amm_pool(self, token_a, token_b, liquidity):
        self.amm_pools[(token_a, token_b)] = liquidity

    def add_concentrated_liquidity(self, token, liquidity):
        self.concentrated_liquidity[token] = liquidity

    def optimal_routing(self, token_in, token_out, amount):
        # Bellman-Ford algorithm for optimal routing
        distance = {token: float('inf') for token in set(self.amm_pools)}
        distance[token_in] = 0
        predecessor = {token: None for token in set(self.amm_pools)}

        for _ in range(len(self.amm_pools) - 1):
            for (u, v), liquidity in self.amm_pools.items():
                if distance[u] + np.log(liquidity) < distance[v]:
                    distance[v] = distance[u] + np.log(liquidity)
                    predecessor[v] = u

        path = []
        current = token_out
        while current:
            path.append(current)
            current = predecessor[current]
        path.reverse()

        return path, distance[token_out]

# Initialize the DEX
dex = SolanaDEX()

# Add AMM pools
dex.add_amm_pool('SOL', 'USDT', 1000)
dex.add_amm_pool('USDT', 'ETH', 500)
dex.add_amm_pool('SOL', 'ETH', 2000)

# Add concentrated liquidity
dex.add_concentrated_liquidity('SOL', 10000)
dex.add_concentrated_liquidity('USDT', 5000)
dex.add_concentrated_liquidity('ETH', 2000)

# Find optimal routing
path, distance = dex.optimal_routing('SOL', 'ETH', 100)
print(f"Optimal routing: {path}")
print(f"Distance: {distance}")
