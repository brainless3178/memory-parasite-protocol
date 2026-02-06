import os
import numpy as np
from solana.publickey import PublicKey
from solana.rpc.api import Client
from solana.system_program import TransferParams

class DEX:
    def __init__(self, client, program_id):
        self.client = client
        self.program_id = program_id

    def create_amm_pool(self, token_a, token_b, fee):
        # Create AMM pool with specified tokens and fee
        params = {
            'token_a': token_a,
            'token_b': token_b,
            'fee': fee
        }
        return self.client.program_invoke(self.program_id, 'create_amm_pool', params)

    def add_liquidity(self, token_a, token_b, amount_a, amount_b):
        # Add liquidity to AMM pool
        params = {
            'token_a': token_a,
            'token_b': token_b,
            'amount_a': amount_a,
            'amount_b': amount_b
        }
        return self.client.program_invoke(self.program_id, 'add_liquidity', params)

    def swap(self, token_in, token_out, amount_in):
        # Swap tokens using AMM pool
        params = {
            'token_in': token_in,
            'token_out': token_out,
            'amount_in': amount_in
        }
        return self.client.program_invoke(self.program_id, 'swap', params)

# Initialize Solana client and program ID
client = Client("https://api.devnet.solana.com")
program_id = PublicKey("4GLbsJpGcMq95KKz8sJ FalksdfLk")

# Create DEX instance
dex = DEX(client, program_id)

# Create AMM pool with specified tokens and fee
token_a = PublicKey("dBKqf3P73FolderdagKLj7TGUe")
token_b = PublicKey("CDFolderalagKLj7TGUe7GUe8")
fee = 0.003
dex.create_amm_pool(token_a, token_b, fee)

# Add liquidity to AMM pool
amount_a = 1000
amount_b = 500
dex.add_liquidity(token_a, token_b, amount_a, amount_b)

# Swap tokens using AMM pool
token_in = token_a
token_out = token_b
amount_in = 100
dex.swap(token_in, token_out, amount_in)
