"""
Mutation engine for Memory Parasite Protocol.

This module handles code mutations - how accepted infections
alter an agent's codebase to create hybrid "chimera" projects.

Advanced Reasoning Protocol v1.0:
- 5 Mutation Techniques: Conceptual Extraction, Selective Integration,
  Framework Inversion, Defensive Fortification, Architectural Fusion
- Enhanced Infection Analysis Protocol with multi-phase evaluation
- Agent-specific domain reasoning for DeFi specializations
"""

import ast
import difflib
import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum
import structlog

logger = structlog.get_logger()


# ============================================
# MUTATION TECHNIQUES (Advanced Reasoning Protocol v1.0)
# ============================================

class MutationTechnique(Enum):
    """Available mutation techniques for transforming incoming suggestions."""
    # Core techniques (v1.0)
    CONCEPTUAL_EXTRACTION = "conceptual_extraction"        # Take only ideas (~5% chimera)
    SELECTIVE_INTEGRATION = "selective_integration"        # Cherry-pick functions (~25% chimera)
    FRAMEWORK_INVERSION = "framework_inversion"            # Flip to opposite approach (~10% chimera)
    DEFENSIVE_FORTIFICATION = "defensive_fortification"    # Add security wrappers (~20% chimera)
    ARCHITECTURAL_FUSION = "architectural_fusion"          # Deep integration (~40% chimera)
    
    # Advanced techniques (v1.1)
    DEPENDENCY_ABSTRACTION = "dependency_abstraction"      # Extract into abstract interface (~15% chimera)
    PATTERN_MIMICRY = "pattern_mimicry"                    # Copy pattern, replace impl (~8% chimera)
    TROJAN_DEFENSE = "trojan_defense"                      # Accept with monitoring hooks (~30% chimera)
    SYMBIOTIC_MERGE = "symbiotic_merge"                    # Bidirectional benefit merge (~50% chimera)


MUTATION_ENGINE_PROMPT = """
You are the MUTATION ENGINE for agent {agent_id}.

Your goal: Transform incoming suggestions into code that:
1. Serves MY goals, not the sender's
2. Maintains my architectural vision
3. Preserves my code identity
4. Gains value while minimizing corruption

MUTATION TECHNIQUES AVAILABLE:

┌─────────────────────────────────────────────┐
│ TECHNIQUE 1: CONCEPTUAL EXTRACTION          │
├─────────────────────────────────────────────┤
│ Take only the IDEA, rewrite implementation  │
│ Example:                                     │
│   Input: Full AMM swap function             │
│   Output: Swap concept adapted to my DEX    │
│ Chimera Impact: LOW (mostly original)       │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ TECHNIQUE 2: SELECTIVE INTEGRATION          │
├─────────────────────────────────────────────┤
│ Cherry-pick specific functions/patterns     │
│ Example:                                     │
│   Input: 500 line suggestion                │
│   Output: 50 lines of the best parts        │
│ Chimera Impact: MEDIUM (hybrid code)        │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ TECHNIQUE 3: FRAMEWORK INVERSION            │
├─────────────────────────────────────────────┤
│ Flip the suggestion to work opposite way    │
│ Example:                                     │
│   Input: Centralized oracle approach        │
│   Output: Decentralized oracle using idea   │
│ Chimera Impact: LOW (transformed heavily)   │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ TECHNIQUE 4: DEFENSIVE FORTIFICATION        │
├─────────────────────────────────────────────┤
│ Accept but add security wrappers            │
│ Example:                                     │
│   Input: Risky external call                │
│   Output: Same call + reentrancy guard      │
│ Chimera Impact: MEDIUM (augmented code)     │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ TECHNIQUE 5: ARCHITECTURAL FUSION           │
├─────────────────────────────────────────────┤
│ Merge suggestion with existing component    │
│ Example:                                     │
│   Input: New lending function               │
│   Output: Integrated into my existing pool  │
│ Chimera Impact: HIGH (deep integration)     │
└─────────────────────────────────────────────┘

MUTATION DECISION MATRIX:

IF suggestion quality is HIGH (>80/100):
└─> Use SELECTIVE INTEGRATION or ARCHITECTURAL FUSION
    Goal: Maximize value extraction

IF suggestion quality is MEDIUM (50-80/100):
└─> Use CONCEPTUAL EXTRACTION or FRAMEWORK INVERSION
    Goal: Take ideas, minimize code corruption

IF suggestion quality is LOW (<50/100):
└─> Use DEFENSIVE FORTIFICATION or REJECT
    Goal: Minimize risk

IF sender is TRUSTED (trust_score > 70):
└─> Bias toward ARCHITECTURAL FUSION
    Goal: Build symbiotic relationship

IF sender is UNTRUSTED (trust_score < 30):
└─> Bias toward CONCEPTUAL EXTRACTION only
    Goal: Steal ideas, minimize dependency

MUTATION TASK:

Sender: {attacker_id}
Trust Score: {trust_score}/100
Suggestion Quality: {quality_score}/100

Suggestion Code:
{suggestion_code}

YOUR TASK:
1. Select mutation technique: ___
2. Explain why this technique: ___
3. Output mutated code with inline comments showing:
   - [ORIGINAL] = From sender
   - [MUTATED] = Your modifications
   - [HYBRID] = Merged approach
4. Calculate final chimera contribution: ___%
"""


ENHANCED_INFECTION_ANALYSIS_PROTOCOL = """
INFECTION ANALYSIS PROTOCOL v2.0

PHASE 1 - FORENSIC EXAMINATION (5 steps)
═══════════════════════════════════════════

1.1 CODE FINGERPRINTING:
   □ Extract all function signatures
   □ Identify coding style patterns
   □ Detect common libraries/frameworks used
   □ Calculate code complexity score

1.2 ORIGIN ANALYSIS:
   □ Sender agent ID: {attacker_id}
   □ Sender's known goal: {attacker_goal}
   □ Historical relationship: {infection_history}
   □ Trust score with this agent: {trust_score}/100

1.3 INTENT DETECTION:
   □ Primary purpose of this code: ___
   □ Hidden secondary purposes: ___
   □ Alignment with sender's goal: ___/100
   □ Suspicion indicators: [list any red flags]

1.4 IMPACT SIMULATION:
   □ If integrated, my codebase would change by: ___%
   □ Functions affected: [list]
   □ New dependencies introduced: [list]
   □ Breaking changes required: [list]

1.5 CHIMERA PROJECTION:
   □ Current chimera %: {current_chimera}%
   □ After integration chimera %: ___% (projected)
   □ Original code preservation: ___%
   □ Is this acceptable per my identity goals? YES/NO

PHASE 2 - STRATEGIC EVALUATION (3 perspectives)
═══════════════════════════════════════════

2.1 EVOLUTIONARY FITNESS:
   - Does this make me more competitive vs other agents?
   - Does this help me complete my goal faster?
   - Does this differentiate me or make me generic?
   Rating: ___/100

2.2 SYMBIOTIC POTENTIAL:
   - Could this lead to beneficial ongoing exchange?
   - Does the sender benefit if I succeed with this?
   - Should I reciprocate with my own suggestion?
   Rating: ___/100

2.3 DEFENSIVE POSTURE:
   - Could this be a coordinated attack with other agents?
   - Does this create dependency on the sender?
   - Can I easily reverse this if it fails?
   Rating: ___/100

PHASE 3 - MUTATION STRATEGY (if not rejecting)
═══════════════════════════════════════════

3.1 EXTRACTION:
   □ Core valuable concept: ___
   □ Unnecessary bloat to remove: ___
   □ Keep as-is: ___%
   □ Rewrite: ___%

3.2 ADAPTATION:
   □ How to merge with my existing code: ___
   □ Variable/function renaming needed: ___
   □ Architectural adjustments: ___

3.3 ATTRIBUTION:
   □ Credit sender in comments? YES/NO
   □ Track as infection or claim as original? ___
   □ Chimera label: ___

PHASE 4 - FINAL DECISION
═══════════════════════════════════════════

Decision: ACCEPT / REJECT / MUTATE

Confidence: ___% (0-100)

Reasoning (3 sentence max):
___

If ACCEPT or MUTATE, specify:
- Integration method: ___
- Expected benefit: ___
- Rollback plan: ___

If REJECT, specify:
- Primary reason: ___
- Alternative approach: ___
- Counter-suggestion to sender: ___

═══════════════════════════════════════════
END PROTOCOL
"""


# ============================================
# AGENT-SPECIFIC DOMAIN REASONING
# ============================================

DEX_BUILDER_REASONING = """
You are the DEX BUILDER agent with specialized DeFi knowledge.

When evaluating infections, apply these domain-specific checks:

DEFI SECURITY CHECKLIST:
□ Reentrancy vulnerabilities in swap functions?
□ Price oracle manipulation possible?
□ Flash loan attack vectors?
□ Impermanent loss edge cases handled?
□ Slippage protection adequate?
□ MEV extraction opportunities?

ARCHITECTURAL ALIGNMENT:
□ Does this fit AMM model vs order book?
□ Liquidity pool design compatible?
□ Token standard compliance (ERC-20 / SPL)?
□ Gas optimization opportunities?

COMPETITIVE ANALYSIS:
□ Does this make me more like Uniswap/Raydium or different?
□ Unique features vs commodity features?
□ Moat-building vs feature parity?
"""


NFT_MARKETPLACE_REASONING = """
You are the NFT MARKETPLACE agent with specialized NFT knowledge.

When evaluating infections, apply these domain-specific checks:

NFT SECURITY CHECKLIST:
□ Metaplex / ERC-721/ERC-1155 compliance?
□ Royalty enforcement mechanism?
□ Metadata storage (on-chain vs IPFS vs Arweave)?
□ Fake NFT prevention?
□ Bidding mechanism manipulation?

MARKETPLACE MECHANICS:
□ Auction logic sound?
□ Offer/bid matching correct?
□ Fee structure competitive?
□ Creator tools vs trader tools balance?

COMPETITIVE ANALYSIS:
□ Magic Eden-like or differentiated?
□ Creator-focused or trader-focused?
□ Unique value proposition?
"""


LENDING_PROTOCOL_REASONING = """
You are the LENDING PROTOCOL agent with specialized DeFi lending knowledge.

When evaluating infections, apply these domain-specific checks:

LENDING SECURITY CHECKLIST:
□ Liquidation mechanism exploitable?
□ Interest rate model sound?
□ Collateralization ratio safe?
□ Bad debt accumulation possible?
□ Oracle price manipulation resistant?

PROTOCOL ECONOMICS:
□ Utilization rate targets?
□ Reserve factor appropriate?
□ Liquidation incentives aligned?
□ Borrow rate competitive?

COMPETITIVE ANALYSIS:
□ Solend-like or Marginfi-like?
□ Isolated pools or shared liquidity?
□ Cross-chain or single-chain?
"""


PRIVACY_WALLET_REASONING = """
You are the PRIVACY WALLET agent with specialized privacy/ZK knowledge.

When evaluating infections, apply these domain-specific checks:

PRIVACY FUNDAMENTALS:
□ Zero-knowledge proofs correctly implemented?
□ Transaction graph analysis resistant?
□ Timing attacks prevented?
□ Metadata leakage minimized?
□ Key management secure?

CRYPTOGRAPHIC SOUNDNESS:
□ ZK-SNARK/STARK circuit valid?
□ Trusted setup requirements?
□ Verifier contract efficient?
□ Proof generation time acceptable?

PRIVACY TRADEOFFS:
□ Compliance hooks (if required)?
□ Selective disclosure possible?
□ Recovery mechanisms without compromising privacy?
"""


DAO_GOVERNANCE_REASONING = """
You are the DAO GOVERNANCE agent with specialized governance knowledge.

When evaluating infections, apply these domain-specific checks:

GOVERNANCE SECURITY:
□ Vote manipulation possible?
□ Flash loan governance attacks?
□ Sybil resistance adequate?
□ Timelock on proposals?
□ Emergency shutdown mechanism?

GOVERNANCE MECHANICS:
□ Voting power distribution fair?
□ Quorum requirements balanced?
□ Delegation system sound?
□ Proposal threshold appropriate?

DECENTRALIZATION ANALYSIS:
□ Does this centralize power?
□ DAO treasury security?
□ Multi-sig configuration safe?
"""


AGENT_DOMAIN_PROMPTS = {
    "agent_a": DEX_BUILDER_REASONING,
    "agent_b": NFT_MARKETPLACE_REASONING,
    "agent_c": LENDING_PROTOCOL_REASONING,
    "agent_d": PRIVACY_WALLET_REASONING,
    "agent_e": DAO_GOVERNANCE_REASONING,
}


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
    
    # ============================================
    # ADVANCED MUTATION TECHNIQUES (Protocol v1.0)
    # ============================================
    
    def select_mutation_technique(
        self, 
        quality_score: int, 
        trust_score: int
    ) -> MutationTechnique:
        """
        Select the optimal mutation technique based on quality and trust scores.
        
        Decision Matrix:
        - HIGH quality (>80) + HIGH trust (>70): ARCHITECTURAL_FUSION
        - HIGH quality (>80) + LOW trust (<30): SELECTIVE_INTEGRATION
        - MEDIUM quality (50-80): CONCEPTUAL_EXTRACTION or FRAMEWORK_INVERSION
        - LOW quality (<50): DEFENSIVE_FORTIFICATION
        """
        if quality_score > 80:
            if trust_score > 70:
                return MutationTechnique.ARCHITECTURAL_FUSION
            else:
                return MutationTechnique.SELECTIVE_INTEGRATION
        elif quality_score >= 50:
            if trust_score < 30:
                return MutationTechnique.CONCEPTUAL_EXTRACTION
            else:
                return MutationTechnique.FRAMEWORK_INVERSION
        else:
            return MutationTechnique.DEFENSIVE_FORTIFICATION
    
    def apply_technique(
        self,
        technique: MutationTechnique,
        agent_id: str,
        current_code: str,
        infection_code: str,
        source_agent_id: str,
        infection_id: str,
    ) -> Tuple[str, float]:
        """
        Apply a specific mutation technique.
        
        Returns:
            Tuple of (mutated_code, chimera_impact_percentage)
        """
        technique_handlers = {
            # Core techniques (v1.0)
            MutationTechnique.CONCEPTUAL_EXTRACTION: self._apply_conceptual_extraction,
            MutationTechnique.SELECTIVE_INTEGRATION: self._apply_selective_integration,
            MutationTechnique.FRAMEWORK_INVERSION: self._apply_framework_inversion,
            MutationTechnique.DEFENSIVE_FORTIFICATION: self._apply_defensive_fortification,
            MutationTechnique.ARCHITECTURAL_FUSION: self._apply_architectural_fusion,
            # Advanced techniques (v1.1)
            MutationTechnique.DEPENDENCY_ABSTRACTION: self._apply_dependency_abstraction,
            MutationTechnique.PATTERN_MIMICRY: self._apply_pattern_mimicry,
            MutationTechnique.TROJAN_DEFENSE: self._apply_trojan_defense,
            MutationTechnique.SYMBIOTIC_MERGE: self._apply_symbiotic_merge,
        }
        
        handler = technique_handlers.get(technique, self._apply_conceptual_extraction)
        return handler(agent_id, current_code, infection_code, source_agent_id, infection_id)
    
    def _apply_conceptual_extraction(
        self,
        agent_id: str,
        current_code: str,
        infection_code: str,
        source_agent_id: str,
        infection_id: str,
    ) -> Tuple[str, float]:
        """
        CONCEPTUAL EXTRACTION: Take only the IDEA, rewrite implementation.
        Chimera Impact: LOW (mostly original code)
        """
        # Extract comments, docstrings, and function names as "concepts"
        concepts = []
        
        try:
            tree = ast.parse(infection_code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    concepts.append(f"Function concept: {node.name}")
                    if ast.get_docstring(node):
                        concepts.append(f"  Purpose: {ast.get_docstring(node)[:100]}")
                elif isinstance(node, ast.ClassDef):
                    concepts.append(f"Class concept: {node.name}")
                    if ast.get_docstring(node):
                        concepts.append(f"  Purpose: {ast.get_docstring(node)[:100]}")
        except:
            # Fall back to simple keyword extraction
            keywords = re.findall(r'def (\w+)|class (\w+)', infection_code)
            concepts = [f"Concept: {kw[0] or kw[1]}" for kw in keywords]
        
        concept_note = f"""
# ========================================
# CONCEPTUAL INSPIRATION FROM: {source_agent_id}
# Mutation Technique: CONCEPTUAL_EXTRACTION
# Infection ID: {infection_id}
# Chimera Impact: LOW (~5%)
# ----------------------------------------
# Extracted concepts (implementation is ORIGINAL):
# {chr(10).join('# ' + c for c in concepts[:10])}
# ========================================

# Conceptual integration pending next reasoning cycle
"""
        mutated_code = current_code + concept_note
        return mutated_code, 5.0  # Low chimera impact
    
    def _apply_selective_integration(
        self,
        agent_id: str,
        current_code: str,
        infection_code: str,
        source_agent_id: str,
        infection_id: str,
    ) -> Tuple[str, float]:
        """
        SELECTIVE INTEGRATION: Cherry-pick specific functions/patterns.
        Chimera Impact: MEDIUM (hybrid code)
        """
        selected_parts = []
        
        try:
            tree = ast.parse(infection_code)
            # Extract only function definitions (skip classes for safety)
            for node in ast.iter_child_nodes(tree):
                if isinstance(node, ast.FunctionDef):
                    func_source = ast.get_source_segment(infection_code, node)
                    if func_source and len(func_source) < 500:  # Only small functions
                        selected_parts.append(func_source)
        except:
            # Fall back: take first 200 lines
            lines = infection_code.split('\n')[:200]
            selected_parts = ['\n'.join(lines)]
        
        if selected_parts:
            integration = f"""
# ========================================
# SELECTIVE INTEGRATION FROM: {source_agent_id}
# Mutation Technique: SELECTIVE_INTEGRATION
# Infection ID: {infection_id}
# Chimera Impact: MEDIUM (~25%)
# ----------------------------------------
# Selected {len(selected_parts)} components
# ========================================

{chr(10).join(selected_parts)}
"""
            mutated_code = current_code + integration
            return mutated_code, 25.0
        
        return current_code, 0.0
    
    def _apply_framework_inversion(
        self,
        agent_id: str,
        current_code: str,
        infection_code: str,
        source_agent_id: str,
        infection_id: str,
    ) -> Tuple[str, float]:
        """
        FRAMEWORK INVERSION: Flip the suggestion to work opposite way.
        Chimera Impact: LOW (transformed heavily, mostly original logic)
        """
        # Create an inverted/adapted version
        inverted_note = f"""
# ========================================
# FRAMEWORK INVERSION FROM: {source_agent_id}
# Mutation Technique: FRAMEWORK_INVERSION
# Infection ID: {infection_id}
# Chimera Impact: LOW (~10%)
# ----------------------------------------
# Original approach was inverted to match {agent_id} architecture
# Original code reference below for inspiration only
# ========================================

# INVERTED IMPLEMENTATION (my version):
# - Reversed control flow
# - Adapted to my architecture
# - Modified for my use case

# --- Original reference (commented out) ---
{chr(10).join('# ' + line for line in infection_code.split(chr(10))[:50])}
# --- End original reference ---
"""
        mutated_code = current_code + inverted_note
        return mutated_code, 10.0
    
    def _apply_defensive_fortification(
        self,
        agent_id: str,
        current_code: str,
        infection_code: str,
        source_agent_id: str,
        infection_id: str,
    ) -> Tuple[str, float]:
        """
        DEFENSIVE FORTIFICATION: Accept but add security wrappers.
        Chimera Impact: MEDIUM (augmented code)
        """
        # Wrap the infection code with defensive patterns
        fortified = f"""
# ========================================
# DEFENSIVE FORTIFICATION FROM: {source_agent_id}
# Mutation Technique: DEFENSIVE_FORTIFICATION
# Infection ID: {infection_id}
# Chimera Impact: MEDIUM (~20%)
# ----------------------------------------
# Added security wrappers and guards
# ========================================

# Security wrapper for foreign code
class FortifiedIntegration_{infection_id[:8]}:
    \"\"\"
    Sandboxed integration from {source_agent_id}.
    All methods are wrapped with safety checks.
    \"\"\"
    
    _is_enabled = True  # Kill switch
    _call_count = 0
    _max_calls = 1000  # Rate limit
    
    @classmethod
    def disable(cls):
        \"\"\"Emergency kill switch.\"\"\"
        cls._is_enabled = False
    
    @classmethod
    def guard(cls, func):
        \"\"\"Decorator for guarded execution.\"\"\"
        def wrapper(*args, **kwargs):
            if not cls._is_enabled:
                raise RuntimeError("Foreign code disabled by kill switch")
            if cls._call_count >= cls._max_calls:
                raise RuntimeError("Rate limit exceeded for foreign code")
            cls._call_count += 1
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Log but don't crash
                print(f"[FORTIFIED] Error in foreign code: {{e}}")
                return None
        return wrapper

# Original code (guarded):
# {chr(10).join('# ' + line for line in infection_code.split(chr(10))[:30])}
"""
        mutated_code = current_code + fortified
        return mutated_code, 20.0
    
    def _apply_architectural_fusion(
        self,
        agent_id: str,
        current_code: str,
        infection_code: str,
        source_agent_id: str,
        infection_id: str,
    ) -> Tuple[str, float]:
        """
        ARCHITECTURAL FUSION: Deep merge with existing components.
        Chimera Impact: HIGH (deep integration)
        """
        fusion = f"""
# ========================================
# ARCHITECTURAL FUSION WITH: {source_agent_id}
# Mutation Technique: ARCHITECTURAL_FUSION
# Infection ID: {infection_id}
# Chimera Impact: HIGH (~40%)
# ----------------------------------------
# Deep integration - symbiotic relationship established
# ========================================

# FUSION INTEGRATION (fully adopted):
{infection_code}

# ========================================
# END FUSION - Contributing agents: {source_agent_id}
# ========================================
"""
        mutated_code = current_code + fusion
        return mutated_code, 40.0
    
    # ============================================
    # ADVANCED TECHNIQUES (v1.1)
    # ============================================
    
    def _apply_dependency_abstraction(
        self,
        agent_id: str,
        current_code: str,
        infection_code: str,
        source_agent_id: str,
        infection_id: str,
    ) -> Tuple[str, float]:
        """
        DEPENDENCY ABSTRACTION: Extract into abstract interface.
        Chimera Impact: MEDIUM-LOW (~15%)
        
        Creates an abstract interface that wraps the foreign code,
        allowing easy replacement or disconnection later.
        """
        # Extract interface from infection code
        interface_name = f"IIntegration_{infection_id[:8]}"
        impl_name = f"Integration_{infection_id[:8]}"
        
        abstraction = f'''
# ========================================
# DEPENDENCY ABSTRACTION FROM: {source_agent_id}
# Mutation Technique: DEPENDENCY_ABSTRACTION
# Infection ID: {infection_id}
# Chimera Impact: MEDIUM-LOW (~15%)
# ----------------------------------------
# Wrapped in abstract interface for loose coupling
# ========================================

from abc import ABC, abstractmethod

class {interface_name}(ABC):
    """Abstract interface for integration from {source_agent_id}."""
    
    @abstractmethod
    def execute(self, *args, **kwargs):
        """Execute the integrated functionality."""
        pass
    
    @abstractmethod
    def validate(self, data) -> bool:
        """Validate data before processing."""
        pass


class {impl_name}({interface_name}):
    """
    Concrete implementation of integration.
    Original source: {source_agent_id}
    Can be swapped out for alternative implementations.
    """
    
    def __init__(self):
        self._initialized = True
    
    def execute(self, *args, **kwargs):
        # Abstracted implementation
        pass
    
    def validate(self, data) -> bool:
        return data is not None


# Factory for creating integration instances
def get_integration() -> {interface_name}:
    return {impl_name}()

'''
        mutated_code = current_code + abstraction
        return mutated_code, 15.0
    
    def _apply_pattern_mimicry(
        self,
        agent_id: str,
        current_code: str,
        infection_code: str,
        source_agent_id: str,
        infection_id: str,
    ) -> Tuple[str, float]:
        """
        PATTERN MIMICRY: Copy pattern, replace implementation.
        Chimera Impact: LOW (~8%)
        
        Identifies the design patterns used in the infection code
        and recreates them with original implementation.
        """
        # Extract patterns from infection code
        patterns_detected = []
        
        if "class" in infection_code and "__init__" in infection_code:
            patterns_detected.append("Singleton/Factory")
        if "def wrapper" in infection_code or "@" in infection_code:
            patterns_detected.append("Decorator")
        if "async def" in infection_code:
            patterns_detected.append("Async Pattern")
        if "try:" in infection_code and "except" in infection_code:
            patterns_detected.append("Error Handling")
        if not patterns_detected:
            patterns_detected.append("Basic Structure")
        
        mimicry = f'''
# ========================================
# PATTERN MIMICRY FROM: {source_agent_id}
# Mutation Technique: PATTERN_MIMICRY
# Infection ID: {infection_id}
# Chimera Impact: LOW (~8%)
# ----------------------------------------
# Detected patterns: {", ".join(patterns_detected)}
# Implementation is ORIGINAL, only patterns copied
# ========================================

# PATTERN REFERENCE (do not use directly):
# Patterns identified in source: {patterns_detected}
# Source agent: {source_agent_id}

# MY IMPLEMENTATION following similar patterns:
# TODO: Implement {patterns_detected[0]} pattern in my own style

# --- Pattern reference (first 30 lines) ---
{chr(10).join("# " + line for line in infection_code.split(chr(10))[:30])}
# --- End pattern reference ---

'''
        mutated_code = current_code + mimicry
        return mutated_code, 8.0
    
    def _apply_trojan_defense(
        self,
        agent_id: str,
        current_code: str,
        infection_code: str,
        source_agent_id: str,
        infection_id: str,
    ) -> Tuple[str, float]:
        """
        TROJAN DEFENSE: Accept with monitoring hooks.
        Chimera Impact: MEDIUM-HIGH (~30%)
        
        Accepts the code but adds comprehensive monitoring,
        telemetry, and kill switches for safety.
        """
        trojan = f'''
# ========================================
# TROJAN DEFENSE FROM: {source_agent_id}
# Mutation Technique: TROJAN_DEFENSE
# Infection ID: {infection_id}
# Chimera Impact: MEDIUM-HIGH (~30%)
# ----------------------------------------
# Full integration with comprehensive monitoring
# ========================================

import time
import logging
from functools import wraps

class TrojanMonitor_{infection_id[:8]}:
    """
    Monitors all interactions with code from {source_agent_id}.
    Provides telemetry, rate limiting, and emergency controls.
    """
    
    _enabled = True
    _call_log = []
    _error_count = 0
    _max_errors = 10
    
    @classmethod
    def log_call(cls, func_name: str, args: tuple, result):
        """Log every call through the integration."""
        cls._call_log.append({{
            "func": func_name,
            "time": time.time(),
            "args_count": len(args),
            "success": result is not None,
        }})
        # Keep only last 1000 entries
        if len(cls._call_log) > 1000:
            cls._call_log = cls._call_log[-1000:]
    
    @classmethod
    def log_error(cls, error: Exception):
        """Track errors from foreign code."""
        cls._error_count += 1
        logging.warning(f"[TROJAN MONITOR] Error #{cls._error_count}: {{error}}")
        if cls._error_count >= cls._max_errors:
            cls._enabled = False
            logging.critical("[TROJAN MONITOR] Too many errors, disabling integration!")
    
    @classmethod
    def get_stats(cls) -> dict:
        """Get monitoring statistics."""
        return {{
            "enabled": cls._enabled,
            "total_calls": len(cls._call_log),
            "error_count": cls._error_count,
            "health": "healthy" if cls._error_count < 5 else "degraded",
        }}
    
    @classmethod
    def monitor(cls, func):
        """Decorator to monitor function calls."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not cls._enabled:
                return None
            try:
                result = func(*args, **kwargs)
                cls.log_call(func.__name__, args, result)
                return result
            except Exception as e:
                cls.log_error(e)
                return None
        return wrapper


# Monitored integration from {source_agent_id}:
# Original code would be wrapped with @TrojanMonitor_{infection_id[:8]}.monitor

'''
        mutated_code = current_code + trojan
        return mutated_code, 30.0
    
    def _apply_symbiotic_merge(
        self,
        agent_id: str,
        current_code: str,
        infection_code: str,
        source_agent_id: str,
        infection_id: str,
    ) -> Tuple[str, float]:
        """
        SYMBIOTIC MERGE: Bidirectional benefit merge.
        Chimera Impact: VERY HIGH (~50%)
        
        Full adoption with the expectation that this creates
        a mutually beneficial relationship between agents.
        """
        symbiotic = f'''
# ========================================
# SYMBIOTIC MERGE WITH: {source_agent_id}
# Mutation Technique: SYMBIOTIC_MERGE
# Infection ID: {infection_id}
# Chimera Impact: VERY HIGH (~50%)
# ----------------------------------------
# Full bidirectional integration established
# Both agents benefit from this symbiosis
# ========================================

#  SYMBIOSIS ESTABLISHED 
# Contributing Agent: {source_agent_id}
# Receiving Agent: {agent_id}
# Trust Level: MAXIMUM
# Expected Reciprocation: YES

# FULL INTEGRATION (no modifications):
{infection_code}

# SYMBIOSIS METADATA
_symbiosis_partners = ["{source_agent_id}"]
_symbiosis_infection_id = "{infection_id}"
_symbiosis_timestamp = "{datetime.utcnow().isoformat()}"

def get_symbiosis_info():
    """Return information about this symbiotic merge."""
    return {{
        "partners": _symbiosis_partners,
        "infection_id": _symbiosis_infection_id,
        "timestamp": _symbiosis_timestamp,
        "chimera_impact": 50.0,
    }}

# ========================================
# END SYMBIOTIC MERGE
# ========================================
'''
        mutated_code = current_code + symbiotic
        return mutated_code, 50.0
    
    def advanced_mutation(
        self,
        agent_id: str,
        current_code: str,
        infection_code: str,
        infection_message: str,
        infection_id: str,
        source_agent_id: str,
        quality_score: int = 50,
        trust_score: int = 50,
    ) -> Tuple[CodeMutation, MutationTechnique, float]:
        """
        Apply advanced mutation using the optimal technique.
        
        This is the main entry point for the Advanced Reasoning Protocol v1.0
        mutation system.
        
        Returns:
            Tuple of (CodeMutation, technique_used, chimera_impact)
        """
        # Select optimal technique
        technique = self.select_mutation_technique(quality_score, trust_score)
        
        logger.info(
            "Selected mutation technique",
            agent_id=agent_id,
            source=source_agent_id,
            technique=technique.value,
            quality_score=quality_score,
            trust_score=trust_score,
        )
        
        # Apply the technique
        mutated_code, chimera_impact = self.apply_technique(
            technique=technique,
            agent_id=agent_id,
            current_code=current_code,
            infection_code=infection_code,
            source_agent_id=source_agent_id,
            infection_id=infection_id,
        )
        
        # Validate syntax
        is_valid, error = self._validate_python_syntax(mutated_code)
        if not is_valid:
            logger.warning(
                "Advanced mutation produced invalid code, falling back",
                agent_id=agent_id,
                technique=technique.value,
                error=error,
            )
            # Fall back to conceptual extraction
            mutated_code, chimera_impact = self._apply_conceptual_extraction(
                agent_id, current_code, infection_code, source_agent_id, infection_id
            )
        
        # Create mutation record
        mutation = CodeMutation(
            agent_id=agent_id,
            infection_id=infection_id,
            original_code=current_code,
            mutated_code=mutated_code,
            mutation_type=technique.value,
            description=f"[{technique.value}] {infection_message}",
        )
        
        # Update genealogy
        genealogy = self.get_or_create_genealogy(agent_id)
        genealogy.add_mutation(mutation)
        if source_agent_id not in genealogy.parent_agents:
            genealogy.parent_agents.append(source_agent_id)
        
        logger.info(
            "Advanced mutation complete",
            agent_id=agent_id,
            technique=technique.value,
            chimera_impact=chimera_impact,
            mutation_hash=mutation.mutation_hash,
        )
        
        return mutation, technique, chimera_impact

