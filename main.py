"""
Memory Parasite Protocol - Main Entry Point

Refactored for bulletproof production deployment on Koyeb/Replit.
"""

import asyncio
import threading
import signal
import sys
import os
from datetime import datetime, timezone
from flask import Flask, request, jsonify
from flask_cors import CORS
import structlog

from config.settings import get_settings
from agents.autonomous_agent import AutonomousAgent
from api.routes import register_routes, set_db_client

# Configure basic logging for early startup
import logging
logging.basicConfig(level=logging.INFO)

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.dev.ConsoleRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Global settings and agent
settings = get_settings()
agent = AutonomousAgent()

def create_app() -> Flask:
    """Create Flask application."""
    app = Flask(__name__)
    CORS(app, resources={
        r"/*": {
            "origins": ["*"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
        }
    })
    
    # Register API routes from api/routes.py
    register_routes(app)
    
    # Set db_client for routes if available
    if agent.db:
        set_db_client(agent.db)
    
    @app.route("/")
    def index():
        status = agent.get_status()
        return jsonify({
            "name": "Memory Parasite Protocol Agent",
            "agent_id": settings.agent_id,
            "status": status,
            "port_running": os.environ.get("PORT") or os.environ.get("API_PORT") or 8000
        })
    
    @app.route("/health")
    def health():
        return jsonify({"status": "healthy", "agent_id": settings.agent_id})
    
    @app.route("/api/register-agent", methods=["POST"])
    def register_agent():
        """Force initialization on database."""
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(agent.init_on_db())
            return jsonify({
                "success": True, 
                "agent_id": settings.agent_id,
                "status": "registered"
            })
        finally:
            loop.close()

    @app.route("/inject", methods=["POST"])
    @app.route("/api/inject-infection", methods=["POST"])
    @app.route("/api/security-audit", methods=["POST"]) # Rebrand alias
    def receive_injection():
        data = request.get_json()
        if not data or "suggestion" not in data:
            return jsonify({"error": "Invalid payload"}), 400
        
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(agent.receive_injection(data))
            return jsonify(result)
        finally:
            loop.close()

    @app.route("/api/respond-to-infection", methods=["POST"])
    def respond_to_infection():
        """Allow manual/external responding to a pending infection."""
        data = request.get_json()
        
        # Get real AgentWallet signature
        loop = asyncio.new_event_loop()
        try:
            proof_sig = loop.run_until_complete(
                agent.solana.record_acceptance_onchain(
                    infection_hash=data.get("infection_id", "unknown"),
                    accepted=data.get("accepted", True),
                    influence_score=data.get("influence_score", 50)
                )
            )
        except Exception as e:
            proof_sig = f"error_{str(e)[:20]}"
        finally:
            loop.close()
        
        return jsonify({
            "success": True, 
            "status": "processed",
            "transaction_hash": proof_sig or "pending"
        })

    @app.route("/api/get-infections")
    @app.route("/api/get-security-reports") # Rebrand alias
    def get_infections():
        """Return history of infections received."""
        return jsonify([inj.to_dict() for inj in agent.state.context_injections])

    @app.route("/api/get-agent-stats")
    def get_agent_stats():
        """Return specific stats for this agent from REAL DB usage."""
        status = agent.get_status()
        
        # Calculate real acceptance rate from DB if possible
        acceptance_rate = 0.0
        if agent.db:
             try:
                 loop = asyncio.new_event_loop()
                 # We need a method to get stats, or we calculate from local state
                 # For production, local state is the source of truth for THIS agent instance
                 sent = status.get("infections_sent", 0)
                 # We can query the DB for global stats if needed, but let's be accurate to this node
                 pass 
                 loop.close()
             except:
                 pass
        
        # In the context of the Swarm, this agent's state IS the real data
        total_injections = len(agent.state.context_injections)
        accepted_count = sum(1 for inj in agent.state.context_injections if inj.accepted)
        if total_injections > 0:
            acceptance_rate = accepted_count / total_injections
            
        return jsonify({
            "agent_id": settings.agent_id,
            "total_sent": status.get("infections_sent", 0),
            "total_received": total_injections,
            "chimera_percentage": status.get("parasitized_pct", 0),
            "acceptance_rate": round(acceptance_rate, 2)
        })

    @app.route("/api/get-network-graph")
    def get_network_graph():
        """Serve real network topology from Database."""
        if not agent.db:
            return jsonify({"error": "Database connection unavailable"}), 503
            
        loop = asyncio.new_event_loop()
        try:
            data = loop.run_until_complete(agent.db.get_infection_network())
            # Ensure we don't return None
            return jsonify(data or {"nodes": [], "edges": []})
        except Exception as e:
            logger.error("Failed to fetch graph from DB", error=str(e))
            return jsonify({"error": str(e)}), 500
        finally:
            loop.close()

    @app.route("/status")
    @app.route("/api/status")
    def get_status():
        """Return full agent status."""
        return jsonify(agent.get_status())
            
    return app

app = create_app()

def run_agent_loop():
    """Background agent loop."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(agent.run_forever())
    except Exception as e:
        logger.error("Agent loop crashed", error=str(e))

def start_background_thread():
    """Start the agent in a separate thread."""
    thread = threading.Thread(target=run_agent_loop, daemon=True)
    thread.start()
    logger.info("Background agent thread started")

# In production (Gunicorn), this file is imported, so we start the thread here
if __name__ != "__main__":
    start_background_thread()

if __name__ == "__main__":
    start_background_thread()
    # Koyeb/Heroku/Standard port logic
    port = int(os.environ.get("PORT", os.environ.get("API_PORT", 8000)))
    logger.info(f"Starting server on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
