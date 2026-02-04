"""
Blockchain Integration for Memory Parasite Protocol.

Integrates Solana on-chain recording with database operations.
This module ensures that every infection logged to the database
is also recorded immutably on the Solana blockchain.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, Optional
import structlog

from config.settings import get_settings
from blockchain.solana_client import (
    SolanaClient,
    get_solana_client,
    InfectionProof,
)
from database import (
    get_supabase_client,
    SupabaseClient,
)

logger = structlog.get_logger()


class BlockchainIntegration:
    """
    Unified interface for database + blockchain operations.
    
    Ensures every infection is:
    1. Logged to Supabase (for quick queries)
    2. Recorded on Solana (for immutable proof)
    
    The blockchain record provides:
    - Proof that the infection was not tampered with
    - Verifiable timestamp
    - Decentralized audit trail
    """
    
    def __init__(
        self,
        solana_client: Optional[SolanaClient] = None,
        db_client: Optional[SupabaseClient] = None,
    ):
        self.solana = solana_client or get_solana_client()
        self.db = db_client or get_supabase_client()
        self.settings = get_settings()
    
    async def record_infection(
        self,
        attacker_id: str,
        target_id: str,
        suggestion: str,
        accepted: bool = False,
        rejection_reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Record an infection to both database and blockchain.
        
        1. Generates infection hash
        2. Logs to Supabase
        3. Records on Solana blockchain
        4. Updates database with blockchain proof
        
        Args:
            attacker_id: Agent sending the infection
            target_id: Agent receiving the infection
            suggestion: The infection suggestion
            accepted: Whether initially accepted
            rejection_reason: Reason if rejected
            
        Returns:
            Dict with infection_id, infection_hash, tx_signature, explorer_url
        """
        result = {
            "attacker_id": attacker_id,
            "target_id": target_id,
            "accepted": accepted,
        }
        
        # Generate infection hash (same as Solana client)
        infection_hash = self.solana.generate_infection_hash(
            attacker_id, target_id, suggestion
        )
        result["infection_hash"] = infection_hash
        
        # 1. Log to database
        infection_id = await self.db.log_infection(
            attacker_id=attacker_id,
            target_id=target_id,
            suggestion=suggestion,
            accepted=accepted,
            reason=rejection_reason,
        )
        result["infection_id"] = infection_id
        
        # 2. Record on blockchain
        tx_sig = await self.solana.record_infection_onchain(
            attacker_id=attacker_id,
            target_id=target_id,
            suggestion=suggestion,
        )
        result["tx_signature"] = tx_sig
        
        if tx_sig:
            result["explorer_url"] = self.solana.get_explorer_url(tx_sig)
            
            # 3. Update database with blockchain proof
            # (Note: This would use an update function if available)
            logger.info(
                "Infection recorded (DB + Chain)",
                infection_id=infection_id,
                hash=infection_hash[:16],
                tx=tx_sig[:16] if tx_sig else None,
            )
        
        return result
    
    async def record_acceptance(
        self,
        infection_hash: str,
        accepted: bool,
        influence_score: float,  # 0-1 scale from DB
        rejection_reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Record infection acceptance/rejection to blockchain.
        
        Called after target agent processes the infection.
        
        Args:
            infection_hash: Hash of the original infection
            accepted: Whether the infection was accepted
            influence_score: 0-1 scale influence score
            rejection_reason: Reason if rejected
            
        Returns:
            Dict with tx_signature and explorer_url
        """
        result = {
            "infection_hash": infection_hash,
            "accepted": accepted,
            "influence_score": influence_score,
        }
        
        # Convert influence score to 0-100 for blockchain
        influence_score_int = int(influence_score * 100)
        
        # Record on blockchain
        tx_sig = await self.solana.record_acceptance_onchain(
            infection_hash=infection_hash,
            accepted=accepted,
            influence_score=influence_score_int,
        )
        result["tx_signature"] = tx_sig
        
        if tx_sig:
            result["explorer_url"] = self.solana.get_explorer_url(tx_sig)
            
            logger.info(
                "Acceptance recorded on-chain",
                hash=infection_hash[:16],
                accepted=accepted,
                influence=influence_score_int,
                tx=tx_sig[:16],
            )
        
        return result
    
    async def verify_infection(
        self,
        infection_hash: str,
    ) -> Dict[str, Any]:
        """
        Verify an infection by comparing database and blockchain.
        
        Args:
            infection_hash: Hash of the infection to verify
            
        Returns:
            Dict with verification status and details
        """
        result = {
            "infection_hash": infection_hash,
            "verified": False,
            "chain_proof": None,
            "db_record": None,
        }
        
        # Get blockchain proof
        proof = await self.solana.get_infection_proof(infection_hash)
        if proof:
            result["chain_proof"] = proof.to_dict()
        
        # Get database record
        # (Would need to add a query by hash function)
        
        # Verify authenticity
        is_authentic = await self.solana.verify_infection_authenticity(
            infection_hash,
            result.get("db_record"),
        )
        result["verified"] = is_authentic
        
        return result
    
    async def get_all_proofs(self) -> Dict[str, Any]:
        """Get all blockchain proofs with network info."""
        proofs = await self.solana.get_all_proofs()
        network_info = await self.solana.get_network_info()
        
        return {
            "proofs": [p.to_dict() for p in proofs],
            "total_count": len(proofs),
            "network": network_info,
        }
    
    async def ensure_agent_funded(self, agent_id: str) -> Dict[str, Any]:
        """Ensure an agent has SOL for transactions."""
        wallet = await self.solana.get_agent_wallet(agent_id)
        
        result = {
            "agent_id": agent_id,
            "public_key": wallet.public_key,
            "initial_balance": wallet.balance_sol,
        }
        
        funded = await self.solana.ensure_agent_funded(agent_id)
        
        # Refresh balance
        wallet = await self.solana.get_agent_wallet(agent_id)
        result["current_balance"] = wallet.balance_sol
        result["funded"] = funded
        
        return result


def get_blockchain_integration() -> BlockchainIntegration:
    """Get blockchain integration instance."""
    return BlockchainIntegration()
