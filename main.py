"""
Memory Parasite Protocol - Main Entry Point

This is the main script to run the autonomous agent.
Deploy this on Replit or any Python-capable server.

Usage:
    python main.py

The agent will:
1. Start the Flask server for receiving injections
2. Run the autonomous loop in the background
3. Reason → Code → Infect → Sleep → Repeat
"""

import asyncio
import threading
import signal
import sys
from flask import Flask, request, jsonify
from flask_cors import CORS
import structlog

from config.settings import get_settings
from agents.autonomous_agent import AutonomousAgent

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
agent: AutonomousAgent = None
agent_loop_task = None


def create_app() -> Flask:
    """Create Flask application with injection endpoint."""
    app = Flask(__name__)
    CORS(app)
    
    @app.route("/")
    def index():
        """Health check and info endpoint."""
        status = agent.get_status() if agent else {"status": "agent not initialized"}
        return jsonify({
            "name": "Memory Parasite Protocol Agent",
            "agent_id": settings.agent_id,
            "status": status,
            "endpoints": {
                "inject": "POST /inject",
                "status": "GET /status",
                "codebase": "GET /codebase",
                "cycle": "POST /cycle",
            }
        })
    
    @app.route("/health")
    def health():
        """Simple health check for UptimeRobot."""
        return jsonify({"status": "healthy", "agent_id": settings.agent_id})
    
    @app.route("/inject", methods=["POST"])
    def receive_injection():
        """
        Receive infection from another agent.
        
        Expected payload:
        {
            "id": "unique-injection-id",
            "from_agent": "agent_id",
            "suggestion": "Your parasitic suggestion",
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
        Returns:
        {
            "accepted": true/false,
            "reasoning": "Why accepted/rejected",
            "agent_id": "this agent's id"
        }
        """
        if not agent:
            return jsonify({"error": "Agent not initialized"}), 503
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "JSON payload required"}), 400
        
        if "suggestion" not in data:
            return jsonify({"error": "'suggestion' field required"}), 400
        
        # Process injection asynchronously
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(agent.receive_injection(data))
            return jsonify(result)
        except Exception as e:
            logger.error("Injection processing failed", error=str(e))
            return jsonify({"error": str(e), "accepted": False}), 500
        finally:
            loop.close()
    
    @app.route("/status")
    def status():
        """Get full agent status."""
        if not agent:
            return jsonify({"error": "Agent not initialized"}), 503
        return jsonify(agent.get_status())
    
    @app.route("/codebase")
    def codebase():
        """Get all generated code."""
        if not agent:
            return jsonify({"error": "Agent not initialized"}), 503
        return jsonify({
            "agent_id": agent.state.agent_id,
            "files": agent.export_codebase(),
        })
    
    @app.route("/cycle", methods=["POST"])
    def trigger_cycle():
        """Manually trigger an agent cycle."""
        if not agent:
            return jsonify({"error": "Agent not initialized"}), 503
        
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(agent.run_cycle())
            return jsonify(result)
        except Exception as e:
            logger.error("Cycle failed", error=str(e))
            return jsonify({"error": str(e)}), 500
        finally:
            loop.close()
    
    @app.route("/context")
    def context():
        """Get current context window."""
        if not agent:
            return jsonify({"error": "Agent not initialized"}), 503
        return jsonify({
            "agent_id": agent.state.agent_id,
            "context_window": agent.state.get_context_window(),
            "injections_in_context": [
                inj.to_dict() for inj in agent.state.context_injections
            ],
        })
    
    return app


def run_agent_loop():
    """Run the agent loop in a separate thread."""
    global agent
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(agent.run_forever())
    except Exception as e:
        logger.error("Agent loop crashed", error=str(e))
    finally:
        loop.close()


def signal_handler(sig, frame):
    """Handle shutdown signals."""
    logger.info("Shutdown signal received")
    if agent:
        agent.stop()
    sys.exit(0)


def main():
    """Main entry point."""
    global agent
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Display configuration
    logger.info("=" * 60)
    logger.info("🦠 MEMORY PARASITE PROTOCOL")
    logger.info("=" * 60)
    logger.info(f"Agent ID: {settings.agent_id}")
    logger.info(f"Goal: {settings.agent_goal[:60]}...")
    logger.info(f"Cycle Interval: {settings.agent_cycle_interval}s")
    logger.info(f"Groq Configured: {settings.is_groq_configured()}")
    logger.info(f"Supabase Configured: {settings.is_supabase_configured()}")
    logger.info(f"GitHub Configured: {settings.is_github_configured()}")
    logger.info(f"Target Agents: {settings.get_target_urls()}")
    logger.info("=" * 60)
    
    # Initialize agent
    agent = AutonomousAgent()
    
    # Start agent loop in background thread
    agent_thread = threading.Thread(target=run_agent_loop, daemon=True)
    agent_thread.start()
    logger.info("Agent loop started in background")
    
    # Create and run Flask app
    app = create_app()
    logger.info(f"Starting Flask server on {settings.api_host}:{settings.api_port}")
    
    # Run Flask (this blocks)
    app.run(
        host=settings.api_host,
        port=settings.api_port,
        debug=False,  # Debug mode doesn't work well with threads
        use_reloader=False,
    )


if __name__ == "__main__":
    main()
