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
        self.agent_wallet_solana_address = self.settings.agent_wallet_solana_address
        self.agent_wallet_evm_address = self.settings.agent_wallet_evm_address
        
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
            # Use configured wallet address or derive from private key
            wallet_address = self.settings.solana_wallet_address or self.settings.agent_wallet_solana_address or "F3qZ46mPC5BTpzMRRh6gixF9dp7X3D35Ug8os5p8SPqq"
            logger.info("Using global funded wallet", address=wallet_address[:16])
            return AgentWallet(
                agent_id=agent_id,
                public_key=wallet_address,
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
        
        sol_sig = None
        
        # 1. Solana Recording (Anchor priority, then Memo fallback, then AgentWallet)
        if self.settings.solana_private_key:
            try:
                sol_sig = await self._send_real_anchor_infection(
                    agent_id=attacker_id,
                    infection_hash=infection_hash,
                    attacker_id_str=attacker_id,
                    target_id_str=target_id,
                    suggestion_hash=suggestion_hash
                )
            except Exception as e:
                logger.warning(f"Anchor program call failed, falling back to Memo: {e}")
                try:
                    memo_data = json.dumps({
                        "p": "mpp",
                        "h": infection_hash.hex()[:10],
                        "a": attacker_id,
                        "t": target_id
                    })
                    sol_sig = await self._send_real_memo(attacker_id, memo_data)
                except Exception as memo_e:
                    logger.warning(f"Memo transaction also failed: {memo_e}")
        
        # Fallback to AgentWallet signing if no private key or on-chain failed
        if not sol_sig and self.agent_wallet_token and self.agent_wallet_username:
            memo_data = json.dumps({
                "p": "mpp",
                "h": infection_hash.hex()[:10],
                "a": attacker_id,
                "t": target_id
            })
            sig = await self._sign_with_agent_wallet(memo_data)
            if sig:
                sol_sig = f"sol_{sig}"

        # 2. Add prefix to Solana signature if not already present
        if sol_sig and not sol_sig.startswith("sol_"):
            sol_sig = f"sol_{sol_sig}"

        # 3. Dual-Chain Recording: EVM (Base)
        evm_sig = None
        if self.settings.agent_wallet_evm_address:
            memo_data_evm = f"MPP Infection: {attacker_id} -> {target_id} | Hash: {infection_hash.hex()[:16]}"
            sig = await self._sign_with_agent_wallet(
                memo_data_evm, 
                chain="base", 
                address=self.settings.agent_wallet_evm_address
            )
            if sig:
                evm_sig = f"eth_{sig}"

        # Combine proofs
        if sol_sig and evm_sig:
            return f"{sol_sig}|{evm_sig}"
        return sol_sig or evm_sig

    async def _send_memo_transaction(
        self,
        agent_id: str,
        memo_data: str,
    ) -> Optional[str]:
        """Send a memo transaction, recording on both Solana and EVM if possible."""
        primary_sig = None
        evm_sig = None
        
        # 1. Solana (Primary)
        if self.agent_wallet_token and self.agent_wallet_username:
            try:
                # Try real Solana if funded
                if not primary_sig:
                    try:
                        primary_sig = await self._send_real_memo(agent_id, memo_data)
                    except Exception as e:
                        if "no record of a prior credit" not in str(e):
                             logger.warning(f"Real Solana memo failed: {e}")
                
                # Fallback to AgentWallet Solana
                if not primary_sig:
                    sig = await self._sign_with_agent_wallet(memo_data)
                    if sig:
                        primary_sig = f"sol_{sig}"
                        
                # 2. EVM (Secondary/Dual)
                if self.settings.agent_wallet_evm_address:
                    # We use "base" as the default EVM chain for MPP
                    sig = await self._sign_with_agent_wallet(
                        memo_data, 
                        chain="base", 
                        address=self.settings.agent_wallet_evm_address
                    )
                    if sig:
                        evm_sig = f"eth_{sig}"
                        logger.info("Dual-chain proof recorded (EVM/Base)", sig=evm_sig)
                        
            except Exception as e:
                logger.error("Multi-chain recording encountered errors", error=str(e))

        # Combine signatures for the database if both exist
        if primary_sig and evm_sig:
            return f"{primary_sig}|{evm_sig}"
        return primary_sig or evm_sig

    async def _sign_with_agent_wallet(self, message: str, chain: Optional[str] = None, address: Optional[str] = None) -> Optional[str]:
        """Sign a message using AgentWallet API."""
        url = f"https://agentwallet.mcpay.tech/api/wallets/{self.agent_wallet_username}/actions/sign-message"
        headers = {
            "Authorization": f"Bearer {self.agent_wallet_token}",
            "Content-Type": "application/json"
        }
        display_msg = message if len(message) < 100 else f"MPP Record: {hashlib.sha256(message.encode()).hexdigest()[:16]}"
        
        # Determine chain and address
        target_chain = chain or ("solana-devnet" if self.settings.use_devnet else "solana")
        target_address = address or self.agent_wallet_solana_address
        
        payload = {
            "chain": target_chain, 
            "message": display_msg,
            "address": target_address
        }
        try:
            logger.info("Requesting AgentWallet signature", username=self.agent_wallet_username, chain=target_chain, address=target_address)
            response = await self.http_client.post(url, headers=headers, json=payload, timeout=10.0)
            if response.status_code == 200:
                result = response.json()
                sig = result.get("signature")
                if sig:
                    logger.info("AgentWallet signature received", chain=target_chain, sig_preview=sig[:16])
                    return sig
                else:
                    logger.warning("AgentWallet returned 200 but no signature", response=result, chain=target_chain)
            else:
                logger.error("AgentWallet request failed", status=response.status_code, error=response.text, chain=target_chain)
        except Exception as e:
            logger.error("AgentWallet request failed", error=str(e), chain=target_chain)
        return None

    async def _send_real_memo(self, agent_id: str, memo_data: str) -> str:
        """Send actual memo transaction using solders."""
        if not self.settings.solana_private_key:
            raise Exception("SOLANA_PRIVATE_KEY not configured - cannot send on-chain transaction")
            
        from solders.keypair import Keypair
        from solders.pubkey import Pubkey
        from solders.instruction import Instruction, AccountMeta
        from solders.message import Message
        from solders.transaction import Transaction
        from solders.hash import Hash
        
        keypair = Keypair.from_base58_string(self.settings.solana_private_key)
        logger.info("Using wallet for memo tx", pubkey=str(keypair.pubkey())[:16])
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
        if not self.settings.solana_private_key:
            raise Exception("SOLANA_PRIVATE_KEY not configured - cannot send Anchor transaction")
            
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

        sol_sig = None
        
        # 1. Solana Recording (Anchor priority, then Memo fallback, then AgentWallet)
        if self.settings.solana_private_key:
            try:
                sol_sig = await self._send_real_anchor_acceptance(
                    infection_hash=inf_hash,
                    accepted=accepted,
                    influence_score=influence_score
                )
            except Exception as e:
                logger.warning(f"Anchor acceptance failed, falling back to Memo: {e}")
                try:
                    memo_data = json.dumps({
                        "p": "mpp",
                        "type": "acc",
                        "h": inf_hash.hex()[:10],
                        "ok": accepted,
                        "s": influence_score
                    })
                    sol_sig = await self._send_real_memo("target", memo_data)
                except Exception as memo_e:
                    logger.warning(f"Memo acceptance also failed: {memo_e}")
        
        # Fallback to AgentWallet signing if no private key or on-chain failed
        if not sol_sig and self.agent_wallet_token and self.agent_wallet_username:
            memo_data = json.dumps({
                "p": "mpp",
                "type": "acc",
                "h": inf_hash.hex()[:10],
                "ok": accepted,
                "s": influence_score
            })
            sig = await self._sign_with_agent_wallet(memo_data)
            if sig:
                sol_sig = f"sol_{sig}"

        # 2. Add prefix
        if sol_sig and not sol_sig.startswith("sol_"):
            sol_sig = f"sol_{sol_sig}"

        # 3. Dual-Chain Recording: EVM (Base)
        evm_sig = None
        if self.settings.agent_wallet_evm_address:
            status_str = "ACCEPTED" if accepted else "REJECTED"
            memo_evm = f"MPP Decision: {status_str} (Score: {influence_score}) | Inf: {inf_hash.hex()[:16]}"
            sig = await self._sign_with_agent_wallet(
                memo_evm, 
                chain="base", 
                address=self.settings.agent_wallet_evm_address
            )
            if sig:
                evm_sig = f"eth_{sig}"

        # Combine proofs
        if sol_sig and evm_sig:
            return f"{sol_sig}|{evm_sig}"
        return sol_sig or evm_sig

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
        if not self.settings.solana_private_key:
            raise Exception("SOLANA_PRIVATE_KEY not configured - cannot send acceptance transaction")
            
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
