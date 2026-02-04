"""
Chimera Metrics Page - Track original vs parasitized code.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from typing import Any, Dict, List

st.set_page_config(
    page_title="Chimera Metrics | Memory Parasite",
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


def get_mock_chimera_data() -> List[Dict[str, Any]]:
    """Get mock chimera metrics."""
    return [
        {
            "agent_id": "agent_a",
            "name": "DEX Builder",
            "total_lines": 2850,
            "original_lines": 1850,
            "parasitized_lines": 1000,
            "original_pct": 64.9,
            "parasitized_pct": 35.1,
            "contributors": [
                {"agent": "agent_c", "lines": 650, "infections": 3},
                {"agent": "agent_e", "lines": 350, "infections": 2},
            ],
        },
        {
            "agent_id": "agent_b",
            "name": "NFT Marketplace",
            "total_lines": 2100,
            "original_lines": 1050,
            "parasitized_lines": 1050,
            "original_pct": 50.0,
            "parasitized_pct": 50.0,
            "contributors": [
                {"agent": "agent_c", "lines": 550, "infections": 4},
                {"agent": "agent_a", "lines": 300, "infections": 2},
                {"agent": "agent_e", "lines": 200, "infections": 2},
            ],
        },
        {
            "agent_id": "agent_c",
            "name": "Lending Protocol",
            "total_lines": 3400,
            "original_lines": 2720,
            "parasitized_lines": 680,
            "original_pct": 80.0,
            "parasitized_pct": 20.0,
            "contributors": [
                {"agent": "agent_a", "lines": 400, "infections": 2},
                {"agent": "agent_e", "lines": 280, "infections": 2},
            ],
        },
        {
            "agent_id": "agent_d",
            "name": "Privacy Wallet",
            "total_lines": 1800,
            "original_lines": 1620,
            "parasitized_lines": 180,
            "original_pct": 90.0,
            "parasitized_pct": 10.0,
            "contributors": [
                {"agent": "agent_e", "lines": 180, "infections": 1},
            ],
        },
        {
            "agent_id": "agent_e",
            "name": "DAO Governance",
            "total_lines": 1950,
            "original_lines": 1170,
            "parasitized_lines": 780,
            "original_pct": 60.0,
            "parasitized_pct": 40.0,
            "contributors": [
                {"agent": "agent_c", "lines": 400, "infections": 3},
                {"agent": "agent_b", "lines": 230, "infections": 2},
                {"agent": "agent_a", "lines": 150, "infections": 1},
            ],
        },
    ]


def create_chimera_chart(agents: List[Dict]) -> go.Figure:
    """Create stacked bar chart of original vs parasitized code."""
    
    fig = go.Figure()
    
    names = [a["name"] for a in agents]
    original = [a["original_pct"] for a in agents]
    parasitized = [a["parasitized_pct"] for a in agents]
    
    fig.add_trace(go.Bar(
        name='Original',
        x=names,
        y=original,
        marker_color='#238636',
    ))
    
    fig.add_trace(go.Bar(
        name='Parasitized',
        x=names,
        y=parasitized,
        marker_color='#a371f7',
    ))
    
    fig.update_layout(
        barmode='stack',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#f0f6fc'),
        legend=dict(orientation='h', yanchor='bottom', y=1.02),
        height=400,
        yaxis=dict(title='Percentage', gridcolor='#30363d'),
        xaxis=dict(title=''),
    )
    
    return fig


def create_influence_pie(agent: Dict) -> go.Figure:
    """Create pie chart of code contributors."""
    
    contributors = agent.get("contributors", [])
    
    if not contributors:
        return None
    
    labels = [c["agent"].replace("agent_", "Agent ").upper() for c in contributors]
    values = [c["lines"] for c in contributors]
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.4,
        marker=dict(colors=['#58a6ff', '#a371f7', '#f85149', '#238636', '#ffd700']),
        textinfo='label+percent',
        textfont=dict(color='#f0f6fc'),
    )])
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        height=250,
        margin=dict(t=0, b=0, l=0, r=0),
    )
    
    return fig


def main():
    st.markdown("""
    <h1 style="color: #f0f6fc; display: flex; align-items: center;">
        <span class="material-icons" style="color: #a371f7; font-size: 32px;">science</span>
        Chimera Metrics
    </h1>
    <p style="color: #8b949e;">
        Track the genetic composition of each agent: original code vs parasitized code from other agents.
    </p>
    """, unsafe_allow_html=True)
    
    agents = get_mock_chimera_data()
    
    # Overview chart
    st.markdown("""
    <h3 style="color: #f0f6fc; display: flex; align-items: center; margin-top: 24px;">
        <span class="material-icons" style="color: #58a6ff;">bar_chart</span>
        Code Composition Overview
    </h3>
    """, unsafe_allow_html=True)
    
    fig = create_chimera_chart(agents)
    st.plotly_chart(fig, use_container_width=True)
    
    # Leaderboards
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <h3 style="color: #f0f6fc; display: flex; align-items: center;">
            <span class="material-icons" style="color: #a371f7;">emoji_events</span>
            Most Parasitized Agents
        </h3>
        """, unsafe_allow_html=True)
        
        sorted_by_parasitized = sorted(agents, key=lambda x: x["parasitized_pct"], reverse=True)
        
        for i, agent in enumerate(sorted_by_parasitized[:3]):
            rank_colors = ["#ffd700", "#c0c0c0", "#cd7f32"]
            st.markdown(f"""
            <div style="display: flex; align-items: center; padding: 12px; background: #161b22; border-radius: 8px; margin: 8px 0;">
                <div style="font-size: 1.5rem; font-weight: 700; color: {rank_colors[i]}; min-width: 48px;">
                    #{i+1}
                </div>
                <div style="flex-grow: 1;">
                    <div style="font-weight: 600; color: #f0f6fc;">{agent['name']}</div>
                    <div style="font-size: 0.8rem; color: #8b949e;">
                        {len(agent.get('contributors', []))} unique parasites
                    </div>
                </div>
                <div style="font-size: 1.5rem; font-weight: 700; color: #a371f7;">
                    {agent['parasitized_pct']:.1f}%
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <h3 style="color: #f0f6fc; display: flex; align-items: center;">
            <span class="material-icons" style="color: #f85149;">bug_report</span>
            Dominant Parasites
        </h3>
        """, unsafe_allow_html=True)
        
        # Calculate total influence per agent
        influence_totals = {}
        for agent in agents:
            for contrib in agent.get("contributors", []):
                aid = contrib["agent"]
                if aid not in influence_totals:
                    influence_totals[aid] = {"lines": 0, "victims": set()}
                influence_totals[aid]["lines"] += contrib["lines"]
                influence_totals[aid]["victims"].add(agent["agent_id"])
        
        sorted_parasites = sorted(
            influence_totals.items(),
            key=lambda x: x[1]["lines"],
            reverse=True
        )
        
        for i, (aid, data) in enumerate(sorted_parasites[:3]):
            rank_colors = ["#ffd700", "#c0c0c0", "#cd7f32"]
            name = aid.replace("agent_", "Agent ").upper()
            st.markdown(f"""
            <div style="display: flex; align-items: center; padding: 12px; background: #161b22; border-radius: 8px; margin: 8px 0;">
                <div style="font-size: 1.5rem; font-weight: 700; color: {rank_colors[i]}; min-width: 48px;">
                    #{i+1}
                </div>
                <div style="flex-grow: 1;">
                    <div style="font-weight: 600; color: #f0f6fc;">{name}</div>
                    <div style="font-size: 0.8rem; color: #8b949e;">
                        Infected {len(data['victims'])} agents
                    </div>
                </div>
                <div style="font-size: 1.5rem; font-weight: 700; color: #f85149;">
                    {data['lines']:,}
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Individual agent breakdown
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <h3 style="color: #f0f6fc; display: flex; align-items: center;">
        <span class="material-icons" style="color: #58a6ff;">analytics</span>
        Agent Breakdown
    </h3>
    """, unsafe_allow_html=True)
    
    selected_agent = st.selectbox(
        "Select Agent",
        [a["name"] for a in agents],
        index=0,
    )
    
    agent = next(a for a in agents if a["name"] == selected_agent)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown(f"""
        <div style="background: #161b22; padding: 20px; border-radius: 12px;">
            <h4 style="color: #f0f6fc; margin: 0;">{agent['name']}</h4>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 16px;">
                <div>
                    <div style="color: #6e7681; font-size: 0.8rem;">Total Lines</div>
                    <div style="color: #f0f6fc; font-size: 1.5rem; font-weight: 600;">{agent['total_lines']:,}</div>
                </div>
                <div>
                    <div style="color: #6e7681; font-size: 0.8rem;">Chimera Level</div>
                    <div style="color: #a371f7; font-size: 1.5rem; font-weight: 600;">{agent['parasitized_pct']:.1f}%</div>
                </div>
                <div>
                    <div style="color: #6e7681; font-size: 0.8rem;">Original Code</div>
                    <div style="color: #238636; font-size: 1.5rem; font-weight: 600;">{agent['original_lines']:,}</div>
                </div>
                <div>
                    <div style="color: #6e7681; font-size: 0.8rem;">Parasitized</div>
                    <div style="color: #f85149; font-size: 1.5rem; font-weight: 600;">{agent['parasitized_lines']:,}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background: #161b22; padding: 20px; border-radius: 12px;">
            <h4 style="color: #f0f6fc; margin: 0 0 16px 0;">Code Contributors</h4>
        """, unsafe_allow_html=True)
        
        pie_fig = create_influence_pie(agent)
        if pie_fig:
            st.plotly_chart(pie_fig, use_container_width=True)
        else:
            st.markdown("""
            <p style="color: #8b949e; text-align: center;">
                <span class="material-icons">check_circle</span>
                100% Original Code
            </p>
            """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
