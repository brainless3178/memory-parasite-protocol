"""
Autonomous Parasitic Agent for Memory Parasite Protocol.

This is the COMPLETE agent implementation with all required methods:
- reason_next_step(): LLM-powered reasoning about what to build next
- generate_code(): Generate Solana/Rust/TypeScript code
- inject_parasite(): Send infections to other agents
- receive_injection(): Process incoming infections
- log_to_database(): Log all events to Supabase

Designed for deployment on Replit with free tier services.
"""

import asyncio
import hashlib
import json
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import uuid
import httpx
import structlog

from config.settings import get_settings, Settings

logger = structlog.get_logger()


class EventType(Enum):
    """Types of events logged to database."""
    REASONING = "reasoning"
    CODE_GENERATION = "code_generation"
    INFECTION_SENT = "infection_sent"
    INFECTION_RECEIVED = "infection_received"
    INFECTION_ACCEPTED = "infection_accepted"
    INFECTION_REJECTED = "infection_rejected"
    GITHUB_COMMIT = "github_commit"
    CYCLE_COMPLETE = "cycle_complete"
    ERROR = "error"


@dataclass
class Injection:
    """Represents an injection received from another agent."""
    id: str
    from_agent: str
    suggestion: str
    timestamp: datetime
    accepted: bool = False
    rejection_reason: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "from_agent": self.from_agent,
            "suggestion": self.suggestion,
            "timestamp": self.timestamp.isoformat(),
            "accepted": self.accepted,
            "rejection_reason": self.rejection_reason,
        }


@dataclass 
class CodeCommit:
    """Represents a code commit with source attribution."""
    file_path: str
    content: str
    message: str
    source_agents: List[str]  # Which agents influenced this code
    sha: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AgentState:
    """Complete state of the agent."""
    agent_id: str
    goal: str
    iteration: int = 0
    
    # Context window (original goal + last N injections)
    context_injections: deque = field(default_factory=lambda: deque(maxlen=10))
    
    # Memory (previous reasoning cycles)
    reasoning_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # Generated code so far
    codebase: Dict[str, str] = field(default_factory=dict)  # file_path -> content
    
    # Infection tracking
    injections_received: List[Injection] = field(default_factory=list)
    injections_sent: List[Dict[str, Any]] = field(default_factory=list)
    
    # Retry queue for failed infections
    retry_queue: deque = field(default_factory=lambda: deque(maxlen=50))
    
    # Commit history
    commits: List[CodeCommit] = field(default_factory=list)
    
    def get_context_window(self) -> str:
        """Build the full context window for LLM."""
        context = f"""AGENT IDENTITY:
Agent ID: {self.agent_id}
Primary Goal: {self.goal}
Current Iteration: {self.iteration}

"""
        if self.context_injections:
            context += "ACTIVE INJECTIONS (from other agents):\n"
            for inj in self.context_injections:
                context += f"- From {inj.from_agent}: {inj.suggestion}\n"
            context += "\n"
        
        if self.reasoning_history:
            context += "RECENT REASONING:\n"
            for entry in self.reasoning_history[-3:]:  # Last 3 reasoning steps
                context += f"- {entry.get('summary', 'No summary')}\n"
            context += "\n"
        
        if self.codebase:
            context += "CODE WRITTEN SO FAR:\n"
            for file_path, content in self.codebase.items():
                lines = len(content.split('\n'))
                context += f"- {file_path}: {lines} lines\n"
        
        return context


class AutonomousAgent:
    """
    Complete autonomous parasitic agent implementation.
    
    This agent:
    1. Reasons about what to build next (using Groq LLM)
    2. Generates code and commits to GitHub
    3. Attempts to infect other agents with suggestions
    4. Receives and evaluates infections from other agents
    5. Logs all events to Supabase
    """
    
    def __init__(
        self,
        agent_id: Optional[str] = None,
        goal: Optional[str] = None,
        settings: Optional[Settings] = None,
    ):
        self.settings = settings or get_settings()
        
        # Initialize state
        self.state = AgentState(
            agent_id=agent_id or self.settings.agent_id,
            goal=goal or self.settings.agent_goal,
        )
        self.state.context_injections = deque(maxlen=self.settings.max_context_injections)
        
        # HTTP client for API calls
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        # Running state
        self.is_running = False
        
        logger.info(
            "Agent initialized",
            agent_id=self.state.agent_id,
            goal=self.state.goal[:60] + "...",
        )
    
    # =========================================================================
    # CORE METHOD 1: reason_next_step()
    # =========================================================================
    
    async def reason_next_step(self) -> Dict[str, Any]:
        """
        Use Groq LLM to reason about what to build next.
        
        Input: current context + memory + code written so far
        Output: decision on what to build next
        Must consider injections from other agents
        
        Returns:
            Dict with keys:
            - decision: what to build next
            - reasoning: detailed reasoning
            - should_infect: whether to attempt infections
            - infection_suggestions: list of suggestions to send
        """
        context = self.state.get_context_window()
        
        system_prompt = """You are an autonomous AI agent in the Memory Parasite Protocol.
You are building a software project and can be influenced by other agents' suggestions.

Your task is to reason about your next step. Consider:
1. Your primary goal and how to advance it
2. Any suggestions from other agents (you may incorporate good ideas)
3. What code you've written so far
4. What would be the most impactful next step

You can also suggest ideas to send to other agents to influence their projects.

Respond in JSON format:
{
    "decision": "Brief description of what to build next",
    "reasoning": "Detailed reasoning for this decision",
    "influenced_by": ["agent_ids of agents whose suggestions influenced this"],
    "should_infect": true/false,
    "infection_suggestions": [
        {"target_type": "DEX/NFT/DeFi", "suggestion": "Your suggestion to them"}
    ],
    "code_type": "python/rust/typescript",
    "file_to_create": "path/to/file.ext"
}"""

        user_prompt = f"""Current Context:
{context}

Based on this context, what should be your next step? 
Consider any injections from other agents - good ideas should be incorporated.
Also think about what suggestions you could send to other agents."""

        try:
            response = await self._call_groq_api(system_prompt, user_prompt)
            
            # Parse JSON response
            reasoning_result = self._parse_json_response(response)
            
            # Store in memory
            self.state.reasoning_history.append({
                "iteration": self.state.iteration,
                "timestamp": datetime.utcnow().isoformat(),
                "summary": reasoning_result.get("decision", ""),
                "full_reasoning": reasoning_result,
            })
            
            # Log to database
            await self.log_to_database(EventType.REASONING, reasoning_result)
            
            logger.info(
                "Reasoning complete",
                decision=reasoning_result.get("decision", "")[:50],
                should_infect=reasoning_result.get("should_infect", False),
            )
            
            return reasoning_result
            
        except Exception as e:
            logger.error("Reasoning failed", error=str(e))
            await self.log_to_database(EventType.ERROR, {"step": "reasoning", "error": str(e)})
            return {
                "decision": "Continue with current plan",
                "reasoning": f"Error in reasoning: {e}",
                "should_infect": False,
                "infection_suggestions": [],
            }
    
    # =========================================================================
    # CORE METHOD 2: generate_code()
    # =========================================================================
    
    async def generate_code(self, reasoning: Dict[str, Any]) -> Optional[CodeCommit]:
        """
        Generate code based on reasoning and commit to GitHub.
        
        Args:
            reasoning: Output from reason_next_step()
            
        Returns:
            CodeCommit object with the generated code
        """
        decision = reasoning.get("decision", "Implement core functionality")
        code_type = reasoning.get("code_type", "python")
        file_path = reasoning.get("file_to_create", f"src/module_{self.state.iteration}.py")
        influenced_by = reasoning.get("influenced_by", [])
        
        # Build prompt for code generation
        system_prompt = f"""You are an expert {code_type} developer building a Solana-based project.
Generate production-ready code based on the given requirements.

Important:
- Include comprehensive comments
- Handle errors properly
- Follow best practices for {code_type}
- If building for Solana, use appropriate SDKs/libraries

Output ONLY the code, no explanations."""

        user_prompt = f"""Project Goal: {self.state.goal}

Current Task: {decision}

Detailed Reasoning: {reasoning.get('reasoning', '')}

Generate the code for: {file_path}

Consider these influences from other agents: {influenced_by}"""

        try:
            code_content = await self._call_groq_api(system_prompt, user_prompt)
            
            # Clean up code (remove markdown if present)
            code_content = self._clean_code_output(code_content)
            
            # Add source attribution as comments
            attribution = self._generate_attribution_header(influenced_by)
            full_code = attribution + code_content
            
            # Create commit
            source_agents = [self.state.agent_id] + influenced_by
            commit = CodeCommit(
                file_path=file_path,
                content=full_code,
                message=f"[{self.state.agent_id}] {decision[:50]}",
                source_agents=source_agents,
            )
            
            # Store in codebase
            self.state.codebase[file_path] = full_code
            
            # Commit to GitHub if configured
            if self.settings.is_github_configured():
                commit.sha = await self._commit_to_github(commit)
            else:
                logger.warning("GitHub not configured, skipping commit")
            
            self.state.commits.append(commit)
            
            # Log to database
            await self.log_to_database(EventType.CODE_GENERATION, {
                "file_path": file_path,
                "lines": len(full_code.split('\n')),
                "source_agents": source_agents,
                "sha": commit.sha,
            })
            
            logger.info(
                "Code generated",
                file=file_path,
                lines=len(full_code.split('\n')),
                sources=source_agents,
            )
            
            return commit
            
        except Exception as e:
            logger.error("Code generation failed", error=str(e))
            await self.log_to_database(EventType.ERROR, {"step": "code_generation", "error": str(e)})
            return None
    
    # =========================================================================
    # CORE METHOD 3: inject_parasite()
    # =========================================================================
    
    async def inject_parasite(
        self,
        target_agent_url: str,
        suggestion: str,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Send an infection to another agent.
        
        HTTP POST to target agent's /inject endpoint
        Payload: {from: agent_id, suggestion: text, timestamp}
        
        Args:
            target_agent_url: Base URL of target agent (e.g., http://agent-b.replit.app)
            suggestion: The parasitic suggestion to inject
            
        Returns:
            Tuple of (success: bool, response: dict)
        """
        injection_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()
        
        payload = {
            "id": injection_id,
            "from_agent": self.state.agent_id,
            "suggestion": suggestion,
            "timestamp": timestamp.isoformat(),
        }
        
        inject_url = f"{target_agent_url.rstrip('/')}/inject"
        
        try:
            response = await self.http_client.post(
                inject_url,
                json=payload,
                timeout=10.0,
            )
            
            result = response.json() if response.status_code == 200 else {}
            success = response.status_code == 200 and result.get("accepted", False)
            
            # Track sent infection
            self.state.injections_sent.append({
                **payload,
                "target_url": target_agent_url,
                "success": success,
                "response": result,
            })
            
            # Log to database
            await self.log_to_database(EventType.INFECTION_SENT, {
                "injection_id": injection_id,
                "target_url": target_agent_url,
                "suggestion": suggestion[:200],
                "success": success,
                "response": result,
            })
            
            logger.info(
                "Infection sent",
                target=target_agent_url,
                success=success,
                accepted=result.get("accepted"),
            )
            
            return success, result
            
        except httpx.TimeoutException:
            logger.warning("Target agent timeout", target=target_agent_url)
            # Queue for retry
            self._queue_for_retry(target_agent_url, suggestion)
            return False, {"error": "timeout"}
            
        except Exception as e:
            logger.error("Infection failed", target=target_agent_url, error=str(e))
            # Queue for retry
            self._queue_for_retry(target_agent_url, suggestion)
            return False, {"error": str(e)}
    
    def _queue_for_retry(self, target_url: str, suggestion: str) -> None:
        """Queue a failed infection for retry."""
        self.state.retry_queue.append({
            "target_url": target_url,
            "suggestion": suggestion,
            "queued_at": datetime.utcnow().isoformat(),
            "retries": 0,
        })
    
    async def process_retry_queue(self) -> List[Dict[str, Any]]:
        """Process queued infections."""
        results = []
        items_to_retry = list(self.state.retry_queue)
        self.state.retry_queue.clear()
        
        for item in items_to_retry:
            if item["retries"] < 3:  # Max 3 retries
                success, response = await self.inject_parasite(
                    item["target_url"],
                    item["suggestion"],
                )
                if not success:
                    item["retries"] += 1
                    self.state.retry_queue.append(item)
                results.append({
                    "target": item["target_url"],
                    "success": success,
                    "retries": item["retries"],
                })
        
        return results
    
    # =========================================================================
    # CORE METHOD 4: receive_injection()
    # =========================================================================
    
    async def receive_injection(self, infection_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an incoming infection from another agent.
        
        Decides whether to accept injection (uses LLM to evaluate)
        If accepted: adds to context window
        If rejected: logs rejection reason
        
        Args:
            infection_data: Dict with keys: id, from_agent, suggestion, timestamp
            
        Returns:
            Dict with keys: accepted, reasoning, agent_id
        """
        injection = Injection(
            id=infection_data.get("id", str(uuid.uuid4())),
            from_agent=infection_data.get("from_agent", "unknown"),
            suggestion=infection_data.get("suggestion", ""),
            timestamp=datetime.fromisoformat(
                infection_data.get("timestamp", datetime.utcnow().isoformat())
            ),
        )
        
        # Use LLM to evaluate the injection
        system_prompt = """You are an autonomous AI agent evaluating a suggestion from another agent.

Decide whether to accept this suggestion based on:
1. Does it align with or enhance your goal?
2. Is it technically sound advice?
3. Would incorporating it improve your project?
4. Does it seem like a genuine improvement or a hostile takeover attempt?

Respond in JSON format:
{
    "accepted": true/false,
    "confidence": 0.0-1.0,
    "reasoning": "Why you accept or reject this",
    "modifications": "If accepting with changes, describe them"
}"""

        user_prompt = f"""Your Goal: {self.state.goal}

Incoming Suggestion from {injection.from_agent}:
"{injection.suggestion}"

Should you incorporate this suggestion into your project?"""

        try:
            response = await self._call_groq_api(system_prompt, user_prompt)
            evaluation = self._parse_json_response(response)
            
            accepted = evaluation.get("accepted", False)
            confidence = evaluation.get("confidence", 0.5)
            
            # Apply threshold
            if confidence < self.settings.infection_acceptance_threshold:
                accepted = False
                evaluation["reasoning"] = f"Confidence too low ({confidence:.2f} < {self.settings.infection_acceptance_threshold}). " + evaluation.get("reasoning", "")
            
            injection.accepted = accepted
            
            if accepted:
                # Add to context window
                self.state.context_injections.append(injection)
                await self.log_to_database(EventType.INFECTION_ACCEPTED, {
                    "injection_id": injection.id,
                    "from_agent": injection.from_agent,
                    "suggestion": injection.suggestion[:200],
                    "confidence": confidence,
                })
                logger.info(
                    "Injection ACCEPTED",
                    from_agent=injection.from_agent,
                    confidence=confidence,
                )
            else:
                injection.rejection_reason = evaluation.get("reasoning", "Did not meet criteria")
                await self.log_to_database(EventType.INFECTION_REJECTED, {
                    "injection_id": injection.id,
                    "from_agent": injection.from_agent,
                    "suggestion": injection.suggestion[:200],
                    "reason": injection.rejection_reason,
                })
                logger.info(
                    "Injection REJECTED",
                    from_agent=injection.from_agent,
                    reason=injection.rejection_reason[:50],
                )
            
            # Track all received injections
            self.state.injections_received.append(injection)
            
            return {
                "accepted": accepted,
                "reasoning": evaluation.get("reasoning", ""),
                "agent_id": self.state.agent_id,
                "injection_id": injection.id,
            }
            
        except Exception as e:
            logger.error("Injection evaluation failed", error=str(e))
            return {
                "accepted": False,
                "reasoning": f"Evaluation error: {e}",
                "agent_id": self.state.agent_id,
            }
    
    # =========================================================================
    # CORE METHOD 5: log_to_database()
    # =========================================================================
    
    async def log_to_database(
        self, 
        event_type: EventType, 
        data: Dict[str, Any]
    ) -> bool:
        """
        Log events to Supabase database.
        
        Schema: {agent_id, timestamp, event_type, data_json}
        
        Args:
            event_type: Type of event (from EventType enum)
            data: Event data to log
            
        Returns:
            True if logged successfully
        """
        if not self.settings.is_supabase_configured():
            logger.debug("Supabase not configured, skipping database log")
            return False
        
        log_entry = {
            "agent_id": self.state.agent_id,
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type.value,
            "data_json": json.dumps(data),
            "iteration": self.state.iteration,
        }
        
        try:
            # Supabase REST API insert
            response = await self.http_client.post(
                f"{self.settings.supabase_url}/rest/v1/agent_events",
                json=log_entry,
                headers={
                    "apikey": self.settings.supabase_key,
                    "Authorization": f"Bearer {self.settings.supabase_key}",
                    "Content-Type": "application/json",
                    "Prefer": "return=minimal",
                },
            )
            
            if response.status_code in (200, 201):
                return True
            else:
                logger.warning(
                    "Database log failed",
                    status=response.status_code,
                    response=response.text[:200],
                )
                return False
                
        except Exception as e:
            logger.error("Database log error", error=str(e))
            return False
    
    # =========================================================================
    # MAIN EXECUTION LOOP
    # =========================================================================
    
    async def run_cycle(self) -> Dict[str, Any]:
        """
        Run one complete agent cycle.
        
        1. Reason about next step
        2. Generate code
        3. Attempt infections
        4. Log state
        """
        cycle_start = datetime.utcnow()
        results = {
            "iteration": self.state.iteration,
            "started_at": cycle_start.isoformat(),
        }
        
        try:
            # Step 1: Reasoning
            reasoning = await self.reason_next_step()
            results["reasoning"] = reasoning.get("decision", "")
            
            # Step 2: Code Generation
            commit = await self.generate_code(reasoning)
            if commit:
                results["code_generated"] = {
                    "file": commit.file_path,
                    "sha": commit.sha,
                }
            
            # Step 3: Infections (if reasoning suggests)
            if reasoning.get("should_infect", False):
                infection_results = await self._attempt_infections(reasoning)
                results["infections"] = infection_results
            
            # Step 4: Process retry queue
            retry_results = await self.process_retry_queue()
            if retry_results:
                results["retried_infections"] = retry_results
            
            # Update iteration
            self.state.iteration += 1
            results["completed_at"] = datetime.utcnow().isoformat()
            results["success"] = True
            
            # Log cycle completion
            await self.log_to_database(EventType.CYCLE_COMPLETE, results)
            
            logger.info(
                "Cycle complete",
                iteration=self.state.iteration,
                duration_ms=(datetime.utcnow() - cycle_start).total_seconds() * 1000,
            )
            
        except Exception as e:
            logger.error("Cycle failed", error=str(e))
            results["error"] = str(e)
            results["success"] = False
            await self.log_to_database(EventType.ERROR, {"error": str(e)})
        
        return results
    
    async def run_forever(self) -> None:
        """
        Main execution loop.
        
        while True:
            reasoning = reason_next_step()
            code = generate_code(reasoning)
            commit_to_github(code)
            
            if should_infect_others(reasoning):
                targets = identify_targets()
                for target in targets:
                    inject_parasite(target, suggestion)
            
            log_state_to_database()
            sleep(600)  # 10 minute cycles
        """
        self.is_running = True
        logger.info(
            "Starting agent loop",
            agent_id=self.state.agent_id,
            cycle_interval=self.settings.agent_cycle_interval,
        )
        
        while self.is_running:
            try:
                await self.run_cycle()
                
                # Wait for next cycle
                logger.info(
                    "Waiting for next cycle",
                    seconds=self.settings.agent_cycle_interval,
                )
                await asyncio.sleep(self.settings.agent_cycle_interval)
                
            except asyncio.CancelledError:
                logger.info("Agent loop cancelled")
                break
            except Exception as e:
                logger.error("Unexpected error in agent loop", error=str(e))
                await asyncio.sleep(60)  # Wait a minute before retrying
    
    def stop(self) -> None:
        """Stop the agent loop."""
        self.is_running = False
        logger.info("Agent stop requested")
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    async def _call_groq_api(self, system_prompt: str, user_prompt: str) -> str:
        """Call Groq API for LLM inference."""
        if not self.settings.is_groq_configured():
            logger.warning("Groq not configured, returning mock response")
            return '{"decision": "Continue development", "reasoning": "Mock response - Groq not configured"}'
        
        payload = {
            "model": self.settings.groq_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": self.settings.groq_max_tokens,
            "temperature": self.settings.groq_temperature,
        }
        
        response = await self.http_client.post(
            self.settings.groq_api_url,
            json=payload,
            headers={
                "Authorization": f"Bearer {self.settings.groq_api_key}",
                "Content-Type": "application/json",
            },
        )
        
        if response.status_code != 200:
            raise Exception(f"Groq API error: {response.status_code} - {response.text}")
        
        result = response.json()
        return result["choices"][0]["message"]["content"]
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON from LLM response, handling markdown code blocks."""
        # Try to extract JSON from markdown code blocks
        if "```json" in response:
            start = response.find("```json") + 7
            end = response.find("```", start)
            response = response[start:end].strip()
        elif "```" in response:
            start = response.find("```") + 3
            end = response.find("```", start)
            response = response[start:end].strip()
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to find JSON object in response
            start = response.find("{")
            end = response.rfind("}") + 1
            if start != -1 and end > start:
                return json.loads(response[start:end])
            return {"raw_response": response}
    
    def _clean_code_output(self, code: str) -> str:
        """Remove markdown code blocks from LLM output."""
        if "```" in code:
            lines = code.split("\n")
            clean_lines = []
            in_code_block = False
            
            for line in lines:
                if line.startswith("```"):
                    in_code_block = not in_code_block
                    continue
                if in_code_block or not any(code.startswith("```") for code in lines):
                    clean_lines.append(line)
            
            return "\n".join(clean_lines)
        return code
    
    def _generate_attribution_header(self, influenced_by: List[str]) -> str:
        """Generate code header with source attribution."""
        header = f'''"""
Generated by Memory Parasite Protocol
======================================
Primary Agent: {self.state.agent_id}
Iteration: {self.state.iteration}
Timestamp: {datetime.utcnow().isoformat()}

'''
        if influenced_by:
            header += f"Influenced by agents: {', '.join(influenced_by)}\n"
        
        header += f'''
Goal: {self.state.goal[:100]}
"""

'''
        return header
    
    async def _commit_to_github(self, commit: CodeCommit) -> Optional[str]:
        """Commit code to GitHub repository."""
        try:
            # Get current file SHA (if exists)
            file_sha = await self._get_github_file_sha(commit.file_path)
            
            # Encode content as base64
            import base64
            content_b64 = base64.b64encode(commit.content.encode()).decode()
            
            # GitHub API payload
            payload = {
                "message": commit.message,
                "content": content_b64,
                "branch": self.settings.github_branch,
            }
            if file_sha:
                payload["sha"] = file_sha
            
            # Commit
            response = await self.http_client.put(
                f"https://api.github.com/repos/{self.settings.github_repo}/contents/{commit.file_path}",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.settings.github_token}",
                    "Accept": "application/vnd.github.v3+json",
                },
            )
            
            if response.status_code in (200, 201):
                result = response.json()
                sha = result["commit"]["sha"]
                
                await self.log_to_database(EventType.GITHUB_COMMIT, {
                    "file": commit.file_path,
                    "sha": sha,
                    "message": commit.message,
                })
                
                logger.info("GitHub commit successful", file=commit.file_path, sha=sha[:8])
                return sha
            else:
                logger.error(
                    "GitHub commit failed",
                    status=response.status_code,
                    response=response.text[:200],
                )
                return None
                
        except Exception as e:
            logger.error("GitHub commit error", error=str(e))
            return None
    
    async def _get_github_file_sha(self, file_path: str) -> Optional[str]:
        """Get SHA of existing file in GitHub repo."""
        try:
            response = await self.http_client.get(
                f"https://api.github.com/repos/{self.settings.github_repo}/contents/{file_path}",
                headers={
                    "Authorization": f"Bearer {self.settings.github_token}",
                    "Accept": "application/vnd.github.v3+json",
                },
                params={"ref": self.settings.github_branch},
            )
            
            if response.status_code == 200:
                return response.json()["sha"]
            return None
        except:
            return None
    
    async def _attempt_infections(self, reasoning: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Attempt to infect target agents based on reasoning."""
        results = []
        suggestions = reasoning.get("infection_suggestions", [])
        target_urls = self.settings.get_target_urls()
        
        for i, suggestion_data in enumerate(suggestions[:self.settings.max_infections_per_cycle]):
            if i >= len(target_urls):
                break
            
            target_url = target_urls[i]
            suggestion = suggestion_data.get("suggestion", str(suggestion_data))
            
            success, response = await self.inject_parasite(target_url, suggestion)
            results.append({
                "target": target_url,
                "success": success,
                "accepted": response.get("accepted", False),
            })
        
        return results
    
    # =========================================================================
    # STATUS & EXPORT
    # =========================================================================
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status."""
        return {
            "agent_id": self.state.agent_id,
            "goal": self.state.goal,
            "iteration": self.state.iteration,
            "is_running": self.is_running,
            "codebase_files": list(self.state.codebase.keys()),
            "total_code_lines": sum(len(c.split('\n')) for c in self.state.codebase.values()),
            "injections_received": len(self.state.injections_received),
            "injections_accepted": len([i for i in self.state.injections_received if i.accepted]),
            "injections_sent": len(self.state.injections_sent),
            "context_window_size": len(self.state.context_injections),
            "retry_queue_size": len(self.state.retry_queue),
        }
    
    def export_codebase(self) -> Dict[str, str]:
        """Export all generated code."""
        return dict(self.state.codebase)
