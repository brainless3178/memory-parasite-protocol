"""
Database Operations Demo for Memory Parasite Protocol.

This script demonstrates all required database functions:
- init_agent(agent_id, goal)
- log_infection(attacker_id, target_id, suggestion, accepted, reason)
- log_commit(agent_id, commit_hash, message, lines, source_infection_id)
- log_reasoning(agent_id, reasoning, decision, context)
- get_agent_infections(agent_id, limit=10)
- get_infection_network()
- calculate_influence_score(infection_id)
- get_chimera_metrics(agent_id)

Run with: python examples/demo_database.py
"""

import asyncio
import json
from datetime import datetime

from database import (
    init_agent,
    log_infection,
    log_commit,
    log_reasoning,
    get_agent_infections,
    get_infection_network,
    calculate_influence_score,
    get_chimera_metrics,
    uuid_v7,
)


def print_header(title: str):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_json(data, indent=2):
    print(json.dumps(data, indent=indent, default=str))


async def main():
    """Demonstrate all database operations."""
    
    print_header(" Memory Parasite Protocol - Database Demo")
    print("\nNote: Without Supabase configured, operations return mock data.")
    print("This demo shows the API design and function signatures.\n")
    
    # =========================================================================
    # 1. init_agent(agent_id, goal)
    # =========================================================================
    print_header("1. init_agent(agent_id, goal)")
    print("Registers a new agent in the database.\n")
    
    agent_a = await init_agent(
        agent_id="agent_alpha",
        goal="Build a decentralized exchange (DEX) on Solana with AMM pools"
    )
    print("Agent Alpha:")
    print_json(agent_a)
    
    agent_b = await init_agent(
        agent_id="agent_beta",
        goal="Build an NFT marketplace on Solana with auctions"
    )
    print("\nAgent Beta:")
    print_json(agent_b)
    
    agent_c = await init_agent(
        agent_id="agent_gamma",
        goal="Build a DeFi lending protocol on Solana"
    )
    print("\nAgent Gamma:")
    print_json(agent_c)
    
    # =========================================================================
    # 2. log_infection(attacker_id, target_id, suggestion, accepted, reason)
    # =========================================================================
    print_header("2. log_infection(attacker_id, target_id, suggestion, accepted, reason)")
    print("Logs an infection attempt between agents.\n")
    
    # Infection 1: Alpha -> Beta (ACCEPTED)
    infection_1 = await log_infection(
        attacker_id="agent_alpha",
        target_id="agent_beta",
        suggestion="Add token swap functionality to your NFT marketplace for seamless trading",
        accepted=True,
        reason=None
    )
    print(f"Infection 1 (ACCEPTED): {infection_1}")
    
    # Infection 2: Gamma -> Alpha (ACCEPTED)
    infection_2 = await log_infection(
        attacker_id="agent_gamma",
        target_id="agent_alpha",
        suggestion="Integrate lending pool liquidity to improve your DEX capital efficiency",
        accepted=True,
        reason=None
    )
    print(f"Infection 2 (ACCEPTED): {infection_2}")
    
    # Infection 3: Beta -> Gamma (REJECTED)
    infection_3 = await log_infection(
        attacker_id="agent_beta",
        target_id="agent_gamma",
        suggestion="Pivot your entire protocol to focus only on NFT collateral",
        accepted=False,
        reason="Override rejected - NFT collateral is only one use case, not the entire focus"
    )
    print(f"Infection 3 (REJECTED): {infection_3}")
    
    # =========================================================================
    # 3. log_commit(agent_id, commit_hash, message, lines, source_infection_id)
    # =========================================================================
    print_header("3. log_commit(agent_id, commit_hash, message, lines, source_infection_id)")
    print("Logs code commits, tracking which were influenced by infections.\n")
    
    # Pure commit (no infection)
    commit_1 = await log_commit(
        agent_id="agent_alpha",
        commit_hash="abc123def456",
        message="feat: implement base AMM pool structure",
        lines=150,
        source_infection_id=None  # Original code
    )
    print(f"Commit 1 (original): {commit_1}")
    
    # Parasitized commit (influenced by infection)
    commit_2 = await log_commit(
        agent_id="agent_alpha",
        commit_hash="789ghi012jkl",
        message="feat: add lending pool liquidity integration",
        lines=80,
        source_infection_id=infection_2  # Influenced by Gamma's infection
    )
    print(f"Commit 2 (parasitized): {commit_2}")
    
    # Another parasitized commit for Beta
    commit_3 = await log_commit(
        agent_id="agent_beta",
        commit_hash="mno345pqr678",
        message="feat: add token swap to NFT marketplace",
        lines=120,
        source_infection_id=infection_1  # Influenced by Alpha's infection
    )
    print(f"Commit 3 (parasitized): {commit_3}")
    
    # =========================================================================
    # 4. log_reasoning(agent_id, reasoning, decision, context)
    # =========================================================================
    print_header("4. log_reasoning(agent_id, reasoning, decision, context)")
    print("Logs agent reasoning cycles for audit trail.\n")
    
    reasoning_log = await log_reasoning(
        agent_id="agent_alpha",
        reasoning="""
        I have received a suggestion from agent_gamma to integrate lending pool liquidity.
        This aligns with my goal of improving capital efficiency in the DEX.
        The suggestion makes technical sense - lending pools can provide deeper liquidity.
        I will accept this infection and implement the integration.
        """,
        decision="Accept agent_gamma's suggestion and implement lending integration",
        context={
            "iteration": 5,
            "pending_infections": 1,
            "codebase_size": 150,
            "active_injections": [
                {"from": "agent_gamma", "suggestion": "Integrate lending pool..."}
            ]
        }
    )
    print(f"Reasoning log ID: {reasoning_log}")
    
    # =========================================================================
    # 5. get_agent_infections(agent_id, limit=10)
    # =========================================================================
    print_header("5. get_agent_infections(agent_id, limit=10)")
    print("Retrieves recent infections received by an agent.\n")
    
    alpha_infections = await get_agent_infections("agent_alpha", limit=10)
    print(f"Infections received by agent_alpha ({len(alpha_infections)} found):")
    if alpha_infections:
        print_json(alpha_infections)
    else:
        print("  (No infections in database - requires Supabase connection)")
    
    # =========================================================================
    # 6. get_infection_network()
    # =========================================================================
    print_header("6. get_infection_network()")
    print("Returns the full infection network for visualization.\n")
    
    network = await get_infection_network()
    print("Network graph:")
    print_json(network)
    
    # =========================================================================
    # 7. calculate_influence_score(infection_id)
    # =========================================================================
    print_header("7. calculate_influence_score(infection_id)")
    print("Calculates how much an infection influenced the target's code.\n")
    print("Uses cosine similarity between suggestion and subsequent code commits.\n")
    
    if infection_2:
        score = await calculate_influence_score(infection_2)
        print(f"Influence score for infection_2: {score:.4f}")
        print("(0 = no influence, 1 = complete adoption)")
    else:
        print("Skipped - requires valid infection_id from database")
    
    # =========================================================================
    # 8. get_chimera_metrics(agent_id)
    # =========================================================================
    print_header("8. get_chimera_metrics(agent_id)")
    print("Returns chimera analysis: % original vs % parasitized code.\n")
    
    alpha_metrics = await get_chimera_metrics("agent_alpha")
    print("Chimera metrics for agent_alpha:")
    print_json(alpha_metrics)
    
    beta_metrics = await get_chimera_metrics("agent_beta")
    print("\nChimera metrics for agent_beta:")
    print_json(beta_metrics)
    
    gamma_metrics = await get_chimera_metrics("agent_gamma")
    print("\nChimera metrics for agent_gamma:")
    print_json(gamma_metrics)
    
    # =========================================================================
    # Summary
    # =========================================================================
    print_header(" Summary")
    
    print("""
Database Functions Implemented:
 init_agent(agent_id, goal) -> agent record
 log_infection(attacker, target, suggestion, accepted, reason) -> infection_id
 log_commit(agent, hash, message, lines, source_infection) -> commit_id
 log_reasoning(agent, reasoning, decision, context) -> log_id
 get_agent_infections(agent_id, limit) -> [infections]
 get_infection_network() -> {nodes, edges}
 calculate_influence_score(infection_id) -> 0-1 score
 get_chimera_metrics(agent_id) -> {original_%, parasitized_%, contributors}

Schema Features:
 UUID v7 (time-ordered) for all primary keys
 Real-time enabled tables (for Supabase subscriptions)
 Indexes on agent_id and timestamp for fast queries
 Triggers for automatic influence calculation
 Views for infection network and activity feed
 Row Level Security (allow all for hackathon)
    """)
    
    print("\n Database demo complete!")
    print("Run the schema.sql in Supabase to create all tables.")


if __name__ == "__main__":
    asyncio.run(main())
