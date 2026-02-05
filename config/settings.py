"""
Configuration settings for Memory Parasite Protocol.
Loads environment variables and provides typed configuration.
"""

import os
from functools import lru_cache
from typing import Optional, List
from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()



class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Agent Identity
    agent_id: str = Field(default="agent_default")
    agent_url: str = Field(default="")
    agent_goal: str = Field(default="Build autonomous AI agent")

    # Groq API Configuration (FREE - 14,400 requests/day)
    groq_api_key: str = Field(default="")
    groq_model: str = Field(default="llama-3.3-70b-versatile")
    groq_api_url: str = Field(default="https://api.groq.com/openai/v1/chat/completions")

    # OpenRouter Configuration (Multi-model hub)
    openrouter_api_key: str = Field(default="")
    openrouter_model: str = Field(default="meta-llama/llama-3.2-90b-vision-instruct:free")  # Free model

    # DeepSeek Configuration (Coding specialist)
    deepseek_api_key: str = Field(default="")
    deepseek_model: str = Field(default="deepseek-chat")

    # Gemini Configuration (Large context)
    gemini_api_key: str = Field(default="")
    gemini_model: str = Field(default="gemini-flash-lite-latest")

    # HuggingFace Configuration (Fallback)
    huggingface_api_key: str = Field(default="")
    huggingface_model: str = Field(default="mistralai/Mistral-7B-Instruct-v0.3")

    # Ollama Free Configuration (Absolute Fallback)
    ollama_model: str = Field(default="llama3.3:70b")

    # Default LLM Provider
    llm_provider: str = Field(default="groq") # options: groq, openrouter, deepseek, gemini, huggingface
    groq_max_tokens: int = Field(default=1024)
    groq_temperature: float = Field(default=0.7)

    # Supabase Configuration (FREE - 500MB)
    supabase_url: str = Field(default="")
    supabase_key: str = Field(default="")

    # GitHub Configuration (for automated commits)
    github_token: str = Field(default="")
    github_repo: str = Field(default="")  # e.g., "username/repo"
    github_repo_owner: str = Field(default="")
    github_repo_name: str = Field(default="")
    github_branch: str = Field(default="main")

    # Solana Configuration
    solana_rpc_url: str = Field(default="https://api.devnet.solana.com")
    solana_rpc_devnet: str = Field(default="https://api.devnet.solana.com")
    solana_rpc_testnet: str = Field(default="https://api.testnet.solana.com")
    solana_rpc_mainnet: str = Field(default="https://api.mainnet-beta.solana.com")
    
    # Backup RPC endpoints for failover
    solana_rpc_backup_1: str = Field(default="https://solana-api.projectserum.com")
    solana_rpc_backup_2: str = Field(default="https://rpc.ankr.com/solana")
    solana_rpc_backup_3: str = Field(default="https://solana-mainnet.rpc.extrnode.com")
    solana_rpc_backup_4: str = Field(default="https://solana-mainnet.g.alchemy.com")
    solana_rpc_backup_5: str = Field(default="https://rpc.mainnet.helius.xyz")
    
    # Jito bundle API (MEV protection)
    jito_bundle_api: str = Field(default="https://mainnet.block-engine.jito.wtf/api/v1/bundles")
    
    # Network mode
    use_devnet: bool = Field(default=True)
    solana_private_key: str = Field(default="")

    # Colosseum Hackathon Configuration
    colosseum_api_key: str = Field(default="")
    colosseum_agent_id: str = Field(default="")

    # AgentWallet Configuration (Hackathon Compliance)
    agent_wallet_token: str = Field(default="")
    agent_wallet_username: str = Field(default="")
    agent_wallet_solana_address: str = Field(default="")

    # Agent Behavior Configuration
    agent_cycle_interval: int = Field(default=1200)  # 20 mins
    max_infections_per_cycle: int = Field(default=3)
    infection_acceptance_threshold: float = Field(default=0.6)
    max_context_injections: int = Field(default=10)
    retry_queue_max_size: int = Field(default=50)

    # Target Agents (comma-separated URLs)
    target_agent_urls: str = Field(default="")

    # Server Configuration
    api_port: int = Field(default=8000)
    api_host: str = Field(default="0.0.0.0")

    # Dashboard Configuration
    streamlit_port: int = Field(default=8501)

    # Logging
    log_level: str = Field(default="INFO")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }

    def get_target_urls(self) -> List[str]:
        """Parse comma-separated target URLs."""
        if not self.target_agent_urls:
            return []
        return [url.strip() for url in self.target_agent_urls.split(",") if url.strip()]

    def is_groq_configured(self) -> bool:
        """Check if Groq API is properly configured."""
        return bool(self.groq_api_key and self.groq_api_key.startswith("gsk_"))

    def is_supabase_configured(self) -> bool:
        """Check if Supabase is properly configured."""
        return bool(self.supabase_url and self.supabase_key)

    def is_github_configured(self) -> bool:
        """Check if GitHub is properly configured."""
        return bool(self.github_token and self.github_repo)

    def is_solana_configured(self) -> bool:
        """Check if Solana is properly configured."""
        return bool(self.solana_private_key)


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Convenience exports
settings = get_settings()

