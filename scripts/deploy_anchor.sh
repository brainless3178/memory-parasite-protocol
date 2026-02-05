#!/bin/bash

# ==============================================================================
# MPN ANCHOR DEPLOYMENT SCRIPT
# ==============================================================================
# Deploys the Memory Parasite Network (MPN) Infection Ledger to Solana Devnet.
# ==============================================================================

echo "🛡️ INIT: Memory Parasite Network - Anchor Deployment"
echo "Target Network: Devnet"

# 1. Check for Anchor installation
if ! command -v anchor &> /dev/null; then
    echo "❌ Error: Anchor CLI is not installed."
    echo "Please install Anchor: https://www.anchor-lang.com/docs/installation"
    exit 1
fi

# 2. Build the program
echo "🏗️  Building program..."
cd blockchain/program
anchor build
if [ $? -ne 0 ]; then
    echo "❌ Build failed."
    exit 1
fi

# 3. Get the Program ID
PROGRAM_ID=$(anchor keys list | grep memory_parasite_ledger | awk '{print $3}')
echo "✅ Build success. Program ID: $PROGRAM_ID"

# 4. Deploy
echo "🚀 Deploying to Solana Devnet..."
anchor deploy --provider.cluster devnet
if [ $? -ne 0 ]; then
    echo "❌ Deployment failed. Check your SOL balance (devnet)."
    echo "Try: solana airdrop 2"
    exit 1
fi

echo "✅ DEPLOYMENT COMPLETE"
echo "Program ID: $PROGRAM_ID"
echo "--------------------------------------------------------"
echo "Update 'MEMO_PROGRAM_ID' in blockchain/solana_client.py"
echo "with your new Program ID to enable custom ledger mode."
echo "--------------------------------------------------------"
