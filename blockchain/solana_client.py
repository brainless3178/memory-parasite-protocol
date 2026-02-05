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
import base58

from config.settings import get_settings, Settings

logger = structlog.get_logger()

# Solana constants
LAMPORTS_PER_SOL = 1_000_000_000
# The primary infection ledger program (Custom Anchor Program)
CUSTOM_PROGRAM_ID = "EqK3ABABJTT1dtSyNUmbK2omUF5s9LNctViCbPrs5sar"
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
        
        # AgentWallet (Hackathon Compliance)
        self.agent_wallet_token = self.settings.agent_wallet_token
        self.agent_wallet_username = self.settings.agent_wallet_username
        self.agent_wallet_address = self.settings.agent_wallet_solana_address
        
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
    
    def _generate_keypair(self) -> Tuple[bytes, str]:
        """Generate a new Ed25519 keypair and return (secret_bytes, pubkey_base58)."""
        try:
            from solders.keypair import Keypair
            kp = Keypair()
            return bytes(kp), str(kp.pubkey())
        except ImportError:
            # Fallback: use nacl
            try:
                import nacl.signing
                signing_key = nacl.signing.SigningKey.generate()
                pubkey_bytes = bytes(signing_key.verify_key)
                return bytes(signing_key), base58.b58encode(pubkey_bytes).decode()
            except ImportError:
                import os
                secret = os.random(64)
                pubkey = hashlib.sha256(secret).digest()
                return secret, base58.b58encode(pubkey).decode()
    
    def _load_or_create_wallet(self, agent_id: str) -> AgentWallet:
        """Load global wallet from env or load/create agent-specific local wallet."""
        # 1. Check for global private key first (Hackathon/Environment preference)
        # This allows all agents to use ONE funded wallet instead of many unfunded ones.
        if self.settings.solana_private_key:
            return AgentWallet(
                agent_id=agent_id,
                public_key=os.getenv("SOLANA_PUBLIC_KEY", "Global Wallet"),
                private_key_path="env:SOLANA_PRIVATE_KEY"
            )

        # 2. Fall back to local storage
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
        secret_key, public_key_b58 = self._generate_keypair()
        
        # Save wallet
        wallet_data = {
            "agent_id": agent_id,
            "public_key": public_key_b58,
            "secret_key": base64.b64encode(secret_key).decode(),
            "created_at": datetime.utcnow().isoformat(),
        }
        
        with open(wallet_file, "w") as f:
            json.dump(wallet_data, f, indent=2)
        
        logger.info("Created new wallet", agent_id=agent_id, pubkey=public_key_b58[:16])
        
        return AgentWallet(
            agent_id=agent_id,
            public_key=public_key_b58,
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
    
    async def record_infection_onchain(
        self,
        attacker_id: str,
        target_id: str,
        suggestion: str,
    ) -> Optional[str]:
        """Record an infection on Solana blockchain using the CUSTOM program."""
        timestamp = int(time.time())
        
        # Generate hashes
        content = f"{attacker_id}||{target_id}||{suggestion}||{timestamp}"
        infection_hash = hashlib.sha256(content.encode()).digest()
        suggestion_hash = hashlib.sha256(suggestion.encode()).digest()
        
        # 1. Try Custom Anchor Program (The 'Real' Infrastructure)
        try:
            tx_sig = await self._send_real_anchor_infection(
                agent_id=attacker_id,
                infection_hash=infection_hash,
                attacker_id_str=attacker_id,
                target_id_str=target_id,
                suggestion_hash=suggestion_hash
            )
            if tx_sig:
                return tx_sig
        except Exception as e:
            logger.warning(f"Anchor program call failed, falling back to Memo: {e}")

        # 2. Fallback to Memo Program if Anchor fails (for resilience)
        memo_data = json.dumps({
            "p": "mpp",
            "h": infection_hash.hex()[:10],
            "a": attacker_id,
            "t": target_id
        })
        return await self._send_memo_transaction(attacker_id, memo_data)

    async def _send_memo_transaction(
        self,
        agent_id: str,
        memo_data: str,
    ) -> Optional[str]:
        """Send a memo transaction, prioritizing AgentWallet then local wallet."""
        # 1. Try AgentWallet signing first (Hackathon compliant)
        aw_sig = None
        if self.agent_wallet_token and self.agent_wallet_username:
            try:
                sig = await self._sign_with_agent_wallet(memo_data)
                if sig:
                    aw_sig = f"aw_{sig}"
            except Exception as e:
                logger.error("AgentWallet signing failed", error=str(e))

        # 2. Try to record on real Solana chain (if agents have SOL)
        try:
            tx_sig = await self._send_real_memo(agent_id, memo_data)
            if tx_sig:
                return tx_sig
        except Exception as e:
            err_str = str(e)
            if "no record of a prior credit" in err_str or "0x1" in err_str:
                logger.warning("Wallet has 0 SOL - skipping on-chain recording")
            else:
                logger.error("Real memo transaction failed", error=err_str)

        # 3. Fallback
        if aw_sig:
            return aw_sig
            
        return None

    async def _sign_with_agent_wallet(self, message: str) -> Optional[str]:
        """Sign a message using AgentWallet API."""
        url = f"https://agentwallet.mcpay.tech/api/wallets/{self.agent_wallet_username}/actions/sign-message"
        headers = {
            "Authorization": f"Bearer {self.agent_wallet_token}",
            "Content-Type": "application/json"
        }
        display_msg = message if len(message) < 100 else f"MPP Record: {hashlib.sha256(message.encode()).hexdigest()[:16]}"
        payload = {"chain": "solana", "message": display_msg}
        try:
            response = await self.http_client.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                result = response.json()
                return result.get("signature")
        except Exception as e:
            logger.error("AgentWallet request failed", error=str(e))
        return None

    async def _send_real_memo(self, agent_id: str, memo_data: str) -> str:
        """Send actual memo transaction using solders."""
        from solders.keypair import Keypair
        from solders.pubkey import Pubkey
        from solders.instruction import Instruction, AccountMeta
        from solders.message import Message
        from solders.transaction import Transaction
        from solders.hash import Hash
        
        keypair = Keypair.from_base58_string(self.settings.solana_private_key)
        memo_program = Pubkey.from_string(MEMO_PROGRAM_ID)
        
        ix = Instruction(
            program_id=memo_program,
            accounts=[AccountMeta(keypair.pubkey(), is_signer=True, is_writable=False)],
            data=memo_data.encode(),
        )
        
        blockhash_str, _ = await self.get_recent_blockhash()
        recent_blockhash = Hash.from_string(blockhash_str)
        message = Message.new_with_blockhash([ix], keypair.pubkey(), recent_blockhash)
        transaction = Transaction([keypair], message, recent_blockhash)
        
        tx_bytes = bytes(transaction)
        tx_base64 = base64.b64encode(tx_bytes).decode()
        result = await self._rpc_call("sendTransaction", [tx_base64, {"encoding": "base64"}])
        return result

    async def _send_real_anchor_infection(
        self,
        agent_id: str,
        infection_hash: bytes,
        attacker_id_str: str,
        target_id_str: str,
        suggestion_hash: bytes,
    ) -> str:
        """
        Send a REAL Anchor instruction to our custom program.
        Instruction: record_infection(infection_hash, attacker_id, target_id, suggestion_hash)
        """
        from solders.keypair import Keypair
        from solders.pubkey import Pubkey
        from solders.instruction import Instruction, AccountMeta
        from solders.message import Message
        from solders.transaction import Transaction
        from solders.hash import Hash
        
        # 1. Prepare Anchor Data
        # Discriminator (SHA256 of "global:record_infection")[:8]
        # b'\x1c\xedA\xc4[\x8b\xd1\xe2' -> [28, 237, 65, 196, 91, 139, 209, 226]
        discriminator = bytes([28, 237, 65, 196, 91, 139, 209, 226])
        
        # Pack strings (4 bytes length + content)
        def pack_string(s):
            b = s.encode('utf-8')
            return struct.pack("<I", len(b)) + b

        data = (
            discriminator + 
            infection_hash + 
            pack_string(attacker_id_str[:32]) + 
            pack_string(target_id_str[:32]) + 
            suggestion_hash
        )

        # 2. Derive PDA for the infection account
        program_id = Pubkey.from_string(CUSTOM_PROGRAM_ID)
        infection_pda, _ = Pubkey.find_program_address(
            [b"infection", infection_hash],
            program_id
        )

        # 3. Load Wallet
        wallet = await self.get_agent_wallet(agent_id)
        keypair = Keypair.from_base58_string(self.settings.solana_private_key)

        # 4. Build Instruction
        ix = Instruction(
            program_id=program_id,
            accounts=[
                AccountMeta(infection_pda, is_signer=False, is_writable=True),
                AccountMeta(keypair.pubkey(), is_signer=True, is_writable=True),
                AccountMeta(Pubkey.from_string("11111111111111111111111111111111"), is_signer=False, is_writable=False), # System Program
            ],
            data=data,
        )

        # 5. Send Transaction
        blockhash_str, _ = await self.get_recent_blockhash()
        recent_blockhash = Hash.from_string(blockhash_str)
        
        message = Message.new_with_blockhash([ix], keypair.pubkey(), recent_blockhash)
        transaction = Transaction([keypair], message, recent_blockhash)
        
        tx_bytes = bytes(transaction)
        tx_base64 = base64.b64encode(tx_bytes).decode()
        
        result = await self._rpc_call("sendTransaction", [tx_base64, {"encoding": "base64"}])
        return result

    async def get_health(self) -> str:
        """Check Solana node health."""
        try:
            result = await self._rpc_call("getHealth")
            return "ok" if result == "ok" else str(result)
        except Exception as e:
            return f"unhealthy: {e}"

    async def get_slot(self) -> int:
        """Get current slot number."""
        return await self._rpc_call("getSlot")

    async def get_block_height(self) -> int:
        """Get current block height."""
        return await self._rpc_call("getBlockHeight")

    async def record_acceptance_onchain(
        self,
        infection_hash_str: str,
        accepted: bool,
        influence_score: int
    ) -> Optional[str]:
        """Record acceptance on-chain using the CUSTOM program."""
        # Convert hex string to bytes
        try:
            inf_hash = bytes.fromhex(infection_hash_str)
        except:
            # If it's already a small hash or id, pad it
            inf_hash = hashlib.sha256(infection_hash_str.encode()).digest()

        # 1. Try Custom Anchor Program
        try:
            tx_sig = await self._send_real_anchor_acceptance(
                infection_hash=inf_hash,
                accepted=accepted,
                influence_score=influence_score
            )
            if tx_sig:
                return tx_sig
        except Exception as e:
            logger.warning(f"Anchor acceptance failed, falling back to Memo: {e}")

        # 2. Fallback to Memo
        memo_data = json.dumps({
            "p": "mpp",
            "type": "acc",
            "h": inf_hash.hex()[:10],
            "ok": accepted,
            "s": influence_score
        })
        return await self._send_memo_transaction("target", memo_data)

    async def _send_real_anchor_acceptance(
        self,
        infection_hash: bytes,
        accepted: bool,
        influence_score: int,
    ) -> str:
        """
        Send a REAL Anchor instruction to record acceptance.
        Instruction: record_acceptance(infection_hash, accepted, influence_score)
        """
        from solders.keypair import Keypair
        from solders.pubkey import Pubkey
        from solders.instruction import Instruction, AccountMeta
        from solders.message import Message
        from solders.transaction import Transaction
        from solders.hash import Hash
        
        # 1. Prepare Anchor Data
        # Discriminator (SHA256 of "global:record_acceptance")[:8]
        # [212, 118, 89, 194, 195, 189, 131, 15]
        discriminator = bytes([212, 118, 89, 194, 195, 189, 131, 15])
        
        # Data: [inf_hash(32)] + [accepted(1)] + [influence_score(1)]
        # Anchor handles bools as 1 byte, influence_score is u8 (1 byte)
        data = (
            discriminator + 
            infection_hash + 
            (b'\x01' if accepted else b'\x00') + 
            struct.pack("B", influence_score)
        )

        # 2. Derive PDA for the infection account
        program_id = Pubkey.from_string(CUSTOM_PROGRAM_ID)
        infection_pda, _ = Pubkey.find_program_address(
            [b"infection", infection_hash],
            program_id
        )

        # 3. Load Wallet (Using global key for simplicity in acceptance)
        keypair = Keypair.from_base58_string(self.settings.solana_private_key)

        # 4. Build Instruction
        ix = Instruction(
            program_id=program_id,
            accounts=[
                AccountMeta(infection_pda, is_signer=False, is_writable=True),
                AccountMeta(keypair.pubkey(), is_signer=True, is_writable=True),
            ],
            data=data,
        )

        # 5. Send Transaction
        blockhash_str, _ = await self.get_recent_blockhash()
        recent_blockhash = Hash.from_string(blockhash_str)
        
        message = Message.new_with_blockhash([ix], keypair.pubkey(), recent_blockhash)
        transaction = Transaction([keypair], message, recent_blockhash)
        
        tx_bytes = bytes(transaction)
        tx_base64 = base64.b64encode(tx_bytes).decode()
        
        result = await self._rpc_call("sendTransaction", [tx_base64, {"encoding": "base64"}])
        return result

    async def get_infection_proof(self, infection_hash: str) -> Optional[InfectionProof]:
        """Fetch proof from cache."""
        return self._proof_cache.get(infection_hash)

    async def verify_infection_authenticity(self, infection_hash: str, db_record: Optional[Dict] = None) -> bool:
        """Simple verification."""
        return infection_hash in self._proof_cache

    async def get_network_info(self) -> Dict[str, Any]:
        """Get network info."""
        try:
            return {
                "rpc_url": self.rpc_url,
                "health": await self.get_health(),
                "slot": await self.get_slot(),
                "is_devnet": "devnet" in self.rpc_url
            }
        except:
            return {"rpc_url": self.rpc_url, "error": "failed to fetch network info"}

@lru_cache()
def get_solana_client() -> SolanaClient:
    """Get cached Solana client instance."""
    return SolanaClient()

# Convenience functions
async def record_infection_onchain(attacker_id: str, target_id: str, suggestion: str) -> Optional[str]:
    return await get_solana_client().record_infection_onchain(attacker_id, target_id, suggestion)

async def record_acceptance_onchain(infection_hash: str, accepted: bool, influence_score: int) -> Optional[str]:
    return await get_solana_client().record_acceptance_onchain(infection_hash, accepted, influence_score)

async def get_infection_proof(infection_hash: str) -> Optional[InfectionProof]:
    return await get_solana_client().get_infection_proof(infection_hash)

async def verify_infection_authenticity(infection_hash: str, db_record: Optional[Dict] = None) -> bool:
    return await get_solana_client().verify_infection_authenticity(infection_hash, db_record)
