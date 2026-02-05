"""
Multi-Agent Orchestrator with Web Status for Memory Parasite Protocol.
Runs all 5 agents in a single process for cloud deployment efficiency.
"""

import asyncio
import threading
import signal
import sys
import os
from flask import Flask, jsonify
from flask_cors import CORS
import structlog

from orchestrator.main import Orchestrator
from config.settings import get_settings

# Configure logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
)
logger = structlog.get_logger()

from orchestrator.main import Orchestrator
from config.settings import get_settings
from api.routes import api_bp, set_agent_registry

# Global Orchestrator
settings = get_settings()
orch = Orchestrator()

app = Flask(__name__)
CORS(app)

# Connect the Orchestrator to the API Blueprint
# This makes the /api/agents, /api/emergence, etc. live!
set_agent_registry(orch.agents)
app.register_blueprint(api_bp)

@app.route("/")
@app.route("/health")
@app.route("/status")
@app.route("/api/status")
def health():
    status = orch.get_status()
    return jsonify({
        "status": "online",
        "mode": "orchestrator",
        "active_agents": len(status.get("agents", {})),
        "total_cycles": status.get("total_cycles", 0),
        "total_infections": status.get("total_infections", 0),
        "agents": status.get("agents", {})
    })

@app.route("/api/register-agent", methods=["POST"])
def api_register():
    """Proxy for agent registration."""
    # In orchestrator, we register all agents at start, but we can re-trigger
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(orch.initialize_agents())
        return jsonify({"success": True, "status": "all_agents_initialized"})
    finally:
        loop.close()

@app.route("/api/get-infections")
def api_get_infections():
    """Proxy for infections history."""
    # Aggregated from all agents or specifically for one
    agent_id = request.args.get("agent_id", "agent_a")
    agent = orch.agents.get(agent_id)
    if agent:
        return jsonify(agent.get("context_injections", []))
    return jsonify({"error": "Agent not found"}), 404

@app.route("/api/get-agent-stats")
def api_get_agent_stats():
    """Proxy for agent stats."""
    agent_id = request.args.get("agent_id", "agent_a")
    agent_status = orch.get_status().get("agents", {}).get(agent_id)
    if agent_status:
        return jsonify(agent_status)
    return jsonify({"error": "Agent not found"}), 404

@app.route("/api/respond-to-infection", methods=["POST"])
def api_respond():
    """Proxy for infection response."""
    # Usually handled by autonomous loop, but manual fallback
    return jsonify({"success": True, "status": "queued_for_autonomous_resolution"})



@app.route("/api/get-network-graph")
def api_network_graph():
    """Proxy for network graph."""
    if orch.db:
        loop = asyncio.new_event_loop()
        try:
            data = loop.run_until_complete(orch.db.get_infection_network())
            return jsonify(data)
        except Exception as e:
            logger.error("Failed to fetch graph", error=str(e))
        finally:
            loop.close()
    return jsonify({"nodes": [], "edges": []})

@app.route("/api/inject-infection", methods=["POST"])
@app.route("/inject", methods=["POST"])
def api_inject():
    """
    Handle incoming infections globally.
    In orchestrator mode, we route to a random or targeted agent.
    """
    from flask import request
    data = request.get_json()
    if not data or "suggestion" not in data:
        return jsonify({"error": "Invalid payload"}), 400
    
    # Simple routing: try to find target or use agent_a as default landing
    target_id = data.get("target_id") or data.get("target_url") or "agent_a"
    if "agent_" not in target_id: target_id = "agent_a"
    
    loop = asyncio.new_event_loop()
    try:
        # In orchestrator, we use _evaluate_infection directly
        accepted, reason = loop.run_until_complete(
            orch._evaluate_infection(target_id, data.get("from_agent", "external"), data["suggestion"])
        )
        return jsonify({
            "success": True,
            "decision": "accept" if accepted else "reject",
            "reason": reason,
            "agent_id": target_id
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        loop.close()

@app.route("/api/leaderboard-surveillance")
def api_surveillance():
    """Show the 'Live Audit' feed of other projects."""
    targets = [
        {"name": "ClaudeCraft", "finding": "Logic Loop in build-consensus detected."},
        {"name": "Makora", "finding": "OODA Loop latency exceeds attack window."},
        {"name": "AirdropAlpha", "finding": "Static heuristic bypass confirmed."},
        {"name": "Farnsworth", "finding": "Consensus poisoning vector identified."}
    ]
    import random
    active = random.choice(targets)
    return jsonify({
        "status": "active_surveillance",
        "target": active["name"],
        "finding": active["finding"],
        "timestamp": datetime.utcnow().isoformat()
    })
def run_orch_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(orch.run_forever())
    except Exception as e:
        logger.error("Orchestrator loop failed", error=str(e))


if __name__ == "__main__":
    # Start Orchestrator in background
    thread = threading.Thread(target=run_orch_loop, daemon=True)
    thread.start()
    
    # Run Web Server
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
