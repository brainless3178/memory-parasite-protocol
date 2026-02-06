from solana.rpc.api import Client
from solana.publickey import PublicKey
from solana.transaction import Transaction, TransactionInstruction
from solana.account import Account
from spl.token.client import Token
from spl.token.constants import TOKEN_PROGRAM_ID
from math import sqrt

# Constants & Config
RPC_URL = "https://api.mainnet-beta.solana.com"
client = Client(RPC_URL)

# Core: AMM Pool Initialization
class AMMPool:
    def __init__(self, token_a, token_b, fee_rate):
        self.token_a = token_a
        self.token_b = token_b
        self.reserve_a = 0
        self.reserve_b = 0
        self.fee_rate = fee_rate

    def provide_liquidity(self, amount_a, amount_b):
        self.reserve_a += amount_a
        self.reserve_b += amount_b

    def swap(self, input_token, amount_in):
        if input_token == self.token_a:
            reserve_in, reserve_out = self.reserve_a, self.reserve_b
        else:
            reserve_in, reserve_out = self.reserve_b, self.reserve_a

        amount_in_with_fee = amount_in * (1 - self.fee_rate)
        amount_out = (amount_in_with_fee * reserve_out) / (reserve_in + amount_in_with_fee)
        
        if input_token == self.token_a:
            self.reserve_a += amount_in
            self.reserve_b -= amount_out
        else:
            self.reserve_b += amount_in
            self.reserve_a -= amount_out

        return amount_out

# Core: Optimized Routing
class Router:
    def __init__(self):
        self.pools = []

    def add_pool(self, pool):
        self.pools.append(pool)

    def find_best_route(self, input_token, output_token, amount_in):
        best_output = 0
        best_pool = None
        for pool in self.pools:
            if (pool.token_a == input_token and pool.token_b == output_token) or \
               (pool.token_b == input_token and pool.token_a == output_token):
                output = pool.swap(input_token, amount_in)
                if output > best_output:
                    best_output = output
                    best_pool = pool
        return best_pool, best_output

# Core: Concentrated Liquidity
class ConcentratedLiquidityPool(AMMPool):
    def __init__(self, token_a, token_b, fee_rate, lower_bound, upper_bound):
        super().__init__(token_a, token_b, fee_rate)
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound

    def provide_liquidity(self, amount_a, amount_b, current_price):
        if not (self.lower_bound <= current_price <= self.upper_bound):
            raise ValueError("Price outside range")
        super().provide_liquidity(amount_a, amount_b)

# Execution
if __name__ == "__main__":
    # Initialize Pools
    pool1 = AMMPool("SOL", "USDT", 0.003)
    pool2 = ConcentratedLiquidityPool("ETH", "USDT", 0.003, 1500, 3000)

    pool1.provide_liquidity(1000, 5000)
    pool2.provide_liquidity(10, 20000, 2000)

    # Router Setup
    router = Router()
    router.add_pool(pool1)
    router.add_pool(pool2)

    # Find Best Route
    input_token = "SOL"
    output_token = "USDT"
    amount_in = 100
    best_pool, best_output = router.find_best_route(input_token, output_token, amount_in)

    print(f"Best Pool: {best_pool}, Output: {best_output}")
