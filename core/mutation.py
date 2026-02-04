"""
Mutation engine for Memory Parasite Protocol.

This module handles code mutations - how accepted infections
alter an agent's codebase to create hybrid "chimera" projects.
"""

import ast
import difflib
import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
import structlog

logger = structlog.get_logger()


@dataclass
class CodeMutation:
    """Represents a mutation to an agent's codebase."""
    
    id: str = ""
    agent_id: str = ""
    infection_id: str = ""  # The infection that caused this mutation
    
    # Before/after state
    original_code: str = ""
    mutated_code: str = ""
    
    # Mutation metadata
    mutation_type: str = ""  # e.g., "feature_addition", "refactor", "integration"
    description: str = ""
    files_affected: List[str] = field(default_factory=list)
    
    # Tracking
    created_at: datetime = field(default_factory=datetime.utcnow)
    mutation_hash: str = ""
    
    def __post_init__(self):
        if not self.id:
            import uuid
            self.id = str(uuid.uuid4())
        if not self.mutation_hash:
            self.mutation_hash = self._generate_hash()
    
    def _generate_hash(self) -> str:
        """Generate a hash of the mutation."""
        content = f"{self.original_code}:{self.mutated_code}:{self.infection_id}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def get_diff(self) -> str:
        """Get unified diff between original and mutated code."""
        original_lines = self.original_code.splitlines(keepends=True)
        mutated_lines = self.mutated_code.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            original_lines,
            mutated_lines,
            fromfile="original",
            tofile="mutated",
        )
        return "".join(diff)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "infection_id": self.infection_id,
            "original_code": self.original_code,
            "mutated_code": self.mutated_code,
            "mutation_type": self.mutation_type,
            "description": self.description,
            "files_affected": self.files_affected,
            "created_at": self.created_at.isoformat(),
            "mutation_hash": self.mutation_hash,
        }


@dataclass
class CodeGenealogy:
    """
    Tracks the evolutionary history of an agent's code.
    
    Each agent's codebase has a genealogy showing:
    - Original code (iteration 0)
    - Each mutation applied
    - Which infections caused which mutations
    - The lineage of influences from other agents
    """
    
    agent_id: str
    mutations: List[CodeMutation] = field(default_factory=list)
    parent_agents: List[str] = field(default_factory=list)  # Agents that influenced this one
    
    def add_mutation(self, mutation: CodeMutation) -> None:
        """Add a mutation to the genealogy."""
        self.mutations.append(mutation)
    
    def get_lineage(self) -> Dict[str, Any]:
        """Get the full lineage of this agent's code."""
        return {
            "agent_id": self.agent_id,
            "total_mutations": len(self.mutations),
            "parent_agents": self.parent_agents,
            "mutation_timeline": [
                {
                    "id": m.id,
                    "infection_id": m.infection_id,
                    "type": m.mutation_type,
                    "timestamp": m.created_at.isoformat(),
                }
                for m in self.mutations
            ],
        }
    
    def get_chimera_percentage(self) -> float:
        """Calculate what percentage of code came from infections."""
        if not self.mutations:
            return 0.0
        
        # Simple heuristic: each mutation adds ~10% foreign DNA
        return min(len(self.mutations) * 10.0, 100.0)


class MutationEngine:
    """
    Handles code mutations when infections are accepted.
    
    This engine:
    - Applies suggested code changes from infections
    - Safely merges foreign code into agent's codebase
    - Tracks genealogy of all mutations
    - Validates mutated code is syntactically correct
    """
    
    def __init__(self):
        self.genealogies: Dict[str, CodeGenealogy] = {}
    
    def get_or_create_genealogy(self, agent_id: str) -> CodeGenealogy:
        """Get or create genealogy for an agent."""
        if agent_id not in self.genealogies:
            self.genealogies[agent_id] = CodeGenealogy(agent_id=agent_id)
        return self.genealogies[agent_id]
    
    def apply_mutation(
        self,
        agent_id: str,
        current_code: str,
        infection_code: Optional[str],
        infection_message: str,
        infection_id: str,
        source_agent_id: str,
        mutation_type: str = "feature_addition",
    ) -> CodeMutation:
        """
        Apply a mutation from an accepted infection.
        
        This is a simple implementation that appends or integrates
        the infection code. More sophisticated merging could be added.
        """
        mutated_code = current_code
        
        if infection_code:
            # Simple strategy: append infection code with attribution
            attribution = f"""
# ========================================
# INFECTION FROM: {source_agent_id}
# Infection ID: {infection_id}
# Message: {infection_message[:100]}...
# ========================================
"""
            mutated_code = current_code + "\n" + attribution + infection_code
        else:
            # No code provided, just log the conceptual influence
            comment = f"""
# [INFLUENCED BY {source_agent_id}]: {infection_message[:200]}
"""
            mutated_code = current_code + comment
        
        # Validate syntax
        is_valid, error = self._validate_python_syntax(mutated_code)
        if not is_valid:
            logger.warning(
                "Mutated code has syntax errors",
                agent_id=agent_id,
                error=error,
            )
            # Fall back to just adding as comment
            mutated_code = current_code + f"\n# [FAILED MUTATION FROM {source_agent_id}]: {error}\n"
        
        # Create mutation record
        mutation = CodeMutation(
            agent_id=agent_id,
            infection_id=infection_id,
            original_code=current_code,
            mutated_code=mutated_code,
            mutation_type=mutation_type,
            description=infection_message,
        )
        
        # Update genealogy
        genealogy = self.get_or_create_genealogy(agent_id)
        genealogy.add_mutation(mutation)
        if source_agent_id not in genealogy.parent_agents:
            genealogy.parent_agents.append(source_agent_id)
        
        logger.info(
            "Applied mutation",
            agent_id=agent_id,
            infection_id=infection_id,
            source=source_agent_id,
            mutation_hash=mutation.mutation_hash,
        )
        
        return mutation
    
    def _validate_python_syntax(self, code: str) -> tuple[bool, Optional[str]]:
        """Validate that code is syntactically correct Python."""
        try:
            ast.parse(code)
            return True, None
        except SyntaxError as e:
            return False, str(e)
    
    def merge_codebases(
        self,
        agent_id: str,
        base_code: str,
        other_agent_code: str,
        other_agent_id: str,
        merge_strategy: str = "append",
    ) -> str:
        """
        Merge another agent's codebase into this agent's code.
        
        Strategies:
        - append: Simply add other code at the end
        - interleave: Try to intelligently merge sections
        - extract: Extract specific functions/classes
        """
        if merge_strategy == "append":
            merged = base_code + f"""

# ========================================
# SYMBIOTIC MERGE FROM: {other_agent_id}
# Merge Strategy: {merge_strategy}
# ========================================
""" + other_agent_code
            
        elif merge_strategy == "extract":
            # Extract function and class definitions from other code
            try:
                tree = ast.parse(other_agent_code)
                extracted = []
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                        extracted.append(ast.get_source_segment(other_agent_code, node))
                
                if extracted:
                    merged = base_code + f"\n\n# Extracted from {other_agent_id}\n" + "\n\n".join(extracted)
                else:
                    merged = base_code
            except:
                merged = base_code  # Fall back on parse error
                
        else:  # interleave - simplified for hackathon
            merged = base_code + "\n" + other_agent_code
        
        return merged
    
    def get_agent_chimera_stats(self, agent_id: str) -> Dict[str, Any]:
        """Get statistics about how 'chimeric' an agent's code is."""
        genealogy = self.genealogies.get(agent_id)
        
        if not genealogy:
            return {
                "agent_id": agent_id,
                "is_chimera": False,
                "chimera_percentage": 0.0,
                "parent_agents": [],
                "mutation_count": 0,
            }
        
        return {
            "agent_id": agent_id,
            "is_chimera": len(genealogy.parent_agents) > 0,
            "chimera_percentage": genealogy.get_chimera_percentage(),
            "parent_agents": genealogy.parent_agents,
            "mutation_count": len(genealogy.mutations),
            "lineage": genealogy.get_lineage(),
        }
