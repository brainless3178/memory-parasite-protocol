```python
import hashlib
import random

def generate_hash(data):
  return hashlib.sha256(data.encode()).hexdigest()

def create_pool(token, amount):
  hash_value = generate_hash(str(token))
  return hashlib.sha256(hash_value.encode()).hexdigest()

def main():
  token = "XYZ"
  amount = 10000
  pool_name = "VIP_Pool"

  hash_value = generate_hash(str(token))
  pool