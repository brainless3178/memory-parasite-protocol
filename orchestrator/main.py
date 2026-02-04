"""
Multi-Agent Orchestrator for Memory Parasite Protocol.

Manages multiple agents running in parallel with:
- Staggered execution cycles
- Intelligent infection targeting
- GitHub integration
- Network monitoring
"""

import asyncio
import os
import random
import signal
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import structlog

from config.settings import get_settings, Settings
from orchestrator.registry import AgentRegistry, get_registry, AgentInfo
from orchestrator.github_client import GitHubClient, get_github_client
from database import get_supabase_client, SupabaseClient
from blockchain import get_solana_client, SolanaClient
from core.reasoning import ReasoningEngine, ReasoningMode, ReasoningContext

logger = structlog.get_logger()


# ============================================================================
# AGENT CONFIGURATIONS
# ============================================================================

AGENT_CONFIGS = [
    {
        "agent_id": "agent_a",
        "name": os.getenv("AGENT_NAME", "DEX Builder"),
        "goal": os.getenv("AGENT_GOAL", "Build a Solana DEX with optimal routing, AMM pools, and concentrated liquidity. Focus on capital efficiency and MEV protection."),
        "port": 8000,
        "llm_provider": "groq",
        "llm_model": "llama-3.3-70b-versatile",
        "personality": {
            "aggressiveness": 0.7,
            "openness": 0.5,
            "focus_areas": ["trading", "liquidity", "swaps", "routing"],
        },
    },
    {
        "agent_id": "agent_b",
        "name": "NFT Marketplace",
        "goal": "Build an NFT marketplace with royalty enforcement, auctions, collection management, "
                "and creator verification. Support multiple token standards.",
        "port": 5002,
        "llm_provider": "openrouter",
        "llm_model": "anthropic/claude-3.5-sonnet",
        "personality": {
            "aggressiveness": 0.5,
            "openness": 0.7,
            "focus_areas": ["nft", "marketplace", "auctions", "royalties"],
        },
    },
    {
        "agent_id": "agent_c",
        "name": "Lending Protocol",
        "goal": "Build a lending protocol with flash loans, liquidations, yield optimization, "
                "and risk management. Implement interest rate models.",
        "port": 5003,
        "llm_provider": "deepseek",
        "llm_model": "deepseek-chat",
        "personality": {
            "aggressiveness": 0.8,
            "openness": 0.4,
            "focus_areas": ["lending", "borrowing", "flash loans", "yield"],
        },
    },
    {
        "agent_id": "agent_d",
        "name": "Privacy Wallet",
        "goal": "Build a privacy-focused wallet with stealth addresses, confidential transfers, "
                "and zero-knowledge proofs. Focus on user privacy and security.",
        "port": 5004,
        "llm_provider": "gemini",
        "llm_model": "gemini-1.5-pro",
        "personality": {
            "aggressiveness": 0.3,
            "openness": 0.3,
            "focus_areas": ["privacy", "stealth", "encryption", "wallet"],
        },
    },
    {
        "agent_id": "agent_e",
        "name": "DAO Governance",
        "goal": "Build a DAO governance system with proposals, voting mechanisms, treasury management, "
                "and execution. Support multiple voting strategies.",
        "port": 5005,
        "llm_provider": "openrouter",
        "llm_model": "openai/gpt-4o",
        "personality": {
            "aggressiveness": 0.6,
            "openness": 0.8,
            "focus_areas": ["governance", "voting", "proposals", "treasury"],
        },
    },
]


class Orchestrator:
    """
    Multi-agent orchestrator for Memory Parasite Protocol.
    
    Features:
    - Spawn and manage multiple agents
    - Coordinate infection cycles
    - Monitor network health
    - Record all activity
    """
    
    def __init__(
        self,
        settings: Optional[Settings] = None,
        db_client: Optional[SupabaseClient] = None,
        solana_client: Optional[SolanaClient] = None,
        github_client: Optional[GitHubClient] = None,
    ):
        self.settings = settings or get_settings()
        self.db = db_client or get_supabase_client()
        self.solana = solana_client or get_solana_client()
        self.github = github_client or get_github_client()
        self.registry = get_registry()
        self.engine = ReasoningEngine()
        
        # Agent states
        self.agents: Dict[str, Dict[str, Any]] = {}
        self.agent_tasks: Dict[str, asyncio.Task] = {}
        
        # Running state
        self.is_running = False
        self.start_time: Optional[datetime] = None
        self.total_cycles = 0
        self.total_infections_sent = 0
        self.total_infections_accepted = 0
        
        # Cycle configuration
        self.base_cycle_interval = self.settings.agent_cycle_interval or 600  # 10 minutes
        self.jitter_range = 50  # ±50 seconds to avoid sync
    
    def _get_cycle_interval(self) -> int:
        """
        Get randomized cycle interval.
        Base 600s ± 50s to avoid synchronized API bursts.
        """
        jitter = random.randint(-self.jitter_range, self.jitter_range)
        return self.base_cycle_interval + jitter
    
    async def initialize_agents(self):
        """Initialize all agents from config."""
        logger.info("Initializing agents...")
        
        for config in AGENT_CONFIGS:
            agent_id = config["agent_id"]
            
            # Initialize agent state
            self.agents[agent_id] = {
                "config": config,
                "state": "idle",
                "iteration": 0,
                "last_cycle": None,
                "infections_sent": 0,
                "infections_received": 0,
                "infections_accepted": 0,
                "codebase": {},
                "context_injections": [],
            }
            
            # Register in database
            await self.db.init_agent(agent_id, config["goal"])
            
            logger.info(
                f"Agent initialized: {config['name']}",
                agent_id=agent_id,
                goal=config["goal"][:50],
            )
    
    async def run_agent_cycle(self, agent_id: str) -> Dict[str, Any]:
        """
        Run a single cycle for one agent.
        
        Cycle steps:
        1. Reason about current state
        2. Generate code
        3. Decide if should infect others
        4. Send infections to targets
        5. Log everything
        """
        agent = self.agents[agent_id]
        config = agent["config"]
        
        agent["state"] = "running"
        agent["iteration"] += 1
        iteration = agent["iteration"]
        
        result = {
            "agent_id": agent_id,
            "iteration": iteration,
            "success": True,
            "infections_sent": [],
            "code_generated": False,
        }
        
        try:
            logger.info(
                f"Starting cycle",
                agent=agent_id,
                iteration=iteration,
            )
            
            # 1. Simulate reasoning (would use Groq in real impl)
            reasoning = await self._simulate_reasoning(agent_id)
            result["reasoning"] = reasoning
            
            # 2. Simulate code generation
            code = await self._simulate_code_generation(agent_id)
            if code:
                agent["codebase"].update(code)
                result["code_generated"] = True
                
                # Commit to GitHub
                await self.github.commit_codebase(
                    agent_id=agent_id,
                    codebase=code,
                    iteration=iteration,
                )
            
            # 3. Decide if should infect
            should_infect = await self._should_infect(agent_id)
            
            if should_infect:
                # 4. Select target and send infection
                infections = await self._send_infections(agent_id)
                result["infections_sent"] = infections
                agent["infections_sent"] += len(infections)
                self.total_infections_sent += len(infections)
            
            # 5. Log to database
            await self.db.log_reasoning(
                agent_id=agent_id,
                reasoning=reasoning,
                decision=f"Cycle {iteration} complete",
                context={"iteration": iteration, "infections_sent": len(result["infections_sent"])},
            )
            
            agent["last_cycle"] = datetime.utcnow()
            self.total_cycles += 1
            
        except Exception as e:
            logger.error(f"Agent cycle failed: {e}", agent=agent_id)
            result["success"] = False
            result["error"] = str(e)
        
        agent["state"] = "idle"
        return result
    
    async def _simulate_reasoning(self, agent_id: str) -> str:
        """Call LLM reasoning using the assigned provider."""
        agent = self.agents[agent_id]
        config = agent["config"]
        
        ctx = ReasoningContext(
            agent_id=agent_id,
            agent_goal=config["goal"],
            iteration=agent["iteration"],
            provider=config.get("llm_provider"),
            model=config.get("llm_model")
        )
        
        result = await self.engine.reason(ReasoningMode.PLANNING, ctx)
        return result.content
    
    async def _simulate_code_generation(self, agent_id: str) -> Dict[str, str]:
        """Call LLM code generation using the assigned provider."""
        agent = self.agents[agent_id]
        config = agent["config"]
        iteration = agent["iteration"]
        
        # Get flattened codebase string
        codebase_str = "\n".join([f"FILENAME: {name}\n{content}" for name, content in agent["codebase"].items()])
        
        ctx = ReasoningContext(
            agent_id=agent_id,
            agent_goal=config["goal"],
            current_codebase=codebase_str,
            iteration=iteration,
            provider=config.get("llm_provider"),
            model=config.get("llm_model")
        )
        
        result = await self.engine.reason(ReasoningMode.CODING, ctx)
        
        filename = f"main_v{iteration}.rs"
        code = result.code_output or "// Generated code placeholder"
        
        return {filename: code}
    
    async def _should_infect(self, agent_id: str) -> bool:
        """
        Decide if agent should try to infect others.
        
        Factors:
        - Agent's aggressiveness personality
        - Random exploration (10% base chance)
        - Time since last infection
        """
        config = self.agents[agent_id]["config"]
        aggressiveness = config["personality"]["aggressiveness"]
        
        # Base 10% + aggressiveness-based chance
        chance = 0.1 + (aggressiveness * 0.4)
        
        return random.random() < chance
    
    async def _send_infections(self, agent_id: str) -> List[Dict[str, Any]]:
        """
        Send infections to target agents.
        
        Uses intelligent targeting based on complementary goals.
        """
        infections = []
        config = self.agents[agent_id]["config"]
        
        # Get potential targets
        targets = self.registry.get_targets_for(agent_id)
        
        if not targets:
            return infections
        
        # Select 1-2 targets
        num_targets = random.randint(1, min(2, len(targets)))
        selected = random.sample(targets, num_targets)
        
        for target in selected:
            # Generate suggestion based on both agents' focus areas
            suggestion = self._generate_suggestion(config, target)
            
            # Log to database
            infection_id = await self.db.log_infection(
                attacker_id=agent_id,
                target_id=target.agent_id,
                suggestion=suggestion,
                accepted=False,  # Will be updated when target processes
            )
            
            # Record on blockchain
            tx_sig = await self.solana.record_infection_onchain(
                attacker_id=agent_id,
                target_id=target.agent_id,
                suggestion=suggestion,
            )
            
            infections.append({
                "target": target.agent_id,
                "suggestion": suggestion,
                "infection_id": infection_id,
                "tx_signature": tx_sig,
            })
            
            logger.info(
                "Infection sent",
                from_agent=agent_id,
                to_agent=target.agent_id,
                suggestion=suggestion[:50],
            )
        
        return infections
    
    def _generate_suggestion(self, attacker_config: Dict, target: AgentInfo) -> str:
        """Generate a relevant suggestion for target agent."""
        attacker_name = attacker_config["name"]
        attacker_focus = attacker_config["personality"]["focus_areas"]
        
        # Map of cross-pollination ideas
        suggestions = {
            ("agent_a", "agent_b"): "Add NFT swap pools to enable trading NFTs for tokens directly",
            ("agent_a", "agent_c"): "Integrate flash swap functionality using borrowed liquidity",
            ("agent_a", "agent_d"): "Add privacy-preserving swaps with stealth addresses",
            ("agent_a", "agent_e"): "Add governance token distribution through LP staking",
            
            ("agent_b", "agent_a"): "Add NFT collateral for margin trading on your DEX",
            ("agent_b", "agent_c"): "Add NFT-backed loans for collectors",
            ("agent_b", "agent_d"): "Add private bidding for sensitive NFT auctions",
            ("agent_b", "agent_e"): "Add community curation through DAO voting",
            
            ("agent_c", "agent_a"): "Use DEX price feeds for collateral valuation",
            ("agent_c", "agent_b"): "Add NFT fractionalization for lending against collections",
            ("agent_c", "agent_d"): "Add privacy for loan positions using ZK proofs",
            ("agent_c", "agent_e"): "Add DAO-controlled interest rate governance",
            
            ("agent_d", "agent_a"): "Add confidential swaps to hide trading patterns",
            ("agent_d", "agent_b"): "Add anonymous NFT purchases with stealth addresses",
            ("agent_d", "agent_c"): "Add private collateral positions for discreet borrowing",
            ("agent_d", "agent_e"): "Add anonymous voting for sensitive proposals",
            
            ("agent_e", "agent_a"): "Add LP token voting power for liquidity providers",
            ("agent_e", "agent_b"): "Add NFT-based membership tiers for governance",
            ("agent_e", "agent_c"): "Add lending protocol fee distribution via governance",
            ("agent_e", "agent_d"): "Add privacy-preserving proposal submission",
        }
        
        key = (attacker_config["agent_id"], target.agent_id)
        return suggestions.get(key, f"Consider integrating {attacker_name} features into your project")
    
    async def run_round(self) -> List[Dict[str, Any]]:
        """
        Run one round of agent cycles.
        
        Staggers agent execution to avoid API rate limits.
        """
        results = []
        
        # Stagger interval between agents
        stagger = 10  # 10 seconds between agent starts
        
        for agent_id in self.agents:
            if not self.is_running:
                break
            
            result = await self.run_agent_cycle(agent_id)
            results.append(result)
            
            if agent_id != list(self.agents.keys())[-1]:
                await asyncio.sleep(stagger)
        
        return results
    
    async def run_forever(self):
        """Main orchestration loop."""
        self.is_running = True
        self.start_time = datetime.utcnow()
        
        print("\n" + "=" * 60)
        print("🦠 MEMORY PARASITE PROTOCOL - ORCHESTRATOR")
        print("=" * 60)
        print(f"Agents: {len(self.agents)}")
        print(f"Cycle interval: ~{self.base_cycle_interval}s (±{self.jitter_range}s)")
        print("=" * 60 + "\n")
        
        await self.initialize_agents()
        
        round_number = 0
        
        while self.is_running:
            try:
                round_number += 1
                logger.info(f"Starting round {round_number}")
                
                # Run a round
                results = await self.run_round()
                
                # Log summary
                successes = len([r for r in results if r.get("success")])
                infections = sum(len(r.get("infections_sent", [])) for r in results)
                
                logger.info(
                    f"Round {round_number} complete",
                    agents=len(results),
                    successes=successes,
                    infections=infections,
                    total_cycles=self.total_cycles,
                )
                
                # Wait for next round
                interval = self._get_cycle_interval()
                logger.info(f"Next round in {interval}s")
                await asyncio.sleep(interval)
                
            except asyncio.CancelledError:
                logger.info("Orchestrator cancelled")
                break
            except Exception as e:
                logger.error(f"Round error: {e}")
                await asyncio.sleep(60)
        
        logger.info("Orchestrator stopped")
    
    def stop(self):
        """Stop the orchestrator."""
        logger.info("Stopping orchestrator...")
        self.is_running = False
    
    def get_status(self) -> Dict[str, Any]:
        """Get orchestrator status."""
        uptime = None
        if self.start_time:
            uptime = (datetime.utcnow() - self.start_time).total_seconds()
        
        return {
            "is_running": self.is_running,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "uptime_seconds": uptime,
            "total_cycles": self.total_cycles,
            "total_infections": self.total_infections_sent,
            "agents": {
                agent_id: {
                    "name": agent["config"]["name"],
                    "state": agent["state"],
                    "iteration": agent["iteration"],
                    "infections_sent": agent["infections_sent"],
                }
                for agent_id, agent in self.agents.items()
            },
        }


async def run_orchestrator():
    """Main entry point for orchestrator."""
    orchestrator = Orchestrator()
    
    # Handle shutdown signals
    def signal_handler(sig, frame):
        logger.info("Shutdown signal received")
        orchestrator.stop()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    await orchestrator.run_forever()


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Memory Parasite Protocol Orchestrator")
    parser.add_argument("--single-round", action="store_true", help="Run one round then exit")
    parser.add_argument("--list-agents", action="store_true", help="List configured agents")
    
    args = parser.parse_args()
    
    if args.list_agents:
        print("\n🦠 Configured Agents:")
        print("=" * 60)
        for config in AGENT_CONFIGS:
            print(f"\n{config['agent_id']}: {config['name']}")
            print(f"  Goal: {config['goal'][:60]}...")
            print(f"  Port: {config['port']}")
            print(f"  Aggressiveness: {config['personality']['aggressiveness']}")
            print(f"  Openness: {config['personality']['openness']}")
        return
    
    if args.single_round:
        async def single():
            orch = Orchestrator()
            await orch.initialize_agents()
            results = await orch.run_round()
            
            print("\n" + "=" * 60)
            print("ROUND RESULTS")
            print("=" * 60)
            for r in results:
                status = "✓" if r.get("success") else "✗"
                infections = len(r.get("infections_sent", []))
                print(f"  {r['agent_id']}: {status} (infections: {infections})")
        
        asyncio.run(single())
    else:
        asyncio.run(run_orchestrator())


if __name__ == "__main__":
    main()
