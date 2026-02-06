from solana.rpc.api import Client
from solana.publickey import PublicKey
from solana.transaction import Transaction
from spl.token.constants import TOKEN_PROGRAM_ID
from spl.token.instructions import transfer, approve, create_account
from math import sqrt

class SolanaDEX:
    def __init__(self, rpc_url):
        self.client = Client(rpc_url)
        self.pools = {}
        self.liquidity_providers = {}

    def create_pool(self, token_a, token_b, fee=0.3):
        pool_key = f"{token_a}-{token_b}"
        if pool_key in self.pools:
            raise Exception("Pool already exists.")
        self.pools[pool_key] = {
            "token_a": token_a,
            "token_b": token_b,
            "fee": fee,
            "reserves": {"token_a": 0, "token_b": 0}
        }

    def provide_liquidity(self, pool_key, amount_a, amount_b, provider):
        if pool_key not in self.pools:
            raise Exception("Pool does not exist.")
        pool = self.pools[pool_key]
        pool["reserves"]["token_a"] += amount_a
        pool["reserves"]["token_b"] += amount_b
        self.liquidity_providers.setdefault(provider, {}).setdefault(pool_key, {"token_a": 0, "token_b": 0})
        self.liquidity_providers[provider][pool_key]["token_a"] += amount_a
        self.liquidity_providers[provider][pool_key]["token_b"] += amount_b

    def swap(self, pool_key, input_token, input_amount):
        if pool_key not in self.pools:
            raise Exception("Pool does not exist.")
        pool = self.pools[pool_key]
        if input_token not in (pool["token_a"], pool["token_b"]):
            raise Exception("Invalid token for this pool.")
        output_token = pool["token_b"] if input_token == pool["token_a"] else pool["token_a"]
        reserve_in = pool["reserves"][f"token_{input_token[-1]}"]
        reserve_out = pool["reserves"][f"token_{output_token[-1]}"]
        fee_adjustment = 1 - pool["fee"] / 100
        input_amount_with_fee = input_amount * fee_adjustment
        new_reserve_in = reserve_in + input_amount_with_fee
        new_reserve_out = reserve_in * reserve_out / new_reserve_in
        output_amount = reserve_out - new_reserve_out
        pool["reserves"][f"token_{input_token[-1]}"] = new_reserve_in
        pool["reserves"][f"token_{output_token[-1]}"] = new_reserve_out
        return output_amount

    def optimal_route(self, start_token, end_token, amount):
        routes = [(key, self.swap(key, start_token, amount)) for key in self.pools if start_token in key]
        routes = sorted(routes, key=lambda x: x[1], reverse=True)
        return routes[0] if routes else None

    def concentrate_liquidity(self, pool_key, range_start, range_end, provider, amount):
        if pool_key not in self.pools:
            raise Exception("Pool does not exist.")
        pool = self.pools[pool_key]
        key_range = f"{range_start}-{range_end}"
        if key_range not in self.liquidity_providers.setdefault(provider, {}):
            self.liquidity_providers[provider][key_range] = {"amount": 0}
        self.liquidity_providers[provider][key_range]["amount"] += amount
        pool["reserves"]["concentrated"] = pool["reserves"].get("concentrated", 0) + amount

dex = SolanaDEX("https://api.mainnet-beta.solana.com")
dex.create_pool("USDC", "SOL")
dex.provide_liquidity("USDC-SOL", 10000, 500, "provider_1")
output = dex.swap("USDC-SOL", "USDC", 100)
print(f"Output: {output}")
