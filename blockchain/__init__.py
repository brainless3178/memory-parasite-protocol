"""
Blockchain module for Memory Parasite Protocol.

Provides immutable on-chain proof of infections using Solana devnet.
"""
from blockchain.solana_client import (
    SolanaClient,
    get_solana_client,
    InfectionProof,
    AgentWallet,
    # Convenience functions
    record_infection_onchain,
    record_acceptance_onchain,
    get_infection_proof,
    verify_infection_authenticity,
)
from blockchain.integration import BlockchainIntegration

__all__ = [
    # Client
    "SolanaClient",
    "get_solana_client",
    # Data classes
    "InfectionProof",
    "AgentWallet",
    # Convenience functions
    "record_infection_onchain",
    "record_acceptance_onchain",
    "get_infection_proof",
    "verify_infection_authenticity",
    # Integration
    "BlockchainIntegration",
]
