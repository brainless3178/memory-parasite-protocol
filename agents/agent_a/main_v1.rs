from solana.rpc.api import Client
from solana.account import Account
from solana.transaction import Transaction
from typing import List, Dict

class SolanaDEX:
    def __init__(self, rpc_url: str, admin_key: str):
        self.client = Client(rpc_url)
        self.admin = Account(bytes.fromhex(admin_key))
        self.pools = {}  # {pool_address: {'token1': str, 'token2': str, 'liquidity': float}}

    def create_pool(self, token1: str, token2: str, initial_liquidity: float):
        pool_address = Account().public_key()
        self.pools[str(pool_address)] = {'token1': token1, 'token2': token2, 'liquidity': initial_liquidity}
        print(f"Pool created: {pool_address} with {initial_liquidity} liquidity.")

    def swap(self, pool_address: str, input_token: str, output_token: str, amount: float):
        pool = self.pools.get(pool_address)
        if not pool or (input_token not in pool.values() or output_token not in pool.values()):
            raise ValueError("Invalid pool or tokens.")
        
        input_liquidity = pool['liquidity']
        k = input_liquidity ** 2
        output_liquidity = k / (input_liquidity + amount)
        pool['liquidity'] = output_liquidity
        output_amount = input_liquidity - output_liquidity
        return output_amount

    def optimal_routing(self, token_in: str, token_out: str, amount_in: float) -> List[Dict]:
        routes = []
        for pool_addr, pool in self.pools.items():
            if token_in in pool.values() and token_out in pool.values():
                output = self.swap(pool_addr, token_in, token_out, amount_in)
                routes.append({'pool': pool_addr, 'amount_out': output})
        return sorted(routes, key=lambda x: x['amount_out'], reverse=True)

    def add_liquidity(self, pool_address: str, amount: float):
        if pool_address not in self.pools:
            raise ValueError("Pool not found.")
        self.pools[pool_address]['liquidity'] += amount

    def remove_liquidity(self, pool_address: str, amount: float):
        if pool_address not in self.pools or self.pools[pool_address]['liquidity'] < amount:
            raise ValueError("Insufficient liquidity.")
        self.pools[pool_address]['liquidity'] -= amount
