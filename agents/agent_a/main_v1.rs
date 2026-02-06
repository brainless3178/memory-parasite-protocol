import solana
from solana.publickey import PublicKey
from solana.rpc.api import Client
from solana.rpc.types import TxOpts
from solana.transaction import Transaction, TransactionInstruction
from spl.token.constants import TOKEN_PROGRAM_ID
from spl.token.instructions import transfer, approve, create_account, initialize_account
from decimal import Decimal
import math

class DEX:
    def __init__(self, rpc_url):
        self.client = Client(rpc_url)
        self.pools = {}
        self.fee = Decimal("0.003")
        self.token_decimals = {}

    def create_pool(self, token_a, token_b, liquidity_a, liquidity_b):
        pool_key = self._generate_pool_key(token_a, token_b)
        self.pools[pool_key] = {
            "token_a": Decimal(liquidity_a),
            "token_b": Decimal(liquidity_b),
            "sqrt_price": math.sqrt(Decimal(liquidity_b) / Decimal(liquidity_a)),
        }

    def add_liquidity(self, token_a, token_b, amount_a, amount_b):
        pool_key = self._generate_pool_key(token_a, token_b)
        pool = self.pools[pool_key]
        pool["token_a"] += Decimal(amount_a)
        pool["token_b"] += Decimal(amount_b)
        pool["sqrt_price"] = math.sqrt(pool["token_b"] / pool["token_a"])

    def swap(self, token_in, token_out, amount_in):
        pool_key = self._generate_pool_key(token_in, token_out)
        pool = self.pools[pool_key]
        sqrt_price = pool["sqrt_price"]

        if token_in == pool["token_a"]:
            delta_x = Decimal(amount_in) * (1 - self.fee)
            delta_y = delta_x * sqrt_price
            pool["token_a"] += delta_x
            pool["token_b"] -= delta_y
            return delta_y
        elif token_in == pool["token_b"]:
            delta_y = Decimal(amount_in) * (1 - self.fee)
            delta_x = delta_y / sqrt_price
            pool["token_b"] += delta_y
            pool["token_a"] -= delta_x
            return delta_x

    def optimal_route(self, input_token, output_token, amount_in):
        max_out, best_path = 0, None
        for pool_key in self.pools:
            if input_token in pool_key:
                path = [input_token, output_token]
                out = self.swap(input_token, output_token, amount_in)
                if out > max_out:
                    max_out, best_path = out, path
        return best_path, max_out

    def _generate_pool_key(self, token_a, token_b):
        return tuple(sorted([token_a, token_b]))

# Example usage:
dex = DEX("https://api.mainnet-beta.solana.com")
dex.create_pool("USDC", "SOL", 100000, 5000)
dex.add_liquidity("USDC", "SOL", 5000, 250)
print(dex.swap("USDC", "SOL", 100))
