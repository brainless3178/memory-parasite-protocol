
"""
Simple script to deploy/update Koyeb service using the provided API key.
Handles App creation and environment variable syncing from .env.
"""
import os
import sys
import time
import httpx
from dotenv import load_dotenv

# Load local environment variables
load_dotenv()

# Configuration
KOYEB_API_URL = "https://app.koyeb.com/v1"
API_KEY = "gmx1edfheee7oz7wo7vr3klrwtkquw7mrv7f3z73koem1h33v1jt1l68db1f33f8"  # User provided
APP_NAME = "memory-parasite-protocol"
SERVICE_NAME = "autonomous-agent-swarm"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def log(msg, type="INFO"):
    print(f"[{type}] {msg}")

def get_app_id(client, app_name):
    """Find App ID by name."""
    try:
        resp = client.get(f"{KOYEB_API_URL}/apps", headers=headers)
        if resp.status_code == 200:
            apps = resp.json().get("apps", [])
            for app in apps:
                if app["name"] == app_name:
                    return app["id"]
    except Exception as e:
        log(f"Failed to list apps: {e}", "ERROR")
    return None

def create_app(client, app_name):
    """Create a new App."""
    log(f"Creating App {app_name}...", "INFO")
    resp = client.post(f"{KOYEB_API_URL}/apps", headers=headers, json={"name": app_name})
    if resp.status_code == 200:
        return resp.json()["app"]["id"]
    log(f"Failed to create app: {resp.text}", "ERROR")
    return None

def get_service_id(client, app_id, service_name):
    """Find Service ID by name within an App."""
    try:
        resp = client.get(f"{KOYEB_API_URL}/services?app_id={app_id}", headers=headers)
        # Note: API might be /services?app_id=... or list all services and filter
        # Let's try listing all services (limited to user scope usually) or filtering
        if resp.status_code == 200:
            services = resp.json().get("services", [])
            for svc in services:
                if svc["name"] == service_name and svc["app_id"] == app_id:
                    return svc["id"]
                    
        # Fallback: List all services
        resp = client.get(f"{KOYEB_API_URL}/services", headers=headers) 
        if resp.status_code == 200:
             services = resp.json().get("services", [])
             for svc in services:
                 if svc["name"] == service_name and svc["app_id"] == app_id:
                     return svc["id"]
    except Exception:
        pass
    return None

def prepare_env_vars():
    """Read .env and format for Koyeb."""
    env_vars = []
    # Relevant keys to sync
    keys_to_sync = [
        "AGENT_ID", "AGENT_GOAL", "GROQ_API_KEY", "SUPABASE_URL", "SUPABASE_KEY",
        "GITHUB_TOKEN", "SOLANA_PRIVATE_KEY", "OPENROUTER_API_KEY", "GEMINI_API_KEY",
        "OLLAMA_BASE_URL", "AGENT_WALLET_KEY"
    ]
    
    # Always set PORT
    env_vars.append({"key": "PORT", "value": "8000"})
    
    for key in keys_to_sync:
        val = os.environ.get(key)
        if val:
            env_vars.append({"key": key, "value": val})
            
    return env_vars

def deploy():
    log(f"🚀 Initializing Koyeb Deployment for {APP_NAME}...", "INFO")
    
    with httpx.Client(timeout=30) as client:
        # 1. Get or Create App
        app_id = get_app_id(client, APP_NAME)
        if not app_id:
            app_id = create_app(client, APP_NAME)
            
        if not app_id:
            log("Could not resolve App ID. Aborting.", "ERROR")
            return

        log(f"App ID: {app_id}", "INFO")

        # 2. Prepare Environment Variables
        env = prepare_env_vars()
        log(f"Prepared {len(env)} environment variables from local .env", "INFO")

        # 3. Define Service Definition
        # We rely on the public repo or git connection.
        # If the user hasn't connected GitHub to Koyeb, falling back to Docker image might be safer if we had one.
        # But we don't have a registry. We must use Git.
        # We assume the user has the repo "brainless3178/memory-parasite-protocol".
        
        service_def = {
            "definition": {
                "name": SERVICE_NAME,
                "type": "GIT",
                "git": {
                    "repository": "brainless3178/memory-parasite-protocol",
                    "branch": "main",
                    "build_command": "",
                    "run_command": "gunicorn --bind 0.0.0.0:8000 --workers 1 --threads 8 --timeout 0 main:app",
                },
                "docker": {
                   "dockerfile": "Dockerfile"
                },
                "env": env,
                "ports": [{"port": 8000, "protocol": "http"}],
                "routes": [{"path": "/", "port": 8000}],
                "regions": ["was"],
                "instance_types": ["nano"]
            }
        }
        
        # 4. Get or Create Service
        service_id = get_service_id(client, app_id, SERVICE_NAME)
        
        if not service_id:
            log(f"Creating Service {SERVICE_NAME}...", "INFO")
            create_resp = client.post(
                f"{KOYEB_API_URL}/services", 
                headers=headers, 
                json={
                    "app_id": app_id, 
                    "definition": service_def["definition"]
                }
            )
            if create_resp.status_code == 200:
                svc = create_resp.json()["service"]
                log(f"Service created! ID: {svc['id']}", "SUCCESS")
                log(f"Status: {svc['status']}", "INFO")
            else:
                log(f"Service creation failed: {create_resp.text}", "ERROR")
        else:
            log(f"Updating Service {service_id} with latest configuration...", "INFO")
            # Update definition (env vars, etc)
            # We need to fetch the latest revision first to respect `version`? 
            # Koyeb update usually requires just the definition
            
            update_resp = client.patch(
                f"{KOYEB_API_URL}/services/{service_id}",
                headers=headers,
                json={"definition": service_def["definition"]}
            )
            
            if update_resp.status_code == 200:
                log("Service configuration updated!", "SUCCESS")
                
                # Trigger Redeploy
                log("Triggering Redeployment...", "INFO")
                redeploy_resp = client.post(
                    f"{KOYEB_API_URL}/services/{service_id}/redeploy", 
                    headers=headers, 
                    json={"deployment_group": "default"}
                )
                if redeploy_resp.status_code == 200:
                    log("Redeployment triggered.", "SUCCESS")
                else:
                    log(f"Redeploy trigger failed: {redeploy_resp.text}", "WARNING")
            else:
                 log(f"Update failed: {update_resp.text}", "ERROR")

if __name__ == "__main__":
    try:
        deploy()
    except Exception as e:
        log(f"Unhandled exception: {e}", "ERROR")
