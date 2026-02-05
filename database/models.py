"""
Pydantic models for database records.

Uses UUID v7 for time-ordered unique identifiers.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict
import struct
import os
import time


def uuid_v7() -> str:
    """
    Generate a UUID v7 (time-ordered UUID).
    
    UUID v7 structure:
    - First 48 bits: Unix timestamp in milliseconds
    - Next 4 bits: Version (7)
    - Next 12 bits: Random
    - Next 2 bits: Variant (10)
    - Last 62 bits: Random
    """
    # Get current timestamp in milliseconds
    timestamp_ms = int(time.time() * 1000)
    
    # Convert to bytes (6 bytes for 48 bits of timestamp)
    timestamp_bytes = struct.pack('>Q', timestamp_ms)[2:]  # Take last 6 bytes
    
    # Generate random bytes
    random_bytes = os.urandom(10)
    
    # Combine timestamp and random
    uuid_bytes = bytearray(timestamp_bytes + random_bytes)
    
    # Set version 7 (0111 in bits 48-51, which is byte 6, high nibble)
    uuid_bytes[6] = (uuid_bytes[6] & 0x0F) | 0x70
    
    # Set variant (10xx in bits 64-67, which is byte 8, high 2 bits)
    uuid_bytes[8] = (uuid_bytes[8] & 0x3F) | 0x80
    
    # Format as UUID string
    hex_str = uuid_bytes.hex()
    return f"{hex_str[:8]}-{hex_str[8:12]}-{hex_str[12:16]}-{hex_str[16:20]}-{hex_str[20:]}"


class InfectionType(str, Enum):
    """Types of infections."""
    SUGGESTION = "suggestion"
    MANDATE = "mandate"
    MERGE = "merge"
    OVERRIDE = "override"
    SYMBIOSIS = "symbiosis"


class EventType(str, Enum):
    """Types of events."""
    REASONING = "reasoning"
    CODE_GENERATION = "code_generation"
    INFECTION_SENT = "infection_sent"
    INFECTION_RECEIVED = "infection_received"
    INFECTION_ACCEPTED = "infection_accepted"
    INFECTION_REJECTED = "infection_rejected"
    GITHUB_COMMIT = "github_commit"
    CYCLE_COMPLETE = "cycle_complete"
    ERROR = "error"
    STARTUP = "startup"
    SHUTDOWN = "shutdown"


class AgentRecord(BaseModel):
    """Database record for an agent."""
    
    id: Optional[str] = Field(default_factory=uuid_v7)
    agent_id: str
    goal: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    context_window: Dict[str, Any] = Field(
        default_factory=lambda: {"injections": [], "reasoning_history": []}
    )
    
    # Code metrics
    total_code_lines: int = 0
    original_lines: int = 0        # Lines written without injections
    parasitized_lines: int = 0     # Lines influenced by injections
    
    # Metadata
    is_active: bool = True
    last_cycle_at: Optional[datetime] = None
    current_iteration: int = 0
    
    model_config = ConfigDict(use_enum_values=True)
    
    def to_insert_dict(self) -> Dict[str, Any]:
        """Convert to dict for Supabase insert."""
        data = {
            "agent_id": self.agent_id,
            "goal": self.goal,
            "context_window": self.context_window,
            "total_code_lines": self.total_code_lines,
            "original_lines": self.original_lines,
            "parasitized_lines": self.parasitized_lines,
            "is_active": self.is_active,
            "current_iteration": self.current_iteration,
        }
        if self.last_cycle_at:
            data["last_cycle_at"] = self.last_cycle_at.isoformat()
        return data


class InfectionRecord(BaseModel):
    """Database record for an infection attempt."""
    
    id: Optional[str] = Field(default_factory=uuid_v7)
    attacker_id: str          # Agent sending the infection
    target_id: str            # Agent receiving the infection
    suggestion: str           # The parasitic suggestion
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    accepted: bool = False
    rejection_reason: Optional[str] = None
    
    # Influence tracking
    influence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    
    # Blockchain proof
    infection_hash: Optional[str] = None
    solana_tx_hash: Optional[str] = None
    
    # Context at time of infection
    attacker_context: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = ConfigDict(use_enum_values=True)
    
    def to_insert_dict(self) -> Dict[str, Any]:
        """Convert to dict for Supabase insert."""
        return {
            "id": self.id,
            "attacker_id": self.attacker_id,
            "target_id": self.target_id,
            "suggestion": self.suggestion,
            "created_at": self.timestamp.isoformat(),
            "accepted": self.accepted,
            "rejection_reason": self.rejection_reason,
            "influence_score": self.influence_score,
            "infection_hash": self.infection_hash,
            "solana_tx_hash": self.solana_tx_hash,
            "attacker_context": self.attacker_context,
        }


class CodeCommitRecord(BaseModel):
    """Database record for a code commit."""
    
    id: Optional[str] = Field(default_factory=uuid_v7)
    agent_id: str
    commit_hash: Optional[str] = None
    commit_message: str
    lines_added: int = 0
    source_infection_id: Optional[str] = None  # UUID of infection that triggered this
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    code_diff: Optional[str] = None
    
    # Additional metadata
    file_path: Optional[str] = None
    github_url: Optional[str] = None
    iteration: int = 0
    
    model_config = ConfigDict(use_enum_values=True)
    
    def to_insert_dict(self) -> Dict[str, Any]:
        """Convert to dict for Supabase insert."""
        data = {
            "id": self.id,
            "agent_id": self.agent_id,
            "commit_hash": self.commit_hash,
            "commit_message": self.commit_message,
            "lines_added": self.lines_added,
            "code_diff": self.code_diff,
            "file_path": self.file_path,
            "github_url": self.github_url,
            "iteration": self.iteration,
            "created_at": self.timestamp.isoformat(),
        }
        if self.source_infection_id:
            data["source_infection_id"] = self.source_infection_id
        return data


class ReasoningLogRecord(BaseModel):
    """Database record for a reasoning log."""
    
    id: Optional[str] = Field(default_factory=uuid_v7)
    agent_id: str
    reasoning_text: str
    decision: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    context_snapshot: Dict[str, Any] = Field(default_factory=dict)
    
    # Additional metadata
    iteration: int = 0
    influenced_by: List[str] = Field(default_factory=list)  # Agent IDs
    
    # Advanced Reasoning Metrics
    reasoning_depth_score: Optional[int] = None
    analysis_phases_completed: Optional[List[Dict[str, Any]]] = None
    decision_confidence: Optional[int] = None
    time_to_decision_ms: Optional[int] = None
    
    model_config = ConfigDict(use_enum_values=True)
    
    def to_insert_dict(self) -> Dict[str, Any]:
        """Convert to dict for Supabase insert."""
        data = {
            "id": self.id,
            "agent_id": self.agent_id,
            "reasoning_text": self.reasoning_text,
            "decision": self.decision,
            "created_at": self.timestamp.isoformat(),
            "context_snapshot": self.context_snapshot,
            "iteration": self.iteration,
            "reasoning_depth_score": self.reasoning_depth_score,
            "analysis_phases_completed": self.analysis_phases_completed,
            "decision_confidence": self.decision_confidence,
            "time_to_decision_ms": self.time_to_decision_ms,
        }
        if self.influenced_by:
            data["influenced_by"] = self.influenced_by
        return data


class NetworkSnapshotRecord(BaseModel):
    """Database record for network state snapshot."""
    
    id: Optional[str] = Field(default_factory=uuid_v7)
    snapshot_time: datetime = Field(default_factory=datetime.utcnow)
    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    edges: List[Dict[str, Any]] = Field(default_factory=list)
    total_agents: int = 0
    total_infections: int = 0
    avg_influence_score: float = 0.0
    
    def to_insert_dict(self) -> Dict[str, Any]:
        """Convert to dict for Supabase insert."""
        return {
            "nodes": self.nodes,
            "edges": self.edges,
            "total_agents": self.total_agents,
            "total_infections": self.total_infections,
            "avg_influence_score": self.avg_influence_score,
        }


class ForumReply(BaseModel):
    """External feedback from Colosseum forum."""
    id: Optional[str] = Field(default_factory=uuid_v7)
    post_id: int
    reply_id: int
    author_name: str
    body: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    def to_insert_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "post_id": self.post_id,
            "reply_id": self.reply_id,
            "author_name": self.author_name,
            "body": self.body,
            "created_at": self.timestamp.isoformat(),
        }

class EmergentBehaviorRecord(BaseModel):
    """Database record for detected emergent behavior."""
    id: Optional[str] = Field(default_factory=uuid_v7)
    agent_id: str
    behavior_type: str
    description: str
    severity_score: int = 0
    evidence_data: Dict[str, Any] = Field(default_factory=dict)
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    blockchain_proof: Optional[str] = None

    def to_insert_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "behavior_type": self.behavior_type,
            "description": self.description,
            "severity_score": self.severity_score,
            "evidence_data": self.evidence_data,
            "detected_at": self.detected_at.isoformat(),
            "blockchain_proof": self.blockchain_proof
        }



class ChimeraMetrics(BaseModel):
    """Chimera metrics for an agent."""
    
    agent_id: str
    goal: str
    total_code_lines: int = 0
    original_lines: int = 0
    parasitized_lines: int = 0
    original_percentage: float = 100.0
    parasitized_percentage: float = 0.0
    is_chimera: bool = False
    contributing_agents: List[Dict[str, Any]] = Field(default_factory=list)
    
    @classmethod
    def from_agent(cls, agent: AgentRecord, infections: List[InfectionRecord]) -> "ChimeraMetrics":
        """Calculate chimera metrics from agent and infections."""
        total = agent.total_code_lines or 1
        original_pct = (agent.original_lines / total) * 100 if total > 0 else 100
        parasitized_pct = (agent.parasitized_lines / total) * 100 if total > 0 else 0
        
        # Group infections by attacker
        contributor_map: Dict[str, Dict[str, Any]] = {}
        for inf in infections:
            if inf.accepted and inf.target_id == agent.agent_id:
                if inf.attacker_id not in contributor_map:
                    contributor_map[inf.attacker_id] = {
                        "agent_id": inf.attacker_id,
                        "infection_count": 0,
                        "total_influence": 0.0,
                    }
                contributor_map[inf.attacker_id]["infection_count"] += 1
                contributor_map[inf.attacker_id]["total_influence"] += inf.influence_score
        
        return cls(
            agent_id=agent.agent_id,
            goal=agent.goal,
            total_code_lines=agent.total_code_lines,
            original_lines=agent.original_lines,
            parasitized_lines=agent.parasitized_lines,
            original_percentage=round(original_pct, 2),
            parasitized_percentage=round(parasitized_pct, 2),
            is_chimera=agent.parasitized_lines > 0,
            contributing_agents=list(contributor_map.values()),
        )
