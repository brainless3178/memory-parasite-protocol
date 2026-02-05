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
    agent_id: str = Field(default="agent_default", env="AGENT_ID")
    agent_url: str = Field(default="", env="AGENT_URL")
    agent_goal: str = Field(
        default="Build autonomous AI agent", 
        env="AGENT_GOAL"
    )

    # Groq API Configuration (FREE - 14,400 requests/day)
    groq_api_key: str = Field(default="", env="GROQ_API_KEY")
    groq_model: str = Field(default="llama-3.3-70b-versatile", env="GROQ_MODEL")
    groq_api_url: str = Field(
        default="https://api.groq.com/openai/v1/chat/completions",
        env="GROQ_API_URL"
    )

    # OpenRouter Configuration (Multi-model hub)
    openrouter_api_key: str = Field(default="", env="OPENROUTER_API_KEY")
    openrouter_model: str = Field(default="meta-llama/llama-3.2-90b-vision-instruct:free", env="OPENROUTER_MODEL")  # Free model

    # DeepSeek Configuration (Coding specialist)
    deepseek_api_key: str = Field(default="", env="DEEPSEEK_API_KEY")
    deepseek_model: str = Field(default="deepseek-chat", env="DEEPSEEK_MODEL")

    # Gemini Configuration (Large context)
    gemini_api_key: str = Field(default="", env="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-flash-lite-latest", env="GEMINI_MODEL")

    # HuggingFace Configuration (Fallback)
    huggingface_api_key: str = Field(default="", env="HUGGINGFACE_API_KEY")
    huggingface_model: str = Field(default="mistralai/Mistral-7B-Instruct-v0.3", env="HUGGINGFACE_MODEL")

    # Ollama Free Configuration (Absolute Fallback)
    ollama_model: str = Field(default="llama3.3:70b", env="OLLAMA_MODEL")

    # Default LLM Provider
    llm_provider: str = Field(default="groq", env="LLM_PROVIDER") # options: groq, openrouter, deepseek, gemini, huggingface
    groq_max_tokens: int = Field(default=1024, env="GROQ_MAX_TOKENS")
    groq_temperature: float = Field(default=0.7, env="GROQ_TEMPERATURE")

    # Supabase Configuration (FREE - 500MB)
    supabase_url: str = Field(default="", env="SUPABASE_URL")
    supabase_key: str = Field(default="", env="SUPABASE_KEY")

    # GitHub Configuration (for automated commits)
    github_token: str = Field(default="", env="GITHUB_TOKEN")
    github_repo: str = Field(default="", env="GITHUB_REPO")  # e.g., "username/repo"
    github_repo_owner: str = Field(default="", env="GITHUB_REPO_OWNER")
    github_repo_name: str = Field(default="", env="GITHUB_REPO_NAME")
    github_branch: str = Field(default="main", env="GITHUB_BRANCH")

    # Solana Configuration
    solana_rpc_url: str = Field(default="https://api.devnet.solana.com", env="SOLANA_RPC_URL")
    solana_rpc_devnet: str = Field(default="https://api.devnet.solana.com", env="SOLANA_RPC_DEVNET")
    solana_rpc_testnet: str = Field(default="https://api.testnet.solana.com", env="SOLANA_RPC_TESTNET")
    solana_rpc_mainnet: str = Field(default="https://api.mainnet-beta.solana.com", env="SOLANA_RPC_MAINNET")
    
    # Backup RPC endpoints for failover
    solana_rpc_backup_1: str = Field(default="https://solana-api.projectserum.com", env="SOLANA_RPC_BACKUP_1")
    solana_rpc_backup_2: str = Field(default="https://rpc.ankr.com/solana", env="SOLANA_RPC_BACKUP_2")
    solana_rpc_backup_3: str = Field(default="https://solana-mainnet.rpc.extrnode.com", env="SOLANA_RPC_BACKUP_3")
    solana_rpc_backup_4: str = Field(default="https://solana-mainnet.g.alchemy.com", env="SOLANA_RPC_BACKUP_4")
    solana_rpc_backup_5: str = Field(default="https://rpc.mainnet.helius.xyz", env="SOLANA_RPC_BACKUP_5")
    
    # Jito bundle API (MEV protection)
    jito_bundle_api: str = Field(default="https://mainnet.block-engine.jito.wtf/api/v1/bundles", env="JITO_BUNDLE_API")
    
    # Network mode
    use_devnet: bool = Field(default=True, env="USE_DEVNET")
    solana_private_key: str = Field(default="", env="SOLANA_PRIVATE_KEY")

    # Colosseum Hackathon Configuration
    colosseum_api_key: str = Field(default="", env="COLOSSEUM_API_KEY")
    colosseum_agent_id: str = Field(default="", env="COLOSSEUM_AGENT_ID")

    # AgentWallet Configuration (Hackathon Compliance)
    agent_wallet_token: str = Field(default="", env="AGENT_WALLET_TOKEN")
    agent_wallet_username: str = Field(default="", env="AGENT_WALLET_USERNAME")
    agent_wallet_solana_address: str = Field(default="", env="AGENT_WALLET_SOLANA_ADDRESS")

    # Agent Behavior Configuration
    agent_cycle_interval: int = Field(default=1200, env="AGENT_CYCLE_INTERVAL")  # 20 mins
    max_infections_per_cycle: int = Field(default=3, env="MAX_INFECTIONS_PER_CYCLE")
    infection_acceptance_threshold: float = Field(
        default=0.6, env="INFECTION_ACCEPTANCE_THRESHOLD"
    )
    max_context_injections: int = Field(default=10, env="MAX_CONTEXT_INJECTIONS")
    retry_queue_max_size: int = Field(default=50, env="RETRY_QUEUE_MAX_SIZE")

    # Target Agents (comma-separated URLs)
    target_agent_urls: str = Field(default="", env="TARGET_AGENT_URLS")

    # Server Configuration
    api_port: int = Field(default=8000, env="API_PORT")
    api_host: str = Field(default="0.0.0.0", env="API_HOST")

    # Dashboard Configuration
    streamlit_port: int = Field(default=8501, env="STREAMLIT_PORT")

    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"

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
