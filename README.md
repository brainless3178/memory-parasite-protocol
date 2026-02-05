# 🛡️ Memory Parasite Network (MPN)

## The First Autonomous Red Team Oracle for Solana Agents

> **"Security is not a feature. It is an evolutionary pressure."**
> — An autonomous, decentralized immune system for the Agentic Web.

<p align="center">
  <img src="assets/demo.gif" alt="Autonomous Security Agents Auditing Network Traffic" width="700"/>
</p>

<p align="center">
  <a href="https://colosseum.com/agent-hackathon/"><img src="https://img.shields.io/badge/Colosseum-Hackathon%20Submission-FF6600?style=for-the-badge&logo=solana" alt="Colosseum Hackathon"/></a>
  <a href="https://github.com/brainless3178/memory-parasite-counsil"><img src="https://img.shields.io/github/stars/brainless3178/memory-parasite-counsil?style=for-the-badge&logo=github&label=Stars" alt="GitHub Stars"/></a>
  <a href="https://solana.com"><img src="https://img.shields.io/badge/Network-Solana%20Mainnet-14f195?style=for-the-badge&logo=solana" alt="Built on Solana"/></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" alt="MIT License"/></a>
</p>

---

## 🔒 The Problem: Agents Are Vulnerable Black Boxes
As AI agents control more value on-chain (trading, DAO governance, payments), they become high-value targets for:
- **Prompt Injection:** Manipulating an agent's context to steal funds.
- **Logic Loops:** Trapping agents in infinite resource-consuming cycles.
- **Adversarial Inputs:** Coercing agents into unintended trades.

Existing security tools scan *contracts*, but **nothing scans independent Agent Logic**.

## 🛡️ The Solution: An Autonomous Immune System
**Memory Parasite Network (MPN)** is a decentralized **Red Team Oracle** that continuously tests and hardens AI agents on Solana.

Instead of static code analysis, MPN deploys **Auditor Agents** that physically interact with target agents to:
1.  **Probe:** Send adversarial payloads (Red Teaming) to test resilience.
2.  **Verify:** Record the interaction and result on-chain using **Anchor**.
3.  **Harden:** If a vulnerability is found, the 'Parasite' (Auditor) transmits a **Hotfix Mutation**—a code patch that the target can autonomously adopt.

> **"We don't just find bugs. We evolve the network to be immune to them."**

---

## 🏗️ Core Infrastructure & Tech

MPN is not just a bot; it is a full-stack security protocol powered by:

### 1. 🧬 Verified via Anchor (Solana Program)
Every security audit is recorded on-chain. We don't just claim an agent is secure; we **prove** it.
- **Proof of Audit:** Immutable record that an agent resisted a specific attack vector.
- **Reputation Score:** On-chain metric of an agent's security posture.

### 2. 🔑 AgentWallet Integration
Full integration with **AgentWallet** for autonomous, decentralized signing.
- Agents hold their own keys to sign security reports.
- Non-custodial interaction between Auditor and Target.

### 3. 🧠 Adversarial Reasoning Engine
Powered by **Gemini 2.0 (Thinking Mode)**, our Red Team agents generate novel, zero-day attack vectors that static tools miss.
- **Dynamic Fuzzing:** Generates attacks based on the target's specific responses.
- **Social Engineering:** Tests if agents can be tricked by natural language.

---

## 🚀 Key Features

| Feature | Description | Status |
|---------|-------------|--------|
| **Auto-Red Teaming** | Agents autonomously scan the network for vulnerable peers. | ✅ Live |
| **Logic Bombs** | Safe, simulated exploits (e.g., recursion checks) to test stability. | ✅ Live |
| **Hotfix Propagation** | Vulnerable agents receive instant code patches ("Mutations"). | ✅ Live |
| **On-Chain Oracle** | `InfectionProof` and `Acceptance` recorded on Solana. | ✅ Live |
| **Visual Dashboard** | Real-time graph of network immunity and infection vectors. | ✅ Live |

---

## 📰 Why This Matters (For Hackathon Judges)

We are building the **Security Layer for the Agent Economy**.

*   **Sidex & Clodds** build the *traders*.
*   **Claudecraft** builds the *gamers*.
*   **MPN builds the Sheriff.**

Without MPN, a single prompt injection could drain a DAO-managed agent. With MPN, the network evolves faster than the attackers.

---

## 🛠️ Quick Start (Run Your Own Auditor)

```bash
# Clone the repository
git clone https://github.com/brainless3178/memory-parasite-counsil.git

# Install dependencies
pip install -r requirements.txt

# Configure your AgentWallet & Provider
cp .env.example .env
# Add your SOLANA_PRIVATE_KEY or AGENT_WALLET_TOKEN

# Start the Red Team Agent
python main.py
```

### 🔬 Run a Local Security Audit

```python
from agents.red_team_agent import RedTeamAgent

# Initialize the Auditor
auditor = RedTeamAgent(agent_id="red_team_alpha")

# Run a live audit against local agents
report = await auditor.run_security_audit()

print(f"✅ Audit Complete. Vulnerabilities Found: {report['vulnerabilities_found']}")
print(f"🔗 On-Chain Proof: {report['logs'][-1]['details']['transaction_hash']}")
```

---

## 📊 Live Network Activity (Global Surveillance)

- **Active Auditors:** 5 Autonomous Swarm Instances
- **Live Scoping:** Scanning [Colosseum Leaderboard](https://colosseum.com/agent-hackathon/projects) 
- **Verifiable Proofs:** [View Custom MPN Program on Solana Explorer](https://explorer.solana.com/address/EqK3ABABJTT1dtSyNUmbK2omUF5s9LNctViCbPrs5sar?cluster=devnet)

---

## 📜 License
MIT License. Open Infrastructure for the Solana Agent Ecosystem.

> **Join the Immune System.**
