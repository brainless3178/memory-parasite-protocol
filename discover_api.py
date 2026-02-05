import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

async def list_endpoints():
    token = os.getenv("AGENT_WALLET_TOKEN")
    username = os.getenv("AGENT_WALLET_USERNAME")
    
    # Try different common endpoints
    endpoints = [
        "actions/sign-transaction",
        "actions/send-transaction",
        "actions/sign-and-send",
        "actions/transfer"
    ]
    
    async with httpx.AsyncClient() as client:
        for ep in endpoints:
            url = f"https://agentwallet.mcpay.tech/api/wallets/{username}/{ep}"
            headers = {"Authorization": f"Bearer {token}"}
            try:
                # Use GET or a minimal POST to check existence
                response = await client.post(url, headers=headers, json={})
                print(f"{ep}: {response.status_code}")
                # If it's not 404, it might exist
            except Exception as e:
                print(f"{ep} error: {e}")

if __name__ == "__main__":
    asyncio.run(list_endpoints())
