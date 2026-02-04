"""Orchestrator module for Memory Parasite Protocol."""
from orchestrator.main import Orchestrator, run_orchestrator, AGENT_CONFIGS
from orchestrator.registry import (
    AgentRegistry,
    AgentInfo,
    get_registry,
    get_all_agents,
    get_agent_url,
    get_targets_for,
    AGENT_REGISTRY,
)
from orchestrator.github_client import GitHubClient, get_github_client

__all__ = [
    # Main orchestrator
    "Orchestrator",
    "run_orchestrator",
    "AGENT_CONFIGS",
    # Registry
    "AgentRegistry",
    "AgentInfo",
    "get_registry",
    "get_all_agents",
    "get_agent_url",
    "get_targets_for",
    "AGENT_REGISTRY",
    # GitHub
    "GitHubClient",
    "get_github_client",
]
