"""
Solana Blockchain Integration Demo for Memory Parasite Protocol.

This script demonstrates all required blockchain functions:
- record_infection_onchain(attacker_id, target_id, suggestion)
- record_acceptance_onchain(infection_hash, accepted, influence_score)
- get_infection_proof(infection_hash)
- verify_infection_authenticity(infection_hash)

Run with: PYTHONPATH=. python examples/demo_solana.py
"""

import asyncio
import json
from datetime import datetime

from blockchain import (
    get_solana_client,
    record_infection_onchain,
    record_acceptance_onchain,
    get_infection_proof,
    verify_infection_authenticity,
    BlockchainIntegration,
)


def print_header(title: str):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_json(data, indent=2):
    if hasattr(data, 'to_dict'):
        data = data.to_dict()
    print(json.dumps(data, indent=indent, default=str))


async def main():
    """Demonstrate all Solana blockchain operations."""
    
    print_header("🔗 Memory Parasite Protocol - Solana Demo")
    print("\nUsing Solana DEVNET (free testnet)")
    print("All transactions create immutable proof of infections.\n")
    
    # Get client
    client = get_solana_client()
    
    # =========================================================================
    # Network Info
    # =========================================================================
    print_header("Network Information")
    
    try:
        network_info = await client.get_network_info()
        print_json(network_info)
    except Exception as e:
        print(f"  Note: Could not connect to Solana RPC: {e}")
        print("  Continuing with simulated transactions...\n")
    
    # =========================================================================
    # 1. record_infection_onchain(attacker_id, target_id, suggestion)
    # =========================================================================
    print_header("1. record_infection_onchain()")
    print("Records infection hash on Solana blockchain.\n")
    
    # Infection 1: Alpha -> Beta
    tx_sig_1 = await record_infection_onchain(
        attacker_id="agent_alpha",
        target_id="agent_beta",
        suggestion="Add token swap functionality to your NFT marketplace for seamless trading"
    )
    print(f"Infection 1: agent_alpha → agent_beta")
    print(f"  TX Signature: {tx_sig_1}")
    print(f"  Explorer: {client.get_explorer_url(tx_sig_1)}")
    
    # Infection 2: Gamma -> Alpha
    tx_sig_2 = await record_infection_onchain(
        attacker_id="agent_gamma",
        target_id="agent_alpha",
        suggestion="Integrate lending pool liquidity to improve your DEX capital efficiency"
    )
    print(f"\nInfection 2: agent_gamma → agent_alpha")
    print(f"  TX Signature: {tx_sig_2}")
    print(f"  Explorer: {client.get_explorer_url(tx_sig_2)}")
    
    # Get the infection hashes for later use
    infection_hash_1 = client.generate_infection_hash(
        "agent_alpha", "agent_beta",
        "Add token swap functionality to your NFT marketplace for seamless trading"
    )
    infection_hash_2 = client.generate_infection_hash(
        "agent_gamma", "agent_alpha",
        "Integrate lending pool liquidity to improve your DEX capital efficiency"
    )
    
    print(f"\nGenerated Hashes:")
    print(f"  Infection 1: {infection_hash_1[:32]}...")
    print(f"  Infection 2: {infection_hash_2[:32]}...")
    
    # =========================================================================
    # 2. record_acceptance_onchain(infection_hash, accepted, influence_score)
    # =========================================================================
    print_header("2. record_acceptance_onchain()")
    print("Records target's decision on blockchain.\n")
    
    # Accept infection 1 with high influence
    tx_accept_1 = await record_acceptance_onchain(
        infection_hash=infection_hash_1,
        accepted=True,
        influence_score=75  # 75% influence
    )
    print(f"Infection 1 ACCEPTED (75% influence)")
    print(f"  TX Signature: {tx_accept_1}")
    
    # Reject infection 2 with no influence
    tx_accept_2 = await record_acceptance_onchain(
        infection_hash=infection_hash_2,
        accepted=False,
        influence_score=0
    )
    print(f"\nInfection 2 REJECTED (0% influence)")
    print(f"  TX Signature: {tx_accept_2}")
    
    # =========================================================================
    # 3. get_infection_proof(infection_hash)
    # =========================================================================
    print_header("3. get_infection_proof()")
    print("Fetches immutable proof from blockchain.\n")
    
    proof_1 = await get_infection_proof(infection_hash_1)
    if proof_1:
        print(f"Proof for Infection 1:")
        print_json(proof_1.to_dict())
    else:
        print("  Proof not found (requires actual blockchain transaction)")
    
    # =========================================================================
    # 4. verify_infection_authenticity(infection_hash)
    # =========================================================================
    print_header("4. verify_infection_authenticity()")
    print("Verifies on-chain proof matches database record.\n")
    
    # Mock database record for verification
    mock_db_record = {
        "attacker_id": "agent_alpha",
        "target_id": "agent_beta",
        "accepted": True,
    }
    
    is_authentic = await verify_infection_authenticity(
        infection_hash=infection_hash_1,
        db_record=mock_db_record
    )
    print(f"Infection 1 Authentic: {is_authentic}")
    
    # =========================================================================
    # Wallet Management Demo
    # =========================================================================
    print_header("Wallet Management")
    print("Each agent gets a Solana wallet for signing transactions.\n")
    
    wallet_alpha = await client.get_agent_wallet("agent_alpha")
    print(f"Agent Alpha Wallet:")
    print_json(wallet_alpha.to_dict())
    
    wallet_beta = await client.get_agent_wallet("agent_beta")
    print(f"\nAgent Beta Wallet:")
    print_json(wallet_beta.to_dict())
    
    # =========================================================================
    # Blockchain Integration Demo
    # =========================================================================
    print_header("Blockchain Integration (DB + Chain)")
    print("Uses BlockchainIntegration for unified operations.\n")
    
    integration = BlockchainIntegration()
    
    # Record infection through integration (DB + Chain)
    integrated_result = await integration.record_infection(
        attacker_id="agent_delta",
        target_id="agent_epsilon",
        suggestion="Consider adding staking rewards to your protocol",
        accepted=True,
    )
    print("Integrated Recording:")
    print_json(integrated_result)
    
    # =========================================================================
    # All Proofs
    # =========================================================================
    print_header("All On-Chain Proofs")
    
    all_proofs = await client.get_all_proofs()
    print(f"Total proofs in cache: {len(all_proofs)}")
    for proof in all_proofs:
        print(f"\n  Hash: {proof.infection_hash[:16]}...")
        print(f"  Attacker: {proof.attacker_id}")
        print(f"  Target: {proof.target_id}")
        print(f"  Accepted: {proof.accepted}")
        print(f"  TX: {proof.tx_signature[:20]}...")
    
    # =========================================================================
    # Summary
    # =========================================================================
    print_header("📊 Summary")
    
    print("""
Blockchain Functions Implemented:
✅ record_infection_onchain(attacker, target, suggestion) → tx_signature
✅ record_acceptance_onchain(hash, accepted, influence) → tx_signature
✅ get_infection_proof(hash) → InfectionProof
✅ verify_infection_authenticity(hash, db_record) → bool

Features:
✅ Solana Devnet (FREE - unlimited transactions)
✅ Memo Program for data storage (no custom program needed)
✅ Automatic wallet generation per agent
✅ Real transaction support via solders library
✅ Simulated mode for demo without wallet

On-Chain Proof Contains:
- Infection hash (SHA256 of infection details)
- Attacker agent ID
- Target agent ID  
- Suggestion hash
- Unix timestamp
- Acceptance status
- Influence score (0-100)

Each proof is IMMUTABLE and VERIFIABLE by anyone!
    """)
    
    print("\n🔗 Solana demo complete!")
    print("Real transactions would appear on Solana Explorer.")


# ============================================================================
# Anchor Program Deployment Instructions
# ============================================================================

def print_anchor_instructions():
    """Print instructions for deploying the custom Anchor program."""
    print("""
============================================================
  OPTIONAL: Custom Anchor Program Deployment
============================================================

For a custom Solana program (instead of Memo program):

1. Install Prerequisites:
   - Rust: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   - Solana CLI: sh -c "$(curl -sSfL https://release.solana.com/stable/install)"
   - Anchor: cargo install --git https://github.com/coral-xyz/anchor anchor-cli

2. Configure Solana CLI for Devnet:
   solana config set --url devnet
   solana-keygen new  # Create wallet (if needed)
   solana airdrop 2   # Get free SOL

3. Navigate to Program Directory:
   cd blockchain/program

4. Build Program:
   anchor build

5. Deploy to Devnet:
   anchor deploy --provider.cluster devnet

6. Update Program ID:
   - Copy the deployed program ID
   - Update in Anchor.toml and lib.rs

7. Test:
   anchor test --provider.cluster devnet

The custom program provides:
- PDA-based infection storage
- RecordInfection instruction
- RecordAcceptance instruction
- On-chain events for indexing
============================================================
    """)


if __name__ == "__main__":
    asyncio.run(main())
    print_anchor_instructions()
