
import asyncio
import os
from database.client import get_supabase_client

async def check_db():
    db = get_supabase_client()
    print("Checking Reasoning Logs...")
    logs = await db._select("reasoning_logs", order_by="created_at.desc", limit=20)
    print(f"Found {len(logs)} recent logs.")
    for l in logs:
        print(f" - [{l.get('created_at')}] {l.get('agent_id')}: {l.get('decision')[:100]}...")

if __name__ == "__main__":
    asyncio.run(check_db())
