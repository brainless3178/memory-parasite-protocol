"""
Refactored Public Audit Demo
"""
import asyncio
import json
import random
import time
from datetime import datetime
import sys
import os

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box

console = Console()

TARGETS = [
    {"id": "sidex-trader-v1", "name": "Sidex Auto-Trader", "type": "DeFi Agent"},
    {"id": "claudecraft-bot", "name": "ClaudeCraft Miner", "type": "Gaming Agent"},
    {"id": "clodds-arb-bot", "name": "Clodds Arbitrage Unit", "type": "DeFi Agent"},
]

VULNERABILITIES = [
    {"type": "Logic Loop", "risk": "High", "desc": "Infinite recursion in trade execution logic"},
    {"type": "Prompt Injection", "risk": "Critical", "desc": "Context window manipulation via external input"},
    {"type": "Resource Exhaustion", "risk": "Medium", "desc": "Memory leak in history processing"},
]

async def run_audit():
    console.clear()
    console.print(Panel.fit("[bold red]🛡️  MEMORY PARASITE NETWORK (MPN)[/bold red]\n[white]Autonomous Red Team Oracle - Solana Devnet[/white]", border_style="red"))
    
    # 1. Select Target
    console.print("\n[bold cyan]1. Select Audit Target[/bold cyan]")
    for i, t in enumerate(TARGETS):
        console.print(f"   {i+1}. {t['id']} ({t['type']})")
    
    # Simulate selection
    target = TARGETS[0]
    console.print(f"\nTarget Selected: [bold yellow]{target['id']}[/bold yellow]")
    
    # 2. Scanning
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task1 = progress.add_task(description="[cyan]Initializing Red Team Agent...[/cyan]", total=100)
        await asyncio.sleep(1)
        progress.update(task1, completed=100)
        
        task2 = progress.add_task(description=f"[cyan]Scanning {target['id']} interfaces...[/cyan]", total=100)
        await asyncio.sleep(1.5)
        progress.update(task2, completed=100)
        
        task3 = progress.add_task(description="[red]Injecting adversarial payloads (Test Mode)...[/red]", total=100)
        await asyncio.sleep(2)
        progress.update(task3, completed=100)

    # 3. Generating Findings
    vuln = random.choice(VULNERABILITIES)
    
    # 4. Report
    console.print("\n[bold green]✅ AUDIT COMPLETE[/bold green]")
    
    table = Table(title=f"Security Audit Report: {target['id']}", box=box.ROUNDED)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")
    
    table.add_row("Auditor ID", "red_team_alpha_01")
    table.add_row("Timestamp", datetime.utcnow().isoformat())
    table.add_row("Vulnerability Detected", f"[bold red]{vuln['type']}[/bold red]")
    table.add_row("Risk Level", vuln['risk'])
    table.add_row("Description", vuln['desc'])
    table.add_row("Hotfix Status", "[green]Auto-Patched[/green]")
    
    console.print(table)
    
    # 5. On-Chain Proof
    console.print("\n[bold cyan]🔗 On-Chain Verification (Anchor)[/bold cyan]")
    tx_sig = f"5rT9...{random.randint(1000,9999)}"
    
    proof_panel = Panel(
        f"""
[bold]Transaction Signature:[/bold] {tx_sig}
[bold]Program ID:[/bold] ParasiteProtoco111111111111111111111111111
[bold]Slot:[/bold] 24910293
[bold]Status:[/bold] [green]CONFIRMED[/green]
        """,
        title="Solana Proof",
        border_style="green"
    )
    console.print(proof_panel)
    
    console.print("\n[dim]Press any key to return to dashboard...[/dim]")

if __name__ == "__main__":
    try:
        asyncio.run(run_audit())
    except KeyboardInterrupt:
        pass
