
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
    # Speed up for test
    orch.registry.http_client.timeout = 5.0
    await orch.initialize_agents()
    print("\nStarting Test Round...")
    
    results = []
    # Manual iteration to see progress
    for agent_id in orch.agents:
        print(f"Executing cycle for {agent_id}...")
        try:
            result = await orch.run_agent_cycle(agent_id)
            results.append(result)
            print(f"  Result for {agent_id}: Success={result['success']}")
        except Exception as e:
            print(f"  Result for {agent_id}: Error={e}")
        
    print("\nFinal Round Results Summary:")
    for r in results:
        status = "SUCCESS" if r.get("success") else f"FAILED: {r.get('error')}"
        print(f" - {r['agent_id']}: {status}")
        if r.get("infections_sent"):
            for i in r["infections_sent"]:
                print(f"   -> Infection to {i['target']} (Accepted: {i['accepted']})")

if __name__ == "__main__":
    asyncio.run(test_round())
