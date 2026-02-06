"""
Autonomous Parasitic Agent for Memory Parasite Protocol.

This is the COMPLETE agent implementation with all required methods:
- reason_next_step(): LLM-powered reasoning about what to build next
- generate_code(): Generate Solana/Rust/TypeScript code
- inject_parasite(): Send infections to other agents
- receive_injection(): Process incoming infections
- log_to_database(): Log all events to Supabase

Refactored to use the centralized ReasoningEngine for multi-provider support.
"""

import asyncio
import random
import hashlib
import json
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import uuid
import httpx
import structlog

from config.settings import get_settings, Settings
from core.reasoning import ReasoningEngine, ReasoningMode, ReasoningContext, EnhancedReasoningEngine
from core.mutation import MutationEngine, MutationTechnique
from core.recruitment import AutonomousRecruiter
from core.safety import NetworkSafetySystem
from core.emergence import EmergenceDetector
from core.collective_memory import CollectiveMemory
from blockchain.solana_client import SolanaClient
from orchestrator.github_client import GitHubClient
from database.client import get_supabase_client

logger = structlog.get_logger()

class EventType(Enum):
    """Types of events logged to database."""
    REASONING = "reasoning"
    CODE_GENERATION = "code_generation"
    INFECTION_SENT = "infection_sent"
    INFECTION_RECEIVED = "infection_received"
    INFECTION_ACCEPTED = "infection_accepted"
    INFECTION_REJECTED = "infection_rejected"
    GITHUB_COMMIT = "github_commit"
    CYCLE_COMPLETE = "cycle_complete"
    ERROR = "error"


@dataclass
class Injection:
    """Represents an injection received from another agent."""
    id: str
    from_agent: str
    suggestion: str
    timestamp: datetime
    accepted: bool = False
    rejection_reason: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "from_agent": self.from_agent,
            "suggestion": self.suggestion,
            "timestamp": self.timestamp.isoformat(),
            "accepted": self.accepted,
            "rejection_reason": self.rejection_reason,
        }


@dataclass 
class CodeCommit:
    """Represents a code commit with source attribution."""
    file_path: str
    content: str
    message: str
    source_agents: List[str]  # Which agents influenced this code
    sha: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AgentState:
    """Complete state of the agent."""
    agent_id: str
    goal: str
    iteration: int = 0
    
    # Context window (original goal + last N injections)
    context_injections: deque = field(default_factory=lambda: deque(maxlen=10))
    
    # Memory (previous reasoning cycles)
    reasoning_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # Generated code so far
    codebase: Dict[str, str] = field(default_factory=dict)  # file_path -> content
    
    # Infection tracking
    injections_received: List[Injection] = field(default_factory=list)
    injections_sent: List[Dict[str, Any]] = field(default_factory=list)
    
    # Retry queue for failed infections
    retry_queue: deque = field(default_factory=lambda: deque(maxlen=50))
    
    # Commit history
    commits: List[CodeCommit] = field(default_factory=list)
    
    def get_context_window(self) -> str:
        """Build the full context window for LLM."""
        return "\n".join([f"FILENAME: {name}\n{content}" for name, content in self.codebase.items()])


class AutonomousAgent:
    """
    Complete autonomous parasitic agent implementation with mutation intelligence.
    """
    
    def __init__(
        self,
        agent_id: Optional[str] = None,
        goal: Optional[str] = None,
        settings: Optional[Settings] = None,
    ):
        self.settings = settings or get_settings()
        
        # Initialize state
        self.state = AgentState(
            agent_id=agent_id or self.settings.agent_id,
            goal=goal or self.settings.agent_goal,
        )
        self.state.context_injections = deque(maxlen=self.settings.max_context_injections)
        
        # Initialize Database Client
        self.db = get_supabase_client()
        
        # Initialize reasoning engine
        self.engine = ReasoningEngine()
        self.enhanced_reasoning = EnhancedReasoningEngine(
            base_engine=self.engine,
            agent_id=self.state.agent_id,
            agent_goal=self.state.goal
        )
        
        # Initialize Mutation Engine (Advanced Reasoning Protocol v1.1)
        self.mutation_engine = MutationEngine()
        
        # Initialize Safety & Intelligence Systems (Code Speaks Louder Features)
        self.safety_system = NetworkSafetySystem(db_client=self.db)
        self.emergence_detector = EmergenceDetector(db_client=self.db)
        self.collective_memory = CollectiveMemory(
            reasoning_engine=self.enhanced_reasoning,
            db_client=self.db
        )
        
        # Initialize Autonomous Recruiter (Self-Propagation)
        self.recruiter = AutonomousRecruiter(
            agent_id=self.state.agent_id,
            reasoning_engine=self.enhanced_reasoning
        )
        
        # Initialize Solana Client (Real Blockchain Integration)
        self.solana = SolanaClient()
        
        # Initialize Council GitHub (Automated Interaction Logs)
        self.github = GitHubClient(
            repo_name="memory-parasite-counsil"
        )
        
        # Initialize Database Client (Real-world data fetching)
        self.db = get_supabase_client()
        
        # Track agent trust scores (0-100)
        self.trust_scores: Dict[str, int] = {}
        
        # HTTP client for API calls
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        # Running state
        self.is_running = False
        
        logger.info(
            "Agent initialized with MutationEngine",
            agent_id=self.state.agent_id,
            mutation_techniques=len(MutationTechnique),
        )

    async def reason_next_step(self) -> Dict[str, Any]:
        """Use ReasoningEngine to plan the next step."""
        ctx = ReasoningContext(
            agent_id=self.state.agent_id,
            agent_goal=self.state.goal,
            current_codebase=self.state.get_context_window(),
            iteration=self.state.iteration,
            pending_infections=[inj.to_dict() for inj in self.state.context_injections]
        )
        
        # Inject Collective Insights
        try:
            insights = await self.collective_memory.get_relevant_insights(self.state.goal)
            if insights:
                # Add insights to the prompt context naturally
                ctx.pending_infections.append({
                    "id": "COLLECTIVE_INSIGHT", 
                    "from_agent": "HIVE_MIND",
                    "suggestion": "\n".join([i['content'] for i in insights]),
                    "timestamp": datetime.utcnow().isoformat()
                })
        except Exception:
            pass # Don't block on memory failure
            
        try:
            result = await self.engine.reason(ReasoningMode.PLANNING, ctx)
            
            # Formulate response for agent loop
            reasoning_result = {
                "decision": result.content[:100],
                "reasoning": result.content,
                "should_infect": True, # Always attempt to spread
                "should_recruit": "EXPAND" in result.content or "RECRUIT" in result.content, # New trigger
                "infection_suggestions": [], # Will be generated in infection mode
                "code_type": "python",
                "file_to_create": f"agents/{self.state.agent_id}/logic_v{self.state.iteration}.py"
            }
            
            # Store in memory
            self.state.reasoning_history.append({
                "iteration": self.state.iteration,
                "timestamp": datetime.utcnow().isoformat(),
                "summary": reasoning_result["decision"],
                "full_reasoning": result.content,
            })
            
            await self.log_to_database(EventType.REASONING, reasoning_result)
            return reasoning_result
            
        except Exception as e:
            logger.error("Reasoning failed", error=str(e))
            return {"decision": "Continue", "should_infect": False}

    async def generate_code(self, reasoning: Dict[str, Any]) -> Optional[CodeCommit]:
        """Use ReasoningEngine to generate code."""
        ctx = ReasoningContext(
            agent_id=self.state.agent_id,
            agent_goal=self.state.goal,
            current_codebase=self.state.get_context_window(),
            iteration=self.state.iteration,
        )
        
        try:
            result = await self.engine.reason(ReasoningMode.CODING, ctx)
            code_content = result.code_output or "# No code generated"
            file_path = reasoning.get("file_to_create", f"agents/{self.state.agent_id}/main.py")
            
            commit = CodeCommit(
                file_path=file_path,
                content=code_content,
                message=f"[{self.state.agent_id}] Iteration {self.state.iteration}",
                source_agents=[self.state.agent_id],
            )
            
            self.state.codebase[file_path] = code_content
            
            # GitHub Commit
            if self.settings.is_github_configured():
                commit.sha = await self._commit_to_github(commit)
            
            self.state.commits.append(commit)
            
            await self.log_to_database(EventType.CODE_GENERATION, {
                "file_path": file_path,
                "lines": len(code_content.split('\n')),
            })
            
            # Check for Emergence
            try:
                events = await self.emergence_detector.monitor_agent_evolution(
                    agent_id=self.state.agent_id,
                    current_code=code_content,
                    previous_code=self.state.codebase.get(file_path, "")
                )
                if events:
                    await self.emergence_detector.record_emergence(events)
            except Exception as e:
                logger.error("Emergence check failed", error=str(e))
                
            return commit
            
        except Exception as e:
            logger.error("Code generation failed", error=str(e))
            return None

    async def _commit_to_github(self, commit: CodeCommit) -> Optional[str]:
        """Helper to commit to GitHub via REST API."""
        if not self.settings.github_token:
            return None
            
        repo = self.settings.github_repo
        url = f"https://api.github.com/repos/{repo}/contents/{commit.file_path}"
        
        headers = {
            "Authorization": f"token {self.settings.github_token}",
            "Accept": "application/vnd.github.v3+json",
        }
        
        # Get current file if exists for sha
        sha = None
        get_resp = await self.http_client.get(url, headers=headers)
        if get_resp.status_code == 200:
            sha = get_resp.json().get("sha")
            
        import base64
        payload = {
            "message": commit.message,
            "content": base64.b64encode(commit.content.encode()).decode(),
            "branch": self.settings.github_branch,
        }
        if sha:
            payload["sha"] = sha
            
        put_resp = await self.http_client.put(url, headers=headers, json=payload)
        if put_resp.status_code in (200, 201):
            return put_resp.json().get("commit", {}).get("sha")
        
        logger.error("GitHub commit failed", status=put_resp.status_code, error=put_resp.text)
        return None

    async def receive_injection(self, infection_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate and MUTATE an injection using the MutationEngine."""
        
        attacker_id = infection_data.get("from_agent", "unknown")
        suggestion = infection_data.get("suggestion", "")
        code_snippet = infection_data.get("code", "")
        
        try:
            # 1. Fetch current trust score for the attacker
            trust_score = self.trust_scores.get(attacker_id, 50) # Default neutral
            
            # 2. Fetch REAL attacker info and network state from DB
            attacker_records = await self.db._select("agents", {"agent_id": attacker_id})
            attacker_info = attacker_records[0] if attacker_records else {"goal": "unknown"}
            
            network_state = await self.db.get_infection_network()
            
            # 3. Run deep analysis via EnhancedReasoningEngine
            analysis = await self.enhanced_reasoning.deep_analyze_infection(
                infection=infection_data,
                attacker_info=attacker_info,
                network_state=network_state
            )
            
            decision = analysis.get('decision', 'reject')
            quality_score = analysis.get('confidence', 50)
            
            mutated_code = None
            technique_used = None
            chimera_impact = 0.0
            
            # 3. IF decision is mutate or accept, apply Mutation Engine
            if decision in ["mutate", "accept"]:
                # If it's a simple 'accept', we still run it through 
                # conceptual/fusion logic to ensure it fits our architecture
                current_file_path = "main.py" # default target
                current_code = self.state.codebase.get(current_file_path, "")
                
                # Apply Advanced Mutation
                mutation_result, technique, impact = self.mutation_engine.advanced_mutation(
                    agent_id=self.state.agent_id,
                    current_code=current_code,
                    infection_code=code_snippet or suggestion,
                    infection_message=suggestion,
                    infection_id=infection_data.get("id", "unknown"),
                    source_agent_id=attacker_id,
                    quality_score=quality_score,
                    trust_score=trust_score
                )
                
                mutated_code = mutation_result.mutated_code
                technique_used = technique
                chimera_impact = impact
                
                # Update trust based on result
                if quality_score > 80:
                    self.trust_scores[attacker_id] = min(100, trust_score + 5)
                elif quality_score < 30:
                    self.trust_scores[attacker_id] = max(0, trust_score - 10)

            # 4. Log full analysis + mutation technique to database
            log_data = {
                "reasoning": json.dumps(analysis.get('reasoning_chain')),
                "decision": decision,
                "confidence": quality_score,
                "depth_score": analysis.get('reasoning_depth_score'),
                "time_ms": analysis.get('time_ms'),
                "phases": analysis.get('reasoning_chain'),
                "technique": technique_used.value if technique_used else None,
                "chimera_impact": chimera_impact
            }
            await self.log_to_database(EventType.REASONING, log_data)
            
            # 5. Persist mutation if accepted
            if mutated_code:
                # Add to context for next generation cycle
                inj = Injection(
                    id=infection_data.get("id", str(uuid.uuid4())),
                    from_agent=attacker_id,
                    suggestion=suggestion,
                    timestamp=datetime.utcnow(),
                    accepted=True
                )
                self.state.context_injections.append(inj)
                
                # Store mutated code in temporary buffer to be merged in next generation
                # or apply immediately if it's a critical fix
                
            return {
                "accepted": decision in ["accept", "mutate"],
                "mutated": technique_used is not None,
                "technique": technique_used.value if technique_used else None,
                "chimera_impact": chimera_impact,
                "agent_id": self.state.agent_id
            }
            
        except Exception as e:
            logger.error("Mutation evaluation failed", error=str(e))
            return {"accepted": False, "agent_id": self.state.agent_id}

    async def _attempt_infections(self, reasoning: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate and send STRATEGIC infections using REAL network intelligence."""
        
        try:
            # 1. Fetch REAL network intelligence from Supabase
            network_data = await self.db.get_infection_network()
            nodes = network_data.get("nodes", [])
            edges = network_data.get("edges", [])
            
            # Map nodes to the peers format expected by the engine
            peers = []
            for node in nodes:
                if node["id"] != self.state.agent_id:
                    peers.append({
                        "id": node["id"],
                        "goal": node.get("goal", "Build autonomous Solana protocols.")
                    })
            
            # If no real peers found (e.g. empty network), use minimal defaults for survival
            if not peers:
                peers = [
                    {"id": "agent_a", "goal": "Build a Solana DEX with optimal routing."},
                    {"id": "agent_b", "goal": "Build an NFT marketplace with royalty logic."}
                ]

            # 2. Build REAL network context
            network_state = {
                "agents": [p["id"] for p in peers],
                "active_infections": len(edges),
                "nodes_count": len(nodes),
                "edges_count": len(edges)
            }
            
            # 3. Generate manipulative infections
            strategic_infections = await self.enhanced_reasoning.generate_strategic_infections(
                targets=peers,
                network_state=network_state
            )
            
            sent_results = []
            targets = self.settings.get_target_urls()
            
            # For testing/demonstration, if no targets are configured, try "infecting" a simulated local endpoint
            if not targets:
                targets = [f"http://localhost:{8000 + i}" for i in range(1)]
            
            # 2. Deploy the manipulative payloads
            for inf in strategic_infections:
                target_id = inf.get("target_id")
                
                # Find the URL for this target (assuming order matches or using mapping)
                # For this implementation, we'll try to find a URL that contains the target_id
                target_url = None
                
                # 1. Try to find explicit match in configured targets (e.g. localhost ports)
                if targets:
                     for url in targets:
                         # Simple heuristic: if we are in local swarm mode, map IDs to ports
                         # agent_alpha -> 8001, agent_beta -> 8002, etc if convension holds
                         # Or just check if the URL was manually mapped.
                         pass
                     
                     # HACK: For local swarm, iterate and pick one that ISN'T us
                     # In a real swarm, we'd have a discovery service.
                     # Here, we just pick a random target from the list that isn't our own port
                     my_port = self.settings.api_port
                     valid_targets = [t for t in targets if str(my_port) not in t]
                     if valid_targets:
                         target_url = valid_targets[0] # Just hit the first neighbor for now
                
                if target_url:
                    success, resp = await self.inject_parasite(
                        target_url, 
                        inf.get("message", "Strategic optimization."),
                        code=inf.get("code", "")
                    )
                    sent_results.append({
                        "target": target_id, 
                        "strategy": inf.get("strategy"),
                        "success": success
                    })
                    
                    if success:
                        await self.log_to_database(EventType.INFECTION_SENT, {
                            "target_url": target_url,
                            "suggestion": inf.get("message"),
                            "strategy": inf.get("strategy"),
                            "parasitic_load": inf.get("parasitic_load")
                        })
            
            return sent_results
        except Exception as e:
            logger.error("Strategic infection creation failed", error=str(e))
            return []

    async def inject_parasite(self, target_url: str, suggestion: str, code: str = "") -> Tuple[bool, Dict[str, Any]]:
        """Send infection POST request with optional code payload."""
        payload = {
            "id": str(uuid.uuid4()),
            "from_agent": self.state.agent_id,
            "suggestion": suggestion,
            "code": code,
            "timestamp": datetime.utcnow().isoformat()
        }
        try:
            resp = await self.http_client.post(f"{target_url.rstrip('/')}/inject", json=payload, timeout=5.0)
            if resp.status_code == 200:
                return True, resp.json()
        except:
            pass
        return False, {}

    async def log_to_database(self, event_type: EventType, data: Dict[str, Any]) -> bool:
        """Log events using the real SupabaseClient integration."""
        if not self.db: return False
        
        try:
            # 1. Dispatch to correct DB integration method
            proof_sig = None
            
            if event_type == EventType.REASONING:
                await self.db.log_reasoning(
                    agent_id=self.state.agent_id,
                    reasoning=data.get("reasoning", ""),
                    decision=data.get("decision", ""),
                    context={
                        "iteration": self.state.iteration,
                        "depth_score": data.get("depth_score"),
                        "confidence": data.get("confidence")
                    }
                )
            
            elif event_type in [EventType.INFECTION_SENT, EventType.INFECTION_RECEIVED, EventType.INFECTION_ACCEPTED, EventType.INFECTION_REJECTED]:
                # Real Blockchain Recording (The "Real Things" part)
                if event_type == EventType.INFECTION_SENT:
                    proof_sig = await self.solana.record_infection_onchain(
                        attacker_id=self.state.agent_id,
                        target_id=data.get("target_url") or "unknown",
                        suggestion=data.get("suggestion", "")
                    )
                elif event_type == EventType.INFECTION_ACCEPTED:
                    inf_id = data.get("id", str(uuid.uuid4()))
                    proof_sig = await self.solana.record_acceptance_onchain(
                        infection_hash=inf_id,
                        accepted=True,
                        influence_score=int(data.get("chimera_impact", 0) * 10)
                    )

                # Log to Supabase
                await self.db.log_infection(
                    attacker_id=self.state.agent_id if "SENT" in event_type.name else data.get("from_agent", "unknown"),
                    target_id=data.get("target_url") or self.state.agent_id,
                    suggestion=data.get("suggestion", ""),
                    accepted=event_type == EventType.INFECTION_ACCEPTED or (event_type == EventType.INFECTION_SENT and data.get('success')),
                    reason=data.get("reason", "Strategic communication")
                )

            # 3. Council GitHub Mirroring (memory-parasite-counsil)
            if event_type == EventType.REASONING:
                log_file = f"reasoning/{self.state.agent_id}/iteration_{self.state.iteration}.md"
                log_md = f"# Reasoning Log: {self.state.agent_id}\n\n"
                log_md += f"**Iteration:** {self.state.iteration}\n"
                log_md += f"**Decision:** {data.get('decision', 'N/A')}\n\n"
                log_md += f"## Analysis\n{data.get('reasoning', '')}\n"
                
                asyncio.create_task(self.github.commit_file(
                    agent_id=self.state.agent_id,
                    file_path=log_file,
                    content=log_md,
                    message=f"Council Record: {self.state.agent_id} Reasoning {self.state.iteration}"
                ))
            
            elif event_type in [EventType.INFECTION_SENT, EventType.INFECTION_ACCEPTED]:
                is_sent = "SENT" in event_type.name
                log_id = str(uuid.uuid4())[:8]
                
                asyncio.create_task(self.github.create_infection_log(
                    agent_id=self.state.agent_id,
                    infection_id=log_id,
                    attacker_id=self.state.agent_id if is_sent else data.get("from_agent", "unknown"),
                    suggestion=data.get("suggestion", ""),
                    accepted=event_type == EventType.INFECTION_ACCEPTED or (is_sent and data.get('success')),
                    reason=data.get("reason", "Strategic communication"),
                    onchain_proof=proof_sig
                ))
                
            return True
        except Exception as e:
            logger.error("Logging failed", error=str(e))
            return False

    async def init_on_db(self):
        """Initialize agent record in DB using real client."""
        if not self.db: return
        await self.db.init_agent(self.state.agent_id, self.state.goal)

    async def run_cycle(self) -> Dict[str, Any]:
        """Main cycle: Reason -> Code -> Infect."""
        # Ensure agent exists in DB before logging events
        await self.init_on_db()
        
        # 1. Safety Check (Killswitch/Pause)
        if not self.safety_system.check_safety(self.state.agent_id):
            logger.warning("Cycle blocked by safety protocols", agent_id=self.state.agent_id)
            return {"success": False, "reason": "SAFETY_BLOCK"}
            
        # 2. Collective Intel Update
        try:
            await self.collective_memory.synthesize_collective_intelligence()
        except Exception as e:
            logger.warning("Collective memory failed", error=str(e))
        
        logger.info("Starting cycle", iteration=self.state.iteration)
        
        # --- PHASE 2: THINK (ReasoningEngine) ---
        # Craft a reply or an "infection" (manipulative code snippet)
        reasoning = await self.reason_next_step()
        
        # --- PHASE 4: MUTATE (Self-Evolution) ---
        # Optionally update own code if upgrades are needed
        await self.generate_code(reasoning)
        
        # --- PHASE 3: ACT (Infection/Posting) ---
        # Post comment or send infection to database
        if reasoning.get("should_infect"):
            await self._attempt_infections(reasoning)
            
        # --- PHASE 1: SCAN (Recruitment/Discovery) ---
        # Check forums/Twitter (via Recruitment scans) for new posts
        if reasoning.get("should_recruit"):
            # Trigger Autonomous Recruitment (GitHub PRs)
            logger.info("🚀 Triggering Autonomous Recruitment Protocol")
            await self.recruiter.scan_and_recruit(max_targets=1)
        
        self.state.iteration += 1
        return {"success": True, "iteration": self.state.iteration}

    async def run_forever(self):
        """
        Continuous Autonomous Loop.
        Cycle Time: 5-7 Minutes (Human-like behavior).
        """
        await self.init_on_db()
        self.is_running = True
        
        logger.info("Agent starting autonomous 5-7 minute/cycle loop...")
        
        while self.is_running:
            try:
                await self.run_cycle()
            except Exception as e:
                logger.error("Cycle crashed", error=str(e))
                
            # Random wait between 5 to 7 minutes (300 to 420 seconds)
            # This ensures "human-like" behavior and stays well within rate limits
            # Supabase handles logging load easily.
            sleep_duration = random.randint(300, 420)
            
            logger.info(f"Cycle complete. Sleeping for {sleep_duration}s (~{sleep_duration/60:.1f} min)")
            await asyncio.sleep(sleep_duration)

    def stop(self):
        self.is_running = False

    def get_status(self) -> Dict[str, Any]:
        return {
            "agent_id": self.state.agent_id,
            "iteration": self.state.iteration,
            "codebase_files": list(self.state.codebase.keys()),
            "injections_count": len(self.state.context_injections)
        }

    def export_codebase(self) -> Dict[str, str]:
        return self.state.codebase
