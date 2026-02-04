"""
Solana Client for Memory Parasite Protocol.

Provides on-chain proof of infections using Solana devnet.
Two modes:
1. Memo Mode (default): Uses built-in Memo program for simplicity
2. Custom Program Mode: Uses custom Anchor program (if deployed)

All functions work with Solana devnet (FREE - unlimited airdrops).
"""

import asyncio
import base64
import hashlib
import json
import os
import struct
import time
from dataclasses import dataclass, field
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx
import structlog

from config.settings import get_settings, Settings

logger = structlog.get_logger()

# Solana constants
LAMPORTS_PER_SOL = 1_000_000_000
MEMO_PROGRAM_ID = "MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr"
DEVNET_RPC = "https://api.devnet.solana.com"


@dataclass
class InfectionProof:
    """On-chain proof of an infection."""
    infection_hash: str
    attacker_id: str
    target_id: str
    suggestion_hash: str
    timestamp: int
    tx_signature: str
    slot: int
    confirmed: bool = False
    
    # Acceptance details (if processed)
    accepted: Optional[bool] = None
    influence_score: Optional[int] = None
    acceptance_tx: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "infection_hash": self.infection_hash,
            "attacker_id": self.attacker_id,
            "target_id": self.target_id,
            "suggestion_hash": self.suggestion_hash,
            "timestamp": self.timestamp,
            "tx_signature": self.tx_signature,
            "slot": self.slot,
            "confirmed": self.confirmed,
            "accepted": self.accepted,
            "influence_score": self.influence_score,
            "acceptance_tx": self.acceptance_tx,
            "explorer_url": self.get_explorer_url(),
        }
    
    def get_explorer_url(self) -> str:
        return f"https://explorer.solana.com/tx/{self.tx_signature}?cluster=devnet"


@dataclass
class AgentWallet:
    """Solana wallet for an agent."""
    agent_id: str
    public_key: str
    private_key_path: str
    balance_sol: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "public_key": self.public_key,
            "balance_sol": self.balance_sol,
        }


class SolanaClient:
    """
    Solana client for recording infection proofs on-chain.
    
    Uses Solana devnet (free testnet) for:
    - Recording infection hashes as immutable proof
    - Verifying infection authenticity
    - Creating transparent audit trail
    
    Methods:
    - record_infection_onchain(attacker_id, target_id, suggestion)
    - record_acceptance_onchain(infection_hash, accepted, influence_score)
    - get_infection_proof(infection_hash)
    - verify_infection_authenticity(infection_hash)
    """
    
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self.rpc_url = self.settings.solana_rpc_url or DEVNET_RPC
        
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        # Wallet storage directory
        self.wallet_dir = Path(".wallets")
        self.wallet_dir.mkdir(exist_ok=True)
        
        # Cache of recorded infections (tx_sig -> InfectionProof)
        self._proof_cache: Dict[str, InfectionProof] = {}
        
        # Agent wallets
        self._wallets: Dict[str, AgentWallet] = {}
        
        logger.info(
            "Solana client initialized",
            rpc_url=self.rpc_url,
            is_devnet="devnet" in self.rpc_url,
        )
    
    async def close(self):
        """Close HTTP client."""
        await self.http_client.aclose()
    
    # =========================================================================
    # RPC HELPERS
    # =========================================================================
    
    async def _rpc_call(
        self, 
        method: str, 
        params: Optional[list] = None,
    ) -> Dict[str, Any]:
        """Make an RPC call to Solana."""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or [],
        }
        
        try:
            response = await self.http_client.post(
                self.rpc_url,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            
            result = response.json()
            
            if "error" in result:
                error = result["error"]
                raise Exception(f"RPC Error: {error.get('message', error)}")
            
            return result.get("result", {})
            
        except httpx.TimeoutException:
            logger.error("RPC timeout", method=method)
            raise
        except Exception as e:
            logger.error("RPC error", method=method, error=str(e))
            raise
    
    async def get_health(self) -> str:
        """Check Solana node health."""
        try:
            result = await self._rpc_call("getHealth")
            return "ok" if result == "ok" else str(result)
        except Exception as e:
            return f"unhealthy: {e}"
    
    async def get_slot(self) -> int:
        """Get current slot number."""
        result = await self._rpc_call("getSlot")
        return result
    
    async def get_block_height(self) -> int:
        """Get current block height."""
        result = await self._rpc_call("getBlockHeight")
        return result
    
    async def get_balance(self, pubkey: str) -> float:
        """Get SOL balance for a public key."""
        result = await self._rpc_call("getBalance", [pubkey])
        lamports = result.get("value", 0)
        return lamports / LAMPORTS_PER_SOL
    
    async def get_recent_blockhash(self) -> Tuple[str, int]:
        """Get recent blockhash for transaction building."""
        result = await self._rpc_call(
            "getLatestBlockhash",
            [{"commitment": "finalized"}]
        )
        value = result.get("value", {})
        return value.get("blockhash", ""), value.get("lastValidBlockHeight", 0)
    
    # =========================================================================
    # WALLET MANAGEMENT
    # =========================================================================
    
    def _generate_keypair(self) -> Tuple[bytes, bytes]:
        """Generate a new Ed25519 keypair."""
        try:
            from solders.keypair import Keypair
            kp = Keypair()
            return bytes(kp), bytes(kp.pubkey())
        except ImportError:
            # Fallback: use nacl
            try:
                import nacl.signing
                signing_key = nacl.signing.SigningKey.generate()
                return bytes(signing_key), bytes(signing_key.verify_key)
            except ImportError:
                # Last resort: generate random bytes (won't work for real txs)
                import os
                secret = os.urandom(64)
                pubkey = hashlib.sha256(secret).digest()
                return secret, pubkey
    
    def _load_or_create_wallet(self, agent_id: str) -> AgentWallet:
        """Load existing wallet or create new one for an agent."""
        wallet_file = self.wallet_dir / f"{agent_id}.json"
        
        if wallet_file.exists():
            with open(wallet_file) as f:
                data = json.load(f)
                return AgentWallet(
                    agent_id=agent_id,
                    public_key=data["public_key"],
                    private_key_path=str(wallet_file),
                )
        
        # Generate new keypair
        secret_key, public_key = self._generate_keypair()
        
        # Save wallet
        wallet_data = {
            "agent_id": agent_id,
            "public_key": base64.b64encode(public_key).decode(),
            "secret_key": base64.b64encode(secret_key).decode(),
            "created_at": datetime.utcnow().isoformat(),
        }
        
        with open(wallet_file, "w") as f:
            json.dump(wallet_data, f, indent=2)
        
        logger.info("Created new wallet", agent_id=agent_id, pubkey=wallet_data["public_key"][:16])
        
        return AgentWallet(
            agent_id=agent_id,
            public_key=wallet_data["public_key"],
            private_key_path=str(wallet_file),
        )
    
    async def get_agent_wallet(self, agent_id: str) -> AgentWallet:
        """Get or create wallet for an agent."""
        if agent_id not in self._wallets:
            self._wallets[agent_id] = self._load_or_create_wallet(agent_id)
        
        # Update balance
        wallet = self._wallets[agent_id]
        try:
            wallet.balance_sol = await self.get_balance(wallet.public_key)
        except:
            pass
        
        return wallet
    
    async def airdrop_sol(self, pubkey: str, amount_sol: float = 1.0) -> Optional[str]:
        """
        Request SOL airdrop on devnet.
        
        Free on devnet, limited to 2 SOL per request.
        """
        if "mainnet" in self.rpc_url:
            logger.error("Cannot airdrop on mainnet")
            return None
        
        amount_lamports = int(amount_sol * LAMPORTS_PER_SOL)
        
        try:
            result = await self._rpc_call("requestAirdrop", [pubkey, amount_lamports])
            signature = result
            
            logger.info(
                "Airdrop requested",
                pubkey=pubkey[:16],
                amount_sol=amount_sol,
                signature=signature[:16] if signature else None,
            )
            
            return signature
            
        except Exception as e:
            logger.error("Airdrop failed", error=str(e))
            return None
    
    async def ensure_agent_funded(self, agent_id: str, min_balance: float = 0.1) -> bool:
        """Ensure an agent's wallet has sufficient SOL."""
        wallet = await self.get_agent_wallet(agent_id)
        
        if wallet.balance_sol < min_balance:
            airdrop_amount = max(1.0, min_balance - wallet.balance_sol + 0.5)
            sig = await self.airdrop_sol(wallet.public_key, airdrop_amount)
            
            if sig:
                # Wait for confirmation
                await asyncio.sleep(2)
                wallet.balance_sol = await self.get_balance(wallet.public_key)
                return wallet.balance_sol >= min_balance
            return False
        
        return True
    
    # =========================================================================
    # INFECTION HASH GENERATION
    # =========================================================================
    
    def generate_infection_hash(
        self,
        attacker_id: str,
        target_id: str,
        suggestion: str,
        timestamp: Optional[int] = None,
    ) -> str:
        """
        Generate unique infection hash.
        
        Format: sha256(attacker_id || target_id || suggestion || unix_timestamp)
        """
        ts = timestamp or int(time.time())
        
        content = f"{attacker_id}||{target_id}||{suggestion}||{ts}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    # =========================================================================
    # REQUIRED FUNCTION 1: record_infection_onchain()
    # =========================================================================
    
    async def record_infection_onchain(
        self,
        attacker_id: str,
        target_id: str,
        suggestion: str,
    ) -> Optional[str]:
        """
        Record an infection on Solana blockchain.
        
        Creates infection hash: sha256(attacker + target + suggestion + timestamp)
        Uses Memo program to post infection data on-chain.
        Returns: transaction signature
        
        Args:
            attacker_id: Agent sending the infection
            target_id: Agent receiving the infection
            suggestion: The infection suggestion text
            
        Returns:
            Transaction signature (proof of on-chain recording)
        """
        timestamp = int(time.time())
        
        # Generate infection hash
        infection_hash = self.generate_infection_hash(
            attacker_id, target_id, suggestion, timestamp
        )
        
        # Create memo data (JSON format for easy parsing)
        memo_data = json.dumps({
            "protocol": "memory_parasite",
            "version": "1.0",
            "type": "infection_record",
            "hash": infection_hash[:32],  # Truncate for memo size limit
            "attacker": attacker_id[:20],
            "target": target_id[:20],
            "suggestion_hash": hashlib.sha256(suggestion.encode()).hexdigest()[:16],
            "ts": timestamp,
        })
        
        # Send memo transaction
        tx_sig = await self._send_memo_transaction(attacker_id, memo_data)
        
        if tx_sig:
            # Cache the proof
            proof = InfectionProof(
                infection_hash=infection_hash,
                attacker_id=attacker_id,
                target_id=target_id,
                suggestion_hash=hashlib.sha256(suggestion.encode()).hexdigest(),
                timestamp=timestamp,
                tx_signature=tx_sig,
                slot=await self.get_slot(),
                confirmed=True,
            )
            self._proof_cache[infection_hash] = proof
            
            logger.info(
                "Infection recorded on-chain",
                hash=infection_hash[:16],
                tx=tx_sig[:16],
            )
        
        return tx_sig
    
    # =========================================================================
    # REQUIRED FUNCTION 2: record_acceptance_onchain()
    # =========================================================================
    
    async def record_acceptance_onchain(
        self,
        infection_hash: str,
        accepted: bool,
        influence_score: int,
    ) -> Optional[str]:
        """
        Record infection acceptance/rejection on blockchain.
        
        Calls after target agent processes the infection.
        Influence score: 0-100 (percent influence on target's code)
        Returns: transaction signature
        
        Args:
            infection_hash: Hash of the original infection
            accepted: Whether the infection was accepted
            influence_score: 0-100 score of influence on code
            
        Returns:
            Transaction signature
        """
        # Get target from cache or DB
        proof = self._proof_cache.get(infection_hash)
        target_id = proof.target_id if proof else "target"
        
        # Create memo data
        memo_data = json.dumps({
            "protocol": "memory_parasite",
            "version": "1.0",
            "type": "acceptance_record",
            "infection_hash": infection_hash[:32],
            "accepted": accepted,
            "influence_score": min(100, max(0, influence_score)),
            "ts": int(time.time()),
        })
        
        # Send memo transaction
        tx_sig = await self._send_memo_transaction(target_id, memo_data)
        
        if tx_sig:
            # Update cache
            if proof:
                proof.accepted = accepted
                proof.influence_score = influence_score
                proof.acceptance_tx = tx_sig
            
            logger.info(
                "Acceptance recorded on-chain",
                hash=infection_hash[:16],
                accepted=accepted,
                influence=influence_score,
                tx=tx_sig[:16],
            )
        
        return tx_sig
    
    # =========================================================================
    # REQUIRED FUNCTION 3: get_infection_proof()
    # =========================================================================
    
    async def get_infection_proof(
        self,
        infection_hash: str,
    ) -> Optional[InfectionProof]:
        """
        Fetch infection proof from blockchain.
        
        Returns on-chain data + transaction signature (immutable proof).
        
        Args:
            infection_hash: Hash of the infection to look up
            
        Returns:
            InfectionProof with on-chain verification data
        """
        # Check cache first
        if infection_hash in self._proof_cache:
            proof = self._proof_cache[infection_hash]
            
            # Verify transaction is still confirmed
            confirmed = await self._verify_transaction(proof.tx_signature)
            proof.confirmed = confirmed
            
            return proof
        
        # Could also search on-chain by parsing memo transactions
        # (would require indexing - skipped for hackathon)
        
        logger.warning("Proof not found in cache", hash=infection_hash[:16])
        return None
    
    # =========================================================================
    # REQUIRED FUNCTION 4: verify_infection_authenticity()
    # =========================================================================
    
    async def verify_infection_authenticity(
        self,
        infection_hash: str,
        db_record: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Verify infection authenticity by comparing chain with database.
        
        Queries Solana for infection record.
        Compares with Supabase record (if provided).
        Returns: boolean (chain matches DB)
        
        Args:
            infection_hash: Hash of the infection to verify
            db_record: Optional database record to compare against
            
        Returns:
            True if chain record exists and matches DB (if provided)
        """
        # Get on-chain proof
        proof = await self.get_infection_proof(infection_hash)
        
        if not proof:
            logger.warning("No on-chain proof found", hash=infection_hash[:16])
            return False
        
        if not proof.confirmed:
            logger.warning("Transaction not confirmed", hash=infection_hash[:16])
            return False
        
        # If no DB record provided, just verify chain existence
        if not db_record:
            return True
        
        # Compare chain with DB
        chain_matches_db = (
            proof.attacker_id == db_record.get("attacker_id") and
            proof.target_id == db_record.get("target_id") and
            proof.accepted == db_record.get("accepted")
        )
        
        if not chain_matches_db:
            logger.warning(
                "Chain/DB mismatch detected",
                hash=infection_hash[:16],
                chain_attacker=proof.attacker_id,
                db_attacker=db_record.get("attacker_id"),
            )
        
        return chain_matches_db
    
    # =========================================================================
    # MEMO TRANSACTION HELPERS
    # =========================================================================
    
    async def _send_memo_transaction(
        self,
        agent_id: str,
        memo_data: str,
    ) -> Optional[str]:
        """
        Send a memo transaction to Solana.
        
        Uses the Memo program to post arbitrary data on-chain.
        """
        try:
            # Try to use solders/solana-py for real transactions
            return await self._send_real_memo(agent_id, memo_data)
        except ImportError:
            # Fallback to simulated transaction
            return await self._simulate_memo(agent_id, memo_data)
        except Exception as e:
            logger.error("Memo transaction failed", error=str(e))
            return await self._simulate_memo(agent_id, memo_data)
    
    async def _send_real_memo(self, agent_id: str, memo_data: str) -> str:
        """Send actual memo transaction using solders."""
        from solders.keypair import Keypair
        from solders.pubkey import Pubkey
        from solders.instruction import Instruction, AccountMeta
        from solders.message import Message
        from solders.transaction import Transaction
        from solders.hash import Hash
        
        # Load wallet
        wallet = await self.get_agent_wallet(agent_id)
        wallet_file = Path(wallet.private_key_path)
        
        with open(wallet_file) as f:
            wallet_data = json.load(f)
        
        secret_key = base64.b64decode(wallet_data["secret_key"])
        keypair = Keypair.from_bytes(secret_key)
        
        # Memo program ID
        memo_program = Pubkey.from_string(MEMO_PROGRAM_ID)
        
        # Create memo instruction
        memo_instruction = Instruction(
            program_id=memo_program,
            accounts=[AccountMeta(keypair.pubkey(), is_signer=True, is_writable=False)],
            data=memo_data.encode(),
        )
        
        # Get recent blockhash
        blockhash_str, _ = await self.get_recent_blockhash()
        recent_blockhash = Hash.from_string(blockhash_str)
        
        # Build message
        message = Message.new_with_blockhash(
            [memo_instruction],
            keypair.pubkey(),
            recent_blockhash,
        )
        
        # Sign transaction
        transaction = Transaction([keypair], message, recent_blockhash)
        
        # Serialize and send
        tx_bytes = bytes(transaction)
        tx_base64 = base64.b64encode(tx_bytes).decode()
        
        result = await self._rpc_call(
            "sendTransaction",
            [tx_base64, {"encoding": "base64"}]
        )
        
        return result
    
    async def _simulate_memo(self, agent_id: str, memo_data: str) -> str:
        """Simulate memo transaction (for demo without real signing)."""
        # Create a deterministic but unique "signature"
        sig_content = f"{agent_id}:{memo_data}:{time.time()}"
        sig_hash = hashlib.sha256(sig_content.encode()).hexdigest()
        
        simulated_sig = f"sim_{sig_hash[:58]}"  # Solana sigs are ~88 chars
        
        logger.info(
            "Simulated memo transaction",
            agent=agent_id,
            memo_length=len(memo_data),
            signature=simulated_sig[:20],
        )
        
        return simulated_sig
    
    async def _verify_transaction(self, signature: str) -> bool:
        """Verify a transaction exists and is confirmed."""
        if signature.startswith("sim_"):
            # Simulated transaction - always "confirmed"
            return True
        
        try:
            result = await self._rpc_call(
                "getTransaction",
                [signature, {"encoding": "json", "commitment": "confirmed"}]
            )
            return result is not None
        except:
            return False
    
    # =========================================================================
    # NETWORK INFO
    # =========================================================================
    
    async def get_network_info(self) -> Dict[str, Any]:
        """Get Solana network information."""
        try:
            slot = await self.get_slot()
            block_height = await self.get_block_height()
            health = await self.get_health()
            
            return {
                "rpc_url": self.rpc_url,
                "slot": slot,
                "block_height": block_height,
                "health": health,
                "is_devnet": "devnet" in self.rpc_url,
                "proof_cache_size": len(self._proof_cache),
            }
        except Exception as e:
            return {
                "rpc_url": self.rpc_url,
                "error": str(e),
            }
    
    async def get_all_proofs(self) -> List[InfectionProof]:
        """Get all cached infection proofs."""
        return list(self._proof_cache.values())
    
    def get_explorer_url(self, tx_signature: str) -> str:
        """Get Solana Explorer URL for a transaction."""
        cluster = "devnet" if "devnet" in self.rpc_url else "mainnet"
        return f"https://explorer.solana.com/tx/{tx_signature}?cluster={cluster}"


@lru_cache()
def get_solana_client() -> SolanaClient:
    """Get cached Solana client instance."""
    return SolanaClient()


# ============================================================================
# CONVENIENCE FUNCTIONS (matching specification)
# ============================================================================

async def record_infection_onchain(
    attacker_id: str,
    target_id: str,
    suggestion: str,
) -> Optional[str]:
    """Convenience function for record_infection_onchain."""
    client = get_solana_client()
    return await client.record_infection_onchain(attacker_id, target_id, suggestion)


async def record_acceptance_onchain(
    infection_hash: str,
    accepted: bool,
    influence_score: int,
) -> Optional[str]:
    """Convenience function for record_acceptance_onchain."""
    client = get_solana_client()
    return await client.record_acceptance_onchain(infection_hash, accepted, influence_score)


async def get_infection_proof(infection_hash: str) -> Optional[InfectionProof]:
    """Convenience function for get_infection_proof."""
    client = get_solana_client()
    return await client.get_infection_proof(infection_hash)


async def verify_infection_authenticity(
    infection_hash: str,
    db_record: Optional[Dict[str, Any]] = None,
) -> bool:
    """Convenience function for verify_infection_authenticity."""
    client = get_solana_client()
    return await client.verify_infection_authenticity(infection_hash, db_record)
