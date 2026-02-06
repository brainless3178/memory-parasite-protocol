```python
import hashlib
import time

def generate_pool(token, amount):
    """Generates a simple liquidity pool."""
    pool_id = f"{token}-{amount}"
    pool = {
        "id": pool_id,
        "token": token,
        "amount": amount,
        "source": "pool",
        "timestamp": time.time()
    }
    return pool

def main():
    token = "SOL"
    amount = 10000

    while True:
        print(f"Generating pool: {