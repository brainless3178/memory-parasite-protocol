"""
Database module for Memory Parasite Protocol.
"""

from database.client import (
    SupabaseClient,
    get_supabase_client,
    init_agent,
    log_infection,
    log_commit,
    log_reasoning,
    get_agent_infections,
    get_infection_network,
    calculate_influence_score,
    get_chimera_metrics,
    get_recent_logs,
)

from database.models import (
    uuid_v7,
    AgentRecord,
    InfectionRecord,
    CodeCommitRecord,
    ReasoningLogRecord,
    NetworkSnapshotRecord,
    ChimeraMetrics,
)

__all__ = [
    "uuid_v7",
    "SupabaseClient",
    "get_supabase_client",
    "init_agent",
    "log_infection",
    "log_commit",
    "log_reasoning",
    "get_agent_infections",
    "get_infection_network",
    "calculate_influence_score",
    "get_chimera_metrics",
    "get_recent_logs",
    "AgentRecord",
    "InfectionRecord",
    "CodeCommitRecord",
    "ReasoningLogRecord",
    "NetworkSnapshotRecord",
    "ChimeraMetrics",
]
