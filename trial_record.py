import asyncio
import os
import structlog
from blockchain.solana_client import record_infection_onchain, get_solana_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_real_blockchain_recording():
    print("\n" + "="*60)
    print(" MEMORY PARASITE PROTOCOL: REAL-WORLD CONNECTIVITY TEST")
    print("="*60)
    
    attacker_id = "agent_a"
    target_id = "agent_b"
    suggestion = "Real-world connectivity test for Memory Parasite Protocol. Verifying on-chain immutable proof."
    
    client = get_solana_client()
    net_info = await client.get_network_info()
    
    print(f"RPC Endpoint: {net_info.get('rpc_url')}")
    print(f"Health Status: {net_info.get('health')}")
    print(f"Current Slot: {net_info.get('slot')}")
    
    print(f"\nRecording REAL infection on-chain...")
    print(f"Strategy: Record Memo via AgentWallet (Funded with 10 SOL)")
    
    try:
        tx_sig = await record_infection_onchain(attacker_id, target_id, suggestion)
        
        if tx_sig:
            if tx_sig.startswith("sim_"):
                print(f"\n⚠️ FALLBACK: Simulated proof generated (Simulation Mode).")
                print(f"Signature: {tx_sig}")
            else:
                print(f"\n✅ SUCCESS! Real On-Chain Transaction confirmed.")
                print(f"Transaction Signature: {tx_sig}")
                print(f"Explorer URL: https://explorer.solana.com/tx/{tx_sig}?cluster=devnet")
        else:
            print("\n❌ FAILED: Could not record on blockchain.")
            
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
    
    print("="*60 + "\n")

if __name__ == "__main__":
    asyncio.run(test_real_blockchain_recording())
