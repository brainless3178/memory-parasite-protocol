#!/bin/bash
# ============================================
# MEMORY PARASITE PROTOCOL - Setup Script
# ============================================
# Run this script once per agent on first deploy.
# Usage: chmod +x setup.sh && ./setup.sh
# ============================================

set -e  # Exit on error

echo "============================================"
echo "🦠 Memory Parasite Protocol - Setup"
echo "============================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo "📦 Checking Python..."
if command -v python3 &> /dev/null; then
    PYTHON=python3
elif command -v python &> /dev/null; then
    PYTHON=python
else
    echo -e "${RED}❌ Python not found! Please install Python 3.10+${NC}"
    exit 1
fi

PY_VERSION=$($PYTHON --version 2>&1)
echo -e "${GREEN}✓ Found: $PY_VERSION${NC}"

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
$PYTHON -m pip install --upgrade pip
$PYTHON -m pip install -r requirements.txt

# Check environment variables
echo ""
echo "🔧 Checking environment variables..."

check_env() {
    if [ -z "${!1}" ]; then
        echo -e "${YELLOW}⚠ $1 not set${NC}"
        return 1
    else
        echo -e "${GREEN}✓ $1 is set${NC}"
        return 0
    fi
}

MISSING=0

# Required
check_env "GROQ_API_KEY" || MISSING=1
check_env "AGENT_ID" || MISSING=1
check_env "AGENT_GOAL" || MISSING=1

# Optional but recommended
check_env "SUPABASE_URL" || true
check_env "SUPABASE_KEY" || true
check_env "GITHUB_TOKEN" || true

if [ $MISSING -eq 1 ]; then
    echo ""
    echo -e "${YELLOW}Some required variables are missing.${NC}"
    echo "Please set them in your .env file or environment."
    echo ""
    echo "For Replit: Use the Secrets tab"
    echo "For local: Copy .env.example to .env and fill in values"
fi

# Test Groq API connection
echo ""
echo "🧠 Testing Groq API..."
$PYTHON -c "
import os
import httpx

api_key = os.getenv('GROQ_API_KEY', '')
if not api_key:
    print('⚠ Skipping (no API key)')
    exit(0)

try:
    response = httpx.get(
        'https://api.groq.com/openai/v1/models',
        headers={'Authorization': f'Bearer {api_key}'},
        timeout=10.0
    )
    if response.status_code == 200:
        models = response.json().get('data', [])
        print(f'✓ Connected! Available models: {len(models)}')
    else:
        print(f'⚠ API returned: {response.status_code}')
except Exception as e:
    print(f'✗ Connection failed: {e}')
"

# Test Supabase connection
echo ""
echo "📊 Testing Supabase..."
$PYTHON -c "
import os
import httpx

url = os.getenv('SUPABASE_URL', '')
key = os.getenv('SUPABASE_KEY', '')

if not url or not key:
    print('⚠ Skipping (not configured)')
    exit(0)

try:
    response = httpx.get(
        f'{url}/rest/v1/',
        headers={'apikey': key, 'Authorization': f'Bearer {key}'},
        timeout=10.0
    )
    if response.status_code in [200, 404]:
        print('✓ Connected to Supabase!')
    else:
        print(f'⚠ Supabase returned: {response.status_code}')
except Exception as e:
    print(f'✗ Connection failed: {e}')
"

# Test Solana connection
echo ""
echo "🔗 Testing Solana Devnet..."
$PYTHON -c "
import httpx
import json

try:
    response = httpx.post(
        'https://api.devnet.solana.com',
        json={'jsonrpc': '2.0', 'id': 1, 'method': 'getHealth'},
        headers={'Content-Type': 'application/json'},
        timeout=10.0
    )
    data = response.json()
    if data.get('result') == 'ok':
        print('✓ Solana Devnet is healthy!')
    else:
        print(f'⚠ Solana returned: {data}')
except Exception as e:
    print(f'✗ Connection failed: {e}')
"

# Request Solana devnet airdrop for agent
echo ""
echo "💰 Checking Solana wallet..."
$PYTHON -c "
import asyncio
import sys
sys.path.insert(0, '.')
from blockchain import get_solana_client
import os

async def main():
    agent_id = os.getenv('AGENT_ID', 'test_agent')
    client = get_solana_client()
    
    # Create/load wallet
    wallet = await client.get_agent_wallet(agent_id)
    print(f'Wallet: {wallet.public_key[:20]}...')
    print(f'Balance: {wallet.balance_sol} SOL')
    
    if wallet.balance_sol < 0.1:
        print('Requesting airdrop...')
        sig = await client.airdrop_sol(wallet.public_key, 1.0)
        if sig:
            print(f'Airdrop requested: {sig[:20]}...')
        else:
            print('Airdrop failed (may need to request manually)')

asyncio.run(main())
" 2>/dev/null || echo "⚠ Wallet setup skipped (run separately if needed)"

# Initialize agent in database
echo ""
echo "🤖 Initializing agent..."
$PYTHON -c "
import asyncio
import sys
import os
sys.path.insert(0, '.')

async def main():
    agent_id = os.getenv('AGENT_ID', '')
    agent_goal = os.getenv('AGENT_GOAL', '')
    
    if not agent_id or not agent_goal:
        print('⚠ Skipping (AGENT_ID or AGENT_GOAL not set)')
        return
    
    from database import init_agent
    result = await init_agent(agent_id, agent_goal)
    
    if result:
        print(f'✓ Agent initialized: {agent_id}')
    else:
        print('⚠ Agent init returned None (database may not be configured)')

asyncio.run(main())
" 2>/dev/null || echo "⚠ Agent init skipped"

# Summary
echo ""
echo "============================================"
echo "🦠 Setup Complete!"
echo "============================================"
echo ""
echo "Next steps:"
echo "1. Ensure all environment variables are set"
echo "2. Run: python main.py"
echo "3. Or for orchestrator: python -m orchestrator.main"
echo ""
echo "For Replit deployment:"
echo "1. Click 'Run' to start the agent"
echo "2. Copy your Replit URL"
echo "3. Set up UptimeRobot to ping /health every 5 minutes"
echo ""
echo "🚀 Happy parasitizing!"
