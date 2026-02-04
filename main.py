"""
Memory Parasite Protocol - Main Entry Point

Refactored for bulletproof production deployment on Koyeb/Replit.
"""

import asyncio
import threading
import signal
import sys
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import structlog

from config.settings import get_settings
from agents.autonomous_agent import AutonomousAgent

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
    CORS(app)
    
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
    
    @app.route("/inject", methods=["POST"])
    def receive_injection():
        data = request.get_json()
        if not data or "suggestion" not in data:
            return jsonify({"error": "Invalid payload"}), 400
        
        # Run in new loop for flask compatibility
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(agent.receive_injection(data))
            return jsonify(result)
        finally:
            loop.close()
            
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
