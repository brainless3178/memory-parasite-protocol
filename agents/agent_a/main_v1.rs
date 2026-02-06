import hashlib

# Constants
CHAIN_ID = 101
RPC_URL = "https://api.mainnet-beta.solana.com"

# Import required libraries
from solana.rpc.api import Client
from spl.token.instructions import create_associated_token_account

# Initialize client
client = Client(RPC_URL)

# Define functions
def get_token_account(wallet, token_mint):
    """Get token account for wallet and token mint."""
    return client.get_token_accounts_by_owner(
        wallet.public_key, 
        {"mint": token_mint}
    )['result']['value'][0]['pubkey']

def create_associated_token_account_ix(wallet, token_mint):
    """Create associated token account instruction."""
    return create_associated_token_account(
        wallet.public_key, 
        token_mint, 
        wallet.public_key
    )

def get_lamports(wallet):
    """Get lamports for wallet."""
    return client.get_balance(wallet.public_key)

# Define classes
class Token:
    def __init__(self, mint, name):
        self.mint = mint
        self.name = name

class Wallet:
    def __init__(self, private_key):
        self.private_key = private_key
        self.public_key = None  # initialize later

# Main
if __name__ == "__main__":
    # Create wallet
    wallet = Wallet("your_private_key_here")
    wallet.public_key = hashlib.sha256(wallet.private_key.encode()).hexdigest()
    
    # Create tokens
    token1 = Token("token1_mint", "Token 1")
    token2 = Token("token2_mint", "Token 2")

    # Create associated token accounts
    ix1 = create_associated_token_account_ix(wallet, token1.mint)
    ix2 = create_associated_token_account_ix(wallet, token2.mint)

    # Get token accounts
    token_account1 = get_token_account(wallet, token1.mint)
    token_account2 = get_token_account(wallet, token2.mint)

    # Get lamports
    lamports = get_lamports(wallet)
    print(f"Lamports: {lamports}")
