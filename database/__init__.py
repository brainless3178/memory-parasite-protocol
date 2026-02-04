"""Database module for Memory Parasite Protocol."""
from database.models import (
    uuid_v7,
    AgentRecord,
    InfectionRecord,
    CodeCommitRecord,
    ReasoningLogRecord,
    NetworkSnapshotRecord,
    ChimeraMetrics,
)
from database.client import (
    SupabaseClient,
    get_supabase_client,
    # Convenience functions (matching exact specification)
    init_agent,
    log_infection,
    log_commit,
    log_reasoning,
    get_agent_infections,
    get_infection_network,
    calculate_influence_score,
    get_chimera_metrics,
)

__all__ = [
    # UUID v7
    "uuid_v7",
    # Models
    "AgentRecord",
    "InfectionRecord",
    "CodeCommitRecord",
    "ReasoningLogRecord",
    "NetworkSnapshotRecord",
    "ChimeraMetrics",
    # Client
    "SupabaseClient",
    "get_supabase_client",
    # Convenience functions
    "init_agent",
    "log_infection",
    "log_commit",
    "log_reasoning",
    "get_agent_infections",
    "get_infection_network",
    "calculate_influence_score",
    "get_chimera_metrics",
]
