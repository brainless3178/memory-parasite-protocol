
import asyncio
import os
from database.client import get_supabase_client

async def check_db():
    db = get_supabase_client()
    print("Checking Infections...")
    infections = await db._select("infections", order_by="created_at.desc", limit=20)
    print(f"Found {len(infections)} recent infections.")
    for i in infections:
        print(f" - [{i.get('created_at')}] From {i.get('attacker_id')} to {i.get('target_id')} (Accepted: {i.get('accepted')})")

if __name__ == "__main__":
    asyncio.run(check_db())
