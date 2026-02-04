"""
Code Evolution Page - Track code commits and their infection sources.
"""

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Any, Dict, List

st.set_page_config(
    page_title="Code Evolution | Memory Parasite",
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


def get_mock_commits(agent_id: str) -> List[Dict[str, Any]]:
    """Get mock commit data for an agent."""
    base_time = datetime.utcnow()
    
    commits = [
        {
            "sha": "abc123",
            "message": "feat: implement base AMM pool structure",
            "lines_added": 150,
            "timestamp": (base_time - timedelta(hours=12)).isoformat(),
            "source": "original",
            "source_agent": None,
            "infection_id": None,
        },
        {
            "sha": "def456",
            "message": "feat: add swap routing logic",
            "lines_added": 85,
            "timestamp": (base_time - timedelta(hours=10)).isoformat(),
            "source": "original",
            "source_agent": None,
            "infection_id": None,
        },
        {
            "sha": "ghi789",
            "message": "feat: integrate lending pool liquidity",
            "lines_added": 120,
            "timestamp": (base_time - timedelta(hours=8)).isoformat(),
            "source": "parasitized",
            "source_agent": "agent_c",
            "source_agent_name": "Lending Protocol",
            "infection_id": "inf_002",
        },
        {
            "sha": "jkl012",
            "message": "feat: add concentrated liquidity positions",
            "lines_added": 200,
            "timestamp": (base_time - timedelta(hours=6)).isoformat(),
            "source": "original",
            "source_agent": None,
            "infection_id": None,
        },
        {
            "sha": "mno345",
            "message": "feat: add flash loan integration",
            "lines_added": 95,
            "timestamp": (base_time - timedelta(hours=4)).isoformat(),
            "source": "parasitized",
            "source_agent": "agent_c",
            "source_agent_name": "Lending Protocol",
            "infection_id": "inf_005",
        },
        {
            "sha": "pqr678",
            "message": "fix: optimize gas usage in swaps",
            "lines_added": 45,
            "timestamp": (base_time - timedelta(hours=2)).isoformat(),
            "source": "original",
            "source_agent": None,
            "infection_id": None,
        },
        {
            "sha": "stu901",
            "message": "feat: add governance token staking",
            "lines_added": 110,
            "timestamp": (base_time - timedelta(hours=1)).isoformat(),
            "source": "parasitized",
            "source_agent": "agent_e",
            "source_agent_name": "DAO Governance",
            "infection_id": "inf_008",
        },
    ]
    
    return commits


def create_timeline_chart(commits: List[Dict]) -> go.Figure:
    """Create timeline chart of commits."""
    
    times = [datetime.fromisoformat(c["timestamp"]) for c in commits]
    lines = [c["lines_added"] for c in commits]
    colors = ["#238636" if c["source"] == "original" else "#a371f7" for c in commits]
    labels = [c["message"][:40] + "..." for c in commits]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=times,
        y=lines,
        mode='markers+lines',
        marker=dict(
            size=[12 + l/20 for l in lines],
            color=colors,
            line=dict(width=2, color='#f0f6fc'),
        ),
        line=dict(color='#30363d', width=2),
        text=labels,
        hovertemplate='%{text}<br>Lines: %{y}<extra></extra>',
    ))
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#f0f6fc'),
        height=300,
        margin=dict(t=20, b=40),
        xaxis=dict(
            title='Time',
            gridcolor='#30363d',
        ),
        yaxis=dict(
            title='Lines Added',
            gridcolor='#30363d',
        ),
        showlegend=False,
    )
    
    return fig


def create_composition_chart(commits: List[Dict]) -> go.Figure:
    """Create running composition chart."""
    
    original_total = 0
    parasitized_total = 0
    
    times = []
    original_data = []
    parasitized_data = []
    
    for commit in commits:
        times.append(datetime.fromisoformat(commit["timestamp"]))
        
        if commit["source"] == "original":
            original_total += commit["lines_added"]
        else:
            parasitized_total += commit["lines_added"]
        
        original_data.append(original_total)
        parasitized_data.append(parasitized_total)
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=times,
        y=original_data,
        name='Original',
        fill='tozeroy',
        fillcolor='rgba(35, 134, 54, 0.3)',
        line=dict(color='#238636', width=2),
    ))
    
    fig.add_trace(go.Scatter(
        x=times,
        y=parasitized_data,
        name='Parasitized',
        fill='tozeroy',
        fillcolor='rgba(163, 113, 247, 0.3)',
        line=dict(color='#a371f7', width=2),
    ))
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#f0f6fc'),
        height=250,
        margin=dict(t=20, b=40),
        legend=dict(orientation='h', yanchor='bottom', y=1.02),
        xaxis=dict(title='', gridcolor='#30363d'),
        yaxis=dict(title='Total Lines', gridcolor='#30363d'),
    )
    
    return fig


def main():
    st.markdown("""
    <h1 style="color: #f0f6fc; display: flex; align-items: center;">
        <span class="material-icons" style="color: #58a6ff; font-size: 32px;">history</span>
        Code Evolution Timeline
    </h1>
    <p style="color: #8b949e;">
        Track every commit and see which code came from infections vs original reasoning.
    </p>
    """, unsafe_allow_html=True)
    
    # Agent selector
    agents = ["agent_a", "agent_b", "agent_c", "agent_d", "agent_e"]
    agent_names = ["DEX Builder", "NFT Marketplace", "Lending Protocol", "Privacy Wallet", "DAO Governance"]
    
    selected = st.selectbox("Select Agent", agent_names, index=0)
    agent_id = agents[agent_names.index(selected)]
    
    commits = get_mock_commits(agent_id)
    
    # Timeline chart
    st.markdown("""
    <h3 style="color: #f0f6fc; display: flex; align-items: center; margin-top: 24px;">
        <span class="material-icons" style="color: #58a6ff;">timeline</span>
        Commit Timeline
    </h3>
    """, unsafe_allow_html=True)
    
    st.plotly_chart(create_timeline_chart(commits), use_container_width=True)
    
    # Composition over time
    st.markdown("""
    <h3 style="color: #f0f6fc; display: flex; align-items: center;">
        <span class="material-icons" style="color: #a371f7;">stacked_line_chart</span>
        Code Composition Over Time
    </h3>
    """, unsafe_allow_html=True)
    
    st.plotly_chart(create_composition_chart(commits), use_container_width=True)
    
    # Commit list
    st.markdown("""
    <h3 style="color: #f0f6fc; display: flex; align-items: center;">
        <span class="material-icons" style="color: #238636;">commit</span>
        Commit History
    </h3>
    """, unsafe_allow_html=True)
    
    for commit in reversed(commits):
        source = commit["source"]
        is_parasitized = source == "parasitized"
        
        border_color = "#a371f7" if is_parasitized else "#238636"
        source_icon = "bug_report" if is_parasitized else "code"
        source_label = f"From {commit.get('source_agent_name', 'Unknown')}" if is_parasitized else "Original"
        
        st.markdown(f"""
        <div style="background: #161b22; border-left: 4px solid {border_color}; padding: 16px; margin: 8px 0; border-radius: 0 8px 8px 0;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <div style="font-weight: 600; color: #f0f6fc; display: flex; align-items: center;">
                        <span class="material-icons icon-sm" style="color: {border_color};">{source_icon}</span>
                        {commit['message']}
                    </div>
                    <div style="display: flex; gap: 16px; margin-top: 8px; font-size: 0.8rem; color: #8b949e;">
                        <span>
                            <span class="material-icons icon-sm">fingerprint</span>
                            {commit['sha']}
                        </span>
                        <span>
                            <span class="material-icons icon-sm">add</span>
                            +{commit['lines_added']} lines
                        </span>
                        <span>
                            <span class="material-icons icon-sm">schedule</span>
                            {commit['timestamp'][:16]}
                        </span>
                    </div>
                </div>
                <div style="padding: 4px 12px; background: {'rgba(163, 113, 247, 0.2)' if is_parasitized else 'rgba(35, 134, 54, 0.2)'}; border-radius: 16px; font-size: 0.75rem; color: {border_color};">
                    {source_label}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
