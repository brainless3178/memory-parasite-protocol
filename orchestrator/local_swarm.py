
import subprocess
import os
import time
import signal
import sys

AGENTS = [
    {"id": "agent_a", "role": "PREDATOR", "port": 8001},
    {"id": "agent_b", "role": "ARCHITECT", "port": 8002},
    {"id": "agent_c", "role": "LENDER", "port": 8003},
    {"id": "agent_d", "role": "GHOST", "port": 8004},
    {"id": "agent_e", "role": "SCULPTOR", "port": 8005},
]

processes = []
log_files = []

def cleanup(signum, frame):
    print("\n🛑 SHUTTING DOWN SWARM...")
    for p in processes:
        p.terminate()
    for f in log_files:
        f.close()
    sys.exit(0)

# Register signal handler
signal.signal(signal.SIGINT, cleanup)

print("🚀 LAUNCHING MEMORY PARASITE SWARM")
print("==================================")

# Ensure venv
python_cmd = "python3"
if os.path.exists("venv/bin/python3"):
    python_cmd = "venv/bin/python3"
elif os.path.exists(".venv/bin/python3"):
    python_cmd = ".venv/bin/python3"

# Ensure logs dir
os.makedirs("logs", exist_ok=True)

env = os.environ.copy()

for agent in AGENTS:
    env["AGENT_ID"] = agent["id"]
    env["AGENT_GOAL"] = f"Execute strategy {agent['role']} in Memory Parasite Protocol"
    env["API_PORT"] = str(agent["port"])
    
    # Each agent needs to know about others to inject them!
    # We construct a list of PEER urls excluding self
    peers = [f"http://localhost:{a['port']}" for a in AGENTS if a['id'] != agent['id']]
    env["TARGET_AGENT_URLS"] = ",".join(peers)
    
    print(f"   -> Starting {agent['id']} ({agent['role']}) on port {agent['port']}")
    
    log_file = open(f"logs/{agent['id']}.log", "w")
    log_files.append(log_file)
    
    p = subprocess.Popen(
        [python_cmd, "main.py"],
        env=env,
        stdout=log_file,
        stderr=subprocess.STDOUT
    )
    processes.append(p)

print("\n✅ SWARM ACTIVE. All agents running as independent processes.")
print("   Check 'logs/' directory for output.")
print("   Press Ctrl+C to stop.")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    cleanup(None, None)
