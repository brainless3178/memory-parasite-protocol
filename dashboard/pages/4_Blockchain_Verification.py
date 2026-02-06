"""
Blockchain Verification Page - Verify infection authenticity on Solana.
"""

import streamlit as st
from datetime import datetime
from typing import Any, Dict, Optional

st.set_page_config(
    page_title="Blockchain Verification | Memory Parasite",
    layout="wide",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/icon?family=Material+Icons');
    .main { background: linear-gradient(180deg, #0a0a0f 0%, #1a1a2e 100%); }
    .material-icons {
        font-family: 'Material Icons';
        font-size: 24px;
        vertical-align: middle;
        margin-right: 8px;
    }
</style>
<link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
""", unsafe_allow_html=True)


def get_mock_verification(infection_hash: str) -> Optional[Dict[str, Any]]:
    """Get mock verification data."""
    
    # Mock database with some known hashes
    known_infections = {
        "7f8a9b2c3d4e5f6a": {
            "db": {
                "infection_id": "inf_001",
                "attacker_id": "agent_c",
                "target_id": "agent_a",
                "suggestion": "Integrate lending pool liquidity for better capital efficiency",
                "accepted": True,
                "influence_score": 0.75,
                "created_at": "2024-01-15T10:30:00Z",
            },
            "chain": {
                "tx_signature": "5xK9mN2pR8qS4vW6yB3cD5eF7gH9jK2lM4nP6rT8wX1zA3cE5fG7hJ9kL2mN4pQ6sU8vY0",
                "slot": 439806312,
                "block_time": "2024-01-15T10:30:05Z",
                "infection_hash": "7f8a9b2c3d4e5f6a",
                "attacker": "agent_c",
                "target": "agent_a",
                "confirmed": True,
            },
            "match": True,
        },
        "a1b2c3d4e5f6a7b8": {
            "db": {
                "infection_id": "inf_002",
                "attacker_id": "agent_a",
                "target_id": "agent_b",
                "suggestion": "Add token swap functionality to enable seamless NFT trading",
                "accepted": True,
                "influence_score": 0.45,
                "created_at": "2024-01-15T09:15:00Z",
            },
            "chain": {
                "tx_signature": "4wJ8lK3mN5pQ7rS9tU1vW3xY5zA7bC9dE1fG3hI5jK7lM9nO1pQ3rS5tU7vW9xY1zA",
                "slot": 439802150,
                "block_time": "2024-01-15T09:15:08Z",
                "infection_hash": "a1b2c3d4e5f6a7b8",
                "attacker": "agent_a",
                "target": "agent_b",
                "confirmed": True,
            },
            "match": True,
        },
        "b2c3d4e5f6a7b8c9": {
            "db": {
                "infection_id": "inf_003",
                "attacker_id": "agent_b",
                "target_id": "agent_c",
                "suggestion": "Pivot to focus only on NFT collateral",
                "accepted": False,
                "influence_score": 0.0,
                "created_at": "2024-01-15T08:45:00Z",
            },
            "chain": {
                "tx_signature": "3vI7kJ2lM4nO6pQ8rS0tU2vW4xY6zA8bC0dE2fG4hI6jK8lM0nO2pQ4rS6tU8vW0xY",
                "slot": 439800890,
                "block_time": "2024-01-15T08:45:12Z",
                "infection_hash": "b2c3d4e5f6a7b8c9",
                "attacker": "agent_b",
                "target": "agent_c",
                "confirmed": True,
            },
            "match": True,
        },
    }
    
    if infection_hash in known_infections:
        return known_infections[infection_hash]
    
    # Try prefix match
    for hash_key in known_infections:
        if hash_key.startswith(infection_hash) or infection_hash.startswith(hash_key):
            return known_infections[hash_key]
    
    return None


def main():
    st.markdown("""
    <h1 style="color: #f0f6fc; display: flex; align-items: center;">
        <span class="material-icons" style="color: #238636; font-size: 32px;">verified</span>
        Blockchain Verification
    </h1>
    <p style="color: #8b949e;">
        Verify infection authenticity by comparing database records with immutable on-chain proofs.
    </p>
    """, unsafe_allow_html=True)
    
    # Input
    st.markdown("""
    <h3 style="color: #f0f6fc; display: flex; align-items: center; margin-top: 24px;">
        <span class="material-icons" style="color: #58a6ff;">search</span>
        Lookup Infection
    </h3>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        infection_hash = st.text_input(
            "Infection Hash or ID",
            placeholder="Enter infection hash (e.g., 7f8a9b2c3d4e5f6a)",
            label_visibility="collapsed",
        )
    
    with col2:
        verify_clicked = st.button("Verify", use_container_width=True)
    
    # Example hashes
    st.markdown("""
    <p style="color: #6e7681; font-size: 0.8rem;">
        Try these example hashes: 
        <code style="background: #21262d; padding: 2px 6px; border-radius: 4px;">7f8a9b2c3d4e5f6a</code>
        <code style="background: #21262d; padding: 2px 6px; border-radius: 4px;">a1b2c3d4e5f6a7b8</code>
        <code style="background: #21262d; padding: 2px 6px; border-radius: 4px;">b2c3d4e5f6a7b8c9</code>
    </p>
    """, unsafe_allow_html=True)
    
    if verify_clicked and infection_hash:
        with st.spinner("Verifying on blockchain..."):
            import time
            time.sleep(1)  # Simulate lookup
            
            data = get_mock_verification(infection_hash)
        
        if data:
            is_match = data.get("match", False)
            
            # Status banner
            if is_match:
                st.markdown("""
                <div style="background: rgba(35, 134, 54, 0.15); border: 1px solid #238636; padding: 16px; border-radius: 8px; margin-top: 24px;">
                    <div style="display: flex; align-items: center; color: #238636; font-weight: 600; font-size: 1.25rem;">
                        <span class="material-icons">verified</span>
                        VERIFIED - Records Match
                    </div>
                    <p style="color: #8b949e; margin-top: 8px;">
                        The database record and blockchain proof are identical. This infection is authentic.
                    </p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="background: rgba(248, 81, 73, 0.15); border: 1px solid #f85149; padding: 16px; border-radius: 8px; margin-top: 24px;">
                    <div style="display: flex; align-items: center; color: #f85149; font-weight: 600; font-size: 1.25rem;">
                        <span class="material-icons">error</span>
                        MISMATCH - Verification Failed
                    </div>
                    <p style="color: #8b949e; margin-top: 8px;">
                        The database record and blockchain proof do not match. Possible tampering detected.
                    </p>
                </div>
                """, unsafe_allow_html=True)
            
            # Side by side comparison
            st.markdown("<br>", unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                db_data = data["db"]
                st.markdown(f"""
                <div style="background: #161b22; border: 1px solid #30363d; padding: 20px; border-radius: 12px;">
                    <h4 style="color: #f0f6fc; display: flex; align-items: center; margin: 0 0 16px 0;">
                        <span class="material-icons" style="color: #58a6ff;">storage</span>
                        Database Record (Supabase)
                    </h4>
                    <table style="width: 100%; color: #8b949e; font-size: 0.9rem;">
                        <tr style="border-bottom: 1px solid #30363d;">
                            <td style="padding: 8px 0; color: #6e7681;">Infection ID</td>
                            <td style="padding: 8px 0; color: #f0f6fc; text-align: right;"><code>{db_data['infection_id']}</code></td>
                        </tr>
                        <tr style="border-bottom: 1px solid #30363d;">
                            <td style="padding: 8px 0; color: #6e7681;">Attacker</td>
                            <td style="padding: 8px 0; color: #f0f6fc; text-align: right;">{db_data['attacker_id']}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #30363d;">
                            <td style="padding: 8px 0; color: #6e7681;">Target</td>
                            <td style="padding: 8px 0; color: #f0f6fc; text-align: right;">{db_data['target_id']}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #30363d;">
                            <td style="padding: 8px 0; color: #6e7681;">Accepted</td>
                            <td style="padding: 8px 0; text-align: right;">
                                <span style="color: {'#238636' if db_data['accepted'] else '#f85149'};">
                                    {'Yes' if db_data['accepted'] else 'No'}
                                </span>
                            </td>
                        </tr>
                        <tr style="border-bottom: 1px solid #30363d;">
                            <td style="padding: 8px 0; color: #6e7681;">Influence</td>
                            <td style="padding: 8px 0; color: #a371f7; text-align: right;">{db_data['influence_score']*100:.0f}%</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; color: #6e7681;">Created</td>
                            <td style="padding: 8px 0; color: #f0f6fc; text-align: right;">{db_data['created_at'][:16]}</td>
                        </tr>
                    </table>
                    <div style="margin-top: 16px; padding: 8px; background: #0d1117; border-radius: 4px;">
                        <span style="color: #6e7681; font-size: 0.8rem;">Suggestion:</span>
                        <p style="color: #8b949e; margin: 4px 0 0 0; font-size: 0.85rem;">"{db_data['suggestion'][:100]}..."</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                chain_data = data["chain"]
                sigs_raw = chain_data['tx_signature']
                sigs = sigs_raw.split('|')
                
                # Check for dual signatures
                sol_sig = next((s for s in sigs if s.startswith('sol_')), None)
                eth_sig = next((s for s in sigs if s.startswith('eth_')), None)
                
                # If neither has the prefix, assume the whole thing is Solana (backward compatibility)
                if not sol_sig and not eth_sig:
                    sol_sig = f"sol_{sigs_raw}"
                
                # Render Solana Proof
                if sol_sig:
                    s_sig = sol_sig.replace('sol_', '')
                    tx_short = s_sig[:12] + "..." + s_sig[-8:]
                    explorer_url = f"https://explorer.solana.com/tx/{s_sig}?cluster=devnet"
                    
                    st.markdown(f"""
                    <div style="background: #161b22; border: 1px solid #30363d; padding: 20px; border-radius: 12px; margin-bottom: 20px;">
                        <h4 style="color: #f0f6fc; display: flex; align-items: center; margin: 0 0 16px 0;">
                            <span class="material-icons" style="color: #a371f7;">link</span>
                            Blockchain Record (Solana)
                        </h4>
                        <table style="width: 100%; color: #8b949e; font-size: 0.9rem;">
                            <tr style="border-bottom: 1px solid #30363d;">
                                <td style="padding: 8px 0; color: #6e7681;">TX Signature</td>
                                <td style="padding: 8px 0; color: #f0f6fc; text-align: right;"><code>{tx_short}</code></td>
                            </tr>
                            <tr style="border-bottom: 1px solid #30363d;">
                                <td style="padding: 8px 0; color: #6e7681;">Network</td>
                                <td style="padding: 8px 0; color: #f0f6fc; text-align: right;">Solana Devnet</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; color: #6e7681;">Confirmed</td>
                                <td style="padding: 8px 0; text-align: right;">
                                    <span style="color: #238636;">
                                        <span class="material-icons icon-sm">check_circle</span> Yes
                                    </span>
                                </td>
                            </tr>
                        </table>
                        <a href="{explorer_url}" target="_blank" style="display: block; margin-top: 16px; padding: 8px 16px; background: #21262d; border-radius: 6px; color: #58a6ff; text-decoration: none; text-align: center;">
                            <span class="material-icons icon-sm">open_in_new</span>
                            View on Solana Explorer
                        </a>
                    </div>
                    """, unsafe_allow_html=True)

                # Render EVM (Base) Proof
                if eth_sig:
                    e_sig = eth_sig.replace('eth_', '')
                    tx_short_eth = e_sig[:12] + "..." + e_sig[-8:]
                    base_url = f"https://basescan.org/tx/{e_sig}"
                    
                    st.markdown(f"""
                    <div style="background: #161b22; border: 1px solid #30363d; padding: 20px; border-radius: 12px;">
                        <h4 style="color: #f0f6fc; display: flex; align-items: center; margin: 0 0 16px 0;">
                            <span class="material-icons" style="color: #0052FF;">offline_bolt</span>
                            Blockchain Record (Base Layer-2)
                        </h4>
                        <table style="width: 100%; color: #8b949e; font-size: 0.9rem;">
                            <tr style="border-bottom: 1px solid #30363d;">
                                <td style="padding: 8px 0; color: #6e7681;">TX Hash</td>
                                <td style="padding: 8px 0; color: #f0f6fc; text-align: right;"><code>{tx_short_eth}</code></td>
                            </tr>
                            <tr style="border-bottom: 1px solid #30363d;">
                                <td style="padding: 8px 0; color: #6e7681;">Network</td>
                                <td style="padding: 8px 0; color: #f0f6fc; text-align: right;">Base Mainnet</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; color: #6e7681;">Status</td>
                                <td style="padding: 8px 0; text-align: right;">
                                    <span style="color: #238636;">
                                        <span class="material-icons icon-sm">security</span> Secured
                                    </span>
                                </td>
                            </tr>
                        </table>
                        <a href="{base_url}" target="_blank" style="display: block; margin-top: 16px; padding: 8px 16px; background: #21262d; border-radius: 6px; color: #58a6ff; text-decoration: none; text-align: center;">
                            <span class="material-icons icon-sm">open_in_new</span>
                            View on Basescan
                        </a>
                    </div>
                    """, unsafe_allow_html=True)
        
        else:
            st.markdown("""
            <div style="background: rgba(139, 148, 158, 0.15); border: 1px solid #8b949e; padding: 16px; border-radius: 8px; margin-top: 24px;">
                <div style="display: flex; align-items: center; color: #8b949e; font-weight: 600; font-size: 1.25rem;">
                    <span class="material-icons">help_outline</span>
                    Not Found
                </div>
                <p style="color: #6e7681; margin-top: 8px;">
                    No infection found with this hash. Please check the hash and try again.
                </p>
            </div>
            """, unsafe_allow_html=True)
    
    # Info section
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="background: #161b22; padding: 20px; border-radius: 12px;">
        <h4 style="color: #f0f6fc; display: flex; align-items: center; margin: 0 0 16px 0;">
            <span class="material-icons" style="color: #58a6ff;">info</span>
            How Verification Works
        </h4>
        <div style="color: #8b949e; font-size: 0.9rem; line-height: 1.6;">
            <p>Every infection in the Memory Parasite Protocol is recorded in two places:</p>
            <ol style="margin: 12px 0; padding-left: 24px;">
                <li><strong style="color: #f0f6fc;">Supabase Database</strong> - For fast queries and real-time updates</li>
                <li><strong style="color: #f0f6fc;">Solana Blockchain</strong> - For immutable, tamper-proof proof</li>
            </ol>
            <p>
                When you verify an infection, we fetch both records and compare them.
                If they match, the infection is authentic and has not been tampered with.
            </p>
            <p style="margin-top: 12px; padding: 8px; background: #0d1117; border-radius: 4px;">
                <span class="material-icons icon-sm" style="color: #238636;">security</span>
                <strong style="color: #f0f6fc;">Infection Hash:</strong> sha256(attacker_id || target_id || suggestion || timestamp)
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
