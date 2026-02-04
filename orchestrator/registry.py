"""
Agent Registry for Memory Parasite Protocol.

Provides agent discovery and URL management.
Each agent registers itself on startup and can discover other agents.
"""

import os
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import httpx
import structlog

logger = structlog.get_logger()


@dataclass
class AgentInfo:
    """Information about a registered agent."""
    agent_id: str
    goal: str
    url: str
    is_online: bool = False
    last_seen: Optional[datetime] = None
    cycles_completed: int = 0


# ============================================================================
# HARDCODED REGISTRY (Update URLs after Replit deployment)
# ============================================================================

AGENT_REGISTRY: Dict[str, Dict[str, str]] = {
    "agent_a": {
        "name": "DEX Builder",
        "goal": "Build a Solana DEX with optimal routing, AMM pools, and concentrated liquidity",
        "url": os.getenv("AGENT_A_URL", "http://localhost:5001"),
    },
    "agent_b": {
        "name": "NFT Marketplace",
        "goal": "Build an NFT marketplace with royalties, auctions, and collection management",
        "url": os.getenv("AGENT_B_URL", "http://localhost:5002"),
    },
    "agent_c": {
        "name": "Lending Protocol",
        "goal": "Build a lending protocol with flash loans, liquidations, and yield optimization",
        "url": os.getenv("AGENT_C_URL", "http://localhost:5003"),
    },
    "agent_d": {
        "name": "Privacy Wallet",
        "goal": "Build a privacy-focused wallet with stealth addresses and confidential transfers",
        "url": os.getenv("AGENT_D_URL", "http://localhost:5004"),
    },
    "agent_e": {
        "name": "DAO Governance",
        "goal": "Build a DAO governance system with proposals, voting, and treasury management",
        "url": os.getenv("AGENT_E_URL", "http://localhost:5005"),
    },
}


class AgentRegistry:
    """
    Registry for discovering and managing agents.
    
    Provides:
    - get_all_agents() - List all known agents
    - get_agent(agent_id) - Get specific agent info
    - get_targets_for(agent_id) - Get potential infection targets
    - check_health(agent_id) - Check if agent is online
    """
    
    def __init__(self):
        self.agents: Dict[str, AgentInfo] = {}
        self.http_client = httpx.AsyncClient(timeout=10.0)
        self._load_registry()
    
    def _load_registry(self):
        """Load agents from hardcoded registry."""
        for agent_id, info in AGENT_REGISTRY.items():
            self.agents[agent_id] = AgentInfo(
                agent_id=agent_id,
                goal=info["goal"],
                url=info["url"],
            )
        logger.info(f"Loaded {len(self.agents)} agents into registry")
    
    def get_all_agents(self) -> List[AgentInfo]:
        """Get all registered agents."""
        return list(self.agents.values())
    
    def get_agent(self, agent_id: str) -> Optional[AgentInfo]:
        """Get specific agent by ID."""
        return self.agents.get(agent_id)
    
    def get_agent_url(self, agent_id: str) -> Optional[str]:
        """Get URL for an agent."""
        agent = self.agents.get(agent_id)
        return agent.url if agent else None
    
    def get_targets_for(self, agent_id: str) -> List[AgentInfo]:
        """
        Get potential infection targets for an agent.
        Returns all agents except the requesting agent.
        """
        return [
            agent for agent in self.agents.values()
            if agent.agent_id != agent_id
        ]
    
    async def check_health(self, agent_id: str) -> bool:
        """Check if an agent is online by pinging its health endpoint."""
        agent = self.agents.get(agent_id)
        if not agent:
            return False
        
        try:
            response = await self.http_client.get(
                f"{agent.url}/health",
                timeout=5.0,
            )
            
            if response.status_code == 200:
                data = response.json()
                agent.is_online = True
                agent.last_seen = datetime.utcnow()
                agent.cycles_completed = data.get("cycles_completed", 0)
                return True
        except Exception as e:
            logger.debug(f"Health check failed for {agent_id}: {e}")
        
        agent.is_online = False
        return False
    
    async def check_all_health(self) -> Dict[str, bool]:
        """Check health of all agents."""
        results = {}
        for agent_id in self.agents:
            results[agent_id] = await self.check_health(agent_id)
        return results
    
    async def get_online_targets(self, agent_id: str) -> List[AgentInfo]:
        """Get only online agents as potential targets."""
        targets = self.get_targets_for(agent_id)
        
        online_targets = []
        for target in targets:
            is_online = await self.check_health(target.agent_id)
            if is_online:
                online_targets.append(target)
        
        return online_targets
    
    def register_agent(
        self,
        agent_id: str,
        goal: str,
        url: str,
    ) -> AgentInfo:
        """Register a new agent or update existing."""
        agent = AgentInfo(
            agent_id=agent_id,
            goal=goal,
            url=url,
            is_online=True,
            last_seen=datetime.utcnow(),
        )
        self.agents[agent_id] = agent
        logger.info(f"Registered agent: {agent_id} at {url}")
        return agent
    
    def get_registry_status(self) -> Dict[str, any]:
        """Get status of all agents in registry."""
        return {
            "total_agents": len(self.agents),
            "agents": {
                agent_id: {
                    "name": AGENT_REGISTRY.get(agent_id, {}).get("name", agent_id),
                    "goal": agent.goal[:50] + "...",
                    "url": agent.url,
                    "is_online": agent.is_online,
                    "last_seen": agent.last_seen.isoformat() if agent.last_seen else None,
                    "cycles": agent.cycles_completed,
                }
                for agent_id, agent in self.agents.items()
            },
        }
    
    async def close(self):
        """Close HTTP client."""
        await self.http_client.aclose()


# Singleton instance
_registry: Optional[AgentRegistry] = None


def get_registry() -> AgentRegistry:
    """Get the agent registry singleton."""
    global _registry
    if _registry is None:
        _registry = AgentRegistry()
    return _registry


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def get_all_agents() -> List[AgentInfo]:
    """Get all registered agents."""
    return get_registry().get_all_agents()


def get_agent_url(agent_id: str) -> Optional[str]:
    """Get URL for an agent."""
    return get_registry().get_agent_url(agent_id)


def get_targets_for(agent_id: str) -> List[AgentInfo]:
    """Get potential infection targets for an agent."""
    return get_registry().get_targets_for(agent_id)
