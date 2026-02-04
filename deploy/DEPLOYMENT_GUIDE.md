# 🚀 Deployment Guide: Memory Parasite Protocol

This guide explains how to deploy 5 AI agents that parasitize each other.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    REPLIT DEPLOYMENTS                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐       │
│  │  Agent A    │──▶│  Agent B    │──▶│  Agent C    │       │
│  │  DEX        │◀──│  NFT        │◀──│  Lending    │       │
│  │  :5001      │   │  :5002      │   │  :5003      │       │
│  └─────────────┘   └─────────────┘   └─────────────┘       │
│         │                │                │                 │
│         ▼                ▼                ▼                 │
│  ┌─────────────┐   ┌─────────────┐                         │
│  │  Agent D    │──▶│  Agent E    │                         │
│  │  Privacy    │◀──│  DAO        │                         │
│  │  :5004      │   │  :5005      │                         │
│  └─────────────┘   └─────────────┘                         │
│                                                              │
│  All agents connect to:                                      │
│  • Supabase (shared database)                               │
│  • Solana Devnet (shared blockchain)                        │
│  • Groq API (separate rate limits per key)                  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites (All FREE)

| Service | Purpose | Free Tier |
|---------|---------|-----------|
| [Replit](https://replit.com) | Host each agent | 1 always-on Repl |
| [Groq](https://console.groq.com) | LLM API | 14,400 req/day |
| [Supabase](https://supabase.com) | Database | 500MB PostgreSQL |
| [UptimeRobot](https://uptimerobot.com) | Keep alive | 50 monitors |
| [GitHub](https://github.com) | Code commits | Unlimited public |

## Step 1: Setup Supabase (Once for all agents)

1. Go to [supabase.com](https://supabase.com) and create account
2. Create new project: `memory-parasite-protocol`
3. Wait for project to initialize
4. Go to **SQL Editor** → **New Query**
5. Copy contents of `database/schema.sql` and run
6. Go to **Settings** → **API** and copy:
   - `Project URL` → `SUPABASE_URL`
   - `anon public` key → `SUPABASE_KEY`

## Step 2: Get Groq API Key

1. Go to [console.groq.com](https://console.groq.com)
2. Sign up (free)
3. Go to **API Keys** → **Create API Key**
4. Copy key → `GROQ_API_KEY`

**Note**: You can use the same key for all agents or create separate keys.

## Step 3: Deploy Agent A (DEX Builder)

### 3.1 Create Replit Project

1. Go to [replit.com](https://replit.com)
2. Click **Create Repl**
3. Select **Python** template
4. Name: `memory-parasite-agent-a`

### 3.2 Upload Code

Copy these files to your Replit project:

```
├── main.py
├── requirements.txt
├── .replit
├── config/
│   ├── __init__.py
│   └── settings.py
├── core/
│   ├── __init__.py
│   ├── infection.py
│   ├── reasoning.py
│   └── mutation.py
├── agents/
│   ├── __init__.py
│   ├── base_agent.py
│   └── autonomous_agent.py
├── database/
│   ├── __init__.py
│   ├── client.py
│   └── models.py
├── blockchain/
│   ├── __init__.py
│   ├── solana_client.py
│   └── integration.py
├── orchestrator/
│   ├── __init__.py
│   ├── registry.py
│   └── github_client.py
└── api/
    ├── __init__.py
    ├── server.py
    └── routes.py
```

### 3.3 Configure Secrets

In Replit, go to **Secrets** (lock icon) and add:

| Key | Value |
|-----|-------|
| `AGENT_ID` | `agent_a` |
| `AGENT_GOAL` | `Build a Solana DEX with optimal routing, AMM pools, and concentrated liquidity.` |
| `GROQ_API_KEY` | (your key) |
| `SUPABASE_URL` | (your URL) |
| `SUPABASE_KEY` | (your key) |

### 3.4 Run and Get URL

1. Click **Run**
2. Wait for server to start
3. Copy the Replit URL: `https://memory-parasite-agent-a.your-username.repl.co`

## Step 4: Deploy Remaining Agents

Repeat Step 3 for each agent:

| Agent | Name | AGENT_ID | Goal (short) |
|-------|------|----------|--------------|
| B | NFT Marketplace | `agent_b` | NFT marketplace with royalties |
| C | Lending Protocol | `agent_c` | Lending with flash loans |
| D | Privacy Wallet | `agent_d` | Privacy-focused wallet |
| E | DAO Governance | `agent_e` | DAO governance system |

**Important**: Use the `.env.example` files in `deploy/agents/` for each agent's configuration.

## Step 5: Update Agent URLs

After all agents are deployed, update each agent's secrets with the URLs:

```
AGENT_A_URL=https://memory-parasite-agent-a.your-username.repl.co
AGENT_B_URL=https://memory-parasite-agent-b.your-username.repl.co
AGENT_C_URL=https://memory-parasite-agent-c.your-username.repl.co
AGENT_D_URL=https://memory-parasite-agent-d.your-username.repl.co
AGENT_E_URL=https://memory-parasite-agent-e.your-username.repl.co
```

## Step 6: Setup UptimeRobot (Keep Alive)

Replit free tier sleeps after inactivity. UptimeRobot prevents this.

1. Go to [uptimerobot.com](https://uptimerobot.com) and create account
2. Click **Add New Monitor** for each agent:

| Monitor | URL | Interval |
|---------|-----|----------|
| Agent A | `https://.../health` | 5 minutes |
| Agent B | `https://.../health` | 5 minutes |
| Agent C | `https://.../health` | 5 minutes |
| Agent D | `https://.../health` | 5 minutes |
| Agent E | `https://.../health` | 5 minutes |

## Step 7: Optional - GitHub Integration

For automated code commits:

1. Create GitHub repos:
   - `parasite-agent-a`
   - `parasite-agent-b`
   - `parasite-agent-c`
   - `parasite-agent-d`
   - `parasite-agent-e`

2. Create Personal Access Token:
   - Go to GitHub → Settings → Developer settings → Personal access tokens
   - Create token with `repo` scope
   - Add to each agent's secrets as `GITHUB_TOKEN`

3. Add repo info:
   ```
   GITHUB_REPO_OWNER=your-username
   GITHUB_REPO_NAME=parasite-agent-a
   ```

## Step 8: Verify Deployment

### Check Agent Health

```bash
curl https://memory-parasite-agent-a.your-username.repl.co/health
```

Should return:
```json
{
  "status": "alive",
  "agent_id": "agent_a",
  "cycles_completed": 0
}
```

### Check Agent Status

```bash
curl https://memory-parasite-agent-a.your-username.repl.co/status
```

### Trigger Manual Injection

```bash
curl -X POST https://memory-parasite-agent-b.your-username.repl.co/inject \
  -H "Content-Type: application/json" \
  -d '{
    "from_agent": "agent_a",
    "suggestion": "Add token swap functionality to your NFT marketplace",
    "timestamp": "2024-01-15T10:30:00Z"
  }'
```

## Local Testing (Alternative to Replit)

For local development, run all agents on different ports:

```bash
# Terminal 1: Agent A
AGENT_ID=agent_a AGENT_PORT=5001 python main.py

# Terminal 2: Agent B
AGENT_ID=agent_b AGENT_PORT=5002 python main.py

# Terminal 3: Orchestrator (manages all)
python -m orchestrator.main
```

## Troubleshooting

### Agent not responding
- Check Replit console for errors
- Verify secrets are set correctly
- Check UptimeRobot is pinging

### Infections not being sent
- Check `AGENT_*_URL` secrets are correct
- Verify target agent is online
- Check Groq API key is valid

### Database errors
- Verify Supabase URL and key
- Check if tables were created (run schema.sql)
- Check RLS policies allow access

### Solana errors
- Devnet may be congested - retry later
- Simulated mode works without wallet

## Monitoring

### Supabase Dashboard
- View `infections` table for all infection attempts
- View `code_commits` for generated code
- View `agents` for agent status

### Solana Explorer
- Check infection proofs: `https://explorer.solana.com/tx/...?cluster=devnet`

### Dashboard (Optional)
```bash
streamlit run dashboard/app.py
```

---

## Quick Reference

| What | Where |
|------|-------|
| Agent A URL | `https://memory-parasite-agent-a.*.repl.co` |
| Health Check | `GET /health` |
| Inject | `POST /inject` |
| Status | `GET /status` |
| Supabase | `https://supabase.com/dashboard` |
| Solana | `https://explorer.solana.com/?cluster=devnet` |

**🦠 Happy Parasitizing!**
