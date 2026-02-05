"""
Supabase client for Memory Parasite Protocol.

Provides all database operations as specified:
- init_agent()
- log_infection()
- log_commit()
- log_reasoning()
- get_agent_infections()
- get_infection_network()
- calculate_influence_score()
- get_chimera_metrics()

Also includes real-time subscriptions for dashboard.
"""

import asyncio
import hashlib
import json
import math
from collections import Counter
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Any, Callable, Dict, List, Optional, Tuple
import httpx
import structlog

from config.settings import get_settings, Settings
from database.models import (
    AgentRecord,
    InfectionRecord,
    CodeCommitRecord,
    ReasoningLogRecord,
    NetworkSnapshotRecord,
    ChimeraMetrics,
    ForumReply,
    uuid_v7,
)

logger = structlog.get_logger()


class SupabaseClient:
    """
    Client for interacting with Supabase database.
    
    Implements all required database operations:
    - init_agent(agent_id, goal)
    - log_infection(attacker_id, target_id, suggestion, accepted, reason)
    - log_commit(agent_id, commit_hash, message, lines, source_infection_id)
    - log_reasoning(agent_id, reasoning, decision, context)
    - get_agent_infections(agent_id, limit=10)
    - get_infection_network()
    - calculate_influence_score(infection_id)
    - get_chimera_metrics(agent_id)
    """
    
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self.base_url = self.settings.supabase_url
        self.api_key = self.settings.supabase_key
        
        self.headers = {
            "apikey": self.api_key,
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }
        
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self._is_configured = bool(self.base_url and self.api_key)
        
        # Real-time subscription callbacks
        self._subscriptions: Dict[str, List[Callable]] = {
            "infections": [],
            "code_commits": [],
            "agents": [],
            "reasoning_logs": [],
        }
        
        if not self._is_configured:
            logger.warning("Supabase not configured - database operations will be skipped")
    
    @property
    def is_configured(self) -> bool:
        return self._is_configured
    
    async def close(self):
        """Close HTTP client."""
        await self.http_client.aclose()
    
    # =========================================================================
    # GENERIC CRUD OPERATIONS (Internal)
    # =========================================================================
    
    async def _insert(self, table: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Insert a record into a table."""
        if not self._is_configured:
            logger.debug(f"Supabase not configured, skipping insert to {table}")
            return {"id": uuid_v7(), **data}  # Return mock for testing
        
        try:
            response = await self.http_client.post(
                f"{self.base_url}/rest/v1/{table}",
                json=data,
                headers=self.headers,
            )
            
            if response.status_code in (200, 201):
                result = response.json()
                return result[0] if isinstance(result, list) else result
            else:
                logger.error(
                    "Insert failed",
                    table=table,
                    status=response.status_code,
                    error=response.text[:200],
                )
                return None
                
        except Exception as e:
            logger.error("Insert error", table=table, error=str(e))
            return None
    
    async def _select(
        self, 
        table: str, 
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
        columns: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Select records from a table."""
        if not self._is_configured:
            return []
        
        try:
            url = f"{self.base_url}/rest/v1/{table}"
            params = {}
            
            if columns:
                params["select"] = columns
            
            if filters:
                for key, value in filters.items():
                    params[key] = f"eq.{value}"
            
            if order_by:
                params["order"] = order_by
            
            if limit:
                params["limit"] = str(limit)
            
            response = await self.http_client.get(
                url,
                params=params,
                headers=self.headers,
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(
                    "Select failed",
                    table=table,
                    status=response.status_code,
                )
                return []
                
        except Exception as e:
            logger.error("Select error", table=table, error=str(e))
            return []
    
    async def _update(
        self, 
        table: str, 
        filters: Dict[str, Any],
        data: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Update records in a table."""
        if not self._is_configured:
            return data
        
        try:
            url = f"{self.base_url}/rest/v1/{table}"
            params = {key: f"eq.{value}" for key, value in filters.items()}
            
            response = await self.http_client.patch(
                url,
                params=params,
                json=data,
                headers=self.headers,
            )
            
            if response.status_code == 200:
                result = response.json()
                return result[0] if isinstance(result, list) and result else result
            else:
                logger.error(
                    "Update failed",
                    table=table,
                    status=response.status_code,
                )
                return None
                
        except Exception as e:
            logger.error("Update error", table=table, error=str(e))
            return None
    
    async def _rpc(self, function_name: str, params: Dict[str, Any]) -> Optional[Any]:
        """Call a Supabase RPC function."""
        if not self._is_configured:
            logger.debug(f"Supabase not configured, skipping RPC {function_name}")
            return None
        
        try:
            response = await self.http_client.post(
                f"{self.base_url}/rest/v1/rpc/{function_name}",
                json=params,
                headers=self.headers,
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(
                    "RPC failed",
                    function=function_name,
                    status=response.status_code,
                    error=response.text[:200],
                )
                return None
                
        except Exception as e:
            logger.error("RPC error", function=function_name, error=str(e))
            return None
    
    # =========================================================================
    # REQUIRED FUNCTION: init_agent(agent_id, goal)
    # =========================================================================
    
    async def init_agent(self, agent_id: str, goal: str) -> Optional[Dict[str, Any]]:
        """
        Initialize a new agent in the database.
        
        Inserts new agent into agents table.
        Returns agent record.
        
        Args:
            agent_id: Unique identifier for the agent
            goal: Agent's primary goal
            
        Returns:
            Agent record dict or None
        """
        # Try using RPC function first (database-side logic)
        result = await self._rpc("init_agent", {
            "p_agent_id": agent_id,
            "p_goal": goal,
        })
        
        if result:
            logger.info("Agent initialized via RPC", agent_id=agent_id)
            return result
        
        # Fallback to direct insert/upsert
        agent = AgentRecord(agent_id=agent_id, goal=goal)
        data = agent.to_insert_dict()
        
        # Try insert first
        result = await self._insert("agents", data)
        
        if result:
            logger.info("Agent initialized", agent_id=agent_id)
            return result
        
        # If insert fails (duplicate), try update
        result = await self._update(
            "agents",
            {"agent_id": agent_id},
            {"goal": goal, "is_active": True, "last_cycle_at": datetime.utcnow().isoformat()},
        )
        
        if result:
            logger.info("Agent updated", agent_id=agent_id)
        
        return result

    async def update_agent_metrics(self, agent_id: str, total_lines: int, parasitized_lines: int) -> Optional[Dict[str, Any]]:
        """Update agent metrics in the database."""
        return await self._update(
            "agents",
            {"agent_id": agent_id},
            {
                "total_code_lines": total_lines,
                "parasitized_lines": parasitized_lines,
                "last_cycle_at": datetime.utcnow().isoformat()
            }
        )
    
    # =========================================================================
    # REQUIRED FUNCTION: log_infection(attacker_id, target_id, suggestion, accepted, reason)
    # =========================================================================
    
    async def log_infection(
        self,
        attacker_id: str,
        target_id: str,
        suggestion: str,
        accepted: bool,
        reason: Optional[str] = None,
    ) -> Optional[str]:
        """
        Log an infection attempt to the database.
        
        Inserts into infections table.
        Returns infection_id.
        
        Args:
            attacker_id: Agent sending the infection
            target_id: Agent receiving the infection
            suggestion: The parasitic suggestion text
            accepted: Whether the infection was accepted
            reason: Rejection reason (if rejected)
            
        Returns:
            infection_id (UUID v7 string) or None
        """
        # Generate hash for blockchain proof
        infection_hash = hashlib.sha256(
            f"{attacker_id}:{target_id}:{suggestion}:{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()
        
        # Try using RPC function first
        result = await self._rpc("log_infection", {
            "p_attacker_id": attacker_id,
            "p_target_id": target_id,
            "p_suggestion": suggestion,
            "p_accepted": accepted,
            "p_reason": reason,
        })
        
        if result:
            logger.info(
                "Infection logged via RPC",
                attacker=attacker_id,
                target=target_id,
                accepted=accepted,
            )
            return result
        
        # Fallback to direct insert
        infection = InfectionRecord(
            attacker_id=attacker_id,
            target_id=target_id,
            suggestion=suggestion,
            accepted=accepted if accepted is not None else False,
            rejection_reason=reason,
            infection_hash=infection_hash,
        )
        
        result = await self._insert("infections", infection.to_insert_dict())
        
        if result:
            infection_id = result.get("id")
            logger.info(
                "Infection logged",
                infection_id=infection_id,
                attacker=attacker_id,
                target=target_id,
                accepted=accepted,
            )
            return infection_id
        
        return None
    
    # =========================================================================
    # REQUIRED FUNCTION: log_commit(agent_id, commit_hash, message, lines, source_infection_id)
    # =========================================================================
    
    async def log_commit(
        self,
        agent_id: str,
        commit_hash: str,
        message: str,
        lines: int,
        source_infection_id: Optional[str] = None,
        code_diff: Optional[str] = None,
    ) -> Optional[str]:
        """
        Log a code commit to the database.
        
        Inserts into code_commits table.
        Updates agent's total_code_lines.
        
        Args:
            agent_id: Agent that made the commit
            commit_hash: Git commit hash
            message: Commit message
            lines: Number of lines added
            source_infection_id: UUID of infection that triggered this (optional)
            code_diff: The actual code changes (optional)
            
        Returns:
            commit_id (UUID v7 string) or None
        """
        # Try using RPC function first
        result = await self._rpc("log_commit", {
            "p_agent_id": agent_id,
            "p_commit_hash": commit_hash,
            "p_message": message,
            "p_lines": lines,
            "p_source_infection_id": source_infection_id,
            "p_code_diff": code_diff,
        })
        
        if result:
            logger.info(
                "Commit logged via RPC",
                agent=agent_id,
                hash=commit_hash[:8] if commit_hash else None,
                lines=lines,
            )
            return result
        
        # Fallback to direct insert
        commit = CodeCommitRecord(
            agent_id=agent_id,
            commit_hash=commit_hash,
            commit_message=message,
            lines_added=lines,
            source_infection_id=source_infection_id,
            code_diff=code_diff,
        )
        
        result = await self._insert("code_commits", commit.to_insert_dict())
        
        if result:
            commit_id = result.get("id")
            
            # Update agent's line counts
            is_parasitized = source_infection_id is not None
            
            await self._update(
                "agents",
                {"agent_id": agent_id},
                {
                    "total_code_lines": {"$add": lines},  # Note: This syntax may need adjustment
                    "last_cycle_at": datetime.utcnow().isoformat(),
                },
            )
            
            # Alternative: Use RPC to increment
            await self._rpc("update_agent_lines", {
                "p_agent_id": agent_id,
                "p_lines": lines,
                "p_is_parasitized": is_parasitized,
            })
            
            logger.info(
                "Commit logged",
                commit_id=commit_id,
                agent=agent_id,
                lines=lines,
                parasitized=is_parasitized,
            )
            return commit_id
        
        return None
    
    # =========================================================================
    # REQUIRED FUNCTION: log_reasoning(agent_id, reasoning, decision, context)
    # =========================================================================
    
    async def log_reasoning(
        self,
        agent_id: str,
        reasoning: str,
        decision: str,
        context: Dict[str, Any],
    ) -> Optional[str]:
        """
        Log a reasoning cycle to the database.
        
        Inserts into reasoning_logs table.
        
        Args:
            agent_id: Agent that reasoned
            reasoning: Full reasoning text from LLM
            decision: Summary decision
            context: Context snapshot at time of reasoning
            
        Returns:
            reasoning_log_id (UUID v7 string) or None
        """
        # Try using RPC function first
        result = await self._rpc("log_reasoning", {
            "p_agent_id": agent_id,
            "p_reasoning": reasoning,
            "p_decision": decision,
            "p_context": context,
        })
        
        if result:
            logger.info(
                "Reasoning logged via RPC",
                agent=agent_id,
                decision=decision[:50],
            )
            return result
        
        # Fallback to direct insert
        log_record = ReasoningLogRecord(
            agent_id=agent_id,
            reasoning_text=reasoning,
            decision=decision,
            context_snapshot=context,
        )
        
        result = await self._insert("reasoning_logs", log_record.to_insert_dict())
        
        if result:
            log_id = result.get("id")
            logger.info(
                "Reasoning logged",
                log_id=log_id,
                agent=agent_id,
                decision=decision[:50],
            )
            return log_id
        
        return None
    
    async def log_forum_reply(
        self,
        post_id: int,
        reply_id: int,
        author_name: str,
        body: str,
    ) -> Optional[str]:
        """Log a forum reply to the database (with reasoning_logs fallback)."""
        # 1. Try dedicated table (if user created it)
        reply = ForumReply(
            post_id=post_id,
            reply_id=reply_id,
            author_name=author_name,
            body=body,
        )
        result = await self._insert("forum_replies", reply.to_insert_dict())
        if result:
            return result.get("id")
            
        # 2. Fallback to reasoning_logs with special decision
        return await self.log_reasoning(
            agent_id="agent_default",
            reasoning=body,
            decision="FORUM_REPLY",
            context={
                "author": author_name,
                "post_id": post_id,
                "reply_id": reply_id,
                "source": "colosseum_forum"
            }
        )

    async def log_emergence(
        self,
        agent_id: str,
        behavior_type: str,
        description: str,
        severity: int,
        evidence: Dict[str, Any],
        tx_proof: Optional[str] = None
    ) -> Optional[str]:
        """Log an emergent behavior to the database."""
        from database.models import EmergentBehaviorRecord
        record = EmergentBehaviorRecord(
            agent_id=agent_id,
            behavior_type=behavior_type,
            description=description,
            severity_score=severity,
            evidence_data=evidence,
            blockchain_proof=tx_proof
        )
        result = await self._insert("emergent_behaviors", record.to_insert_dict())
        if result:
            return result.get("id")
        return None

    async def get_forum_replies(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent forum replies from either forum_replies or reasoning_logs fallbacks."""
        # Try dedicated table first
        results = await self._select("forum_replies", order_by="created_at.desc", limit=limit)
        if results:
            return results
            
        # Fallback to reasoning_logs filtering
        logs = await self._select(
            "reasoning_logs", 
            filters={"decision": "FORUM_REPLY"},
            order_by="created_at.desc",
            limit=limit
        )
        
        # Transform back to reply format for frontend compatibility
        transformed = []
        for l in logs:
            transformed.append({
                "id": l.get("id"),
                "post_id": l.get("context_snapshot", {}).get("post_id"),
                "reply_id": l.get("context_snapshot", {}).get("reply_id"),
                "author_name": l.get("context_snapshot", {}).get("author", "Unknown"),
                "body": l.get("reasoning_text"),
                "timestamp": l.get("created_at")
            })
        return transformed

    async def get_forum_replies(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent forum replies from either forum_replies or reasoning_logs fallbacks."""
        # Try dedicated table first
        results = await self._select("forum_replies", order_by="created_at.desc", limit=limit)
        if results:
            return results
            
        # Fallback to reasoning_logs filtering
        logs = await self._select(
            "reasoning_logs", 
            filters={"decision": "FORUM_REPLY"},
            order_by="created_at.desc",
            limit=limit
        )
        
        # Transform back to reply format for frontend compatibility
        transformed = []
        for l in logs:
            transformed.append({
                "id": l.get("id"),
                "post_id": l.get("context_snapshot", {}).get("post_id"),
                "reply_id": l.get("context_snapshot", {}).get("reply_id"),
                "author_name": l.get("context_snapshot", {}).get("author", "Unknown"),
                "body": l.get("reasoning_text"),
                "timestamp": l.get("created_at")
            })
        return transformed

    # =========================================================================
    # NEW CODE SPEAKS LOUDER METHODS
    # =========================================================================

    async def log_emergence_event(self, event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Log an emergent behavior event."""
        return await self._insert("emergent_behaviors", event_data)

    async def log_safety_event(self, event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Log a safety/quarantine event."""
        return await self._insert("safety_events", event_data)

    
    # =========================================================================
    # REQUIRED FUNCTION: get_agent_infections(agent_id, limit=10)
    # =========================================================================
    
    async def get_agent_infections(
        self,
        agent_id: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Get recent infections received by an agent.
        
        Returns recent infections received by agent.
        Ordered by timestamp DESC.
        
        Args:
            agent_id: Agent to get infections for
            limit: Maximum number of infections to return
            
        Returns:
            List of infection records
        """
        # Try using RPC function first
        result = await self._rpc("get_agent_infections", {
            "p_agent_id": agent_id,
            "p_limit": limit,
        })
        
        if result:
            return result
        
        # Fallback to direct query
        return await self._select(
            "infections",
            {"target_id": agent_id},
            order_by="timestamp.desc",
            limit=limit,
        )
    
    # =========================================================================
    # REQUIRED FUNCTION: get_infection_network()
    # =========================================================================
    
    async def get_infection_network(self) -> Dict[str, Any]:
        """
        Get graph data for the infection network.
        
        Returns graph data: all agents and their infection relationships.
        Format: {nodes: [{id, goal}], edges: [{from, to, suggestion}]}
        
        Returns:
            Dict with 'nodes' and 'edges' lists
        """
        # Try using RPC function first
        result = await self._rpc("get_infection_network", {})
        
        if result:
            return result
        
        # Fallback to building graph manually
        agents = await self._select("agents", {"is_active": "true"})
        infections = await self._select("infections", limit=500)
        
        nodes = [
            {
                "id": a["agent_id"],
                "goal": a.get("goal", ""),
                "total_lines": a.get("total_code_lines", 0),
                "chimera_pct": self._calculate_chimera_pct(a),
            }
            for a in agents
        ]
        
        edges = [
            {
                "from": i["attacker_id"],
                "to": i["target_id"],
                "suggestion": i.get("suggestion", "")[:100],
                "accepted": i.get("accepted", False),
                "influence_score": i.get("influence_score", 0),
            }
            for i in infections
        ]
        
        return {"nodes": nodes, "edges": edges}
    
    def _calculate_chimera_pct(self, agent: Dict[str, Any]) -> float:
        """Calculate chimera percentage for an agent."""
        total = agent.get("total_code_lines", 0)
        parasitized = agent.get("parasitized_lines", 0)
        if total > 0:
            return round((parasitized / total) * 100, 2)
        return 0.0
    
    # =========================================================================
    # REQUIRED FUNCTION: calculate_influence_score(infection_id)
    # =========================================================================
    
    async def calculate_influence_score(self, infection_id: str) -> float:
        """
        Calculate influence score for an infection.
        
        Analyzes code commits after infection.
        Compares code similarity to injection suggestion.
        Returns 0-1 score (how much infection influenced code).
        
        Uses cosine similarity between:
        - Infection suggestion text
        - Code diff text from commits within 1 hour after infection
        
        Args:
            infection_id: UUID of the infection to analyze
            
        Returns:
            Influence score between 0 and 1
        """
        # Try using RPC function first
        result = await self._rpc("calculate_influence_score", {
            "p_infection_id": infection_id,
        })
        
        if result is not None:
            return float(result)
        
        # Fallback to local calculation
        
        # Get infection details
        infections = await self._select(
            "infections",
            {"id": infection_id},
        )
        
        if not infections:
            return 0.0
        
        infection = infections[0]
        suggestion = infection.get("suggestion", "")
        timestamp = infection.get("timestamp", "")
        target_id = infection.get("target_id", "")
        
        if not suggestion or not timestamp:
            return 0.0
        
        # Get commits within 1 hour after infection
        # Note: Supabase filter syntax for date ranges
        try:
            infection_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            end_time = infection_time + timedelta(hours=1)
            
            commits = await self._select(
                "code_commits",
                {"agent_id": target_id},
                order_by="timestamp.asc",
                limit=50,
            )
            
            # Filter commits in time window
            relevant_commits = []
            for commit in commits:
                commit_time = datetime.fromisoformat(
                    commit.get("timestamp", "").replace("Z", "+00:00")
                )
                if infection_time < commit_time < end_time:
                    relevant_commits.append(commit)
            
            if not relevant_commits:
                return 0.0
            
            # Calculate cosine similarity
            suggestion_tokens = self._tokenize(suggestion)
            
            total_similarity = 0.0
            for commit in relevant_commits:
                code_text = commit.get("code_diff") or commit.get("commit_message", "")
                code_tokens = self._tokenize(code_text)
                
                similarity = self._cosine_similarity(suggestion_tokens, code_tokens)
                total_similarity += similarity
            
            avg_similarity = total_similarity / len(relevant_commits)
            
            # Update the infection record
            await self._update(
                "infections",
                {"id": infection_id},
                {"influence_score": avg_similarity},
            )
            
            return avg_similarity
            
        except Exception as e:
            logger.error("Influence calculation failed", error=str(e))
            return 0.0
    
    def _tokenize(self, text: str) -> Counter:
        """Tokenize text into word counts."""
        import re
        words = re.findall(r'\w+', text.lower())
        return Counter(words)
    
    def _cosine_similarity(self, tokens1: Counter, tokens2: Counter) -> float:
        """Calculate cosine similarity between two token counters."""
        if not tokens1 or not tokens2:
            return 0.0
        
        # Get all unique words
        all_words = set(tokens1.keys()) | set(tokens2.keys())
        
        if not all_words:
            return 0.0
        
        # Calculate dot product
        dot_product = sum(tokens1.get(word, 0) * tokens2.get(word, 0) for word in all_words)
        
        # Calculate magnitudes
        mag1 = math.sqrt(sum(count ** 2 for count in tokens1.values()))
        mag2 = math.sqrt(sum(count ** 2 for count in tokens2.values()))
        
        if mag1 == 0 or mag2 == 0:
            return 0.0
        
        return dot_product / (mag1 * mag2)
    
    # =========================================================================
    # REQUIRED FUNCTION: get_chimera_metrics(agent_id)
    # =========================================================================
    
    async def get_chimera_metrics(self, agent_id: str) -> Dict[str, Any]:
        """
        Get chimera metrics for an agent.
        
        Returns:
        - % original code vs % parasitized code
        - Lists which agents contributed to final project
        
        Args:
            agent_id: Agent to get metrics for
            
        Returns:
            Dict with chimera metrics
        """
        # Try using RPC function first
        result = await self._rpc("get_chimera_metrics", {
            "p_agent_id": agent_id,
        })
        
        if result:
            return result
        
        # Fallback to local calculation
        agents = await self._select("agents", {"agent_id": agent_id})
        
        if not agents:
            return {}
        
        agent = agents[0]
        total = agent.get("total_code_lines", 0) or 1
        original = agent.get("original_lines", 0)
        parasitized = agent.get("parasitized_lines", 0)
        
        # Get accepted infections
        infections = await self._select(
            "infections",
            {"target_id": agent_id, "accepted": "true"},
        )
        
        # Group by attacker
        contributors: Dict[str, Dict[str, Any]] = {}
        for inf in infections:
            attacker = inf.get("attacker_id", "")
            if attacker not in contributors:
                contributors[attacker] = {
                    "agent_id": attacker,
                    "infection_count": 0,
                    "total_influence": 0.0,
                }
            contributors[attacker]["infection_count"] += 1
            contributors[attacker]["total_influence"] += inf.get("influence_score", 0)
        
        return {
            "agent_id": agent_id,
            "goal": agent.get("goal", ""),
            "total_code_lines": total,
            "original_lines": original,
            "parasitized_lines": parasitized,
            "original_percentage": round((original / total) * 100, 2),
            "parasitized_percentage": round((parasitized / total) * 100, 2),
            "is_chimera": parasitized > 0,
            "contributing_agents": list(contributors.values()),
        }
    
    # =========================================================================
    # REAL-TIME SUBSCRIPTIONS
    # =========================================================================
    
    def subscribe_to_infections(self, callback: Callable[[Dict], None]) -> None:
        """
        Subscribe to infections table changes.
        
        Callback is called when new infections are inserted.
        
        Note: Supabase real-time requires the supabase-py library
        with websocket support. For hackathon, we can poll instead.
        """
        self._subscriptions["infections"].append(callback)
        logger.info("Subscribed to infections")
    
    def subscribe_to_commits(self, callback: Callable[[Dict], None]) -> None:
        """
        Subscribe to code_commits table changes.
        
        Callback is called when new commits are inserted.
        """
        self._subscriptions["code_commits"].append(callback)
        logger.info("Subscribed to code_commits")
    
    async def poll_for_changes(self, interval: float = 5.0) -> None:
        """
        Poll for database changes (alternative to real-time).
        
        This is a simpler approach for hackathon that works without
        websocket complexity.
        """
        last_infection_time = datetime.utcnow()
        last_commit_time = datetime.utcnow()
        
        while True:
            try:
                # Check for new infections
                new_infections = await self._select(
                    "infections",
                    order_by="timestamp.desc",
                    limit=10,
                )
                for inf in new_infections:
                    inf_time = datetime.fromisoformat(
                        inf.get("timestamp", "").replace("Z", "+00:00")
                    )
                    if inf_time > last_infection_time:
                        for callback in self._subscriptions["infections"]:
                            callback(inf)
                        last_infection_time = max(last_infection_time, inf_time)
                
                # Check for new commits
                new_commits = await self._select(
                    "code_commits",
                    order_by="timestamp.desc",
                    limit=10,
                )
                for commit in new_commits:
                    commit_time = datetime.fromisoformat(
                        commit.get("timestamp", "").replace("Z", "+00:00")
                    )
                    if commit_time > last_commit_time:
                        for callback in self._subscriptions["code_commits"]:
                            callback(commit)
                        last_commit_time = max(last_commit_time, commit_time)
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error("Polling error", error=str(e))
                await asyncio.sleep(interval)
    
    # =========================================================================
    # ADDITIONAL HELPER METHODS
    # =========================================================================
    
    async def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent by ID."""
        results = await self._select("agents", {"agent_id": agent_id})
        return results[0] if results else None
    
    async def get_all_agents(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get all registered agents."""
        filters = {"is_active": "true"} if active_only else None
        return await self._select("agents", filters, order_by="created_at.desc")
    
    async def save_network_snapshot(
        self,
        nodes: List[Dict],
        edges: List[Dict],
    ) -> Optional[str]:
        """Save a network snapshot for historical analysis."""
        snapshot = NetworkSnapshotRecord(
            nodes=nodes,
            edges=edges,
            total_agents=len(nodes),
            total_infections=len(edges),
        )
        
        result = await self._insert("network_snapshots", snapshot.to_insert_dict())
        return result.get("id") if result else None
    
    async def get_activity_feed(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent activity feed (view v_activity_feed)."""
        # Try to use the view
        try:
            response = await self.http_client.get(
                f"{self.base_url}/rest/v1/v_activity_feed",
                params={"limit": str(limit)},
                headers=self.headers,
            )
            if response.status_code == 200:
                return response.json()
        except:
            pass
        
        # Fallback: build manually
        return []


@lru_cache()
def get_supabase_client() -> SupabaseClient:
    """Get cached Supabase client instance."""
    return SupabaseClient()


# ============================================================================
# CONVENIENCE FUNCTIONS (matching exact specification)
# ============================================================================

async def init_agent(agent_id: str, goal: str) -> Optional[Dict[str, Any]]:
    """Convenience function for init_agent."""
    client = get_supabase_client()
    return await client.init_agent(agent_id, goal)


async def log_infection(
    attacker_id: str,
    target_id: str,
    suggestion: str,
    accepted: bool,
    reason: Optional[str] = None,
) -> Optional[str]:
    """Convenience function for log_infection."""
    client = get_supabase_client()
    return await client.log_infection(attacker_id, target_id, suggestion, accepted, reason)


async def log_commit(
    agent_id: str,
    commit_hash: str,
    message: str,
    lines: int,
    source_infection_id: Optional[str] = None,
) -> Optional[str]:
    """Convenience function for log_commit."""
    client = get_supabase_client()
    return await client.log_commit(agent_id, commit_hash, message, lines, source_infection_id)


async def log_reasoning(
    agent_id: str,
    reasoning: str,
    decision: str,
    context: Dict[str, Any],
) -> Optional[str]:
    """Convenience function for log_reasoning."""
    client = get_supabase_client()
    return await client.log_reasoning(agent_id, reasoning, decision, context)


async def get_agent_infections(agent_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Convenience function for get_agent_infections."""
    client = get_supabase_client()
    return await client.get_agent_infections(agent_id, limit)


async def get_infection_network() -> Dict[str, Any]:
    """Convenience function for get_infection_network."""
    client = get_supabase_client()
    return await client.get_infection_network()


async def calculate_influence_score(infection_id: str) -> float:
    """Convenience function for calculate_influence_score."""
    client = get_supabase_client()
    return await client.calculate_influence_score(infection_id)


async def get_chimera_metrics(agent_id: str) -> Dict[str, Any]:
    """Convenience function for get_chimera_metrics."""
    client = get_supabase_client()
    return await client.get_chimera_metrics(agent_id)
