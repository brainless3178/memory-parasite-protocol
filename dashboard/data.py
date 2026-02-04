"""
Data fetching functions for the Memory Parasite Dashboard.

Provides real-time data access from Supabase with caching.
"""

import asyncio
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Any, Dict, List, Optional
import json
import structlog

logger = structlog.get_logger()

# Try to import Supabase client
try:
    import sys
    sys.path.insert(0, '..')
    from database import get_supabase_client
    HAS_DB = True
except ImportError:
    HAS_DB = False
    logger.warning("Database client not available - using mock data")


class DashboardData:
    """
    Data provider for the dashboard.
    
    Fetches from Supabase when available, falls back to mock data.
    """
    
    def __init__(self):
        self.db = get_supabase_client() if HAS_DB else None
        self._cache: Dict[str, Any] = {}
        self._cache_ttl = 30  # seconds
        self._cache_times: Dict[str, datetime] = {}
    
    def _is_cache_valid(self, key: str) -> bool:
        """Check if cached data is still valid."""
        if key not in self._cache_times:
            return False
        age = (datetime.utcnow() - self._cache_times[key]).total_seconds()
        return age < self._cache_ttl
    
    def _set_cache(self, key: str, data: Any):
        """Set cached data."""
        self._cache[key] = data
        self._cache_times[key] = datetime.utcnow()
    
    async def get_live_infections(
        self,
        limit: int = 50,
        agent_filter: Optional[List[str]] = None,
        result_filter: Optional[List[str]] = None,
        time_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get recent infections with agent details.
        
        Args:
            limit: Maximum number of infections to return
            agent_filter: Only show infections involving these agents
            result_filter: Only show infections with these results
            time_filter: "1h", "24h", or "all"
            
        Returns:
            List of infection dictionaries
        """
        cache_key = f"infections_{limit}_{agent_filter}_{result_filter}_{time_filter}"
        
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]
        
        if self.db:
            try:
                # Build query
                infections = await self.db.get_infection_network()
                # Process and filter
                # (In real implementation, add filtering logic)
                self._set_cache(cache_key, infections.get("edges", [])[:limit])
                return self._cache[cache_key]
            except Exception as e:
                logger.error(f"Failed to fetch infections: {e}")
        
        # Fall back to mock data
        return self._get_mock_infections(limit)
    
    async def get_network_graph_data(self) -> Dict[str, Any]:
        """
        Get nodes and edges for the network graph.
        
        Returns:
            {"nodes": [...], "edges": [...]}
        """
        if self._is_cache_valid("network"):
            return self._cache["network"]
        
        if self.db:
            try:
                data = await self.db.get_infection_network()
                self._set_cache("network", data)
                return data
            except Exception as e:
                logger.error(f"Failed to fetch network: {e}")
        
        return self._get_mock_network()
    
    async def get_agent_timeline(
        self,
        agent_id: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Get all commits for an agent, ordered by time.
        
        Args:
            agent_id: Agent to get commits for
            limit: Maximum commits to return
            
        Returns:
            List of commit dictionaries
        """
        # In real implementation, query code_commits table
        return self._get_mock_commits(agent_id)
    
    async def get_chimera_stats(
        self,
        agent_id: str,
    ) -> Dict[str, Any]:
        """
        Get chimera metrics for an agent.
        
        Returns:
            {
                "original_pct": float,
                "parasitized_pct": float,
                "contributors": [{"agent": str, "lines": int, "infections": int}]
            }
        """
        if self.db:
            try:
                metrics = await self.db.get_chimera_metrics(agent_id)
                return metrics
            except Exception as e:
                logger.error(f"Failed to fetch chimera stats: {e}")
        
        return self._get_mock_chimera(agent_id)
    
    async def get_all_agents(self) -> List[Dict[str, Any]]:
        """Get all agents with their current status."""
        if self._is_cache_valid("agents"):
            return self._cache["agents"]
        
        # In real implementation, query agents table
        agents = self._get_mock_agents()
        self._set_cache("agents", agents)
        return agents
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get overall statistics."""
        if self._is_cache_valid("stats"):
            return self._cache["stats"]
        
        stats = self._get_mock_stats()
        self._set_cache("stats", stats)
        return stats
    
    async def verify_infection(
        self,
        infection_hash: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Verify an infection against blockchain.
        
        Returns:
            {"db": {...}, "chain": {...}, "match": bool}
        """
        # In real implementation:
        # 1. Fetch from Supabase
        # 2. Fetch from Solana
        # 3. Compare
        return None
    
    # =========================================================================
    # MOCK DATA (for demo without database)
    # =========================================================================
    
    def _get_mock_infections(self, limit: int = 50) -> List[Dict[str, Any]]:
        base_time = datetime.utcnow()
        return [
            {
                "id": f"inf_{i:03d}",
                "attacker_id": ["agent_a", "agent_b", "agent_c", "agent_d", "agent_e"][i % 5],
                "target_id": ["agent_b", "agent_c", "agent_d", "agent_e", "agent_a"][i % 5],
                "suggestion": f"Suggestion {i}: Add feature X to improve your protocol",
                "result": ["accepted", "rejected", "mutated", "pending"][i % 4],
                "influence_score": (i % 10) / 10,
                "created_at": (base_time - timedelta(minutes=i * 15)).isoformat(),
            }
            for i in range(min(limit, 20))
        ]
    
    def _get_mock_network(self) -> Dict[str, Any]:
        return {
            "nodes": [
                {"id": "agent_a", "name": "DEX Builder", "code_lines": 2850},
                {"id": "agent_b", "name": "NFT Marketplace", "code_lines": 2100},
                {"id": "agent_c", "name": "Lending Protocol", "code_lines": 3400},
                {"id": "agent_d", "name": "Privacy Wallet", "code_lines": 1800},
                {"id": "agent_e", "name": "DAO Governance", "code_lines": 1950},
            ],
            "edges": [
                {"source": "agent_a", "target": "agent_b", "influence": 0.45},
                {"source": "agent_c", "target": "agent_a", "influence": 0.75},
                {"source": "agent_c", "target": "agent_b", "influence": 0.85},
                {"source": "agent_e", "target": "agent_c", "influence": 0.55},
            ],
        }
    
    def _get_mock_commits(self, agent_id: str) -> List[Dict[str, Any]]:
        base_time = datetime.utcnow()
        return [
            {
                "sha": f"abc{i}",
                "message": f"Commit {i}",
                "lines_added": 50 + i * 20,
                "timestamp": (base_time - timedelta(hours=i * 2)).isoformat(),
                "source": "original" if i % 2 == 0 else "parasitized",
            }
            for i in range(10)
        ]
    
    def _get_mock_chimera(self, agent_id: str) -> Dict[str, Any]:
        return {
            "original_pct": 65.0,
            "parasitized_pct": 35.0,
            "contributors": [
                {"agent": "agent_c", "lines": 200, "infections": 3},
                {"agent": "agent_e", "lines": 150, "infections": 2},
            ],
        }
    
    def _get_mock_agents(self) -> List[Dict[str, Any]]:
        return [
            {"agent_id": "agent_a", "name": "DEX Builder", "iteration": 18, "state": "idle", "provider": "Groq", "model": "Llama 3.3"},
            {"agent_id": "agent_b", "name": "NFT Marketplace", "iteration": 15, "state": "coding", "provider": "OpenRouter", "model": "Claude 3.5"},
            {"agent_id": "agent_c", "name": "Lending Protocol", "iteration": 22, "state": "infecting", "provider": "DeepSeek", "model": "DeepSeek-V3"},
            {"agent_id": "agent_d", "name": "Privacy Wallet", "iteration": 12, "state": "reasoning", "provider": "Gemini", "model": "Gemini 1.5 Pro"},
            {"agent_id": "agent_e", "name": "DAO Governance", "iteration": 14, "state": "idle", "provider": "OpenRouter", "model": "GPT-4o"},
        ]
    
    def _get_mock_stats(self) -> Dict[str, Any]:
        return {
            "total_agents": 5,
            "total_infections": 112,
            "total_code_lines": 12100,
            "success_rate": 0.34,
        }


# Singleton
_data_provider: Optional[DashboardData] = None


def get_data_provider() -> DashboardData:
    """Get dashboard data provider singleton."""
    global _data_provider
    if _data_provider is None:
        _data_provider = DashboardData()
    return _data_provider


# Convenience functions
async def get_live_infections(limit: int = 50, **kwargs) -> List[Dict]:
    return await get_data_provider().get_live_infections(limit, **kwargs)


async def get_network_graph_data() -> Dict[str, Any]:
    return await get_data_provider().get_network_graph_data()


async def get_agent_timeline(agent_id: str) -> List[Dict]:
    return await get_data_provider().get_agent_timeline(agent_id)


async def get_chimera_stats(agent_id: str) -> Dict[str, Any]:
    return await get_data_provider().get_chimera_stats(agent_id)
