"""
Flask API server for Memory Parasite Protocol.

This server exposes HTTP endpoints for:
- Receiving infection attempts from other agents
- Querying agent status
- Triggering manual cycles
- Viewing infection history
"""

from flask import Flask
from flask_cors import CORS
import structlog

from config.settings import get_settings
from api.routes import register_routes

logger = structlog.get_logger()


def create_app() -> Flask:
    """Create and configure Flask application."""
    app = Flask(__name__)
    
    # Enable CORS for dashboard access
    CORS(app, resources={
        r"/api/*": {
            "origins": ["*"],
            "methods": ["GET", "POST", "PUT", "DELETE"],
            "allow_headers": ["Content-Type", "Authorization"],
        }
    })
    
    # Configuration
    settings = get_settings()
    app.config["DEBUG"] = settings.log_level == "DEBUG"
    
    # Register routes
    register_routes(app)
    
    logger.info("Flask app created", debug=app.config["DEBUG"])
    
    return app


def run_server():
    """Run the API server."""
    settings = get_settings()
    app = create_app()
    
    logger.info(
        "Starting API server",
        host=settings.api_host,
        port=settings.api_port,
    )
    
    app.run(
        host=settings.api_host,
        port=settings.api_port,
        debug=settings.log_level == "DEBUG",
    )


if __name__ == "__main__":
    run_server()
