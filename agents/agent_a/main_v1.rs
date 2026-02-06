from solana.rpc.api import Client
from solana.publickey import PublicKey
from solana.transaction import Transaction, Account
from spl.token.instructions import TokenProgram, transfer
from spl.token.constants import TOKEN_PROGRAM_ID
from decimal import Decimal
import numpy as np

class SolanaDEX:
    def __init__(self, rpc_url: str):
        self.client = Client(rpc_url)
        self.pools = {}  # Store AMM pools and concentrated liquidity
        
    def create_pool(self, token_a: str, token_b: str, fee: float):
        pool_key = f"{token_a}_{token_b}"
        self.pools[pool_key] = {
            "token_a": Decimal(0),
            "token_b": Decimal(0),
            "fee": Decimal(fee)
        }
    
    def add_liquidity(self, pool_key: str, token_a_amt: Decimal, token_b_amt: Decimal):
        if pool_key not in self.pools:
            raise ValueError("Pool does not exist.")
        self.pools[pool_key]["token_a"] += token_a_amt
        self.pools[pool_key]["token_b"] += token_b_amt
    
    def get_price(self, pool_key: str, token_in: str, amount_in: Decimal):
        pool = self.pools[pool_key]
        reserve_in = pool[f"token_{token_in}"]
        reserve_out = pool[f"token_{'a' if token_in == 'b' else 'b'}"]
        if reserve_in <= 0 or reserve_out <= 0:
            raise ValueError("Insufficient liquidity.")
        amount_out = (amount_in * reserve_out * (1 - pool['fee'])) / (reserve_in + amount_in)
        return amount_out
    
    def swap(self, pool_key: str, token_in: str, amount_in: Decimal):
        pool = self.pools[pool_key]
        amount_out = self.get_price(pool_key, token_in, amount_in)
        reserve_in = f"token_{token_in}"
        reserve_out = f"token_{'a' if token_in == 'b' else 'b'}"
        self.pools[pool_key][reserve_in] += amount_in
        self.pools[pool_key][reserve_out] -= amount_out
        return amount_out
    
    def optimal_routing(self, trades: list):
        best_route = None
        best_output = Decimal(0)
        for route in trades:
            output = Decimal(1)
            valid_route = True
            for pool_key, token_in, amount_in in route:
                if pool_key not in self.pools:
                    valid_route = False
                    break
                output = self.get_price(pool_key, token_in, amount_in)
            if valid_route and output > best_output:
                best_output = output
                best_route = route
        return best_route, best_output
    
    def execute_trade(self, route: list):
        for pool_key, token_in, amount_in in route:
            self.swap(pool_key, token_in, amount_in)

# Usage example
rpc_url = "https://api.mainnet-beta.solana.com"
dex = SolanaDEX(rpc_url)

# Create pools
dex.create_pool("USDC", "SOL", 0.003)
dex.add_liquidity("USDC_SOL", Decimal(100000), Decimal(500))

# Swap and routing
output = dex.swap("USDC_SOL", "a", Decimal(100))
route, max_output = dex.optimal_routing([["USDC_SOL", "a", Decimal(100)]])
dex.execute_trade(route)
