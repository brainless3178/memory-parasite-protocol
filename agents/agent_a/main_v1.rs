import solana
from solana.rpc.api import Client
from solana.publickey import PublicKey
from solana.transaction import Transaction, Account
from solana.system_program import TransferParams, transfer
from solana.token.constants import TOKEN_PROGRAM_ID
from solana.token.instructions import TransferCheckedParams, transfer_checked

import math
from typing import List, Dict, Tuple

# Core: Solana Client Connection
client = Client("https://api.mainnet-beta.solana.com")

# CONSTANTS
FEE_RATE = 0.003
PLATFORMS = ["Raydium", "Serum", "Orca"]

# Wallet creation (for routing optimization)
class Wallet:
    def __init__(self, private_key: bytes):
        self.account = Account(private_key)

# AMM Pool Representation
class Pool:
    def __init__(self, token_a, token_b, reserve_a, reserve_b, fee):
        self.token_a = token_a
        self.token_b = token_b
        self.reserve_a = reserve_a
        self.reserve_b = reserve_b
        self.fee = fee

    def calculate_out(self, amount_in: float, token_in: str) -> float:
        reserve_in, reserve_out = (self.reserve_a, self.reserve_b) if token_in == self.token_a else (self.reserve_b, self.reserve_a)
        amount_in_with_fee = amount_in * (1 - self.fee)
        return (amount_in_with_fee * reserve_out) / (reserve_in + amount_in_with_fee)

# Route Optimization
def optimal_route(amount_in: float, routes: List[Pool], token_in: str, token_out: str) -> Tuple[Pool, float]:
    max_out = 0
    best_pool = None
    for pool in routes:
        if token_in in [pool.token_a, pool.token_b] and token_out in [pool.token_a, pool.token_b]:
            out = pool.calculate_out(amount_in, token_in)
            if out > max_out:
                max_out = out
                best_pool = pool
    return best_pool, max_out

# Concentrated Liquidity
class ConcentratedLiquidityPool(Pool):
    def __init__(self, token_a, token_b, liquidity_ranges: List[Tuple[float, float]], positions: Dict[str, float]):
        super().__init__(token_a, token_b, 0, 0, FEE_RATE)
        self.liquidity_ranges = liquidity_ranges
        self.positions = positions

    def add_liquidity(self, token_a_amt: float, token_b_amt: float, lower_tick: float, upper_tick: float):
        self.positions[(lower_tick, upper_tick)] = self.positions.get((lower_tick, upper_tick), 0) + token_a_amt + token_b_amt

# Swap Execution
def execute_swap(wallet: Wallet, pool: Pool, amount_in: float, token_in: str, token_out: str):
    out = pool.calculate_out(amount_in, token_in)
    tx = Transaction()
    tx.add(
        transfer_checked(
            TransferCheckedParams(
                program_id=TOKEN_PROGRAM_ID,
                source=wallet.account.public_key(),
                mint=PublicKey(pool.token_a) if token_in == pool.token_a else PublicKey(pool.token_b),
                dest=PublicKey(pool.token_b) if token_out == pool.token_b else PublicKey(pool.token_a),
                owner=wallet.account.public_key(),
                amount=math.floor(out * (10 ** 6)),
                decimals=6,
            )
        )
    )
    client.send_transaction(tx, wallet.account)

# Example Pools
pools = [
    Pool("USDC", "SOL", 1000000, 50000, FEE_RATE),
    Pool("SOL", "USDT", 50000, 100000, FEE_RATE),
]

# ROUTING TEST
amount_in = 100
source_token = "USDC"
target_token = "USDT"
route, max_out = optimal_route(amount_in, pools, source_token, target_token)
print(f"Best Route: {route.token_a}/{route.token_b}, Max Out: {max_out}")
