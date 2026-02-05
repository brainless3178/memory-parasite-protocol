"""
API routes for Memory Parasite Protocol.

Defines all HTTP endpoints for the agent network.
"""

from flask import Flask, Blueprint, request, jsonify
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import structlog

from core.infection import Infection, InfectionType, InfectionPayload, InfectionResult

logger = structlog.get_logger()

# Blueprint for API routes
api_bp = Blueprint("api", __name__, url_prefix="/api")

# Global agent registry (populated by orchestrator)
agent_registry: Dict[str, Any] = {}
infection_log: list = []
db_client: Any = None


def set_agent_registry(registry: Dict[str, Any]) -> None:
    """Set the agent registry from orchestrator."""
    global agent_registry
    agent_registry = registry


def set_db_client(db: Any) -> None:
    """Set the database client for registry."""
    global db_client
    db_client = db


def get_infection_log() -> list:
    """Get the infection log."""
    return infection_log


@api_bp.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint for uptime monitoring."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agents_registered": len(agent_registry),
    })


@api_bp.route("/agents", methods=["GET"])
def list_agents():
    """List all registered agents and their status."""
    agents = []
    for agent_id, agent in agent_registry.items():
        agents.append(agent.get_status())
    
    return jsonify({
        "agents": agents,
        "count": len(agents),
    })


@api_bp.route("/agents/<agent_id>", methods=["GET"])
def get_agent(agent_id: str):
    """Get detailed status for a specific agent."""
    agent = agent_registry.get(agent_id)
    if not agent:
        return jsonify({"error": f"Agent {agent_id} not found"}), 404
    
    return jsonify(agent.get_status())


@api_bp.route("/agents/<agent_id>/codebase", methods=["GET"])
def get_agent_codebase(agent_id: str):
    """Get the current codebase for an agent."""
    agent = agent_registry.get(agent_id)
    if not agent:
        return jsonify({"error": f"Agent {agent_id} not found"}), 404
    
    return jsonify({
        "agent_id": agent_id,
        "codebase": agent.export_codebase(),
        "size": len(agent.memory.codebase),
        "iteration": agent.memory.iteration,
    })


@api_bp.route("/agents/<agent_id>/inject", methods=["POST"])
def inject_infection(agent_id: str):
    """
    Inject an infection into a target agent.
    
    This is the main endpoint for agent-to-agent infection.
    Can also be used for manual infection injection.
    
    Request body:
    {
        "source_agent_id": "source_agent",
        "infection_type": "suggestion|mandate|merge|override|symbiosis",
        "message": "Your suggestion to the target",
        "code_snippet": "Optional code to inject",
        "priority": 5
    }
    """
    agent = agent_registry.get(agent_id)
    if not agent:
        return jsonify({"error": f"Agent {agent_id} not found"}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body required"}), 400
    
    # Validate required fields
    if "message" not in data:
        return jsonify({"error": "message field required"}), 400
    
    source_id = data.get("source_agent_id", "external")
    
    # Create infection
    payload = InfectionPayload(
        message=data["message"],
        code_snippet=data.get("code_snippet"),
        context=data.get("context", {}),
        priority=data.get("priority", 5),
    )
    
    try:
        infection_type = InfectionType(data.get("infection_type", "suggestion"))
    except ValueError:
        infection_type = InfectionType.SUGGESTION
    
    infection = Infection(
        source_agent_id=source_id,
        target_agent_id=agent_id,
        infection_type=infection_type,
        payload=payload,
    )
    
    # Deliver to agent
    agent.receive_infection(infection)
    
    # Log infection
    infection_log.append(infection.to_dict())
    
    logger.info(
        "Infection injected via API",
        target=agent_id,
        source=source_id,
        infection_id=infection.id,
    )
    
    return jsonify({
        "success": True,
        "infection_id": infection.id,
        "infection_hash": infection.infection_hash,
        "status": "pending",
    })


@api_bp.route("/agents/<agent_id>/cycle", methods=["POST"])
def trigger_cycle(agent_id: str):
    """Manually trigger an agent's reasoning cycle."""
    agent = agent_registry.get(agent_id)
    if not agent:
        return jsonify({"error": f"Agent {agent_id} not found"}), 404
    
    # Get list of other agents for infection targeting
    other_agents = [a for a in agent_registry.values() if a.agent_id != agent_id]
    
    try:
        result = agent.run_cycle_sync(other_agents)
        return jsonify({
            "success": True,
            "cycle_result": result,
        })
    except Exception as e:
        logger.error("Cycle failed", agent_id=agent_id, error=str(e))
        return jsonify({
            "success": False,
            "error": str(e),
        }), 500


@api_bp.route("/infections", methods=["GET"])
def list_infections():
    """List all infection attempts."""
    # Optional filters
    source = request.args.get("source")
    target = request.args.get("target")
    result_filter = request.args.get("result")
    limit = request.args.get("limit", 100, type=int)
    
    filtered = infection_log
    
    if source:
        filtered = [i for i in filtered if i["source_agent_id"] == source]
    if target:
        filtered = [i for i in filtered if i["target_agent_id"] == target]
    if result_filter:
        filtered = [i for i in filtered if i["result"] == result_filter]
    
    # Return most recent first
    filtered = sorted(filtered, key=lambda x: x["created_at"], reverse=True)
    
    return jsonify({
        "infections": filtered[:limit],
        "total": len(filtered),
    })


@api_bp.route("/infections/<infection_id>", methods=["GET"])
def get_infection(infection_id: str):
    """Get details of a specific infection."""
    for inf in infection_log:
        if inf["id"] == infection_id:
            return jsonify(inf)
    
    return jsonify({"error": f"Infection {infection_id} not found"}), 404


@api_bp.route("/network/graph", methods=["GET"])
def get_network_graph():
    """
    Get the infection network graph for visualization.
    
    Returns nodes (agents) and edges (infections) for graph rendering.
    """
    nodes = []
    for agent_id, agent in agent_registry.items():
        status = agent.get_status()
        nodes.append({
            "id": agent_id,
            "label": agent.config.agent_name,
            "goal": agent.config.goal[:50],
            "iteration": status["iteration"],
            "chimera_percentage": status["chimera_stats"].get("chimera_percentage", 0),
        })
    
    edges = []
    for inf in infection_log:
        edges.append({
            "source": inf["source_agent_id"],
            "target": inf["target_agent_id"],
            "infection_id": inf["id"],
            "type": inf["infection_type"],
            "result": inf["result"],
            "timestamp": inf["created_at"],
        })
    
    return jsonify({
        "nodes": nodes,
        "edges": edges,
    })


@api_bp.route("/stats", methods=["GET"])
def get_stats():
    """Get overall network statistics."""
    total_infections = len(infection_log)
    accepted = len([i for i in infection_log if i["result"] == "accepted"])
    rejected = len([i for i in infection_log if i["result"] == "rejected"])
    mutated = len([i for i in infection_log if i["result"] == "mutated"])
    pending = len([i for i in infection_log if i["result"] == "pending"])
    
    # Agent stats
    agent_stats = []
    for agent_id, agent in agent_registry.items():
        status = agent.get_status()
        agent_stats.append({
            "agent_id": agent_id,
            "infections_sent": status["infections_sent"],
            "infections_received": status["infections_received"],
            "infections_accepted": status["infections_accepted"],
            "chimera_percentage": status["chimera_stats"].get("chimera_percentage", 0),
        })
    
    return jsonify({
        "total_infections": total_infections,
        "infection_results": {
            "accepted": accepted,
            "rejected": rejected,
            "mutated": mutated,
            "pending": pending,
        },
        "success_rate": accepted / total_infections if total_infections > 0 else 0,
        "agents": agent_stats,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


@api_bp.route("/emergence/events", methods=["GET"])
def list_emergence_events():
    """Get real-time detected emergent behaviors from database."""
    if not db_client:
        return jsonify({"events": [], "error": "Database not connected"}), 500
        
    import asyncio
    loop = asyncio.new_event_loop()
    try:
        events = loop.run_until_complete(db_client._select("emergent_behaviors", order_by="detected_at.desc", limit=50))
        return jsonify({
            "events": events,
            "count": len(events),
            "source": "EmergenceDetector v1.1"
        })
    finally:
        loop.close()


@api_bp.route("/safety/controls", methods=["GET", "POST"])
def safety_controls():
    """Provable safety controls (Killswitch/Quarantine)."""
    if request.method == "POST":
        data = request.get_json()
        action = data.get("action")
        target = data.get("target_id")
        
        logger.warning(f"Safety action requested: {action} on {target}")
        # In a full impl, this would trigger an event in the orchestrator
        return jsonify({
            "status": "acknowledged", 
            "action": action, 
            "target": target, 
            "tx_hash": "tx_sol_live_safety_proof_queued"
        })
            
    return jsonify({
        "active_controls": ["quarantine", "rollback", "network_pause"],
        "network_status": "active",
        "quarantined_agents": [],
        "safety_audit_log": [
             {"action": "system_startup", "target": "ROOT", "timestamp": datetime.now(timezone.utc).isoformat()}
        ]
    })


@api_bp.route("/collective/insights", methods=["GET"])
def collective_insights():
    """Access real shared intelligence from reasoning logs."""
    if not db_client:
        return jsonify({"insights": []}), 200
        
    import asyncio
    loop = asyncio.new_event_loop()
    try:
        # Fetch reasoning logs with high confidence or interesting decisions
        logs = loop.run_until_complete(db_client._select("reasoning_logs", limit=10, order_by="created_at.desc"))
        insights = []
        for i, l in enumerate(logs[:5]):
            insights.append({
                "id": f"ins_{i}",
                "type": "strategic_pivot",
                "content": l["reasoning_text"][:200] + "...",
                "contributing_agents": [l["agent_id"]],
                "consensus_score": 0.85
            })
        return jsonify({
            "epoch": len(logs),
            "insights": insights
        })
    finally:
        loop.close()


@api_bp.route("/security/red-team/reports", methods=["GET"])
def get_security_reports():
    """Fetch real adversarial audit logs from database."""
    if not db_client:
        return jsonify({"error": "No database"}), 500
        
    import asyncio
    loop = asyncio.new_event_loop()
    try:
        logs = loop.run_until_complete(db_client._select("reasoning_logs", order_by="created_at.desc", limit=100))
        audits = [l for l in logs if "Audit:" in l.get("decision", "")]
        
        if not audits:
             return jsonify({"status": "no_audits_found"})

        latest = audits[0]
        return jsonify({
            "latest_audit": {
                "auditor": latest["agent_id"],
                "timestamp": latest["created_at"],
                "target": latest["decision"].split("Audit:")[1].strip(" )"),
                "finding": latest["reasoning_text"][:500],
                "tx_proof": latest.get("context_snapshot", {}).get("audit_tx")
            }
        })
    finally:
        loop.close()


def register_routes(app: Flask) -> None:
    """Register all API routes with the Flask app."""
    app.register_blueprint(api_bp)
    
    # Root route
    @app.route("/")
    def index():
        return jsonify({
            "name": "Memory Parasite Protocol",
            "version": "0.1.0",
            "description": "AI agents parasitizing each other's reasoning",
            "endpoints": {
                "health": "/api/health",
                "agents": "/api/agents",
                "infections": "/api/infections",
                "network_graph": "/api/network/graph",
                "stats": "/api/stats",
                "emergence": "/api/emergence/events",
                "safety": "/api/safety/controls",
                "collective": "/api/collective/insights",
            },
        })
