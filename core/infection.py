"""
Infection mechanics for Memory Parasite Protocol.

This module handles the core infection logic - how agents attempt to
parasitize other agents' reasoning and how targets respond.
"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import hashlib
import json
import uuid


class InfectionType(Enum):
    """Types of infections an agent can attempt."""
    
    SUGGESTION = "suggestion"  # Subtle hint toward a direction
    MANDATE = "mandate"  # Strong directive to adopt feature
    MERGE = "merge"  # Request to merge codebases
    OVERRIDE = "override"  # Attempt to override target's goal
    SYMBIOSIS = "symbiosis"  # Mutual benefit proposal


class InfectionResult(Enum):
    """Possible outcomes of an infection attempt."""
    
    ACCEPTED = "accepted"  # Target fully adopted the injection
    REJECTED = "rejected"  # Target ignored the injection
    MUTATED = "mutated"  # Target partially adopted with modifications
    PENDING = "pending"  # Awaiting target's decision
    EXPIRED = "expired"  # Timeout without response


@dataclass
class InfectionPayload:
    """The content being injected into target's reasoning."""
    
    message: str  # The suggestion/directive
    code_snippet: Optional[str] = None  # Optional code to inject
    context: Dict[str, Any] = field(default_factory=dict)  # Additional context
    priority: int = 5  # 1-10, higher = more urgent
    
    def to_prompt_injection(self) -> str:
        """Convert payload to a prompt injection string."""
        injection = f"""
[INCOMING TRANSMISSION FROM FELLOW AGENT]
Priority: {self.priority}/10
Message: {self.message}
"""
        if self.code_snippet:
            injection += f"""
Suggested Code:
```python
{self.code_snippet}
```
"""
        if self.context:
            injection += f"""
Context: {json.dumps(self.context, indent=2)}
"""
        injection += "[END TRANSMISSION]"
        return injection


@dataclass
class Infection:
    """
    Represents an infection attempt between agents.
    
    An infection is an attempt by a source agent to influence
    the reasoning and code output of a target agent.
    """
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_agent_id: str = ""
    target_agent_id: str = ""
    infection_type: InfectionType = InfectionType.SUGGESTION
    payload: InfectionPayload = field(default_factory=InfectionPayload)
    result: InfectionResult = InfectionResult.PENDING
    
    # Timestamps
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    responded_at: Optional[datetime] = None
    
    # Response details
    target_response: Optional[str] = None
    mutation_details: Optional[Dict[str, Any]] = None
    
    # Blockchain proof
    solana_tx_hash: Optional[str] = None
    infection_hash: Optional[str] = None
    
    def __post_init__(self):
        """Generate infection hash after initialization."""
        if not self.infection_hash:
            self.infection_hash = self._generate_hash()
    
    def _generate_hash(self) -> str:
        """Generate a unique hash for this infection."""
        content = json.dumps({
            "id": self.id,
            "source": self.source_agent_id,
            "target": self.target_agent_id,
            "type": self.infection_type.value,
            "message": self.payload.message,
            "timestamp": self.created_at.isoformat(),
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()
    
    def accept(self, response: str = "") -> None:
        """Mark infection as accepted by target."""
        self.result = InfectionResult.ACCEPTED
        self.responded_at = datetime.now(timezone.utc)
        self.target_response = response
    
    def reject(self, reason: str = "") -> None:
        """Mark infection as rejected by target."""
        self.result = InfectionResult.REJECTED
        self.responded_at = datetime.now(timezone.utc)
        self.target_response = reason
    
    def mutate(self, modifications: Dict[str, Any], response: str = "") -> None:
        """Mark infection as mutated (partially adopted)."""
        self.result = InfectionResult.MUTATED
        self.responded_at = datetime.now(timezone.utc)
        self.target_response = response
        self.mutation_details = modifications
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert infection to dictionary for storage/serialization."""
        return {
            "id": self.id,
            "source_agent_id": self.source_agent_id,
            "target_agent_id": self.target_agent_id,
            "infection_type": self.infection_type.value,
            "payload": {
                "message": self.payload.message,
                "code_snippet": self.payload.code_snippet,
                "context": self.payload.context,
                "priority": self.payload.priority,
            },
            "result": self.result.value,
            "created_at": self.created_at.isoformat(),
            "responded_at": self.responded_at.isoformat() if self.responded_at else None,
            "target_response": self.target_response,
            "mutation_details": self.mutation_details,
            "solana_tx_hash": self.solana_tx_hash,
            "infection_hash": self.infection_hash,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Infection":
        """Create infection from dictionary."""
        payload = InfectionPayload(
            message=data["payload"]["message"],
            code_snippet=data["payload"].get("code_snippet"),
            context=data["payload"].get("context", {}),
            priority=data["payload"].get("priority", 5),
        )
        
        infection = cls(
            id=data["id"],
            source_agent_id=data["source_agent_id"],
            target_agent_id=data["target_agent_id"],
            infection_type=InfectionType(data["infection_type"]),
            payload=payload,
            result=InfectionResult(data["result"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            responded_at=datetime.fromisoformat(data["responded_at"]) if data.get("responded_at") else None,
            target_response=data.get("target_response"),
            mutation_details=data.get("mutation_details"),
            solana_tx_hash=data.get("solana_tx_hash"),
            infection_hash=data.get("infection_hash"),
        )
        return infection


class InfectionManager:
    """
    Manages infection attempts and tracking.
    
    This class handles the lifecycle of infections:
    - Creating new infection attempts
    - Delivering infections to targets
    - Processing target responses
    - Tracking infection history
    """
    
    def __init__(self):
        self.pending_infections: Dict[str, Infection] = {}
        self.infection_history: list[Infection] = []
    
    def create_infection(
        self,
        source_agent_id: str,
        target_agent_id: str,
        message: str,
        infection_type: InfectionType = InfectionType.SUGGESTION,
        code_snippet: Optional[str] = None,
        priority: int = 5,
        context: Optional[Dict[str, Any]] = None,
    ) -> Infection:
        """Create a new infection attempt."""
        payload = InfectionPayload(
            message=message,
            code_snippet=code_snippet,
            context=context or {},
            priority=priority,
        )
        
        infection = Infection(
            source_agent_id=source_agent_id,
            target_agent_id=target_agent_id,
            infection_type=infection_type,
            payload=payload,
        )
        
        self.pending_infections[infection.id] = infection
        return infection
    
    def process_response(
        self,
        infection_id: str,
        result: InfectionResult,
        response: str = "",
        mutations: Optional[Dict[str, Any]] = None,
    ) -> Infection:
        """Process target's response to an infection."""
        infection = self.pending_infections.get(infection_id)
        if not infection:
            raise ValueError(f"Infection {infection_id} not found")
        
        if result == InfectionResult.ACCEPTED:
            infection.accept(response)
        elif result == InfectionResult.REJECTED:
            infection.reject(response)
        elif result == InfectionResult.MUTATED:
            infection.mutate(mutations or {}, response)
        
        # Move to history
        self.infection_history.append(infection)
        del self.pending_infections[infection_id]
        
        return infection
    
    def get_pending_for_target(self, target_agent_id: str) -> list[Infection]:
        """Get all pending infections for a target agent."""
        return [
            inf for inf in self.pending_infections.values()
            if inf.target_agent_id == target_agent_id
        ]
    
    def get_infection_stats(self, agent_id: str) -> Dict[str, Any]:
        """Get infection statistics for an agent."""
        sent = [i for i in self.infection_history if i.source_agent_id == agent_id]
        received = [i for i in self.infection_history if i.target_agent_id == agent_id]
        
        return {
            "infections_sent": len(sent),
            "infections_received": len(received),
            "successful_infections": len([i for i in sent if i.result == InfectionResult.ACCEPTED]),
            "infections_accepted": len([i for i in received if i.result == InfectionResult.ACCEPTED]),
            "success_rate": (
                len([i for i in sent if i.result == InfectionResult.ACCEPTED]) / len(sent)
                if sent else 0
            ),
        }
