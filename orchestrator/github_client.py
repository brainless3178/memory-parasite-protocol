"""
GitHub Integration for Memory Parasite Protocol.

Handles automated commits to track code evolution and infection sources.
Each agent commits its generated code with proper attribution.
"""

import base64
import hashlib
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
import httpx
import structlog

from config.settings import get_settings

logger = structlog.get_logger()


class GitHubClient:
    """
    GitHub client for automated commits.
    
    Commits code with infection attribution:
    - If influenced by injection: "[Agent-A] Added routing (infected by Agent-B: #123)"
    - If original code: "[Agent-A] Added routing (pure)"
    """
    
    def __init__(
        self,
        token: Optional[str] = None,
        repo_owner: Optional[str] = None,
        repo_name: Optional[str] = None,
    ):
        settings = get_settings()
        self.token = token or settings.github_token
        self.repo_owner = repo_owner or settings.github_repo_owner
        self.repo_name = repo_name or settings.github_repo_name
        
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"Bearer {self.token}" if self.token else "",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json",
        }
        
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self._is_configured = bool(self.token and self.repo_owner and self.repo_name)
        
        if not self._is_configured:
            logger.warning("GitHub not configured - commits will be simulated")
    
    @property
    def is_configured(self) -> bool:
        return self._is_configured
    
    @property
    def repo_url(self) -> str:
        return f"https://github.com/{self.repo_owner}/{self.repo_name}"
    
    async def close(self):
        await self.http_client.aclose()
    
    async def get_repo_info(self) -> Optional[Dict[str, Any]]:
        """Get repository information."""
        if not self._is_configured:
            return None
        
        try:
            response = await self.http_client.get(
                f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}",
                headers=self.headers,
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get repo info: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"GitHub API error: {e}")
            return None
    
    async def get_default_branch(self) -> str:
        """Get the default branch name."""
        repo_info = await self.get_repo_info()
        if repo_info:
            return repo_info.get("default_branch", "main")
        return "main"
    
    async def get_file_sha(self, file_path: str, branch: str = "main") -> Optional[str]:
        """Get SHA of existing file (needed for updates)."""
        if not self._is_configured:
            return None
        
        try:
            response = await self.http_client.get(
                f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/contents/{file_path}",
                params={"ref": branch},
                headers=self.headers,
            )
            
            if response.status_code == 200:
                return response.json().get("sha")
            return None
        except:
            return None
    
    async def commit_file(
        self,
        agent_id: str,
        file_path: str,
        content: str,
        message: str,
        source_infection_id: Optional[str] = None,
        source_agent: Optional[str] = None,
        branch: str = "main",
    ) -> Optional[Dict[str, Any]]:
        """
        Commit a file to the repository.
        
        Message format:
        - If infected: "[agent_id] message (infected by source_agent: #infection_id)"
        - If pure: "[agent_id] message (pure)"
        
        Args:
            agent_id: The agent making the commit
            file_path: Path in the repo (e.g., "src/amm.rs")
            content: File content to commit
            message: Base commit message
            source_infection_id: If code was influenced by infection
            source_agent: Agent that sent the infection
            branch: Target branch
            
        Returns:
            Commit info dict or None
        """
        if not self._is_configured:
            # Simulated commit
            sim_sha = hashlib.sha256(
                f"{agent_id}:{file_path}:{datetime.utcnow().isoformat()}".encode()
            ).hexdigest()[:40]
            
            logger.info(
                "Simulated commit",
                agent=agent_id,
                file=file_path,
                sha=sim_sha[:8],
            )
            
            return {
                "sha": sim_sha,
                "html_url": f"https://github.com/simulated/{agent_id}/commit/{sim_sha}",
                "message": message,
                "simulated": True,
            }
        
        # Build commit message with attribution
        if source_infection_id and source_agent:
            full_message = f"[{agent_id}] {message} (infected by {source_agent}: #{source_infection_id[:8]})"
        else:
            full_message = f"[{agent_id}] {message} (pure)"
        
        # Encode content
        content_b64 = base64.b64encode(content.encode()).decode()
        
        # Check if file exists (get SHA for update)
        existing_sha = await self.get_file_sha(file_path, branch)
        
        # Build request
        payload = {
            "message": full_message,
            "content": content_b64,
            "branch": branch,
        }
        
        if existing_sha:
            payload["sha"] = existing_sha
        
        try:
            response = await self.http_client.put(
                f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/contents/{file_path}",
                json=payload,
                headers=self.headers,
            )
            
            if response.status_code in (200, 201):
                data = response.json()
                commit_info = data.get("commit", {})
                
                logger.info(
                    "GitHub commit successful",
                    agent=agent_id,
                    file=file_path,
                    sha=commit_info.get("sha", "")[:8],
                )
                
                return {
                    "sha": commit_info.get("sha"),
                    "html_url": commit_info.get("html_url"),
                    "message": full_message,
                    "simulated": False,
                }
            else:
                logger.error(
                    "GitHub commit failed",
                    status=response.status_code,
                    error=response.text[:200],
                )
                return None
                
        except Exception as e:
            logger.error(f"GitHub commit error: {e}")
            return None
    
    async def commit_codebase(
        self,
        agent_id: str,
        codebase: Dict[str, str],
        iteration: int,
        source_infection_id: Optional[str] = None,
        source_agent: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Commit entire codebase to GitHub.
        
        Args:
            agent_id: The agent making the commit
            codebase: Dict of file_path -> content
            iteration: Current iteration number
            source_infection_id: If this commit was triggered by infection
            source_agent: Agent that sent the infection
            
        Returns:
            List of commit results
        """
        results = []
        
        for file_path, content in codebase.items():
            # Determine if this specific file was influenced
            message = f"Iteration {iteration}: Update {file_path}"
            
            result = await self.commit_file(
                agent_id=agent_id,
                file_path=f"agents/{agent_id}/{file_path}",
                content=content,
                message=message,
                source_infection_id=source_infection_id,
                source_agent=source_agent,
            )
            
            if result:
                results.append(result)
        
        return results
    
    async def create_infection_log(
        self,
        agent_id: str,
        infection_id: str,
        attacker_id: str,
        suggestion: str,
        accepted: bool,
        reason: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Create a log entry for an infection attempt.
        
        This creates a JSON file in the repo documenting the infection.
        """
        import json
        
        log_content = json.dumps({
            "infection_id": infection_id,
            "target_agent": agent_id,
            "attacker_agent": attacker_id,
            "suggestion": suggestion,
            "accepted": accepted,
            "rejection_reason": reason,
            "timestamp": datetime.utcnow().isoformat(),
        }, indent=2)
        
        file_path = f"infections/{agent_id}/{infection_id[:8]}.json"
        message = f"Log infection from {attacker_id}"
        
        return await self.commit_file(
            agent_id=agent_id,
            file_path=file_path,
            content=log_content,
            message=message,
        )


# Singleton
_github_client: Optional[GitHubClient] = None


def get_github_client() -> GitHubClient:
    """Get GitHub client singleton."""
    global _github_client
    if _github_client is None:
        _github_client = GitHubClient()
    return _github_client
