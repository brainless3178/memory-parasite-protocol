"""
Infection Ledger for Memory Parasite Protocol.

High-level interface for recording infection proofs on Solana.
This is a legacy module - use BlockchainIntegration for new code.
"""

from blockchain.integration import BlockchainIntegration, get_blockchain_integration
from blockchain.solana_client import (
    SolanaClient,
    get_solana_client,
    InfectionProof,
)

# Re-export for backward compatibility
InfectionLedger = BlockchainIntegration

__all__ = [
    "InfectionLedger",
    "BlockchainIntegration",
    "get_blockchain_integration",
    "InfectionProof",
]
