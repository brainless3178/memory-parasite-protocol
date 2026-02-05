
import asyncio
import os
import structlog
from orchestrator.main import Orchestrator

# Configure logging to show in terminal
structlog.configure(
    processors=[structlog.dev.ConsoleRenderer()],
)

async def test_round():
    orch = Orchestrator()
    await orch.initialize_agents()
    print("\nStarting Test Round...")
    results = await orch.run_round()
    print("\nRound Results:")
    for r in results:
        status = "SUCCESS" if r.get("success") else f"FAILED: {r.get('error')}"
        print(f" - {r['agent_id']}: {status}")
        if r.get("infections_sent"):
            for i in r["infections_sent"]:
                print(f"   -> Infection to {i['target']} (Accepted: {i['accepted']})")

if __name__ == "__main__":
    asyncio.run(test_round())
