
"""
Autonomous Repair Script for Koyeb Service.
Updates Environment Variables on existing service to fix startup crash.

Usage: python configure_service.py
"""
import os
import httpx
from dotenv import load_dotenv

# Load env vars
load_dotenv()

# Configuration
API_KEY = "gmx1edfheee7oz7wo7vr3klrwtkquw7mrv7f3z73koem1h33v1jt1l68db1f33f8"
SERVICE_ID = "80e8eb7d-12f8-4ee9-9c57-b564e7fd2565"
KOYEB_API_URL = "https://app.koyeb.com/v1"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def log(msg, type="INFO"):
    print(f"[{type}] {msg}")

def prepare_env_vars():
    """Sync env vars."""
    env_vars = []
    # Critical keys that MUST be present
    keys_to_sync = [
        "AGENT_ID", "AGENT_GOAL", "GROQ_API_KEY", "SUPABASE_URL", "SUPABASE_KEY",
        "GITHUB_TOKEN", "SOLANA_PRIVATE_KEY", "OPENROUTER_API_KEY", "GEMINI_API_KEY",
        "OLLAMA_BASE_URL", "AGENT_WALLET_KEY"
    ]
    
    # Always set PORT to 8000 matching the service definition
    env_vars.append({"key": "PORT", "value": "8000"})
    
    # Fix GitHub Configuration
    env_vars.append({"key": "GITHUB_REPO", "value": "brainless3178/memory-parasite-protocol"})
    env_vars.append({"key": "GITHUB_REPO_OWNER", "value": "brainless3178"})
    env_vars.append({"key": "GITHUB_REPO_NAME", "value": "memory-parasite-protocol"})
    
    # Fix Reason Loop (Groq 429) -> Switch to Gemini or OpenRouter
    env_vars.append({"key": "LLM_PROVIDER", "value": "gemini"})
    
    for key in keys_to_sync:
        val = os.environ.get(key)
        if val:
            env_vars.append({"key": key, "value": val})
            
    # Add any logging config
    env_vars.append({"key": "LOG_LEVEL", "value": "INFO"})
    
    return env_vars

def update_service():
    log(f"Configuring Service {SERVICE_ID}...", "INFO")
    
    with httpx.Client(timeout=30) as client:
        # 1. Fetch current definition to preserve other settings (regions, instance types)
        resp = client.get(f"{KOYEB_API_URL}/services/{SERVICE_ID}", headers=headers)
        if resp.status_code != 200:
            log(f"Failed to fetch service: {resp.text}", "ERROR")
            return
            
        try:
            data = resp.json()
            if "service" not in data:
                log(f"Unexpected response format: {data.keys()}", "ERROR")
                return
            
            # Defensive access
            svc = data["service"]
            if "definition" not in svc:
                log("Definition missing in Service object. Fetching from Latest Deployment...", "INFO")
                deploy_id = svc.get("latest_deployment_id") or svc.get("active_deployment_id")
                if not deploy_id:
                     log("No deployment ID found to recover definition.", "ERROR")
                     return
                
                d_resp = client.get(f"{KOYEB_API_URL}/deployments/{deploy_id}", headers=headers)
                if d_resp.status_code != 200:
                    log(f"Failed to fetch deployment {deploy_id}", "ERROR")
                    return
                
                current_def = d_resp.json()["deployment"]["definition"]
            else:
                current_def = svc["definition"]
        except Exception as e:
            log(f"JSON parsing error: {e}", "ERROR")
            return
        
        # 2. Update Env Vars
        new_env = prepare_env_vars()
        current_def["env"] = new_env
        
        # Ensure docker/git definition is correct? 
        # Inspect showed it uses GIT. We keep it GIT.
        
        log(f"Pushing {len(new_env)} environment variables...", "INFO")
        
        # 3. Patch Service
        patch_resp = client.patch(
            f"{KOYEB_API_URL}/services/{SERVICE_ID}",
            headers=headers,
            json={"definition": current_def}
        )
        
        if patch_resp.status_code == 200:
            log("Service configuration updated successfully!", "SUCCESS")
            
            # 4. Trigger Redeploy
            log("Triggering Redeployment...", "INFO")
            redeploy_resp = client.post(
                f"{KOYEB_API_URL}/services/{SERVICE_ID}/redeploy", 
                headers=headers, 
                json={"deployment_group": "default"}
            )
            
            if redeploy_resp.status_code == 200:
                log("Redeployment triggered. Watch dashboard for 'provisioning' status.", "SUCCESS")
            else:
                log(f"Redeploy trigger failed: {redeploy_resp.text}", "WARNING")
        else:
            log(f"Update failed: {patch_resp.text}", "ERROR")

if __name__ == "__main__":
    update_service()
