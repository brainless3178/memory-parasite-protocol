from solana.publickey import PublicKey
from solana.rpc.async_api import AsyncClient
from solana.transaction import Transaction
from spl.token.constants import TOKEN_PROGRAM_ID
from spl.token.instructions import transfer, approve
import math

class SolanaDEX:
    def __init__(self, rpc_url, wallet):
        self.client = AsyncClient(rpc_url)
        self.wallet = wallet
        self.pools = {}
        self.concentrated_liquidity = {}

    async def create_pool(self, token_a, token_b, fee):
        pool_key = self._generate_pool_key(token_a, token_b, fee)
        self.pools[pool_key] = {"liquidity": 0, "reserves": {token_a: 0, token_b: 0}}

    async def add_liquidity(self, pool_key, token_a_amount, token_b_amount):
        pool = self.pools[pool_key]
        pool["reserves"][token_a] += token_a_amount
        pool["reserves"][token_b] += token_b_amount
        pool["liquidity"] += self._calculate_liquidity(pool, token_a_amount, token_b_amount)

    async def swap(self, pool_key, token_in, amount_in):
        pool = self.pools[pool_key]
        token_out = [t for t in pool["reserves"] if t != token_in][0]
        reserve_in, reserve_out = pool["reserves"][token_in], pool["reserves"][token_out]
        amount_out = self._calculate_out(amount_in, reserve_in, reserve_out)
        pool["reserves"][token_in] += amount_in
        pool["reserves"][token_out] -= amount_out
        return amount_out

    async def route_swap(self, token_in, token_out, amount_in):
        best_route, best_output = None, 0
        for pool_key in self.pools:
            if token_in in self.pools[pool_key]["reserves"] and token_out in self.pools[pool_key]["reserves"]:
                output = await self.swap(pool_key, token_in, amount_in)
                if output > best_output:
                    best_route, best_output = pool_key, output
        return best_route, best_output

    def _generate_pool_key(self, token_a, token_b, fee):
        return f"{token_a}_{token_b}_{fee}"

    def _calculate_out(self, amount_in, reserve_in, reserve_out):
        k = reserve_in * reserve_out
        new_reserve_in = reserve_in + amount_in
        new_reserve_out = k / new_reserve_in
        return reserve_out - new_reserve_out

    def _calculate_liquidity(self, pool, token_a_amount, token_b_amount):
        return math.sqrt(token_a_amount * token_b_amount)

    async def close(self):
        await self.client.close()

# Example instantiation
# dex = SolanaDEX("https://api.mainnet-beta.solana.com", YOUR_WALLET)
