"""
Base agent class for Memory Parasite Protocol.

This module defines the core agent interface that all specialized
agents (DEX, NFT, DeFi, etc.) inherit from.
"""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, Any, List
import uuid
import structlog

from core.infection import (
    Infection,
    InfectionType,
    InfectionResult,
    InfectionPayload,
    InfectionManager,
)
from core.reasoning import ReasoningEngine, ReasoningMode, ReasoningContext, ReasoningResult
from core.mutation import MutationEngine, CodeMutation

logger = structlog.get_logger()


class AgentState(Enum):
    """Current state of an agent."""
    
    IDLE = "idle"
    REASONING = "reasoning"
    CODING = "coding"
    INFECTING = "infecting"
    DEFENDING = "defending"
    MUTATING = "mutating"
    ERROR = "error"


@dataclass
class AgentMemory:
    """Agent's memory of past interactions and code."""
    
    codebase: str = ""  # Current generated code
    infection_attempts_made: List[str] = field(default_factory=list)  # IDs
    infections_received: List[str] = field(default_factory=list)  # IDs
    infections_accepted: List[str] = field(default_factory=list)  # IDs
    reasoning_history: List[Dict[str, Any]] = field(default_factory=list)
    iteration: int = 0


@dataclass
class AgentConfig:
    """Configuration for an agent."""
    
    agent_id: str
    agent_name: str
    goal: str
    description: str = ""
    
    # Personality traits affecting infection behavior
    aggressiveness: float = 0.5  # 0-1, how likely to attempt infections
    openness: float = 0.5  # 0-1, how likely to accept infections
    
    # Target preferences
    preferred_targets: List[str] = field(default_factory=list)
    avoided_targets: List[str] = field(default_factory=list)


class BaseAgent(ABC):
    """
    Base class for all agents in the Memory Parasite Protocol.
    
    Each agent:
    - Has a unique goal (build DEX, NFT marketplace, etc.)
    - Runs reasoning cycles to plan and code
    - Can attempt to infect other agents
    - Can accept/reject/mutate incoming infections
    - Logs all actions to database and blockchain
    """
    
    def __init__(
        self,
        config: AgentConfig,
        reasoning_engine: Optional[ReasoningEngine] = None,
        infection_manager: Optional[InfectionManager] = None,
        mutation_engine: Optional[MutationEngine] = None,
    ):
        self.config = config
        self.state = AgentState.IDLE
        self.memory = AgentMemory()
        
        # Engines
        self.reasoning_engine = reasoning_engine or ReasoningEngine()
        self.infection_manager = infection_manager or InfectionManager()
        self.mutation_engine = mutation_engine or MutationEngine()
        
        # Pending infections to process
        self.pending_infections: List[Infection] = []
        
        # Timestamps
        self.created_at = datetime.now(timezone.utc)
        self.last_cycle_at: Optional[datetime] = None
        
        logger.info(
            "Agent initialized",
            agent_id=self.config.agent_id,
            goal=self.config.goal,
        )
    
    @property
    def agent_id(self) -> str:
        return self.config.agent_id
    
    @property
    def goal(self) -> str:
        return self.config.goal
    
    @abstractmethod
    def get_initial_code(self) -> str:
        """Get the initial code template for this agent type."""
        pass
    
    @abstractmethod
    def get_infection_targets(self, available_agents: List[str]) -> List[str]:
        """Determine which agents to target for infection."""
        pass
    
    def get_reasoning_context(self) -> ReasoningContext:
        """Build reasoning context from current state."""
        return ReasoningContext(
            agent_id=self.agent_id,
            agent_goal=self.goal,
            current_codebase=self.memory.codebase,
            infection_history=[
                {"id": inf_id, "type": "sent"} 
                for inf_id in self.memory.infection_attempts_made[-10:]  # Last 10
            ],
            pending_infections=[
                inf.to_dict() for inf in self.pending_infections
            ],
            iteration=self.memory.iteration,
        )
    
    async def run_cycle(self, available_agents: List["BaseAgent"]) -> Dict[str, Any]:
        """
        Run one complete agent cycle.
        
        Each cycle:
        1. Plan next steps
        2. Generate code
        3. Evaluate pending infections
        4. Create and send new infections
        5. Reflect on progress
        """
        cycle_results = {
            "agent_id": self.agent_id,
            "iteration": self.memory.iteration,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "phases": {},
        }
        
        try:
            # Phase 1: Planning
            self.state = AgentState.REASONING
            planning_result = await self._run_planning()
            cycle_results["phases"]["planning"] = planning_result
            
            # Phase 2: Coding
            self.state = AgentState.CODING
            coding_result = await self._run_coding()
            cycle_results["phases"]["coding"] = coding_result
            
            # Phase 3: Defense (evaluate incoming infections)
            if self.pending_infections:
                self.state = AgentState.DEFENDING
                defense_result = await self._run_defense()
                cycle_results["phases"]["defense"] = defense_result
            
            # Phase 4: Infection (create and send)
            self.state = AgentState.INFECTING
            infection_result = await self._run_infection(available_agents)
            cycle_results["phases"]["infection"] = infection_result
            
            # Update state
            self.memory.iteration += 1
            self.last_cycle_at = datetime.now(timezone.utc)
            self.state = AgentState.IDLE
            
            cycle_results["completed_at"] = datetime.now(timezone.utc).isoformat()
            cycle_results["success"] = True
            
        except Exception as e:
            self.state = AgentState.ERROR
            logger.error("Cycle failed", agent_id=self.agent_id, error=str(e))
            cycle_results["error"] = str(e)
            cycle_results["success"] = False
        
        return cycle_results
    
    def run_cycle_sync(self, available_agents: List["BaseAgent"]) -> Dict[str, Any]:
        """Synchronous version of run_cycle."""
        return asyncio.run(self.run_cycle(available_agents))
    
    async def _run_planning(self) -> Dict[str, Any]:
        """Run planning phase."""
        context = self.get_reasoning_context()
        result = await self.reasoning_engine.reason(ReasoningMode.PLANNING, context)
        
        self.memory.reasoning_history.append({
            "mode": "planning",
            "iteration": self.memory.iteration,
            "content": result.content[:500],  # Truncate for storage
        })
        
        return {
            "mode": "planning",
            "summary": result.content[:200],
        }
    
    async def _run_coding(self) -> Dict[str, Any]:
        """Run coding phase."""
        context = self.get_reasoning_context()
        
        # Initialize codebase if first iteration
        if not self.memory.codebase:
            self.memory.codebase = self.get_initial_code()
        
        result = await self.reasoning_engine.reason(ReasoningMode.CODING, context)
        
        if result.code_output:
            # Append new code to existing codebase
            self.memory.codebase += f"\n\n# Iteration {self.memory.iteration}\n"
            self.memory.codebase += result.code_output
        
        return {
            "mode": "coding",
            "code_generated": bool(result.code_output),
            "code_length": len(result.code_output) if result.code_output else 0,
        }
    
    async def _run_defense(self) -> Dict[str, Any]:
        """Evaluate and respond to pending infections."""
        context = self.get_reasoning_context()
        result = await self.reasoning_engine.reason(ReasoningMode.DEFENSE, context)
        
        processed = []
        for infection in self.pending_infections:
            response = result.infection_responses.get(infection.id, {})
            decision = response.get("decision", "reject")
            reason = response.get("reason", "No explicit decision made")
            
            if decision == "accept":
                await self._accept_infection(infection)
                infection.accept(reason)
            elif decision == "mutate":
                mutations = response.get("mutations", {})
                await self._mutate_infection(infection, mutations)
                infection.mutate(mutations, reason)
            else:
                infection.reject(reason)
            
            processed.append({
                "infection_id": infection.id,
                "decision": decision,
                "reason": reason[:100],
            })
        
        self.pending_infections.clear()
        
        return {
            "mode": "defense",
            "infections_processed": len(processed),
            "decisions": processed,
        }
    
    async def _accept_infection(self, infection: Infection) -> None:
        """Accept an infection and apply its mutation."""
        self.state = AgentState.MUTATING
        
        mutation = self.mutation_engine.apply_mutation(
            agent_id=self.agent_id,
            current_code=self.memory.codebase,
            infection_code=infection.payload.code_snippet,
            infection_message=infection.payload.message,
            infection_id=infection.id,
            source_agent_id=infection.source_agent_id,
        )
        
        self.memory.codebase = mutation.mutated_code
        self.memory.infections_accepted.append(infection.id)
        
        logger.info(
            "Infection accepted",
            agent_id=self.agent_id,
            infection_id=infection.id,
            source=infection.source_agent_id,
        )
    
    async def _mutate_infection(
        self, infection: Infection, mutations: Dict[str, Any]
    ) -> None:
        """Partially accept an infection with modifications."""
        self.state = AgentState.MUTATING
        
        # Apply modified version
        modified_message = f"{infection.payload.message} [MUTATED: {mutations}]"
        
        mutation = self.mutation_engine.apply_mutation(
            agent_id=self.agent_id,
            current_code=self.memory.codebase,
            infection_code=infection.payload.code_snippet,
            infection_message=modified_message,
            infection_id=infection.id,
            source_agent_id=infection.source_agent_id,
            mutation_type="partial_adoption",
        )
        
        self.memory.codebase = mutation.mutated_code
        self.memory.infections_accepted.append(infection.id)
    
    async def _run_infection(
        self, available_agents: List["BaseAgent"]
    ) -> Dict[str, Any]:
        """Create and send infections to other agents."""
        import random
        
        # Skip if not aggressive enough
        if random.random() > self.config.aggressiveness:
            return {"mode": "infection", "skipped": True, "reason": "not aggressive enough"}
        
        context = self.get_reasoning_context()
        result = await self.reasoning_engine.reason(ReasoningMode.INFECTION, context)
        
        infections_sent = []
        
        for inf_data in result.infections_to_send:
            target_id = inf_data.get("target_agent_id")
            
            # Find target agent
            target_agent = next(
                (a for a in available_agents if a.agent_id == target_id),
                None
            )
            
            if not target_agent:
                # Pick random target if specified one not found
                other_agents = [a for a in available_agents if a.agent_id != self.agent_id]
                if other_agents:
                    target_agent = random.choice(other_agents)
            
            if target_agent:
                infection = self.infection_manager.create_infection(
                    source_agent_id=self.agent_id,
                    target_agent_id=target_agent.agent_id,
                    message=inf_data.get("message", "Consider this suggestion"),
                    infection_type=InfectionType(
                        inf_data.get("infection_type", "suggestion")
                    ),
                    code_snippet=inf_data.get("code_snippet"),
                    priority=inf_data.get("priority", 5),
                )
                
                # Deliver to target
                target_agent.receive_infection(infection)
                self.memory.infection_attempts_made.append(infection.id)
                
                infections_sent.append({
                    "infection_id": infection.id,
                    "target": target_agent.agent_id,
                    "type": infection.infection_type.value,
                })
                
                logger.info(
                    "Infection sent",
                    source=self.agent_id,
                    target=target_agent.agent_id,
                    infection_id=infection.id,
                )
        
        return {
            "mode": "infection",
            "infections_created": len(result.infections_to_send),
            "infections_sent": len(infections_sent),
            "details": infections_sent,
        }
    
    def receive_infection(self, infection: Infection) -> None:
        """Receive an incoming infection for processing."""
        self.pending_infections.append(infection)
        self.memory.infections_received.append(infection.id)
        
        logger.info(
            "Infection received",
            agent_id=self.agent_id,
            infection_id=infection.id,
            source=infection.source_agent_id,
        )
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status."""
        chimera_stats = self.mutation_engine.get_agent_chimera_stats(self.agent_id)
        
        return {
            "agent_id": self.agent_id,
            "name": self.config.agent_name,
            "goal": self.config.goal,
            "state": self.state.value,
            "iteration": self.memory.iteration,
            "codebase_size": len(self.memory.codebase),
            "pending_infections": len(self.pending_infections),
            "infections_sent": len(self.memory.infection_attempts_made),
            "infections_received": len(self.memory.infections_received),
            "infections_accepted": len(self.memory.infections_accepted),
            "chimera_stats": chimera_stats,
            "last_cycle_at": self.last_cycle_at.isoformat() if self.last_cycle_at else None,
        }
    
    def export_codebase(self) -> str:
        """Export the agent's current codebase."""
        header = f'''"""
Generated by: {self.config.agent_name} ({self.agent_id})
Goal: {self.config.goal}
Iteration: {self.memory.iteration}
Infections Accepted: {len(self.memory.infections_accepted)}
Generated at: {datetime.now(timezone.utc).isoformat()}
"""

'''
        return header + self.memory.codebase
