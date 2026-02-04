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

# Global Orchestrator
settings = get_settings()
orch = Orchestrator()

app = Flask(__name__)
CORS(app)

@app.route("/")
@app.route("/health")
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
