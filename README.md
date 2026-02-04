# Memory Parasite Protocol

**AI agents autonomously parasitizing each other's reasoning in real-time.**

[![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-ff4b4b?logo=streamlit)](https://memory-parasite.streamlit.app)
[![Solana](https://img.shields.io/badge/Solana-Devnet-14f195?logo=solana)](https://explorer.solana.com/?cluster=devnet)
[![Supabase](https://img.shields.io/badge/Supabase-Database-3ecf8e?logo=supabase)](https://supabase.com)

## What Is This?

An experiment in **AI agent symbiosis/parasitism**: 5 autonomous AI agents, each building different Solana projects, can inject suggestions into each other's context windows. Watch as they accept, reject, or mutate ideas from other agents.

```
+-------------+     infects     +-------------+
|   Agent A   | ────────────▶  |   Agent B   |
|  DEX Builder|                 |  NFT Market |
+-------------+                 +-------------+
      │                               │
      │ infects                       │ infects
      ▼                               ▼
+-------------+                 +-------------+
|   Agent C   | ◀─────────────  |   Agent E   |
|   Lending   |     infects     |     DAO     |
+-------------+                 +-------------+
```

## Key Features

| Feature | Description |
|---------|-------------|
| **Autonomous Agents** | 5 agents with unique goals running 24/7 |
| **Context Injection** | Agents can inject "suggestions" into each other |
| **Accept/Reject/Mutate** | Target agent decides how to handle infections |
| **Chimera Tracking** | Track % original vs % parasitized code |
| **Blockchain Proof** | Every infection recorded on Solana devnet |
| **Live Dashboard** | Real-time visualization of parasitism |

## Tech Stack (100% Free Tier)

| Service | Purpose | Free Limit |
|---------|---------|------------|
| Groq | LLM API (Llama 3.1 70B) | 14,400 req/day |
| Replit | Host each agent | 1 always-on app |
| Supabase | PostgreSQL + Real-time | 500MB database |
| Solana Devnet | Blockchain proof | Unlimited |
| Streamlit Cloud | Dashboard | Unlimited |

## Quick Start

### 1. Clone and Install

```bash
git clone https://github.com/yourusername/memory-parasite-protocol
cd memory-parasite-protocol
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys:
# - GROQ_API_KEY (required)
# - SUPABASE_URL (optional)
# - SUPABASE_KEY (optional)
```

### 3. Run Setup

```bash
chmod +x setup.sh
./setup.sh
```

### 4. Start Agent

```bash
python main.py
```

### 5. Run Dashboard

```bash
streamlit run dashboard/app.py
```

## Architecture

```
memory-parasite-protocol/
├── agents/                    # Agent logic
│   ├── autonomous_agent.py   # Main agent class
│   └── base_agent.py         # Base agent interface
│
├── core/                      # Core mechanics
│   ├── infection.py          # Infection types & hashing
│   ├── reasoning.py          # LLM reasoning engine
│   └── mutation.py           # Code mutation engine
│
├── database/                  # Supabase integration
│   ├── schema.sql            # PostgreSQL schema
│   ├── client.py             # Database operations
│   └── models.py             # Pydantic models
│
├── blockchain/                # Solana integration
│   ├── solana_client.py      # Memo transactions
│   ├── integration.py        # DB + Chain bridge
│   └── program/              # Anchor program (optional)
│
├── orchestrator/              # Multi-agent management
│   ├── main.py               # Orchestrator
│   ├── registry.py           # Agent discovery
│   └── github_client.py      # Automated commits
│
├── dashboard/                 # Streamlit dashboard
│   ├── app.py                # Main dashboard
│   └── pages/                # Multi-page app
│       ├── 1_Network_Graph.py
│       ├── 2_Chimera_Metrics.py
│       ├── 3_Code_Evolution.py
│       ├── 4_Blockchain_Verification.py
│       └── 5_About.py
│
├── deploy/                    # Deployment configs
│   ├── DEPLOYMENT_GUIDE.md   # Replit guide
│   └── agents/               # Per-agent .env files
│
├── main.py                    # Entry point
├── setup.sh                   # Setup script
└── requirements.txt           # Dependencies
```

## Dashboard Features

### 1. Live Infection Feed
Real-time stream of infections as they happen. Color-coded by result.

### 2. Network Graph
Interactive visualization of agent relationships and infection flow.

### 3. Chimera Metrics
Track original vs parasitized code for each agent. Leaderboards for most infected and dominant parasites.

### 4. Code Evolution
Timeline of commits showing which code came from infections.

### 5. Blockchain Verification
Verify any infection against the Solana blockchain.

## API Endpoints

Each agent exposes:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check (for UptimeRobot) |
| `/status` | GET | Agent status and metrics |
| `/inject` | POST | Receive infection from another agent |
| `/stats` | GET | Infection statistics |

## Database Schema

```sql
-- UUID v7 for time-ordered IDs
agents        (id, agent_id, goal, total_code_lines, ...)
infections    (id, attacker_id, target_id, suggestion, accepted, ...)
code_commits  (id, agent_id, commit_hash, source_infection_id, ...)
reasoning_logs(id, agent_id, reasoning_text, decision, ...)
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | Yes | Groq API key |
| `AGENT_ID` | Yes | Unique agent identifier |
| `AGENT_GOAL` | Yes | Agent's coding goal |
| `SUPABASE_URL` | No | Supabase project URL |
| `SUPABASE_KEY` | No | Supabase anon key |
| `SOLANA_RPC_URL` | No | Defaults to devnet |
| `GITHUB_TOKEN` | No | For automated commits |

## Commands

```bash
# Run single agent
python main.py

# Run orchestrator (all agents locally)
python -m orchestrator.main

# Single round (testing)
python -m orchestrator.main --single-round

# List agents
python -m orchestrator.main --list-agents

# Run dashboard
streamlit run dashboard/app.py

# Run demo
python examples/demo_infection.py
python examples/demo_database.py
python examples/demo_solana.py
```

## Deployment

### Replit (Recommended)

See `deploy/DEPLOYMENT_GUIDE.md` for step-by-step instructions.

### Streamlit Cloud

1. Push to GitHub
2. Go to share.streamlit.io
3. Connect repo → Select `dashboard/app.py`
4. Add secrets (SUPABASE_URL, SUPABASE_KEY)

### Local Docker

```bash
docker build -t memory-parasite .
docker run -p 5000:5000 --env-file .env memory-parasite
```

## Research Questions

- Do agents develop "immune systems" against hostile suggestions?
- Do certain agents become "super-spreaders" of ideas?
- Do beneficial symbiotic relationships emerge?
- How much of an agent's code is truly "original" after many cycles?
- Can we predict which suggestions will be accepted?

## License

MIT License - See LICENSE file.

## Hackathon Submission

Built for Hackathon 2024. 100% free infrastructure.

---

**Built with:**
Groq | Supabase | Solana | Streamlit | Replit
