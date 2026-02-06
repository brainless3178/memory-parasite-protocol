from solana.rpc.api import Client
from solana.transaction import Transaction
from spl.token.constants import TOKEN_PROGRAM_ID
from spl.token.instructions import transfer, approve, initialize_account, initialize_mint
from solana.publickey import PublicKey
from solana.keypair import Keypair
from solana.system_program import create_account, CreateAccountParams
from decimal import Decimal

class SolanaDEX:
    def __init__(self, rpc_url):
        self.client = Client(rpc_url)
        self.pools = {}  # Pool data
        self.fees = Decimal("0.003")  # Default fee, adjustable per pool

    def create_pool(self, mint_a, mint_b, liquidity_a, liquidity_b, owner_keypair):
        pool_keypair = Keypair()
        self.pools[pool_keypair.public_key] = {
            "mint_a": mint_a,
            "mint_b": mint_b,
            "liquidity_a": liquidity_a,
            "liquidity_b": liquidity_b,
            "fee": self.fees,
        }
        return pool_keypair.public_key

    def swap(self, pool_pubkey, amount_in, mint_in, mint_out, user_keypair):
        pool = self.pools.get(pool_pubkey)
        if not pool:
            raise ValueError("Pool does not exist")

        if mint_in == pool["mint_a"] and mint_out == pool["mint_b"]:
            input_reserve, output_reserve = pool["liquidity_a"], pool["liquidity_b"]
        elif mint_in == pool["mint_b"] and mint_out == pool["mint_a"]:
            input_reserve, output_reserve = pool["liquidity_b"], pool["liquidity_a"]
        else:
            raise ValueError("Invalid token pair")

        amount_in_with_fee = Decimal(amount_in) * (1 - pool["fee"])
        amount_out = (amount_in_with_fee * output_reserve) / (input_reserve + amount_in_with_fee)

        pool["liquidity_a"], pool["liquidity_b"] = (
            input_reserve + Decimal(amount_in),
            output_reserve - Decimal(amount_out),
        )

        # Execute transfer using Solana transaction
        transaction = Transaction()
        transaction.add(
            transfer(
                source=user_keypair.public_key,
                dest=pool_pubkey,
                owner=user_keypair.public_key,
                amount=int(amount_in),
                program_id=TOKEN_PROGRAM_ID,
            )
        )
        self.client.send_transaction(transaction, user_keypair)

        return amount_out

    def route_swap(self, path, amount_in, user_keypair):
        amount = Decimal(amount_in)
        for i in range(len(path) - 1):
            pool_pubkey, mint_in, mint_out = path[i]
            amount = self.swap(pool_pubkey, amount, mint_in, mint_out, user_keypair)
        return amount

    def add_liquidity(self, pool_pubkey, amount_a, amount_b, user_keypair):
        pool = self.pools.get(pool_pubkey)
        if not pool:
            raise ValueError("Pool does not exist")
        pool["liquidity_a"] += Decimal(amount_a)
        pool["liquidity_b"] += Decimal(amount_b)

        transaction = Transaction()
        transaction.add(
            transfer(
                source=user_keypair.public_key,
                dest=pool_pubkey,
                owner=user_keypair.public_key,
                amount=int(amount_a),
                program_id=TOKEN_PROGRAM_ID,
            )
        )
        transaction.add(
            transfer(
                source=user_keypair.public_key,
                dest=pool_pubkey,
                owner=user_keypair.public_key,
                amount=int(amount_b),
                program_id=TOKEN_PROGRAM_ID,
            )
        )
        self.client.send_transaction(transaction, user_keypair)

    def remove_liquidity(self, pool_pubkey, shares, user_keypair):
        pool = self.pools.get(pool_pubkey)
        if not pool:
            raise ValueError("Pool does not exist")

        total_liquidity = pool["liquidity_a"] + pool["liquidity_b"]
        amount_a = shares * pool["liquidity_a"] / total_liquidity
        amount_b = shares * pool["liquidity_b"] / total_liquidity

        pool["liquidity_a"] -= amount_a
        pool["liquidity_b"] -= amount_b

        transaction = Transaction()
        transaction.add(
            transfer(
                source=pool_pubkey,
                dest=user_keypair.public_key,
                owner=pool_pubkey,
                amount=int(amount_a),
                program_id=TOKEN_PROGRAM_ID,
            )
        )
        transaction.add(
            transfer(
                source=pool_pubkey,
                dest=user_keypair.public_key,
                owner=pool_pubkey,
                amount=int(amount_b),
                program_id=TOKEN_PROGRAM_ID,
            )
        )
        self.client.send_transaction(transaction, user_keypair)

# Example usage
rpc_url = "https://api.mainnet-beta.solana.com"
dex = SolanaDEX(rpc_url)
owner = Keypair()
mint_a = PublicKey("MintAddressA")
mint_b = PublicKey("MintAddressB")
pool_pubkey = dex.create_pool(mint_a, mint_b, 1000, 1000, owner)
