
import asyncio
import os
import signal
import subprocess
import sys
import time
from rich.console import Console

console = Console()

AGENTS = [
    {"id": "agent_alpha", "port": 8001, "goal": "Security Auditor"},
    {"id": "agent_beta",  "port": 8002, "goal": "DeFi Trader"},
    {"id": "agent_gamma", "port": 8003, "goal": "NFT minter"},
]

processes = []

def cleanup(signum, frame):
    console.print("\n[bold red]Stopping Swarm...[/bold red]")
    for p in processes:
        p.terminate()
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup)

async def start_swarm():
    console.print("[bold green]🚀 STARTING LOCAL AUTONOMOUS SWARM[/bold green]")
    
    # Define peer network
    target_urls = ",".join([f"http://localhost:{a['port']}" for a in AGENTS])
    
    for agent in AGENTS:
        env = os.environ.copy()
        env["AGENT_ID"] = agent["id"]
        env["AGENT_GOAL"] = agent["goal"]
        env["API_PORT"] = str(agent["port"])
        env["PORT"] = str(agent["port"]) # Compatibility
        env["TARGET_AGENT_URLS"] = target_urls
        # Disable heavy logging for the swarm to keep terminal clean
        env["LOG_LEVEL"] = "WARNING" 
        
        console.print(f"Starting [cyan]{agent['id']}[/cyan] on port [yellow]{agent['port']}[/yellow]...")
        
        # Start process
        p = subprocess.Popen(
            [sys.executable, "main.py"],
            env=env,
            stdout=subprocess.DEVNULL, # Suppress stdout to avoid chaos
            stderr=subprocess.PIPE     # Keep stderr for errors
        )
        processes.append(p)
        
    console.print(f"\n[bold]✅ Swarm Active with {len(AGENTS)} agents.[/bold]")
    console.print("Agents are now running in background. They will autonomously discover and attack each other.")
    console.print("Press Ctrl+C to stop.\n")
    
    # Monitor loop
    while True:
        # Check if any died
        for i, p in enumerate(processes):
            if p.poll() is not None:
                console.print(f"[bold red]❌ {AGENTS[i]['id']} died! Restarting...[/bold red]")
                # Restart logic could go here, but for now just warn
        await asyncio.sleep(5)

if __name__ == "__main__":
    try:
        asyncio.run(start_swarm())
    except KeyboardInterrupt:
        cleanup(None, None)
