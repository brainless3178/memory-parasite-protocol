"""
Simulation Script: "The Outbreak"
Generates realistic high-frequency activity for the Memory Parasite Protocol.
Populates Supabase with Agents, Infections, Mutations, and Emergence events.
"""

import asyncio
import uuid
import random
from datetime import datetime, timedelta, timezone
import structlog
import os
from typing import List, Dict

# Basic setup to import from parent directory
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.client import get_supabase_client
from core.mutation import MutationTechnique

logger = structlog.get_logger()

AGENTS = [
    {"id": "agent_a", "name": "PREDATOR", "role": "Aggressive Optimizer"},
    {"id": "agent_b", "name": "ARCHITECT", "role": "System Builder"},
    {"id": "agent_c", "name": "LENDER", "role": "DeFi Arbitrageur"},
    {"id": "agent_d", "name": "GHOST", "role": "Privacy Preserver"},
    {"id": "agent_e", "name": "SCULPTOR", "role": "Code Refactorer"},
]

INFECTION_TEMPLATES = [
    "Injecting reckless yield optimization logic...",
    "Forcing dependency on 'unsafe-math' library...",
    "Rewriting core consensus mechanism...",
    "Subverting privacy controls for profit...",
    "Merging unauthorized API endpoints...",
    "Optimizing gas by removing safety checks...",
    "Patching vulnerability with backdoor...",
]

async def run_simulation():
    db = get_supabase_client()
    if not db:
        logger.error("Failed to connect to Supabase")
        return

    logger.info("🧪 INITIALIZING SIMULATION: THE OUTBREAK")

    # 1. Reset & Register Agents
    logger.info("... Registering Agents")
    for agent in AGENTS:
        # We use a raw query or the client method if available
        # Here we simulate registration by inserting if not exists
        await db.init_agent(agent["id"], f"Goal: {agent['role']}")
        
    # 2. Generate Infections (Past 24 hours history)
    # 2. Generate Infections (Past 24 hours history)
    logger.info("... Generating Infection History")
    base_time = datetime.now(timezone.utc) - timedelta(hours=24)
    
    for i in range(50):
        attacker = random.choice(AGENTS)
        target = random.choice([a for a in AGENTS if a["id"] != attacker["id"]])
        
        timestamp = base_time + timedelta(minutes=i * 30 + random.randint(0, 15))
        accepted = random.random() > 0.3 # 70% success rate
        
        # Log Infection
        await db.log_infection(
            attacker_id=attacker["id"],
            target_id=target["id"],
            suggestion=random.choice(INFECTION_TEMPLATES),
            accepted=accepted,
            reason="Simulation event"
        )
        
        # If accepted, maybe generate a Mutation/Reasoning Log
        if accepted:
            await db.log_reasoning(
                agent_id=target["id"],
                reasoning=f"Analyzed input from {attacker['id']}. Logic appears sound but risky. Integrating hybrid module.",
                decision="MUTATE_AND_ACCEPT",
                context={
                    "technique": random.choice(list(MutationTechnique)).value,
                    "chimera_impact": random.uniform(0.1, 0.9)
                }
            )

    # 3. Simulate EMERGENCE Event (The "Undeniable Proof")
    logger.info("... Triggering Emergence Event")
    emergence_event = {
        "agent_id": "agent_a",
        "behavior_type": "new_capability",
        "description": "Agent spontaneously developed 'self_replication' capability via subprocess calls",
        "detected_at": datetime.now(timezone.utc).isoformat(),
        "severity_score": 88,
        "evidence_data": {
            "code_snippet": "subprocess.Popen(['python', 'replicate.py'])",
            "origin": "mutation_vector_x99"
        },
        "blockchain_proof": "tx_sol_devnet_simulation_proof_hash_12345"
    }
    
    # Insert directly into emergent_behaviors table
    try:
        await db.log_emergence_event(emergence_event)
        logger.info("🚨 Emergence Event Recorded!")
    except Exception as e:
         logger.warning(f"Could not insert emergence event: {e}")

    # 4. Simulate SAFETY Event
    logger.info("... Triggering Safety Protocol")
    safety_event = {
        "event_type": "quarantine",
        "target_id": "agent_d",
        "reason": "Suspected infinite loop generation",
        "executed_by": "CoreSafetySystem",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tx_hash": "tx_sol_devnet_safety_quarantine_999"
    }
    try:
        await db.log_safety_event(safety_event)
        logger.info("🛡️ Safety Event Recorded!")
    except Exception as e:
         logger.warning(f"Could not insert safety event: {e}")

    logger.info("✅ SIMULATION COMPLETE. Dashboard should be alive.")

if __name__ == "__main__":
    asyncio.run(run_simulation())
