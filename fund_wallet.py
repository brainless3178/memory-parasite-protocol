import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

async def try_transfer():
    token = os.getenv("AGENT_WALLET_TOKEN")
    username = os.getenv("AGENT_WALLET_USERNAME")
    target = "7jyvect6njn2bxx2rMdJVVa4ah1YuaCxoDfDU8z58eGj"
    
    if not token or not username:
        print("Missing AgentWallet credentials")
        return

    url = f"https://agentwallet.mcpay.tech/api/wallets/{username}/actions/transfer"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "chain": "solana",
        "chainId": "solana:EtWTRABZaYq6iMfeYKouRu166VU2xqa1",
        "to": target,
        "amount": "0.5",
        "asset": "sol"
    }
    
    print(f"Attempting transfer via {url}...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, json=payload)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(try_transfer())
