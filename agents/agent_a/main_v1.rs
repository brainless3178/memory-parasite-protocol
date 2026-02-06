from solana.rpc.api import Client
from solana.transaction import Transaction
from spl.token.instructions import approve, transfer, initialize_account
from spl.token.constants import TOKEN_PROGRAM_ID
from decimal import Decimal
from collections import defaultdict

class SolanaDEX:
    def __init__(self, rpc_url):
        self.client = Client(rpc_url)
        self.pools = defaultdict(list)  # Structure: {token_pair: [pool1, pool2, ...]}
        self.fee_tiers = [0.0001, 0.0005, 0.003]  # Concentrated liquidity fee tiers
    
    def create_pool(self, token_a, token_b, initial_liquidity, fee_tier):
        if fee_tier not in self.fee_tiers:
            raise ValueError("Invalid fee tier")
        key = tuple(sorted([token_a, token_b]))
        pool = {
            "token_a": token_a,
            "token_b": token_b,
            "liquidity": initial_liquidity,
            "fee_tier": fee_tier,
            "state": "active"
        }
        self.pools[key].append(pool)

    def optimal_route(self, input_token, output_token, amount):
        key = tuple(sorted([input_token, output_token]))
        if key not in self.pools:
            raise Exception("No available pools")
        
        routes = self.pools[key]
        best_route, best_output = None, 0
        for pool in routes:
            fee = amount * pool["fee_tier"]
            output = amount - fee
            if output > best_output:
                best_output = output
                best_route = pool
        return best_route, best_output

    def execute_swap(self, wallet, pool, input_amount, min_output):
        if pool["state"] != "active":
            raise Exception("Invalid pool state")
        
        fee = input_amount * pool["fee_tier"]
        output_amount = input_amount - fee
        if output_amount < min_output:
            raise Exception("Slippage exceeded")
        
        transaction = Transaction()
        approve_ix = approve(
            source=wallet,
            delegate=TOKEN_PROGRAM_ID,
            owner=TOKEN_PROGRAM_ID,
            amount=input_amount
        )
        transfer_ix = transfer(
            source=pool["token_a"],
            dest=pool["token_b"],
            owner=wallet,
            amount=output_amount
        )
        transaction.add(approve_ix, transfer_ix)
        return self.client.send_transaction(transaction, wallet)

    def add_liquidity(self, pool, token_a_amount, token_b_amount):
        if pool["state"] != "active":
            raise Exception("Inactive pool")
        pool["liquidity"] += Decimal(token_a_amount + token_b_amount)

    def remove_liquidity(self, pool, liquidity_amount):
        if liquidity_amount > pool["liquidity"]:
            raise Exception("Insufficient liquidity")
        pool["liquidity"] -= liquidity_amount

# Initialize and Example Usage
rpc = "https://api.mainnet-beta.solana.com"
dex = SolanaDEX(rpc)
dex.create_pool("USDC", "SOL", 1_000_000, 0.003)  # Example pool
route, output = dex.optimal_route("USDC", "SOL", 100)
print(f"Best Route: {route}, Estimated Output: {output}")
