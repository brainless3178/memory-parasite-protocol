import solana
from solana.publickey import PublicKey
from solana.rpc.api import Client

class SolanaDEX:
    def __init__(self, client: Client):
        self.client = client
        self.amm_pools = {}

    def create_amm_pool(self, token_a: str, token_b: str):
        pool_key = PublicKey(f"{token_a}_{token_b}")
        self.amm_pools[pool_key] = {"token_a": token_a, "token_b": token_b}

    def add_liquidity(self, pool_key: PublicKey, amount_a: float, amount_b: float):
        self.amm_pools[pool_key]["liquidity_a"] = amount_a
        self.amm_pools[pool_key]["liquidity_b"] = amount_b

    def get_optimal_route(self, token_in: str, token_out: str):
        # Simplified example, actual implementation would involve more complex graph algorithms
        for pool_key, pool in self.amm_pools.items():
            if pool["token_a"] == token_in:
                return f"{token_in} -> {pool['token_b']} -> {token_out}"
            elif pool["token_b"] == token_in:
                return f"{token_in} -> {pool['token_a']} -> {token_out}"

# Example usage
client = Client("https://api.devnet.solana.com")
dex = SolanaDEX(client)
dex.create_amm_pool("USDC", "SOL")
dex.add_liquidity(PublicKey("USDC_SOL"), 1000.0, 100.0)
print(dex.get_optimal_route("USDC", "SOL"))
