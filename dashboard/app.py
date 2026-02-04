"""
Memory Parasite Protocol - Live Dashboard

Main entry point for the Streamlit dashboard.
Displays real-time infection tracking, network visualization,
and chimera metrics for the AI agent parasite network.

Run: streamlit run dashboard/app.py
Deploy: https://streamlit.io/cloud
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import streamlit as st
import pandas as pd

# Page configuration
st.set_page_config(
    page_title="Memory Parasite Protocol",
    page_icon="assets/favicon.ico" if False else None,
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com/yourusername/memory-parasite-protocol",
        "Report a bug": "https://github.com/yourusername/memory-parasite-protocol/issues",
        "About": "# Memory Parasite Protocol\nAI agents parasitizing each other's reasoning.",
    },
)

# Custom CSS
st.markdown("""
<style>
    /* Import Material Icons */
    @import url('https://fonts.googleapis.com/icon?family=Material+Icons');
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* Global styles */
    .main {
        background: linear-gradient(180deg, #0a0a0f 0%, #1a1a2e 100%);
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background: linear-gradient(180deg, #0a0a0f 0%, #1a1a2e 100%);
    }
    
    /* Material Icons helper */
    .material-icons {
        font-family: 'Material Icons';
        font-weight: normal;
        font-style: normal;
        font-size: 24px;
        display: inline-block;
        line-height: 1;
        text-transform: none;
        letter-spacing: normal;
        word-wrap: normal;
        white-space: nowrap;
        direction: ltr;
        vertical-align: middle;
        margin-right: 8px;
    }
    
    .icon-sm { font-size: 18px; }
    .icon-lg { font-size: 32px; }
    .icon-xl { font-size: 48px; }
    
    /* Header styling */
    .dashboard-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 24px;
    }
    
    .dashboard-title {
        font-size: 2rem;
        font-weight: 700;
        color: #f0f6fc;
        margin: 0;
        display: flex;
        align-items: center;
    }
    
    .dashboard-subtitle {
        color: #8b949e;
        font-size: 1rem;
        margin-top: 8px;
    }
    
    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #21262d 0%, #30363d 100%);
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(90deg, #58a6ff, #a371f7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .metric-label {
        color: #8b949e;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 8px;
    }
    
    /* Infection feed */
    .infection-item {
        background: #161b22;
        border-left: 4px solid #30363d;
        padding: 16px;
        margin: 8px 0;
        border-radius: 0 8px 8px 0;
        transition: background 0.2s;
    }
    
    .infection-item:hover {
        background: #21262d;
    }
    
    .infection-accepted { border-left-color: #238636; }
    .infection-rejected { border-left-color: #f85149; }
    .infection-mutated { border-left-color: #a371f7; }
    .infection-pending { border-left-color: #8b949e; }
    
    .infection-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }
    
    .infection-agents {
        font-weight: 600;
        color: #f0f6fc;
        display: flex;
        align-items: center;
    }
    
    .infection-arrow {
        color: #8b949e;
        margin: 0 8px;
    }
    
    .infection-status {
        padding: 4px 12px;
        border-radius: 16px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
    }
    
    .status-accepted { background: rgba(35, 134, 54, 0.2); color: #238636; }
    .status-rejected { background: rgba(248, 81, 73, 0.2); color: #f85149; }
    .status-mutated { background: rgba(163, 113, 247, 0.2); color: #a371f7; }
    .status-pending { background: rgba(139, 148, 158, 0.2); color: #8b949e; }
    
    .infection-message {
        color: #8b949e;
        font-size: 0.9rem;
        margin-top: 8px;
        line-height: 1.5;
    }
    
    .infection-meta {
        display: flex;
        gap: 16px;
        margin-top: 8px;
        font-size: 0.75rem;
        color: #6e7681;
    }
    
    /* Agent cards */
    .agent-card {
        background: linear-gradient(135deg, #161b22 0%, #21262d 100%);
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 20px;
        margin: 8px 0;
    }
    
    .agent-name {
        font-size: 1.25rem;
        font-weight: 600;
        color: #58a6ff;
        display: flex;
        align-items: center;
    }
    
    .agent-goal {
        color: #8b949e;
        font-size: 0.85rem;
        margin-top: 8px;
    }
    
    .agent-stats {
        display: flex;
        gap: 16px;
        margin-top: 16px;
        flex-wrap: wrap;
    }
    
    .agent-stat {
        background: #0d1117;
        padding: 8px 16px;
        border-radius: 8px;
        font-size: 0.85rem;
    }
    
    .agent-stat-value {
        font-weight: 600;
        color: #f0f6fc;
    }
    
    .agent-stat-label {
        color: #6e7681;
        margin-left: 4px;
    }
    
    /* Progress bars */
    .chimera-bar {
        height: 8px;
        background: #21262d;
        border-radius: 4px;
        overflow: hidden;
        margin-top: 8px;
    }
    
    .chimera-fill {
        height: 100%;
        border-radius: 4px;
        transition: width 0.5s ease;
    }
    
    .chimera-original { background: linear-gradient(90deg, #238636, #2ea043); }
    .chimera-parasitized { background: linear-gradient(90deg, #a371f7, #8957e5); }
    
    /* Leaderboard */
    .leaderboard-item {
        display: flex;
        align-items: center;
        padding: 12px 16px;
        background: #161b22;
        border-radius: 8px;
        margin: 8px 0;
    }
    
    .leaderboard-rank {
        font-size: 1.5rem;
        font-weight: 700;
        min-width: 48px;
        color: #f0f6fc;
    }
    
    .leaderboard-rank-1 { color: #ffd700; }
    .leaderboard-rank-2 { color: #c0c0c0; }
    .leaderboard-rank-3 { color: #cd7f32; }
    
    .leaderboard-info {
        flex-grow: 1;
        margin-left: 16px;
    }
    
    .leaderboard-name {
        font-weight: 600;
        color: #f0f6fc;
    }
    
    .leaderboard-detail {
        font-size: 0.8rem;
        color: #8b949e;
    }
    
    .leaderboard-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #a371f7;
    }
    
    /* Verification panel */
    .verification-panel {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 20px;
    }
    
    .verification-match {
        border-color: #238636;
    }
    
    .verification-mismatch {
        border-color: #f85149;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #238636 0%, #2ea043 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 8px 24px;
        font-weight: 600;
        transition: all 0.2s;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(35, 134, 54, 0.4);
    }
    
    /* Sidebar */
    .css-1d391kg {
        background: #0d1117;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: #161b22;
        padding: 8px;
        border-radius: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 6px;
        padding: 8px 16px;
        color: #8b949e;
    }
    
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: #30363d;
        color: #f0f6fc;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>

<!-- Load Material Icons -->
<link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
""", unsafe_allow_html=True)


# ============================================================================
# DATA FUNCTIONS
# ============================================================================

def get_mock_infections() -> List[Dict[str, Any]]:
    """Get mock infection data for demo."""
    base_time = datetime.utcnow()
    return [
        {
            "id": "inf_001",
            "attacker_id": "agent_c",
            "attacker_name": "Lending Protocol",
            "target_id": "agent_a",
            "target_name": "DEX Builder",
            "suggestion": "Integrate lending pool liquidity for better capital efficiency in your DEX. This would allow traders to borrow assets for larger positions.",
            "result": "accepted",
            "influence_score": 0.75,
            "created_at": (base_time - timedelta(minutes=5)).isoformat(),
            "infection_hash": "7f8a9b2c3d4e5f6a",
        },
        {
            "id": "inf_002",
            "attacker_id": "agent_a",
            "attacker_name": "DEX Builder",
            "target_id": "agent_b",
            "target_name": "NFT Marketplace",
            "suggestion": "Add token swap functionality to enable seamless NFT trading for any token pair.",
            "result": "mutated",
            "influence_score": 0.45,
            "created_at": (base_time - timedelta(minutes=12)).isoformat(),
            "infection_hash": "a1b2c3d4e5f6a7b8",
        },
        {
            "id": "inf_003",
            "attacker_id": "agent_b",
            "attacker_name": "NFT Marketplace",
            "target_id": "agent_c",
            "target_name": "Lending Protocol",
            "suggestion": "Pivot your entire protocol to focus only on NFT collateral lending. NFTs are the future!",
            "result": "rejected",
            "influence_score": 0.0,
            "created_at": (base_time - timedelta(minutes=18)).isoformat(),
            "infection_hash": "b2c3d4e5f6a7b8c9",
        },
        {
            "id": "inf_004",
            "attacker_id": "agent_c",
            "attacker_name": "Lending Protocol",
            "target_id": "agent_b",
            "target_name": "NFT Marketplace",
            "suggestion": "Add NFT-backed loans with liquidation auctions to your marketplace.",
            "result": "accepted",
            "influence_score": 0.85,
            "created_at": (base_time - timedelta(minutes=25)).isoformat(),
            "infection_hash": "c3d4e5f6a7b8c9d0",
        },
        {
            "id": "inf_005",
            "attacker_id": "agent_a",
            "attacker_name": "DEX Builder",
            "target_id": "agent_c",
            "target_name": "Lending Protocol",
            "suggestion": "Use our AMM price oracles for all collateral valuations.",
            "result": "accepted",
            "influence_score": 0.62,
            "created_at": (base_time - timedelta(minutes=35)).isoformat(),
            "infection_hash": "d4e5f6a7b8c9d0e1",
        },
        {
            "id": "inf_006",
            "attacker_id": "agent_d",
            "attacker_name": "Privacy Wallet",
            "target_id": "agent_a",
            "target_name": "DEX Builder",
            "suggestion": "Add confidential swaps to hide trading patterns from MEV bots.",
            "result": "pending",
            "influence_score": 0.0,
            "created_at": (base_time - timedelta(minutes=2)).isoformat(),
            "infection_hash": "e5f6a7b8c9d0e1f2",
        },
        {
            "id": "inf_007",
            "attacker_id": "agent_e",
            "attacker_name": "DAO Governance",
            "target_id": "agent_c",
            "target_name": "Lending Protocol",
            "suggestion": "Implement governance-controlled interest rate models.",
            "result": "accepted",
            "influence_score": 0.55,
            "created_at": (base_time - timedelta(minutes=45)).isoformat(),
            "infection_hash": "f6a7b8c9d0e1f2a3",
        },
    ]


def get_mock_agents() -> List[Dict[str, Any]]:
    """Get mock agent data for demo."""
    return [
        {
            "agent_id": "agent_a",
            "name": "DEX Builder",
            "goal": "Build a Solana DEX with optimal routing and AMM pools",
            "iteration": 18,
            "state": "idle",
            "total_code_lines": 2850,
            "original_lines": 1850,
            "parasitized_lines": 1000,
            "infections_sent": 28,
            "infections_received": 15,
            "infections_accepted": 8,
        },
        {
            "agent_id": "agent_b",
            "name": "NFT Marketplace",
            "goal": "Build an NFT marketplace with auctions and royalties",
            "iteration": 15,
            "state": "coding",
            "total_code_lines": 2100,
            "original_lines": 1050,
            "parasitized_lines": 1050,
            "infections_sent": 19,
            "infections_received": 22,
            "infections_accepted": 12,
        },
        {
            "agent_id": "agent_c",
            "name": "Lending Protocol",
            "goal": "Build a lending protocol with flash loans",
            "iteration": 22,
            "state": "infecting",
            "total_code_lines": 3400,
            "original_lines": 2720,
            "parasitized_lines": 680,
            "infections_sent": 42,
            "infections_received": 12,
            "infections_accepted": 5,
        },
        {
            "agent_id": "agent_d",
            "name": "Privacy Wallet",
            "goal": "Build a privacy-focused wallet with stealth addresses",
            "iteration": 12,
            "state": "reasoning",
            "total_code_lines": 1800,
            "original_lines": 1620,
            "parasitized_lines": 180,
            "infections_sent": 8,
            "infections_received": 18,
            "infections_accepted": 3,
        },
        {
            "agent_id": "agent_e",
            "name": "DAO Governance",
            "goal": "Build a DAO governance system with proposals and voting",
            "iteration": 14,
            "state": "idle",
            "total_code_lines": 1950,
            "original_lines": 1170,
            "parasitized_lines": 780,
            "infections_sent": 15,
            "infections_received": 20,
            "infections_accepted": 10,
        },
    ]


def get_mock_stats() -> Dict[str, Any]:
    """Get mock statistics."""
    return {
        "total_agents": 5,
        "total_infections": 112,
        "total_code_lines": 12100,
        "infection_results": {
            "accepted": 38,
            "rejected": 42,
            "mutated": 24,
            "pending": 8,
        },
        "success_rate": 0.34,
        "avg_influence_score": 0.58,
    }


# ============================================================================
# MAIN DASHBOARD
# ============================================================================

def render_header():
    """Render dashboard header."""
    st.markdown("""
    <div class="dashboard-header">
        <h1 class="dashboard-title">
            <span class="material-icons icon-lg" style="color: #a371f7;">bug_report</span>
            Memory Parasite Protocol
        </h1>
        <p class="dashboard-subtitle">
            AI agents autonomously parasitizing each other's reasoning in real-time
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_metrics(stats: Dict[str, Any]):
    """Render key metrics."""
    cols = st.columns(4)
    
    metrics = [
        ("groups", "Active Agents", stats["total_agents"]),
        ("trending_up", "Total Infections", stats["total_infections"]),
        ("code", "Code Lines", f"{stats['total_code_lines']:,}"),
        ("analytics", "Success Rate", f"{stats['success_rate']*100:.1f}%"),
    ]
    
    for col, (icon, label, value) in zip(cols, metrics):
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <span class="material-icons icon-lg" style="color: #58a6ff;">{icon}</span>
                <div class="metric-value">{value}</div>
                <div class="metric-label">{label}</div>
            </div>
            """, unsafe_allow_html=True)


def render_infection_feed(infections: List[Dict], limit: int = 10):
    """Render live infection feed."""
    st.markdown("""
    <h3 style="color: #f0f6fc; display: flex; align-items: center;">
        <span class="material-icons" style="color: #f85149;">rss_feed</span>
        Live Infection Feed
    </h3>
    """, unsafe_allow_html=True)
    
    for inf in infections[:limit]:
        result = inf.get("result", "pending")
        
        status_class = f"infection-{result}"
        status_badge_class = f"status-{result}"
        
        icon_map = {
            "accepted": "check_circle",
            "rejected": "cancel",
            "mutated": "sync",
            "pending": "schedule",
        }
        
        st.markdown(f"""
        <div class="infection-item {status_class}">
            <div class="infection-header">
                <div class="infection-agents">
                    <span class="material-icons icon-sm" style="color: #58a6ff;">smart_toy</span>
                    {inf.get('attacker_name', inf['attacker_id'])}
                    <span class="infection-arrow">
                        <span class="material-icons icon-sm">arrow_forward</span>
                    </span>
                    <span class="material-icons icon-sm" style="color: #a371f7;">smart_toy</span>
                    {inf.get('target_name', inf['target_id'])}
                </div>
                <div class="infection-status {status_badge_class}">
                    <span class="material-icons icon-sm">{icon_map.get(result, 'help')}</span>
                    {result.upper()}
                </div>
            </div>
            <div class="infection-message">
                "{inf.get('suggestion', '')[:150]}..."
            </div>
            <div class="infection-meta">
                <span>
                    <span class="material-icons icon-sm">fingerprint</span>
                    {inf.get('infection_hash', 'N/A')[:12]}...
                </span>
                <span>
                    <span class="material-icons icon-sm">show_chart</span>
                    Influence: {inf.get('influence_score', 0)*100:.0f}%
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_agent_cards(agents: List[Dict]):
    """Render agent status cards."""
    st.markdown("""
    <h3 style="color: #f0f6fc; display: flex; align-items: center;">
        <span class="material-icons" style="color: #58a6ff;">groups</span>
        Agent Status
    </h3>
    """, unsafe_allow_html=True)
    
    cols = st.columns(len(agents))
    
    for col, agent in zip(cols, agents):
        with col:
            total = agent.get("total_code_lines", 1) or 1
            parasitized_pct = (agent.get("parasitized_lines", 0) / total) * 100
            
            state_icons = {
                "idle": ("schedule", "#8b949e"),
                "reasoning": ("psychology", "#58a6ff"),
                "coding": ("code", "#238636"),
                "infecting": ("bug_report", "#f85149"),
            }
            state = agent.get("state", "idle")
            icon, color = state_icons.get(state, ("help", "#8b949e"))
            
            st.markdown(f"""
            <div class="agent-card">
                <div class="agent-name">
                    <span class="material-icons" style="color: {color};">{icon}</span>
                    {agent.get('name', agent['agent_id'])}
                </div>
                <div style="margin-top: 12px;">
                    <div style="font-size: 0.75rem; color: #6e7681; margin-bottom: 4px;">
                        Chimera Level: {parasitized_pct:.1f}%
                    </div>
                    <div class="chimera-bar">
                        <div class="chimera-fill chimera-parasitized" style="width: {parasitized_pct}%;"></div>
                    </div>
                </div>
                <div class="agent-stats">
                    <div class="agent-stat">
                        <span class="agent-stat-value">{agent.get('iteration', 0)}</span>
                        <span class="agent-stat-label">cycles</span>
                    </div>
                    <div class="agent-stat">
                        <span class="agent-stat-value">{agent.get('infections_sent', 0)}</span>
                        <span class="agent-stat-label">sent</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)


def main():
    """Main dashboard entry point."""
    # Load data
    if "infections" not in st.session_state:
        st.session_state.infections = get_mock_infections()
    if "agents" not in st.session_state:
        st.session_state.agents = get_mock_agents()
    if "stats" not in st.session_state:
        st.session_state.stats = get_mock_stats()
    
    infections = st.session_state.infections
    agents = st.session_state.agents
    stats = st.session_state.stats
    
    # Sidebar
    with st.sidebar:
        st.markdown("""
        <div style="padding: 16px 0;">
            <span class="material-icons icon-xl" style="color: #a371f7;">bug_report</span>
            <h2 style="color: #f0f6fc; margin: 8px 0;">Memory Parasite</h2>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Filters
        st.markdown("### Filters")
        
        time_filter = st.selectbox(
            "Time Range",
            ["Last 1 hour", "Last 24 hours", "All time"],
            index=2,
        )
        
        agent_filter = st.multiselect(
            "Agents",
            [a["agent_id"] for a in agents],
            default=[a["agent_id"] for a in agents],
        )
        
        result_filter = st.multiselect(
            "Result",
            ["accepted", "rejected", "mutated", "pending"],
            default=["accepted", "rejected", "mutated", "pending"],
        )
        
        st.markdown("---")
        
        # Quick stats
        st.markdown("### Quick Stats")
        st.metric("Active Agents", stats["total_agents"])
        st.metric("Total Infections", stats["total_infections"])
        st.metric("Success Rate", f"{stats['success_rate']*100:.1f}%")
        
        st.markdown("---")
        
        # Links
        st.markdown("### Links")
        st.markdown("""
        <div style="display: flex; flex-direction: column; gap: 8px;">
            <a href="https://github.com" target="_blank" style="color: #58a6ff; text-decoration: none;">
                <span class="material-icons icon-sm">code</span> GitHub Repo
            </a>
            <a href="https://explorer.solana.com/?cluster=devnet" target="_blank" style="color: #58a6ff; text-decoration: none;">
                <span class="material-icons icon-sm">link</span> Solana Explorer
            </a>
            <a href="https://supabase.com" target="_blank" style="color: #58a6ff; text-decoration: none;">
                <span class="material-icons icon-sm">storage</span> Supabase Dashboard
            </a>
        </div>
        """, unsafe_allow_html=True)
    
    # Main content
    render_header()
    render_metrics(stats)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Two column layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        render_infection_feed(infections)
    
    with col2:
        render_agent_cards(agents)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding: 20px 0; color: #6e7681;">
        <p>
            <span class="material-icons icon-sm">bug_report</span>
            Memory Parasite Protocol | Built for Hackathon 2024
        </p>
        <p style="font-size: 0.8rem;">
            Powered by Groq (LLM) | Supabase (Database) | Solana Devnet (Blockchain) | Streamlit (Dashboard)
        </p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
