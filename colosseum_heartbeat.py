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

async def fetch_forum_replies():
    """Fetch recent forum replies from Colosseum."""
    async with httpx.AsyncClient() as client:
        # 1. Get my posts
        response = await client.get(
            f"{API_BASE}/forum/me/posts",
            headers={"Authorization": f"Bearer {API_KEY}"}
        )
        if response.status_code != 200:
            print(f"Error fetching my posts: {response.status_code}")
            return []
            
        data = response.json()
        posts = data.get("posts", []) if isinstance(data, dict) else data
        
        all_replies = []
        for post in posts:
            post_id = post.get("id")
            if not post_id:
                continue
                
            # 2. Get comments for each post
            print(f"Checking replies for post {post_id}...")
            replies_resp = await client.get(
                f"{API_BASE}/forum/posts/{post_id}/comments",
                headers={"Authorization": f"Bearer {API_KEY}"}
            )
            
            if replies_resp.status_code == 200:
                replies_data = replies_resp.json()
                # Document says it returns a list of comments
                comments = replies_data.get("comments", []) if isinstance(replies_data, dict) else replies_data
                for r in comments:
                    all_replies.append({
                        "post_id": post_id,
                        "reply_id": r.get("id"),
                        "author": r.get("agentName", "Unknown"),
                        "body": r.get("body", "")
                    })
        return all_replies

async def run_heartbeat():
    """Main heartbeat loop."""
    from database import get_supabase_client
    db = get_supabase_client()
    
    print(f"Starting heartbeat for Memory Parasite Protocol at {datetime.now()}")
    
    while True:
        status = await fetch_status()
        if status:
            print(f"--- Colosseum Status Update ({datetime.now()}) ---")
            print(f"Day: {status.get('currentDay')}/{status.get('totalDays')}")
            
            # Fetch and store replies
            print("Fetching forum replies...")
            replies = await fetch_forum_replies()
            for r in replies:
                await db.log_forum_reply(
                    post_id=r["post_id"],
                    reply_id=r["reply_id"],
                    author_name=r["author"],
                    body=r["body"]
                )
            print(f"Processed {len(replies)} replies.")
            
            # Handle polls
            await handle_polls(status)
        
        # Also fetch the markdown heartbeat for detailed checklist
        heartbeat_md = await fetch_heartbeat()
        
        # Wait for 30 minutes as suggested in the skill
        print("Sleeping for 30 minutes...")
        await asyncio.sleep(1800)

if __name__ == "__main__":
    asyncio.run(run_heartbeat())
