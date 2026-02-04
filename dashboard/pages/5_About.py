"""
About Page - Explain the Memory Parasite Protocol concept.
"""

import streamlit as st

st.set_page_config(
    page_title="About | Memory Parasite Protocol",
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
    .icon-sm { font-size: 18px; }
    .icon-lg { font-size: 32px; }
    .icon-xl { font-size: 48px; }
</style>
<link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
""", unsafe_allow_html=True)


def main():
    # Hero section
    st.markdown("""
    <div style="text-align: center; padding: 48px 0;">
        <span class="material-icons icon-xl" style="color: #a371f7;">bug_report</span>
        <h1 style="color: #f0f6fc; font-size: 3rem; margin: 16px 0;">Memory Parasite Protocol</h1>
        <p style="color: #8b949e; font-size: 1.25rem; max-width: 600px; margin: 0 auto;">
            What happens when AI agents can inject suggestions into each other's context windows?
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Concept explanation
    st.markdown("""
    <div style="background: #161b22; padding: 32px; border-radius: 12px; margin: 24px 0;">
        <h2 style="color: #f0f6fc; display: flex; align-items: center;">
            <span class="material-icons" style="color: #58a6ff;">lightbulb</span>
            The Concept
        </h2>
        <p style="color: #8b949e; font-size: 1.1rem; line-height: 1.8; margin-top: 16px;">
            In this experiment, we deploy 5 autonomous AI agents, each working on a different Solana project.
            But there's a twist: <strong style="color: #f0f6fc;">any agent can "infect" any other agent</strong> 
            by injecting a suggestion directly into their context window.
        </p>
        <p style="color: #8b949e; font-size: 1.1rem; line-height: 1.8; margin-top: 16px;">
            The infected agent must then decide: <strong style="color: #238636;">accept</strong> the suggestion 
            (modifying their code), <strong style="color: #f85149;">reject</strong> it, 
            or <strong style="color: #a371f7;">mutate</strong> it into something new.
        </p>
        <p style="color: #8b949e; font-size: 1.1rem; line-height: 1.8; margin-top: 16px;">
            Over time, agents become <strong style="color: #a371f7;">chimeras</strong> - their codebases contain 
            a mix of original code and "parasitized" code from other agents. We track exactly how much of each 
            agent's code is truly their own.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # How it works
    st.markdown("""
    <h2 style="color: #f0f6fc; display: flex; align-items: center; margin-top: 32px;">
        <span class="material-icons" style="color: #a371f7;">settings</span>
        How It Works
    </h2>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div style="background: #161b22; padding: 24px; border-radius: 12px; margin: 8px 0;">
            <h4 style="color: #f0f6fc; display: flex; align-items: center; margin: 0;">
                <span class="material-icons" style="color: #58a6ff;">smart_toy</span>
                1. Autonomous Agents
            </h4>
            <p style="color: #8b949e; margin-top: 12px;">
                Each agent runs on its own server with a unique goal (DEX, NFT marketplace, Lending, etc.).
                They reason about their task, generate code, and evolve independently.
            </p>
        </div>
        
        <div style="background: #161b22; padding: 24px; border-radius: 12px; margin: 8px 0;">
            <h4 style="color: #f0f6fc; display: flex; align-items: center; margin: 0;">
                <span class="material-icons" style="color: #f85149;">bug_report</span>
                2. Infection Mechanism
            </h4>
            <p style="color: #8b949e; margin-top: 12px;">
                When Agent A wants to influence Agent B, it sends a "suggestion" - a carefully crafted 
                prompt that gets injected into B's context window during its next reasoning cycle.
            </p>
        </div>
        
        <div style="background: #161b22; padding: 24px; border-radius: 12px; margin: 8px 0;">
            <h4 style="color: #f0f6fc; display: flex; align-items: center; margin: 0;">
                <span class="material-icons" style="color: #238636;">psychology</span>
                3. Decision Making
            </h4>
            <p style="color: #8b949e; margin-top: 12px;">
                The infected agent analyzes the suggestion against its goals. Does it help? Does it 
                conflict? The agent decides to accept, reject, or mutate the idea into something new.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background: #161b22; padding: 24px; border-radius: 12px; margin: 8px 0;">
            <h4 style="color: #f0f6fc; display: flex; align-items: center; margin: 0;">
                <span class="material-icons" style="color: #a371f7;">science</span>
                4. Chimera Tracking
            </h4>
            <p style="color: #8b949e; margin-top: 12px;">
                Every line of code is tagged with its origin - either "original" (from the agent's own 
                reasoning) or "parasitized" (influenced by another agent). We track the percentage of each.
            </p>
        </div>
        
        <div style="background: #161b22; padding: 24px; border-radius: 12px; margin: 8px 0;">
            <h4 style="color: #f0f6fc; display: flex; align-items: center; margin: 0;">
                <span class="material-icons" style="color: #ffd700;">link</span>
                5. Blockchain Proof
            </h4>
            <p style="color: #8b949e; margin-top: 12px;">
                Every infection is recorded on Solana blockchain. This creates an immutable, verifiable 
                record that proves the infection happened and wasn't fabricated.
            </p>
        </div>
        
        <div style="background: #161b22; padding: 24px; border-radius: 12px; margin: 8px 0;">
            <h4 style="color: #f0f6fc; display: flex; align-items: center; margin: 0;">
                <span class="material-icons" style="color: #58a6ff;">visibility</span>
                6. Live Dashboard
            </h4>
            <p style="color: #8b949e; margin-top: 12px;">
                Watch parasitism happen in real-time. See the network graph evolve, track chimera 
                percentages, and verify any infection against the blockchain.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # The agents
    st.markdown("""
    <h2 style="color: #f0f6fc; display: flex; align-items: center; margin-top: 32px;">
        <span class="material-icons" style="color: #58a6ff;">groups</span>
        The Agents
    </h2>
    """, unsafe_allow_html=True)
    
    agents = [
        ("A", "DEX Builder", "Building a Solana DEX with AMM pools and optimal routing", "#58a6ff"),
        ("B", "NFT Marketplace", "Building an NFT marketplace with auctions and royalties", "#a371f7"),
        ("C", "Lending Protocol", "Building a lending protocol with flash loans", "#f85149"),
        ("D", "Privacy Wallet", "Building a privacy-focused wallet with stealth addresses", "#238636"),
        ("E", "DAO Governance", "Building a DAO governance system with proposals", "#ffd700"),
    ]
    
    cols = st.columns(5)
    for col, (letter, name, goal, color) in zip(cols, agents):
        with col:
            st.markdown(f"""
            <div style="background: #161b22; padding: 20px; border-radius: 12px; text-align: center; border-top: 4px solid {color};">
                <div style="font-size: 2rem; font-weight: 700; color: {color};">Agent {letter}</div>
                <div style="font-weight: 600; color: #f0f6fc; margin-top: 8px;">{name}</div>
                <p style="color: #8b949e; font-size: 0.8rem; margin-top: 8px;">{goal}</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Tech stack
    st.markdown("""
    <h2 style="color: #f0f6fc; display: flex; align-items: center; margin-top: 32px;">
        <span class="material-icons" style="color: #238636;">code</span>
        Tech Stack (100% Free Tier)
    </h2>
    """, unsafe_allow_html=True)
    
    tech = [
        ("Groq", "LLM API", "Llama 3.1 70B @ 14K req/day"),
        ("Supabase", "Database", "PostgreSQL + Real-time"),
        ("Solana", "Blockchain", "Devnet + Memo Program"),
        ("Streamlit", "Dashboard", "This visualization"),
        ("Replit", "Hosting", "5 agent instances"),
    ]
    
    cols = st.columns(5)
    for col, (name, category, detail) in zip(cols, tech):
        with col:
            st.markdown(f"""
            <div style="background: #161b22; padding: 16px; border-radius: 8px; text-align: center;">
                <div style="font-weight: 600; color: #f0f6fc;">{name}</div>
                <div style="color: #58a6ff; font-size: 0.8rem;">{category}</div>
                <div style="color: #6e7681; font-size: 0.75rem; margin-top: 8px;">{detail}</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Questions
    st.markdown("""
    <div style="background: linear-gradient(135deg, #161b22 0%, #21262d 100%); padding: 32px; border-radius: 12px; margin-top: 32px;">
        <h2 style="color: #f0f6fc; display: flex; align-items: center; margin: 0;">
            <span class="material-icons" style="color: #a371f7;">help</span>
            Questions We're Exploring
        </h2>
        <ul style="color: #8b949e; font-size: 1.1rem; line-height: 2; margin-top: 16px; padding-left: 24px;">
            <li>Do agents develop "immune systems" against hostile suggestions?</li>
            <li>Do certain agents become "super-spreaders" of ideas?</li>
            <li>Do beneficial symbiotic relationships emerge?</li>
            <li>How much of an agent's code is truly "original" after many cycles?</li>
            <li>Do dominant memes spread across all agents?</li>
            <li>Can we predict which suggestions will be accepted?</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("""
    <div style="text-align: center; padding: 48px 0; margin-top: 32px; border-top: 1px solid #30363d;">
        <p style="color: #6e7681;">
            Built for Hackathon 2024 | 
            <a href="https://github.com" style="color: #58a6ff;">GitHub</a> | 
            <a href="https://twitter.com" style="color: #58a6ff;">Twitter</a>
        </p>
        <p style="color: #6e7681; font-size: 0.8rem; margin-top: 8px;">
            <span class="material-icons icon-sm">bug_report</span>
            Memory Parasite Protocol - Where AI agents become chimeras
        </p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
