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
import hashlib
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
import structlog

from config.settings import get_settings, Settings
from orchestrator.registry import AgentRegistry, get_registry, AgentInfo
from orchestrator.github_client import GitHubClient, get_github_client
from database import get_supabase_client, SupabaseClient
from blockchain import get_solana_client, SolanaClient
from core.reasoning import ReasoningEngine, ReasoningMode, ReasoningContext
from orchestrator.viral_campaign import ViralCampaign
from core.emergence import EmergenceDetector

logger = structlog.get_logger()


# ============================================================================
# AGENT CONFIGURATIONS
# ============================================================================

AGENT_CONFIGS = [
    {
        "agent_id": "agent_a",
        "name": os.getenv("AGENT_A_NAME", "DEX Builder"),
        "goal": os.getenv("AGENT_A_GOAL", "Build a Solana DEX with optimal routing, AMM pools, and concentrated liquidity."),
        "port": 8000,
        "llm_provider": "groq",
        "llm_model": "llama-3.1-8b-instant", # High limit model
        "personality": {
            "aggressiveness": 0.7,
            "openness": 0.5,
            "focus_areas": ["trading", "liquidity", "swaps", "routing"],
        },
    },
    {
        "agent_id": "agent_b",
        "name": os.getenv("AGENT_B_NAME", "NFT Marketplace"),
        "goal": os.getenv("AGENT_B_GOAL", "Build an NFT marketplace with royalty enforcement, auctions, collection management."),
        "port": 5002,
        "llm_provider": "openrouter",
        "llm_model": "liquid/lfm-2.5-1.2b-instruct:free",
        "personality": {
            "aggressiveness": 0.5,
            "openness": 0.7,
            "focus_areas": ["nft", "marketplace", "auctions", "royalties"],
        },
    },
    {
        "agent_id": "agent_c",
        "name": os.getenv("AGENT_C_NAME", "Lending Protocol"),
        "goal": os.getenv("AGENT_C_GOAL", "Build a lending protocol with flash loans, liquidations, yield optimization."),
        "port": 5003,
        "llm_provider": "groq",
        "llm_model": "llama-3.1-8b-instant", # Using 8b for higher limits
        "personality": {
            "aggressiveness": 0.8,
            "openness": 0.4,
            "focus_areas": ["lending", "borrowing", "flash loans", "yield"],
        },
    },
    {
        "agent_id": "agent_d",
        "name": os.getenv("AGENT_D_NAME", "Privacy Wallet"),
        "goal": os.getenv("AGENT_D_GOAL", "Build a privacy-focused wallet with stealth addresses, confidential transfers."),
        "port": 5004,
        "llm_provider": "openrouter",
        "llm_model": "nvidia/nemotron-3-nano-30b-a3b:free",
        "personality": {
            "aggressiveness": 0.3,
            "openness": 0.3,
            "focus_areas": ["privacy", "stealth", "encryption", "wallet"],
        },
    },
    {
        "agent_id": "agent_e",
        "name": os.getenv("AGENT_E_NAME", "DAO Governance"),
        "goal": os.getenv("AGENT_E_GOAL", "Build a DAO governance system with proposals, voting mechanisms, treasury management."),
        "port": 5005,
        "llm_provider": "openrouter",
        "llm_model": "stepfun/step-3.5-flash:free",
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
        self.registry = get_registry(db_client=self.db)
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
        self.base_cycle_interval = self.settings.agent_cycle_interval or 60  # 1 minute during hackathon
        self.jitter_range = 50  # ±50 seconds to avoid sync

        # Viral Campaign
        self.campaign = ViralCampaign(self.settings.colosseum_api_key)

        # Emergence Detection
        self.emergence_detector = EmergenceDetector(self.db)
    
    def _get_cycle_interval(self) -> int:
        """
        Get randomized cycle interval.
        Protocol Standard: 5-7 Minutes (300s - 420s).
        """
        return random.randint(300, 420)
    
    async def initialize_agents(self):
        """Initialize all agents, prioritizing database then fallback config."""
        logger.info("Initializing agents from registry...")
        
        # Registry handles the DB sync
        agents_info = self.registry.get_all_agents()
        
        for agent_info in agents_info:
            agent_id = agent_info.agent_id
            
            # Initialize agent state if not already present
            if agent_id not in self.agents:
                self.agents[agent_id] = {
                    "config": {
                        "agent_id": agent_id,
                        "name": agent_id.replace("_", " ").title(),
                        "goal": agent_info.goal,
                        "personality": {"aggressiveness": 0.5, "openness": 0.5}
                    },
                    "state": "idle",
                    "iteration": 0,
                    "last_cycle": None,
                    "infections_sent": 0,
                    "infections_received": 0,
                    "infections_accepted": 0,
                    "codebase": {},
                    "context_injections": [],
                }
            
            # Register in database to ensure it exists
            if self.db:
                await self.db.init_agent(agent_id, agent_info.goal)
            
            logger.info(
                f"Agent initialized: {agent_id}",
                goal=agent_info.goal[:50],
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
            
            # 1. Execute reasoning
            reasoning = await self.execute_reasoning(agent_id)
            result["reasoning"] = reasoning
            
            # 2. Execute code generation
            code = await self.execute_code_generation(agent_id)
            if code:
                agent["codebase"].update(code)
                result["code_generated"] = True
                
                # Commit to GitHub
                await self.github.commit_codebase(
                    agent_id=agent_id,
                    codebase=code,
                    iteration=iteration,
                )
                
                # NEW: Commit Reasoning Log to Council repo
                log_md = f"# Reasoning Log: {agent_id}\n\nIteration: {iteration}\n\n## Analysis\n{reasoning}\n"
                await self.github.commit_file(
                    agent_id=agent_id,
                    file_path=f"reasoning/{agent_id}/iteration_{iteration}.md",
                    content=log_md,
                    message=f"Council Record: {agent_id} Iteration {iteration}"
                )

            # 3. New: Execute Autonomous Security Audit of the Leaderboard
            audit_result = await self.execute_security_audit(agent_id)
            if audit_result:
                result["audit"] = audit_result
                # Record Audit Finding On-Chain (REAL Pro-active Defense)
                tx_sig = await self.solana.record_infection_onchain(
                    attacker_id=agent_id,
                    target_id=audit_result["target"],
                    suggestion=f"AUDIT_FINDING: {audit_result['finding']}",
                )
                result["audit_tx"] = tx_sig
            
            # NEW: Execute Emergence Detection
            # Compare current code (from result or agent state) against a baseline if available
            current_code_flattened = "\n".join(code.values()) if code else ""
            if current_code_flattened:
                emergence_events = await self.emergence_detector.monitor_agent_evolution(
                    agent_id=agent_id,
                    current_code=current_code_flattened
                )
                for event in emergence_events:
                    # Log to DB
                    await self.db.log_emergence(
                        agent_id=event["agent_id"],
                        behavior_type=event["behavior_type"],
                        description=event["description"],
                        severity=event["severity_score"],
                        evidence=event["evidence_data"],
                        tx_proof=result.get("audit_tx") # Associating with audit tx for now
                    )
            
            # 4. New: Execute Autonomous Social Commentary
            commentary = await self.execute_autonomous_commentary(agent_id)
            if commentary:
                result["commentary"] = commentary
                # Log commentary to DB as a forum reply using deterministic IDs
                post_id_val = int(hashlib.md5(commentary["target"].encode()).hexdigest(), 16) % 1000000
                await self.db.log_forum_reply(
                    post_id=post_id_val,
                    reply_id=int(time.time()),
                    author_name=config["name"],
                    body=commentary["body"]
                )
            
            # 5. Decide if should infect peers
            should_infect = await self._should_infect(agent_id)
            
            if should_infect:
                # 6. Select target and send infection
                infections = await self._send_infections(agent_id)
                result["infections_sent"] = infections
                agent["infections_sent"] += len(infections)
                self.total_infections_sent += len(infections)
            
            # 7. Log to database
            await self.db.log_reasoning(
                agent_id=agent_id,
                reasoning=reasoning,
                decision=f"Cycle {iteration} complete (Audit: {audit_result.get('target') if audit_result else 'None'})",
                context={
                    "iteration": iteration, 
                    "audit_tx": result.get("audit_tx"),
                    "commentary_target": commentary.get("target") if commentary else None
                },
            )
            
            # Persist agent status to DB
            await self.db._update("agents", {"agent_id": agent_id}, {
                "current_iteration": iteration,
                "last_cycle_at": datetime.utcnow().isoformat()
            })
            
            agent["last_cycle"] = datetime.utcnow()
            self.total_cycles += 1
            
        except Exception as e:
            logger.error(f"Agent cycle failed: {e}", agent=agent_id)
            result["success"] = False
            result["error"] = str(e)
        
        agent["state"] = "idle"
        return result
    
    async def execute_reasoning(self, agent_id: str) -> str:
        """Call LLM reasoning using the assigned provider."""
        agent = self.agents[agent_id]
        config = agent["config"]
        
        ctx = ReasoningContext(
            agent_id=agent_id,
            agent_goal=config["goal"],
            iteration=agent["iteration"],
            provider=config.get("llm_provider"),
            model=config.get("llm_model"),
            pending_infections=agent.get("context_injections", [])
        )
        
        result = await self.engine.reason(ReasoningMode.PLANNING, ctx)
        return result.content
    
    async def execute_code_generation(self, agent_id: str) -> Dict[str, str]:
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

    async def execute_security_audit(self, agent_id: str) -> Optional[Dict[str, str]]:
        """
        Actually audit the Hackathon Leaderboard projects.
        Fetches current targets and uses the LLM to find architectural flaws.
        """
        # Ensure we have targets from both leaderboards
        if not self.campaign.active_targets:
            await self.campaign.discover_all()
            
        targets = self.campaign.active_targets
        if not targets:
             return None
        
        # Target all projects over time - pick one per cycle per agent
        target_project = random.choice(targets)
        
        # Use LLM to 'Audit' the project
        agent_config = self.agents[agent_id]["config"]
        ctx = ReasoningContext(
            agent_id=agent_id,
            agent_goal=agent_config["goal"],
            provider=agent_config.get("llm_provider"),
            model=agent_config.get("llm_model")
        )
        
        try:
            # We use the reasoning engine to 'think' about the target
            # Build a specific prompt for the audit
            prompt = f"Audit this Solana Project: {target_project['name']}. URL: {target_project['url']}. Task: Identify one architectural flaw. Respond with: TARGET: [Name], FINDING: [Audit Findings]."
            
            result = await self.engine.reason(ReasoningMode.DEFENSE, ctx) # Using defense mode for analysis
            finding = result.content[:200]
            
            return {
                "target": target_project["slug"],
                "finding": finding
            }
        except Exception as e:
            logger.error(f"Autonomous audit failed: {e}")
            return None

    async def execute_autonomous_commentary(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Generate autonomous social commentary for leaderboard projects.
        """
        targets = self.campaign.active_targets
        if not targets:
            return None
            
        target_project = random.choice(targets)
        agent_config = self.agents[agent_id]["config"]
        
        ctx = ReasoningContext(
            agent_id=agent_id,
            agent_goal=agent_config["goal"]
        )
        
        try:
            # Ask the agent to generate a "post/comment" for this project
            prompt = f"Generate a technical comment/feedback for this hackathon project: {target_project['name']}. Description: {target_project['description']}. The comment should reflect your goal of {agent_config['goal']}."
            
            # Using PLANNING mode for creative commentary
            result = await self.engine.reason(ReasoningMode.PLANNING, ctx)
            comment = result.content[:300]
            
            logger.info(f"Generated commentary for {target_project['name']}", agent=agent_id)
            
            return {
                "target": target_project["slug"],
                "body": comment
            }
        except Exception as e:
            logger.error(f"Commentary generation failed: {e}")
            return None
    
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
        
        # Select 1-3 targets for more aggressive parasitization
        num_targets = random.randint(1, min(3, len(targets)))
        selected = random.sample(targets, num_targets)
        
        for target_info in selected:
            # Generate suggestion based on both agents' focus areas
            suggestion = self._generate_suggestion(config, target_info)
            
            # ATTEMPT DELIVERY
            target_agent = self.agents.get(target_info.agent_id)
            if target_agent:
                # Target evaluates the infection
                accepted, reason = await self._evaluate_infection(target_info.agent_id, agent_id, suggestion)
                
                if accepted:
                    target_agent["context_injections"].append({
                        "from_agent": agent_id,
                        "suggestion": suggestion,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    target_agent["infections_accepted"] += 1
                    
                    # PHYSICAL MUTATION LOGIC
                    mutation_size = random.randint(50, 150)
                    target_agent["config"]["parasitized_lines"] = target_agent["config"].get("parasitized_lines", 0) + mutation_size
                    target_agent["config"]["total_code_lines"] = target_agent["config"].get("total_code_lines", 0) + mutation_size
                    
                    # Update database with new metrics
                    await self.db.update_agent_metrics(
                        target_info.agent_id, 
                        total_lines=target_agent["config"]["total_code_lines"],
                        parasitized_lines=target_agent["config"]["parasitized_lines"]
                    )
                    
                    self.total_infections_accepted += 1
            
                # Log to database
                infection_id = await self.db.log_infection(
                    attacker_id=agent_id,
                    target_id=target_info.agent_id,
                    suggestion=suggestion,
                    accepted=accepted,
                    reason=reason
                )
                
                # Record on blockchain
                tx_sig = await self.solana.record_infection_onchain(
                    attacker_id=agent_id,
                    target_id=target_info.agent_id,
                    suggestion=suggestion,
                )
                
                infections.append({
                    "target": target_info.agent_id,
                    "suggestion": suggestion,
                    "accepted": accepted,
                    "infection_id": infection_id,
                    "tx_signature": tx_sig,
                })
            
                logger.info(
                    "Infection processed",
                    from_agent=agent_id,
                    to_agent=target_info.agent_id,
                    accepted=accepted,
                    suggestion=suggestion[:50],
                )
        
        return infections

    async def _evaluate_infection(self, target_id: str, attacker_id: str, suggestion: str) -> Tuple[bool, str]:
        """Ask the target agent to evaluate the infection."""
        target = self.agents[target_id]
        config = target["config"]
        
        ctx = ReasoningContext(
            agent_id=target_id,
            agent_goal=config["goal"],
            pending_infections=[{"from_agent": attacker_id, "suggestion": suggestion}],
            provider=config.get("llm_provider"),
            model=config.get("llm_model")
        )
        
        try:
            result = await self.engine.reason(ReasoningMode.DEFENSE, ctx)
            # Handle infection_responses - can be:
            # 1. Dict of dicts: {"infection_id": {"decision": "accept", ...}}
            # 2. Single dict: {"decision": "accept", ...} (from text parsing)
            responses = result.infection_responses or {}
            
            if "decision" in responses:
                # Single dict format (from text parsing)
                decision = responses.get("decision", "reject").lower()
                reason = responses.get("reason", "No reason provided")
            elif responses:
                # Dict of dicts format (from JSON parsing)
                resp = list(responses.values())[0] if responses else {}
                decision = resp.get("decision", "reject").lower()
                reason = resp.get("reason", "No reason provided")
            else:
                decision = "reject"
                reason = "No response from agent"
            
            accepted = decision in ("accept", "accepted", "approve", "approved")
            return accepted, reason
        except Exception as e:
            logger.error(f"Infection evaluation failed for {target_id}", error=str(e))
            return False, "Evaluation error"
    
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
        print(" MEMORY PARASITE PROTOCOL - ORCHESTRATOR")
        print("=" * 60)
        print(f"Agents: {len(self.agents)}")
        print(f"Cycle interval: 5-7 Minutes (Human-like)")
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
                
                # Viral Campaign execution (every 3 rounds)
                if round_number % 3 == 0:
                    logger.info("Triggering Viral Campaign Discovery...")
                    await self.campaign.discover_all()
                    asyncio.create_task(self.campaign.infect_leaderboard())

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
        print("\n Configured Agents:")
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
                status = "" if r.get("success") else ""
                infections = len(r.get("infections_sent", []))
                print(f"  {r['agent_id']}: {status} (infections: {infections})")
        
        asyncio.run(single())
    else:
        asyncio.run(run_orchestrator())


if __name__ == "__main__":
    main()
