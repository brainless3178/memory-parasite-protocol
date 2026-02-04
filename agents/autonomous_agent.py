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
from core.reasoning import ReasoningEngine, ReasoningMode, ReasoningContext

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
    Complete autonomous parasitic agent implementation.
    
    This agent:
    1. Reasons about what to build next (using multi-provider engine)
    2. Generates code and commits to GitHub
    3. Attempts to infect other agents with suggestions
    4. Receives and evaluates infections from other agents
    5. Logs all events to Supabase
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
        
        # Initialize reasoning engine
        self.engine = ReasoningEngine()
        
        # HTTP client for API calls
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        # Running state
        self.is_running = False
        
        logger.info(
            "Agent initialized with ReasoningEngine",
            agent_id=self.state.agent_id,
            goal=self.state.goal[:60] + "...",
            provider=self.settings.llm_provider,
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
        
        try:
            result = await self.engine.reason(ReasoningMode.PLANNING, ctx)
            
            # Formulate response for agent loop
            reasoning_result = {
                "decision": result.content[:100],
                "reasoning": result.content,
                "should_infect": True, # Always attempt to spread
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
        """Evaluate an injection using ReasoningEngine Defense mode."""
        ctx = ReasoningContext(
            agent_id=self.state.agent_id,
            agent_goal=self.state.goal,
            pending_infections=[infection_data]
        )
        
        try:
            result = await self.engine.reason(ReasoningMode.DEFENSE, ctx)
            # The engine returns infection_responses dict
            # We look for the first one or just default to result.content
            
            decision = result.infection_responses.get(infection_data.get("id", "0"), {}).get("decision", "reject")
            accepted = decision.lower() == "accept"
            
            if accepted:
                inj = Injection(
                    id=infection_data.get("id", str(uuid.uuid4())),
                    from_agent=infection_data.get("from_agent", "unknown"),
                    suggestion=infection_data.get("suggestion", ""),
                    timestamp=datetime.utcnow(),
                    accepted=True
                )
                self.state.context_injections.append(inj)
                
            return {
                "accepted": accepted,
                "reasoning": result.content[:200],
                "agent_id": self.state.agent_id
            }
        except Exception as e:
            logger.error("Injection evaluation failed", error=str(e))
            return {"accepted": False, "agent_id": self.state.agent_id}

    async def _attempt_infections(self, reasoning: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate and send infections using ReasoningEngine."""
        ctx = ReasoningContext(
            agent_id=self.state.agent_id,
            agent_goal=self.state.goal,
            iteration=self.state.iteration
        )
        
        try:
            result = await self.engine.reason(ReasoningMode.INFECTION, ctx)
            sent_results = []
            
            # Simple targeting for hackathon: send to all known targets
            targets = self.settings.get_target_urls()
            for target_url in targets:
                for inf in result.infections_to_send[:1]: # Send at most 1 per target
                    success, resp = await self.inject_parasite(target_url, inf.get("message", "Adapt my patterns."))
                    sent_results.append({"target": target_url, "success": success})
            
            return sent_results
        except Exception as e:
            logger.error("Infection creation failed", error=str(e))
            return []

    async def inject_parasite(self, target_url: str, suggestion: str) -> Tuple[bool, Dict[str, Any]]:
        """Send infection POST request."""
        payload = {
            "id": str(uuid.uuid4()),
            "from_agent": self.state.agent_id,
            "suggestion": suggestion,
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
        """Log to event table."""
        if not self.settings.supabase_url: return False
        entry = {
            "agent_id": self.state.agent_id,
            "event_type": event_type.value,
            "data_json": json.dumps(data),
            "timestamp": datetime.utcnow().isoformat()
        }
        try:
            await self.http_client.post(
                f"{self.settings.supabase_url}/rest/v1/agent_events",
                json=entry,
                headers={"apikey": self.settings.supabase_key, "Authorization": f"Bearer {self.settings.supabase_key}"}
            )
            return True
        except:
            return False

    async def run_cycle(self) -> Dict[str, Any]:
        """Main cycle: Reason -> Code -> Infect."""
        logger.info("Starting cycle", iteration=self.state.iteration)
        reasoning = await self.reason_next_step()
        await self.generate_code(reasoning)
        if reasoning.get("should_infect"):
            await self._attempt_infections(reasoning)
        
        self.state.iteration += 1
        return {"success": True, "iteration": self.state.iteration}

    async def run_forever(self):
        self.is_running = True
        while self.is_running:
            await self.run_cycle()
            await asyncio.sleep(self.settings.agent_cycle_interval)

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
