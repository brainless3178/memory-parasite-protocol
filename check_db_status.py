
import asyncio
import os
from database.client import get_supabase_client

async def check_db():
    db = get_supabase_client()
    print("Checking Agents...")
    agents = await db._select("agents")
    print(f"Found {len(agents)} agents.")
    for a in agents:
        print(f" - {a.get('agent_id')}: {a.get('is_active')}")
    
    print("\nChecking Infections...")
    infections = await db._select("infections", limit=5)
    print(f"Found {len(infections)} recent infections.")
    for i in infections:
        print(f" - From {i.get('attacker_id')} to {i.get('target_id')} (Accepted: {i.get('accepted')})")

if __name__ == "__main__":
    asyncio.run(check_db())
