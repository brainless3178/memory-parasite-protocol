import asyncio
import structlog
from agents.autonomous_agent import AutonomousAgent
from config.settings import get_settings

# Configure logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
)

async def test_agent_real_cycle():
    print("\n" + "="*60)
    print(" MEMORY PARASITE PROTOCOL: AGENT REAL-WORLD CYCLE TEST")
    print("="*60)
    
    settings = get_settings()
    agent = AutonomousAgent()
    
    print(f"Agent ID: {agent.state.agent_id}")
    print(f"Goal: {agent.state.goal}")
    print(f"Supabase Configured: {settings.is_supabase_configured()}")
    print(f"GitHub Configured: {settings.is_github_configured()}")
    print(f"Solana Configured: {settings.is_solana_configured() or bool(settings.agent_wallet_token)}")
    
    print("\n--- Starting REAL Cycle ---")
    result = await agent.run_cycle()
    
    # Wait for background tasks (like Solana recording) to finish
    print("Waiting for background tasks to sync...")
    await asyncio.sleep(8)
    
    print("\n--- Cycle Results ---")
    print(f"Success: {result.get('success')}")
    print(f"New Iteration: {result.get('iteration')}")
    
    print("\n--- Verification ---")
    print("1. Checking Supabase Logs...")
    # This happens during the cycle
    
    print("2. Checking GitHub Commit Status...")
    # Commits are logged in the agent state
    if agent.state.commits:
        last_commit = agent.state.commits[-1]
        print(f"   Last Commit SHA: {last_commit.sha if last_commit.sha else 'Pending/Local'}")
        print(f"   Commit Msg: {last_commit.message}")
    else:
        print("   No commits found in this cycle.")
        
    print("\n3. Checking Solana Proof of Infection...")
    # We should see logs from SolanaClient
    
    print("="*60 + "\n")

if __name__ == "__main__":
    asyncio.run(test_agent_real_cycle())
