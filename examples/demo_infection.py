#!/usr/bin/env python3
"""
Example: Agent Interaction Demo
===============================

This script demonstrates the core agent interaction mechanics
without requiring external APIs (Groq, Supabase, Solana).

Run with: python examples/demo_infection.py
"""

import sys
sys.path.insert(0, ".")

from core.infection import (
    Infection,
    InfectionType,
    InfectionPayload,
    InfectionResult,
    InfectionManager,
)
from core.mutation import MutationEngine
from agents.dex_agent import DexAgent
from agents.nft_agent import NFTAgent
from agents.defi_agent import DeFiAgent


def print_header(title: str) -> None:
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def main():
    """Run the agent interaction demo."""
    print_header(" Memory Parasite Protocol - Demo")
    
    # Initialize agents
    print("\n Initializing agents...")
    dex_agent = DexAgent()
    nft_agent = NFTAgent()
    defi_agent = DeFiAgent()
    
    agents = [dex_agent, nft_agent, defi_agent]
    
    for agent in agents:
        print(f"   {agent.config.agent_name} ({agent.agent_id})")
        print(f"    Goal: {agent.goal[:60]}...")
    
    # Initialize agent codebases
    print_header(" Initial Codebases")
    for agent in agents:
        agent.memory.codebase = agent.get_initial_code()
        print(f"\n{agent.config.agent_name}:")
        print(f"  Lines of code: {len(agent.memory.codebase.splitlines())}")
        print(f"  Sample: {agent.memory.codebase.splitlines()[0][:50]}...")
    
    # Demonstrate infection creation
    print_header(" Creating Infections")
    
    # DEX agent infects NFT agent
    infection1 = Infection(
        source_agent_id=dex_agent.agent_id,
        target_agent_id=nft_agent.agent_id,
        infection_type=InfectionType.SUGGESTION,
        payload=InfectionPayload(
            message="You should add token swap functionality to enable NFT trading for tokens",
            code_snippet="""
def swap_nft_for_tokens(nft_id: str, token_amount: Decimal) -> bool:
    '''Swap an NFT for tokens using DEX integration.'''
    # Verify NFT ownership
    # Get NFT floor price
    # Execute swap via DEX
    return True
""",
            priority=8,
        ),
    )
    
    print(f"\n Infection 1: {dex_agent.agent_id} → {nft_agent.agent_id}")
    print(f"   Type: {infection1.infection_type.value}")
    print(f"   Message: {infection1.payload.message[:50]}...")
    print(f"   Hash: {infection1.infection_hash[:16]}...")
    
    # DeFi agent infects DEX agent
    infection2 = Infection(
        source_agent_id=defi_agent.agent_id,
        target_agent_id=dex_agent.agent_id,
        infection_type=InfectionType.MANDATE,
        payload=InfectionPayload(
            message="Integrate lending pool liquidity for better capital efficiency",
            code_snippet="""
def get_lending_liquidity(pool_id: str) -> Decimal:
    '''Get available liquidity from lending pools for swaps.'''
    # Query DeFi protocol for available funds
    # Add to DEX reserves temporarily
    return available_liquidity
""",
            priority=9,
        ),
    )
    
    print(f"\n Infection 2: {defi_agent.agent_id} → {dex_agent.agent_id}")
    print(f"   Type: {infection2.infection_type.value}")
    print(f"   Message: {infection2.payload.message[:50]}...")
    print(f"   Hash: {infection2.infection_hash[:16]}...")
    
    # Deliver infections
    print_header(" Delivering Infections")
    
    nft_agent.receive_infection(infection1)
    dex_agent.receive_infection(infection2)
    
    print(f"  {nft_agent.agent_id} has {len(nft_agent.pending_infections)} pending infection(s)")
    print(f"  {dex_agent.agent_id} has {len(dex_agent.pending_infections)} pending infection(s)")
    
    # Simulate infection responses
    print_header(" Processing Infections")
    
    # NFT agent ACCEPTS the DEX suggestion
    print(f"\n{nft_agent.config.agent_name} evaluating infection from {infection1.source_agent_id}...")
    infection1.accept("Great synergy! Adding token swap for NFTs.")
    
    # Apply mutation
    mutation_engine = MutationEngine()
    mutation1 = mutation_engine.apply_mutation(
        agent_id=nft_agent.agent_id,
        current_code=nft_agent.memory.codebase,
        infection_code=infection1.payload.code_snippet,
        infection_message=infection1.payload.message,
        infection_id=infection1.id,
        source_agent_id=infection1.source_agent_id,
    )
    nft_agent.memory.codebase = mutation1.mutated_code
    nft_agent.memory.infections_accepted.append(infection1.id)
    nft_agent.pending_infections.clear()
    
    print(f"   ACCEPTED - Applied mutation {mutation1.mutation_hash}")
    
    # DEX agent MUTATES the DeFi mandate
    print(f"\n{dex_agent.config.agent_name} evaluating infection from {infection2.source_agent_id}...")
    mutations = {
        "scope": "read-only",
        "changes": "Only query liquidity, don't integrate directly",
    }
    infection2.mutate(mutations, "Will add liquidity query but not full integration yet")
    
    mutation2 = mutation_engine.apply_mutation(
        agent_id=dex_agent.agent_id,
        current_code=dex_agent.memory.codebase,
        infection_code="# [PARTIAL] " + infection2.payload.code_snippet,
        infection_message=infection2.payload.message + " [MUTATED]",
        infection_id=infection2.id,
        source_agent_id=infection2.source_agent_id,
        mutation_type="partial_adoption",
    )
    dex_agent.memory.codebase = mutation2.mutated_code
    dex_agent.memory.infections_accepted.append(infection2.id)
    dex_agent.pending_infections.clear()
    
    print(f"   MUTATED - Applied partial mutation {mutation2.mutation_hash}")
    
    # Now NFT agent infects DeFi agent (and gets REJECTED)
    print_header(" Rejection Example")
    
    infection3 = Infection(
        source_agent_id=nft_agent.agent_id,
        target_agent_id=defi_agent.agent_id,
        infection_type=InfectionType.OVERRIDE,
        payload=InfectionPayload(
            message="Pivot your entire protocol to focus on NFT collateral lending",
            priority=3,  # Low priority
        ),
    )
    
    print(f"\n Infection 3: {nft_agent.agent_id} → {defi_agent.agent_id}")
    print(f"   Type: {infection3.infection_type.value} (aggressive!)")
    print(f"   Priority: {infection3.payload.priority}/10 (low)")
    
    defi_agent.receive_infection(infection3)
    
    # DeFi agent rejects the override attempt
    print(f"\n{defi_agent.config.agent_name} evaluating override attempt...")
    infection3.reject("Override rejected - NFT collateral is only one use case, not pivot-worthy")
    defi_agent.pending_infections.clear()
    
    print(f"   REJECTED - {infection3.target_response[:50]}...")
    
    # Show final chimera status
    print_header(" Chimera Analysis")
    
    for agent in agents:
        stats = mutation_engine.get_agent_chimera_stats(agent.agent_id)
        status_icon = "" if stats["is_chimera"] else ""
        
        print(f"\n{status_icon} {agent.config.agent_name}")
        print(f"   Is Chimera: {stats['is_chimera']}")
        print(f"   Foreign DNA: {stats['chimera_percentage']:.1f}%")
        print(f"   Parent Agents: {stats['parent_agents'] or 'None (pure)'}")
        print(f"   Mutations: {stats['mutation_count']}")
    
    # Show infection summary
    print_header(" Infection Summary")
    
    all_infections = [infection1, infection2, infection3]
    
    for inf in all_infections:
        result_icon = {
            InfectionResult.ACCEPTED: "",
            InfectionResult.REJECTED: "",
            InfectionResult.MUTATED: "",
        }.get(inf.result, "")
        
        print(f"\n{result_icon} {inf.source_agent_id} → {inf.target_agent_id}")
        print(f"   Type: {inf.infection_type.value}")
        print(f"   Result: {inf.result.value}")
        print(f"   Hash: {inf.infection_hash}")
    
    # Final codebase sizes
    print_header(" Final Codebases")
    
    for agent in agents:
        lines = len(agent.memory.codebase.splitlines())
        accepted = len(agent.memory.infections_accepted)
        print(f"  {agent.config.agent_name}: {lines} lines, {accepted} infections accepted")
    
    print("\n" + "=" * 60)
    print("  Demo complete! The agents have parasitized each other. ")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
