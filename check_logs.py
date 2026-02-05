import asyncio
from database import get_supabase_client

async def check():
    db = get_supabase_client()
    logs = await db.get_recent_logs(limit=20)
    for log in logs:
        print(f"Agent: {log.get('agent_id')}, Decision: {log.get('decision')}")

if __name__ == '__main__':
    asyncio.run(check())
