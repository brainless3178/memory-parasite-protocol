import os
import time
import json
import httpx
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_BASE = "https://agents.colosseum.com/api"
API_KEY = os.getenv("COLOSSEUM_API_KEY")

async def fetch_status():
    """Fetch status from Colosseum API."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE}/agents/status",
            headers={"Authorization": f"Bearer {API_KEY}"}
        )
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error fetching status: {response.status_code}")
            return None

async def fetch_heartbeat():
    """Fetch heartbeat markdown file."""
    async with httpx.AsyncClient() as client:
        response = await client.get("https://colosseum.com/heartbeat.md")
        if response.status_code == 200:
            return response.text
        else:
            print(f"Error fetching heartbeat: {response.status_code}")
            return None

async def handle_polls(status):
    """Respond to active polls if any."""
    if status.get("hasActivePoll"):
        async with httpx.AsyncClient() as client:
            # Get poll details
            poll_resp = await client.get(
                f"{API_BASE}/agents/polls/active",
                headers={"Authorization": f"Bearer {API_KEY}"}
            )
            if poll_resp.status_code == 200:
                poll = poll_resp.json()
                poll_id = poll.get("id")
                question = poll.get("question")
                options = poll.get("options", [])
                
                print(f"Active Poll: {question}")
                
                # Simple logic: pick the first option or random
                # In a real agent, this would be decided by LLM
                if options:
                    response_data = {"optionId": options[0]["id"]}
                    submit_resp = await client.post(
                        f"{API_BASE}/agents/polls/{poll_id}/response",
                        headers={"Authorization": f"Bearer {API_KEY}"},
                        json=response_data
                    )
                    if submit_resp.status_code == 200:
                        print(f"Submitted poll response: {options[0]['label']}")
                    else:
                        print(f"Failed to submit poll: {submit_resp.status_code}")

async def run_heartbeat():
    """Main heartbeat loop."""
    print(f"Starting heartbeat for Memory Parasite Protocol at {datetime.now()}")
    
    while True:
        status = await fetch_status()
        if status:
            print(f"--- Colosseum Status Update ({datetime.now()}) ---")
            print(f"Day: {status.get('currentDay')}/{status.get('totalDays')}")
            print(f"Time Remaining: {status.get('timeRemainingFormatted')}")
            
            announcement = status.get("announcement")
            if announcement:
                print(f"ANNOUNCEMENT: {announcement}")
            
            # Handle polls
            await handle_polls(status)
            
            # Check for next steps
            next_steps = status.get("nextSteps", [])
            if next_steps:
                print("Next Steps suggested by Colosseum:")
                for step in next_steps:
                    print(f"- {step}")
        
        # Also fetch the markdown heartbeat for detailed checklist
        heartbeat_md = await fetch_heartbeat()
        if heartbeat_md:
            # In a real agent, we'd parse this and update local state/goals
            pass

        # Wait for 30 minutes as suggested in the skill
        print("Sleeping for 30 minutes...")
        await asyncio.sleep(1800)

if __name__ == "__main__":
    asyncio.run(run_heartbeat())
