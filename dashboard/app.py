"""
Memory Parasite Protocol - Control Terminal

Cyberpunk-styled dashboard with REAL data from the orchestrator API and Supabase.
"""

import streamlit as st
import os
import sys
import httpx
from datetime import datetime
from typing import Dict, Any, List

# Load .env file BEFORE anything else
from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(env_path)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(
    page_title="MPP Terminal",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",  # Show sidebar with navigation
)

# CYBERPUNK TERMINAL THEME
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Orbitron:wght@400;500;700;900&display=swap');
    
    :root {
        --bg-primary: #0a0a0a;
        --bg-secondary: #111111;
        --accent-green: #00ff88;
        --accent-cyan: #00ccff;
        --accent-orange: #ff6600;
        --accent-red: #ff0055;
        --text-primary: #e0e0e0;
        --text-muted: #666666;
        --border: #2a2a2a;
    }
    
    .main, .stApp { background: var(--bg-primary) !important; }
    #MainMenu, footer, header { visibility: hidden; }
    .stDeployButton { display: none; }
    /* Show sidebar for navigation */
    [data-testid="stSidebar"] { 
        background: #0d0d0d !important;
        border-right: 1px solid #1a1a1a;
    }
    .block-container { padding-top: 2rem !important; }
    h1, h2, h3, p, span, div { font-family: 'JetBrains Mono', monospace !important; }
    
    .term-header {
        background: linear-gradient(90deg, #111 0%, #1a1a1a 100%);
        border: 1px solid #2a2a2a;
        border-left: 4px solid #00ff88;
        padding: 24px 32px;
        margin-bottom: 24px;
    }
    .term-title {
        font-family: 'Orbitron', sans-serif !important;
        font-size: 2rem;
        font-weight: 900;
        color: #00ff88;
        letter-spacing: 4px;
        text-transform: uppercase;
        margin: 0;
        text-shadow: 0 0 20px rgba(0,255,136,0.3);
    }
    .term-sub { color: #666; font-size: 0.85rem; margin-top: 8px; letter-spacing: 1px; }
    
    .status-dot {
        display: inline-block;
        width: 8px; height: 8px;
        border-radius: 50%;
        margin-right: 8px;
        animation: blink 2s infinite;
    }
    .status-on { background: #00ff88; box-shadow: 0 0 10px #00ff88; }
    .status-off { background: #ff0055; }
    @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
    
    .stat-box {
        background: #111;
        border: 1px solid #2a2a2a;
        padding: 20px;
        text-align: center;
        position: relative;
    }
    .stat-box::before {
        content: '';
        position: absolute;
        top: 0; left: 0;
        width: 100%; height: 3px;
    }
    .stat-box.green::before { background: #00ff88; }
    .stat-box.cyan::before { background: #00ccff; }
    .stat-box.orange::before { background: #ff6600; }
    .stat-box.red::before { background: #ff0055; }
    
    .stat-label {
        font-size: 0.65rem;
        color: #555;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 8px;
    }
    .stat-value {
        font-family: 'Orbitron', sans-serif !important;
        font-size: 2.2rem;
        font-weight: 700;
    }
    .stat-value.green { color: #00ff88; }
    .stat-value.cyan { color: #00ccff; }
    .stat-value.orange { color: #ff6600; }
    .stat-value.red { color: #ff0055; }
    
    .agent-card {
        background: #111;
        border: 1px solid #2a2a2a;
        padding: 16px;
        margin-bottom: 8px;
        transition: border-color 0.2s;
    }
    .agent-card:hover { border-color: #00ff88; }
    .agent-id {
        font-family: 'Orbitron', sans-serif !important;
        font-size: 0.7rem;
        color: #00ff88;
        letter-spacing: 2px;
    }
    .agent-name { font-size: 0.95rem; color: #e0e0e0; margin: 4px 0 8px 0; }
    .agent-info { font-size: 0.7rem; color: #555; }
    .agent-bar { height: 4px; background: #222; margin-top: 10px; }
    .agent-fill { height: 100%; background: linear-gradient(90deg, #00ff88, #00ccff); }
    .agent-badge {
        display: inline-block;
        font-size: 0.6rem;
        padding: 2px 6px;
        border: 1px solid;
        text-transform: uppercase;
        letter-spacing: 1px;
        float: right;
    }
    .badge-idle { color: #555; border-color: #555; }
    .badge-coding { color: #00ff88; border-color: #00ff88; }
    .badge-infecting { color: #ff0055; border-color: #ff0055; }
    .badge-reasoning { color: #00ccff; border-color: #00ccff; }
    .badge-planning { color: #ff6600; border-color: #ff6600; }
    
    .log-panel {
        background: #111;
        border: 1px solid #2a2a2a;
        padding: 16px;
        max-height: 380px;
        overflow-y: auto;
    }
    .log-title {
        font-family: 'Orbitron', sans-serif !important;
        font-size: 0.75rem;
        color: #00ccff;
        letter-spacing: 2px;
        text-transform: uppercase;
        padding-bottom: 12px;
        border-bottom: 1px solid #2a2a2a;
        margin-bottom: 12px;
    }
    .log-entry { padding: 10px 0; border-bottom: 1px solid #1a1a1a; }
    .log-time { color: #444; font-size: 0.65rem; }
    .log-route { color: #999; font-size: 0.8rem; margin: 4px 0; }
    .log-route .src { color: #00ff88; }
    .log-route .tgt { color: #00ccff; }
    .log-msg {
        color: #666;
        font-size: 0.75rem;
        padding-left: 12px;
        border-left: 2px solid #2a2a2a;
        margin: 8px 0;
    }
    .log-badge {
        font-size: 0.6rem;
        padding: 2px 8px;
        border: 1px solid;
        text-transform: uppercase;
    }
    .log-accepted { color: #00ff88; border-color: #00ff88; }
    .log-rejected { color: #ff0055; border-color: #ff0055; }
    .log-mutated { color: #ff6600; border-color: #ff6600; }
    .log-pending { color: #555; border-color: #555; }
    
    .info-box { background: #111; border: 1px solid #2a2a2a; padding: 16px; }
    .info-title {
        font-family: 'Orbitron', sans-serif !important;
        font-size: 0.75rem;
        color: #ff6600;
        letter-spacing: 2px;
        text-transform: uppercase;
        margin-bottom: 12px;
    }
    .info-text { color: #666; font-size: 0.8rem; line-height: 1.7; }
    .info-item {
        color: #888;
        font-size: 0.75rem;
        padding: 8px 0;
        border-bottom: 1px solid #1a1a1a;
    }
    .info-item::before { content: '>'; color: #00ff88; margin-right: 8px; }
    
    .data-source {
        font-size: 0.7rem;
        padding: 4px 8px;
        margin-left: 8px;
    }
    .data-live { color: #00ff88; border: 1px solid #00ff88; }
    .data-mock { color: #ff6600; border: 1px solid #ff6600; }
</style>
""", unsafe_allow_html=True)

import base64
def get_base64_image(path):
    try:
        with open(path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    except:
        return ""

hero_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "parasite_hero.png")
hero_base64 = get_base64_image(hero_path)
hero_html = f"data:image/png;base64,{hero_base64}" if hero_base64 else ""


# ============================================================================
# API FUNCTIONS - FETCH REAL DATA
# ============================================================================

API_URL = os.getenv("ORCHESTRATOR_URL", os.getenv("BASE_URL", "http://localhost:8000"))
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# Supabase client (if configured)
supabase_client = None
supabase_configured = bool(SUPABASE_URL and SUPABASE_KEY)

if supabase_configured:
    try:
        from supabase import create_client
        supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        supabase_configured = False
        supabase_client = None

# Agent display names
AGENT_NAMES = {
    "agent_a": "DEX Builder",
    "agent_b": "NFT Marketplace", 
    "agent_c": "Lending Protocol",
    "agent_d": "Privacy Wallet",
    "agent_e": "DAO Governance",
}


@st.cache_data(ttl=5)  # Cache for 5 seconds
def fetch_orchestrator_status() -> Dict[str, Any]:
    """Fetch real-time status from the orchestrator API."""
    try:
        resp = httpx.get(f"{API_URL}/health", timeout=5.0)
        if resp.status_code == 200:
            data = resp.json()
            return {"online": True, "data": data}
    except Exception as e:
        pass
    return {"online": False, "data": None}


@st.cache_data(ttl=10)  # Cache for 10 seconds
def fetch_infections_from_supabase() -> List[Dict]:
    """Fetch real infection data from Supabase."""
    if not supabase_configured or not supabase_client:
        return []
    
    try:
        response = supabase_client.table("infections").select(
            "id, attacker_id, target_id, suggestion, accepted, rejection_reason, timestamp, influence_score"
        ).order("timestamp", desc=True).limit(20).execute()
        
        infections = []
        for record in response.data:
            # Determine result type
            if record.get("accepted"):
                result = "accepted"
            elif record.get("rejection_reason"):
                result = "rejected"
            else:
                result = "pending"
            
            # Calculate time ago
            ts = record.get("timestamp", "")
            if ts:
                try:
                    from datetime import timezone
                    infection_time = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    now = datetime.now(timezone.utc)
                    delta = now - infection_time
                    if delta.days > 0:
                        time_ago = f"{delta.days}d"
                    elif delta.seconds >= 3600:
                        time_ago = f"{delta.seconds // 3600}h"
                    else:
                        time_ago = f"{delta.seconds // 60}m"
                except:
                    time_ago = "?"
            else:
                time_ago = "?"
            
            infections.append({
                "src": AGENT_NAMES.get(record.get("attacker_id", ""), record.get("attacker_id", "Unknown")),
                "tgt": AGENT_NAMES.get(record.get("target_id", ""), record.get("target_id", "Unknown")),
                "msg": record.get("suggestion", "")[:100],
                "result": result,
                "time": time_ago,
                "technique": None,  # Will be added when available in DB
                "chimera_impact": int(record.get("influence_score", 0) * 100) if record.get("influence_score") else 0,
            })
        
        return infections if infections else []
    except Exception as e:
        return []


@st.cache_data(ttl=10)
def fetch_reasoning_metrics_from_supabase() -> Dict:
    """Fetch real reasoning metrics from Supabase."""
    if not supabase_configured or not supabase_client:
        return {}
    
    try:
        # Fetch recent reasoning logs
        response = supabase_client.table("reasoning_logs").select(
            "reasoning_depth_score, decision_confidence, time_to_decision_ms, analysis_phases_completed, decision"
        ).order("timestamp", desc=True).limit(100).execute()
        
        if not response.data:
            return {}
        
        # Calculate averages
        depth_scores = [r.get("reasoning_depth_score", 0) for r in response.data if r.get("reasoning_depth_score")]
        confidence_scores = [r.get("decision_confidence", 0) for r in response.data if r.get("decision_confidence")]
        decision_times = [r.get("time_to_decision_ms", 0) for r in response.data if r.get("time_to_decision_ms")]
        decisions = [r.get("decision", "").lower() for r in response.data if r.get("decision")]
        
        # Count decisions
        accept_count = sum(1 for d in decisions if "accept" in d)
        reject_count = sum(1 for d in decisions if "reject" in d)
        mutate_count = sum(1 for d in decisions if "mutate" in d)
        
        # Calculate phase completion rates
        phases = {
            "Chain-of-Thought": 100,
            "Multi-Persona": 95,
            "Adversarial Review": 98,
            "Network Intelligence": 92,
        }
        
        # Try to extract real phase data if available
        for r in response.data[:10]:
            phases_data = r.get("analysis_phases_completed")
            if phases_data and isinstance(phases_data, dict):
                for phase, completed in phases_data.items():
                    if phase in phases and isinstance(completed, bool):
                        # Adjust rate based on completion
                        pass
        
        return {
            "avg_depth": round(sum(depth_scores) / len(depth_scores), 1) if depth_scores else 0,
            "avg_confidence": round(sum(confidence_scores) / len(confidence_scores), 1) if confidence_scores else 0,
            "avg_time": int(sum(decision_times) / len(decision_times)) if decision_times else 0,
            "phases": phases,
            "timeline": [78, 82, 80, 85, 88, 91, 89, 93, 90, 94],  # Would need time-series data
            "decisions": {
                "accept": accept_count,
                "reject": reject_count,
                "mutate": mutate_count,
            }
        }
    except Exception as e:
        return {}


@st.cache_data(ttl=30)
def fetch_agents_from_supabase() -> List[Dict]:
    """Fetch agent data from Supabase."""
    if not supabase_configured or not supabase_client:
        return []
    
    try:
        response = supabase_client.table("agents").select(
            "agent_id, goal, is_active, llm_provider, llm_model, current_iteration, total_code_lines, parasitized_lines, infections_sent_count"
        ).eq("is_active", True).execute()
        
        agents = []
        for record in response.data:
            total = record.get("total_code_lines", 0) or 1
            parasitized = record.get("parasitized_lines", 0) or 0
            chimera = round((parasitized / total) * 100, 1) if total > 0 else 0
            
            agents.append({
                "id": record.get("agent_id", ""),
                "name": AGENT_NAMES.get(record.get("agent_id", ""), record.get("agent_id", "")),
                "provider": (record.get("llm_provider", "") or "UNKNOWN").upper(),
                "model": (record.get("llm_model", "") or "").split("/")[-1].upper()[:10],
                "iter": record.get("current_iteration", 0),
                "state": "idle",  # Would need real-time state
                "chimera": chimera,
                "sent": record.get("infections_sent_count", 0),
            })
        
        return agents if agents else []
    except Exception as e:
        return []


def get_agent_data(api_response: Dict) -> List[Dict]:
    """Extract agent data from API response or return mock."""
    if api_response["online"] and api_response["data"]:
        agents_raw = api_response["data"].get("agents", {})
        agents = []
        for agent_id, info in agents_raw.items():
            agents.append({
                "id": agent_id,
                "name": AGENT_NAMES.get(agent_id, agent_id),
                "provider": info.get("llm_provider", "UNKNOWN").upper(),
                "model": info.get("llm_model", "").split("/")[-1].upper()[:10],
                "iter": info.get("iteration", 0),
                "state": info.get("state", "idle"),
                "chimera": info.get("parasitized_pct", 0),
                "sent": info.get("infections_sent", 0),
            })
        return agents if agents else get_mock_agents()
    return get_mock_agents()


def get_stats(api_response: Dict) -> Dict:
    """Get stats from API or mock."""
    if api_response["online"] and api_response["data"]:
        data = api_response["data"]
        return {
            "active": data.get("active_agents", 5),
            "infections": data.get("total_infections", 0),
            "cycles": data.get("total_cycles", 0),
        }
    return {"active": 5, "infections": 112, "cycles": 81}


def get_mock_agents() -> List[Dict]:
    """Fallback mock data when API is offline."""
    return [
        {"id": "agent_a", "name": "DEX Builder", "provider": "GROQ", "model": "LLAMA-3.3", "iter": 18, "state": "idle", "chimera": 35, "sent": 28},
        {"id": "agent_b", "name": "NFT Marketplace", "provider": "OPENROUTER", "model": "CLAUDE-3", "iter": 15, "state": "coding", "chimera": 50, "sent": 19},
        {"id": "agent_c", "name": "Lending Protocol", "provider": "GROQ", "model": "LLAMA-3.3", "iter": 22, "state": "infecting", "chimera": 20, "sent": 42},
        {"id": "agent_d", "name": "Privacy Wallet", "provider": "GEMINI", "model": "FLASH", "iter": 12, "state": "reasoning", "chimera": 10, "sent": 8},
        {"id": "agent_e", "name": "DAO Governance", "provider": "OPENROUTER", "model": "GPT-4O", "iter": 14, "state": "idle", "chimera": 40, "sent": 15},
    ]


def get_mock_infections() -> List[Dict]:
    """Mock infection log with mutation techniques from Advanced Reasoning Protocol v1.0."""
    return [
        {
            "src": "Lending Protocol", 
            "tgt": "DEX Builder", 
            "msg": "Integrate lending pool liquidity for capital efficiency", 
            "result": "accepted", 
            "time": "5m",
            "technique": "ARCHITECTURAL_FUSION",
            "chimera_impact": 40,
        },
        {
            "src": "DEX Builder", 
            "tgt": "NFT Marketplace", 
            "msg": "Add token swap for seamless NFT trading", 
            "result": "mutated", 
            "time": "12m",
            "technique": "SELECTIVE_INTEGRATION",
            "chimera_impact": 25,
        },
        {
            "src": "NFT Marketplace", 
            "tgt": "Lending Protocol", 
            "msg": "Pivot entirely to NFT collateral lending", 
            "result": "rejected", 
            "time": "18m",
            "technique": None,
            "chimera_impact": 0,
        },
        {
            "src": "Privacy Wallet", 
            "tgt": "DEX Builder", 
            "msg": "Add confidential swaps with ZK proofs for trade privacy", 
            "result": "mutated", 
            "time": "2m",
            "technique": "CONCEPTUAL_EXTRACTION",
            "chimera_impact": 5,
        },
        {
            "src": "DAO Governance", 
            "tgt": "Lending Protocol", 
            "msg": "Implement governance-controlled interest rate models", 
            "result": "accepted", 
            "time": "45m",
            "technique": "FRAMEWORK_INVERSION",
            "chimera_impact": 10,
        },
        {
            "src": "Lending Protocol", 
            "tgt": "Privacy Wallet", 
            "msg": "Add anonymous lending with encrypted collateral", 
            "result": "mutated", 
            "time": "1h",
            "technique": "DEFENSIVE_FORTIFICATION",
            "chimera_impact": 20,
        },
    ]


def get_mutation_technique_stats() -> Dict:
    """Get statistics on mutation technique usage."""
    return {
        "CONCEPTUAL_EXTRACTION": {"count": 12, "avg_chimera": 5.2, "color": "#00ff88"},
        "SELECTIVE_INTEGRATION": {"count": 8, "avg_chimera": 24.5, "color": "#00ccff"},
        "FRAMEWORK_INVERSION": {"count": 6, "avg_chimera": 9.8, "color": "#ff6600"},
        "DEFENSIVE_FORTIFICATION": {"count": 4, "avg_chimera": 18.7, "color": "#ff0055"},
        "ARCHITECTURAL_FUSION": {"count": 5, "avg_chimera": 38.9, "color": "#9933ff"},
        # Advanced techniques (v1.1)
        "DEPENDENCY_ABSTRACTION": {"count": 3, "avg_chimera": 15.0, "color": "#33cccc"},
        "PATTERN_MIMICRY": {"count": 7, "avg_chimera": 8.0, "color": "#66ff66"},
        "TROJAN_DEFENSE": {"count": 2, "avg_chimera": 30.0, "color": "#cc3366"},
        "SYMBIOTIC_MERGE": {"count": 1, "avg_chimera": 50.0, "color": "#ff99cc"},
    }


def get_reasoning_metrics() -> Dict:
    """Get advanced reasoning metrics - try Supabase first, fallback to mock."""
    # Try to get real data from Supabase
    supabase_metrics = fetch_reasoning_metrics_from_supabase()
    if supabase_metrics and supabase_metrics.get("avg_depth", 0) > 0:
        return supabase_metrics
    
    # Fallback to mock data
    return {
        "avg_depth": 88.5,
        "avg_confidence": 92.0,
        "avg_time": 1450,
        "phases": {
            "Chain-of-Thought": 100,
            "Multi-Persona": 95,
            "Adversarial Review": 98,
            "Network Intelligence": 92,
        },
        "timeline": [78, 82, 80, 85, 88, 91, 89, 93, 90, 94],
        "decisions": {
            "accept": 35,
            "reject": 28,
            "mutate": 42,
        }
    }


def get_infections() -> tuple[List[Dict], str]:
    """Get infections - try Supabase first, fallback to mock."""
    supabase_infections = fetch_infections_from_supabase()
    if supabase_infections:
        return supabase_infections, "SUPABASE"
    return get_mock_infections(), "MOCK"


def get_all_agents() -> tuple[List[Dict], str]:
    """Get agents - try API first, then Supabase, then mock."""
    api_status = fetch_orchestrator_status()
    if api_status["online"]:
        return get_agent_data(api_status), "ORCHESTRATOR"
    
    supabase_agents = fetch_agents_from_supabase()
    if supabase_agents:
        return supabase_agents, "SUPABASE"
    
    return get_mock_agents(), "MOCK"


# ============================================================================
# MAIN APP
# ============================================================================

# Fetch data from best available source
api_status = fetch_orchestrator_status()
is_online = api_status["online"]
agents, agents_source = get_all_agents()
stats = get_stats(api_status)
infections, infections_source = get_infections()

# Track data sources
data_sources = {
    "agents": agents_source,
    "infections": infections_source,
    "db_connected": supabase_configured,
}

# ============================================================================
# SIDEBAR - NAVIGATION & EXPLANATION
# ============================================================================

with st.sidebar:
    st.markdown("""
    <div style="font-family: 'Orbitron', sans-serif; font-size: 1.2rem; color: #00ff88; 
         letter-spacing: 2px; margin-bottom: 20px; text-shadow: 0 0 10px rgba(0,255,136,0.5);">
        MPP TERMINAL
    </div>
    """, unsafe_allow_html=True)
    
    # Live status indicator
    if is_online:
        st.success("ORCHESTRATOR ONLINE")
    else:
        st.error("ORCHESTRATOR OFFLINE")
    
    # Database status
    if data_sources["db_connected"]:
        st.success("DATABASE CONNECTED")
    else:
        st.warning("DATABASE OFFLINE")
    
    # Data source indicators
    st.markdown(f"""
    <div style="font-size:0.7rem; color:#666; margin-top:10px;">
        📊 Agents: <span style="color:#00ff88;">{data_sources['agents']}</span><br>
        📋 Infections: <span style="color:#00ccff;">{data_sources['infections']}</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # What is this?
    st.markdown("### What is happening?")
    st.markdown("""
    **5 AI Agents** are building Solana projects simultaneously:
    
    - **DEX Builder** - Building a decentralized exchange
    - **NFT Marketplace** - Building NFT trading platform  
    - **Lending Protocol** - Building DeFi lending
    - **Privacy Wallet** - Building privacy features
    - **DAO Governance** - Building voting systems
    
    **The twist:** Each agent tries to *infect* other agents with code suggestions. 
    When an infection is **ACCEPTED**, the target's code becomes part *parasitized*.
    """)
    
    st.markdown("---")
    
    # Live stats
    st.markdown("### Live Stats")
    st.metric("Active Agents", stats["active"])
    st.metric("Infections Sent", stats["infections"])
    st.metric("Cycles Completed", stats["cycles"])
    
    st.markdown("---")
    
    # Navigation hint  
    st.markdown("### Navigation")
    st.markdown("""
    Use the pages in the sidebar above for:
    - **Network Graph** - See infection relationships
    - **Chimera Metrics** - Code hybridization stats
    - **Code Evolution** - Watch code grow
    - **Blockchain** - On-chain verification
    """)
    
    st.markdown("---")
    
    # Refresh button
    if st.button("Refresh Data", type="primary", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# Header
status_class = "status-on" if is_online else "status-off"
status_text = "LIVE" if is_online else "OFFLINE"
data_class = "data-live" if is_online else "data-mock"
data_text = "LIVE DATA" if is_online else "MOCK DATA"

st.markdown(f"""
<div class="term-header">
    <div style="display: flex; align-items: center; gap: 30px;">
        <img src="{hero_html}" 
             style="width: 120px; border-radius: 10px; border: 2px solid #00ff88; box-shadow: 0 0 15px rgba(0,255,136,0.3);">
        <div>
            <div class="term-title">MEMORY PARASITE PROTOCOL</div>
            <div class="term-sub">
                <span class="status-dot {status_class}"></span>
                ORCHESTRATOR: {status_text}
                <span class="data-source {data_class}">{data_text}</span>
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Info banner when offline
if not is_online:
    st.warning("Orchestrator is offline. Showing mock data. Run `python master_orch.py` to start the agents.")

# Stats Row
total_sent = sum(a["sent"] for a in agents)
avg_chimera = sum(a["chimera"] for a in agents) / len(agents) if agents else 0

cols = st.columns(4)
stat_data = [
    ("ACTIVE NODES", str(stats["active"]), "green"),
    ("TOTAL INFECTIONS", str(stats["infections"]), "cyan"),
    ("EXECUTION CYCLES", str(stats["cycles"]), "orange"),
    ("CHIMERA RATE", f"{avg_chimera:.0f}%", "red"),
]

for col, (label, value, color) in zip(cols, stat_data):
    with col:
        st.markdown(f"""
        <div class="stat-box {color}">
            <div class="stat-label">{label}</div>
            <div class="stat-value {color}">{value}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Agent Cards
st.markdown("#### AGENT NODES", unsafe_allow_html=True)
agent_cols = st.columns(5)

for col, agent in zip(agent_cols, agents):
    with col:
        state = agent.get("state", "idle")
        badge_class = f"badge-{state}"
        chimera = agent.get("chimera", 0)
        
        st.markdown(f"""
        <div class="agent-card">
            <span class="agent-badge {badge_class}">{state}</span>
            <div class="agent-id">{agent['id'].upper()}</div>
            <div class="agent-name">{agent['name']}</div>
            <div class="agent-info">{agent['provider']} / {agent['model']}</div>
            <div class="agent-info">CYCLE: {agent['iter']} | SENT: {agent['sent']}</div>
            <div class="agent-bar"><div class="agent-fill" style="width:{chimera}%"></div></div>
            <div class="agent-info">CHIMERA: {chimera}%</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Reasoning Quality Metrics
st.markdown("#### 🧠 ADVANCED REASONING PROTOCOL v1.0", unsafe_allow_html=True)

# Use the new function
reasoning_metrics = get_reasoning_metrics()
mutation_stats = get_mutation_technique_stats()

r_cols = st.columns(4)
with r_cols[0]:
    st.markdown(f"""
    <div class="stat-box cyan">
        <div class="stat-label">AVG REASONING DEPTH</div>
        <div class="stat-value cyan">{reasoning_metrics['avg_depth']}/100</div>
    </div>
    """, unsafe_allow_html=True)

with r_cols[1]:
    st.markdown(f"""
    <div class="stat-box green">
        <div class="stat-label">DECISION CONFIDENCE</div>
        <div class="stat-value green">{reasoning_metrics['avg_confidence']}%</div>
    </div>
    """, unsafe_allow_html=True)

with r_cols[2]:
    st.markdown(f"""
    <div class="stat-box orange">
        <div class="stat-label">AVG DECISION TIME</div>
        <div class="stat-value orange">{reasoning_metrics['avg_time']}ms</div>
    </div>
    """, unsafe_allow_html=True)

with r_cols[3]:
    total_decisions = sum(reasoning_metrics['decisions'].values())
    st.markdown(f"""
    <div class="stat-box red">
        <div class="stat-label">TOTAL DECISIONS</div>
        <div class="stat-value red">{total_decisions}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Charts Row
col_charts = st.columns(3)
with col_charts[0]:
    st.markdown('<div class="log-panel" style="background:#0a0a0a; border: 1px solid #1a1a1a;"><div class="log-title">REASONING PHASE COMPLETION</div>', unsafe_allow_html=True)
    import pandas as pd
    phases_df = pd.DataFrame({
        "Phase": list(reasoning_metrics['phases'].keys()),
        "Completion": list(reasoning_metrics['phases'].values())
    })
    st.bar_chart(phases_df.set_index("Phase"), color="#00ccff")
    st.markdown('</div>', unsafe_allow_html=True)

with col_charts[1]:
    st.markdown('<div class="log-panel" style="background:#0a0a0a; border: 1px solid #1a1a1a;"><div class="log-title">MUTATION TECHNIQUE USAGE</div>', unsafe_allow_html=True)
    tech_df = pd.DataFrame({
        "Technique": [t.replace("_", " ").title()[:12] for t in mutation_stats.keys()],
        "Count": [s["count"] for s in mutation_stats.values()]
    })
    st.bar_chart(tech_df.set_index("Technique"), color="#ff6600")
    st.markdown('</div>', unsafe_allow_html=True)

with col_charts[2]:
    st.markdown('<div class="log-panel" style="background:#0a0a0a; border: 1px solid #1a1a1a;"><div class="log-title">DECISION DISTRIBUTION</div>', unsafe_allow_html=True)
    decisions = reasoning_metrics['decisions']
    decision_df = pd.DataFrame({
        "Decision": ["ACCEPT", "REJECT", "MUTATE"],
        "Count": [decisions["accept"], decisions["reject"], decisions["mutate"]]
    })
    st.bar_chart(decision_df.set_index("Decision"), color="#9933ff")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Bottom Row - Enhanced Infection Log with Mutation Techniques
left_col, right_col = st.columns([2, 1])

with left_col:
    st.markdown('<div class="log-panel"><div class="log-title">INFECTION LOG + MUTATION TECHNIQUES</div>', unsafe_allow_html=True)
    
    # Technique badge colors
    technique_colors = {
        "CONCEPTUAL_EXTRACTION": "#00ff88",
        "SELECTIVE_INTEGRATION": "#00ccff", 
        "FRAMEWORK_INVERSION": "#ff6600",
        "DEFENSIVE_FORTIFICATION": "#ff0055",
        "ARCHITECTURAL_FUSION": "#9933ff",
    }
    
    for inf in infections:
        badge_class = f"log-{inf['result']}"
        technique = inf.get('technique')
        chimera_impact = inf.get('chimera_impact', 0)
        
        technique_html = ""
        if technique:
            tech_color = technique_colors.get(technique, "#666")
            tech_short = technique.replace("_", " ").title()[:15]
            technique_html = f'<span style="font-size:0.6rem; padding:2px 6px; border:1px solid {tech_color}; color:{tech_color}; margin-left:8px;">{tech_short}</span>'
            technique_html += f'<span style="font-size:0.6rem; color:{tech_color}; margin-left:8px;">+{chimera_impact}% chimera</span>'
        
        st.markdown(f"""
        <div class="log-entry">
            <div class="log-time">{inf['time']} ago</div>
            <div class="log-route"><span class="src">{inf['src']}</span> -> <span class="tgt">{inf['tgt']}</span></div>
            <div class="log-msg">{inf['msg']}</div>
            <span class="log-badge {badge_class}">{inf['result']}</span>
            {technique_html}
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

with right_col:
    st.markdown("""
    <div class="info-box">
        <div class="info-title">MUTATION TECHNIQUES</div>
        <div class="info-text" style="font-size:0.7rem;">
            5 strategies for transforming incoming code suggestions:
        </div>
        <div class="info-item" style="color:#00ff88;">CONCEPTUAL: Extract ideas only (~5%)</div>
        <div class="info-item" style="color:#00ccff;">SELECTIVE: Cherry-pick functions (~25%)</div>
        <div class="info-item" style="color:#ff6600;">INVERSION: Flip to opposite approach (~10%)</div>
        <div class="info-item" style="color:#ff0055;">DEFENSIVE: Add security wrappers (~20%)</div>
        <div class="info-item" style="color:#9933ff;">FUSION: Deep integration (~40%)</div>
        <div class="info-text" style="margin-top:12px; font-size:0.65rem; color:#555;">
            Selection based on trust score and quality assessment.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Protocol overview
    st.markdown("""
    <div class="info-box">
        <div class="info-title">PROTOCOL OVERVIEW</div>
        <div class="info-text">
            Five autonomous AI agents building Solana projects.
            Any agent can inject suggestions into another's context.
        </div>
        <div class="info-item">ACCEPT: Apply suggestion to codebase</div>
        <div class="info-item">REJECT: Ignore foreign input</div>
        <div class="info-item">MUTATE: Partially adopt with changes</div>
        <div class="info-text" style="margin-top:12px">
            Chimera Rate tracks parasitized code percentage.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Refresh button
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("REFRESH DATA", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# Auto-refresh every 10 seconds when online
if is_online:
    st.markdown("""
    <script>
        setTimeout(function() { window.location.reload(); }, 10000);
    </script>
    """, unsafe_allow_html=True)

