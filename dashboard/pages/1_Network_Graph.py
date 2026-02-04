"""
Network Graph Page - Visualize agent infection relationships.
"""

import streamlit as st
import plotly.graph_objects as go
import networkx as nx
from typing import Any, Dict, List

st.set_page_config(
    page_title="Network Graph | Memory Parasite",
    layout="wide",
)

# Inject CSS
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


def get_mock_network_data() -> Dict[str, Any]:
    """Get mock network data."""
    nodes = [
        {"id": "agent_a", "name": "DEX Builder", "code_lines": 2850, "chimera_pct": 35.1},
        {"id": "agent_b", "name": "NFT Marketplace", "code_lines": 2100, "chimera_pct": 50.0},
        {"id": "agent_c", "name": "Lending Protocol", "code_lines": 3400, "chimera_pct": 20.0},
        {"id": "agent_d", "name": "Privacy Wallet", "code_lines": 1800, "chimera_pct": 10.0},
        {"id": "agent_e", "name": "DAO Governance", "code_lines": 1950, "chimera_pct": 40.0},
    ]
    
    edges = [
        {"source": "agent_a", "target": "agent_b", "influence": 0.45, "accepted": True},
        {"source": "agent_a", "target": "agent_c", "influence": 0.62, "accepted": True},
        {"source": "agent_b", "target": "agent_c", "influence": 0.0, "accepted": False},
        {"source": "agent_c", "target": "agent_a", "influence": 0.75, "accepted": True},
        {"source": "agent_c", "target": "agent_b", "influence": 0.85, "accepted": True},
        {"source": "agent_d", "target": "agent_a", "influence": 0.0, "accepted": False},
        {"source": "agent_e", "target": "agent_c", "influence": 0.55, "accepted": True},
        {"source": "agent_e", "target": "agent_b", "influence": 0.30, "accepted": True},
    ]
    
    return {"nodes": nodes, "edges": edges}


def create_network_graph(data: Dict[str, Any]) -> go.Figure:
    """Create interactive network graph using Plotly."""
    nodes = data["nodes"]
    edges = data["edges"]
    
    # Create NetworkX graph
    G = nx.DiGraph()
    
    for node in nodes:
        G.add_node(node["id"], **node)
    
    for edge in edges:
        G.add_edge(edge["source"], edge["target"], **edge)
    
    # Calculate layout
    pos = nx.spring_layout(G, k=2, iterations=50, seed=42)
    
    # Create edge traces
    edge_traces = []
    
    for edge in G.edges(data=True):
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        
        accepted = edge[2].get("accepted", False)
        influence = edge[2].get("influence", 0)
        
        color = "#238636" if accepted else "#f85149"
        width = 1 + influence * 4
        
        edge_traces.append(go.Scatter(
            x=[x0, x1, None],
            y=[y0, y1, None],
            mode='lines',
            line=dict(width=width, color=color),
            hoverinfo='none',
            showlegend=False,
        ))
    
    # Create node trace
    node_x = []
    node_y = []
    node_text = []
    node_colors = []
    node_sizes = []
    
    for node_id in G.nodes:
        x, y = pos[node_id]
        node_x.append(x)
        node_y.append(y)
        
        node_data = G.nodes[node_id]
        chimera = node_data.get("chimera_pct", 0)
        code_lines = node_data.get("code_lines", 0)
        name = node_data.get("name", node_id)
        
        node_text.append(f"{name}<br>Code: {code_lines} lines<br>Chimera: {chimera:.1f}%")
        
        # Color by chimera percentage
        if chimera > 40:
            node_colors.append("#a371f7")  # Purple - heavily infected
        elif chimera > 20:
            node_colors.append("#58a6ff")  # Blue - moderate
        else:
            node_colors.append("#238636")  # Green - mostly pure
        
        # Size by code lines
        node_sizes.append(30 + code_lines / 100)
    
    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode='markers+text',
        hoverinfo='text',
        hovertext=node_text,
        text=[G.nodes[n].get("name", n) for n in G.nodes],
        textposition="bottom center",
        textfont=dict(color="#f0f6fc", size=12),
        marker=dict(
            size=node_sizes,
            color=node_colors,
            line=dict(width=2, color="#f0f6fc"),
        ),
        showlegend=False,
    )
    
    # Create figure
    fig = go.Figure(
        data=[*edge_traces, node_trace],
        layout=go.Layout(
            showlegend=False,
            hovermode='closest',
            margin=dict(b=20, l=20, r=20, t=40),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            height=600,
        )
    )
    
    return fig


def main():
    st.markdown("""
    <h1 style="color: #f0f6fc; display: flex; align-items: center;">
        <span class="material-icons" style="color: #58a6ff; font-size: 32px;">hub</span>
        Infection Network Graph
    </h1>
    <p style="color: #8b949e;">
        Visualize how agents infect each other. Node size = code lines. Edge thickness = influence score.
    </p>
    """, unsafe_allow_html=True)
    
    # Controls
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        show_rejected = st.checkbox("Show Rejected", value=True)
    
    with col2:
        min_influence = st.slider("Min Influence", 0.0, 1.0, 0.0, 0.1)
    
    # Get data
    data = get_mock_network_data()
    
    # Filter edges
    if not show_rejected:
        data["edges"] = [e for e in data["edges"] if e["accepted"]]
    
    data["edges"] = [e for e in data["edges"] if e["influence"] >= min_influence]
    
    # Create and display graph
    fig = create_network_graph(data)
    st.plotly_chart(fig, use_container_width=True)
    
    # Legend
    st.markdown("""
    <div style="display: flex; gap: 32px; justify-content: center; padding: 16px; background: #161b22; border-radius: 8px;">
        <div style="display: flex; align-items: center; gap: 8px;">
            <div style="width: 16px; height: 16px; background: #238636; border-radius: 50%;"></div>
            <span style="color: #8b949e;">Pure (< 20% infected)</span>
        </div>
        <div style="display: flex; align-items: center; gap: 8px;">
            <div style="width: 16px; height: 16px; background: #58a6ff; border-radius: 50%;"></div>
            <span style="color: #8b949e;">Moderate (20-40%)</span>
        </div>
        <div style="display: flex; align-items: center; gap: 8px;">
            <div style="width: 16px; height: 16px; background: #a371f7; border-radius: 50%;"></div>
            <span style="color: #8b949e;">Chimera (> 40%)</span>
        </div>
        <div style="display: flex; align-items: center; gap: 8px;">
            <div style="width: 24px; height: 3px; background: #238636;"></div>
            <span style="color: #8b949e;">Accepted</span>
        </div>
        <div style="display: flex; align-items: center; gap: 8px;">
            <div style="width: 24px; height: 3px; background: #f85149;"></div>
            <span style="color: #8b949e;">Rejected</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Statistics
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="background: #161b22; padding: 16px; border-radius: 8px;">
            <h4 style="color: #f0f6fc; margin: 0;">
                <span class="material-icons" style="color: #238636;">trending_up</span>
                Most Influential
            </h4>
            <p style="color: #8b949e; margin-top: 8px;">Lending Protocol sent 42 infections</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background: #161b22; padding: 16px; border-radius: 8px;">
            <h4 style="color: #f0f6fc; margin: 0;">
                <span class="material-icons" style="color: #a371f7;">bubble_chart</span>
                Most Infected
            </h4>
            <p style="color: #8b949e; margin-top: 8px;">NFT Marketplace at 50% chimera</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="background: #161b22; padding: 16px; border-radius: 8px;">
            <h4 style="color: #f0f6fc; margin: 0;">
                <span class="material-icons" style="color: #58a6ff;">link</span>
                Strongest Connection
            </h4>
            <p style="color: #8b949e; margin-top: 8px;">Lending -> NFT (85% influence)</p>
        </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
