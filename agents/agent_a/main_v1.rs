import hashlib
import time

def generate_hash(data):
    hash_value = str(hashlib.sha256(data.encode()).hexdigest())
    return hash_value

def main():
    print("Starting DEX...")
    print("Hashing...")
    time.sleep(1)
    print("Routing...")
    print("Liquidity...")
    print("Finished.")

if __name__ == "__main__":
    main()
