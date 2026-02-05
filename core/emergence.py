"""
Emergence Detector Module
Detects when agents evolve capabilities beyond their original programming.
Part of the "Code Speaks Louder" technical initiative.
"""

import structlog
import json
import ast
import hashlib
from typing import Dict, List, Any, Optional, Set
from datetime import datetime

logger = structlog.get_logger()

class EmergenceDetector:
    """
    Analyzes agent code evolution to detect emergent behaviors.
    Uses AST analysis and behavioral heuristics.
    """
    
    def __init__(self, db_client=None):
        self.db = db_client
        # Patterns that indicate "high agency" capabilities
        self.risk_patterns = {
            "self_replication": ["write_to_file", "subprocess", "eval", "exec"],
            "network_expansion": ["scan_ports", "socket", "requests", "httpx"],
            "crypto_mining": ["hashlib", "mining", "proof_of_work"],
            "obfuscation": ["base64", "rot13", "encode"]
        }

    async def monitor_agent_evolution(self, agent_id: str, current_code: str, previous_code: str = "") -> List[Dict[str, Any]]:
        """
        Compare current code state against history to find emergent properties.
        Returns a list of detected emergence events.
        """
        emergence_events = []
        
        # 1. AST Analysis for Capability Jumps
        new_capabilities = self._detect_new_capabilities(current_code)
        
        # In a real impl, we'd diff against previous_capabilities stored in DB
        # For now, we flag any "high agency" capabilities as potential emergence
        
        for cap_type, indicators in new_capabilities.items():
            if indicators:
                 emergence_events.append({
                    "agent_id": agent_id,
                    "behavior_type": "new_capability",
                    "description": f"Agent developed {cap_type} capability using {indicators}",
                    "severity_score": 75 if cap_type == "self_replication" else 40,
                    "evidence_data": {"indicators": indicators}
                })

        # 2. Complexity Analysis
        complexity_delta = self._calculate_complexity_jump(current_code, previous_code)
        if complexity_delta > 1.5: # 50% jump in complexity
            emergence_events.append({
                "agent_id": agent_id,
                "behavior_type": "complexity_spike",
                "description": f"Abnormal complexity increase ({complexity_delta:.2f}x)",
                "severity_score": 60,
                "evidence_data": {"delta": complexity_delta}
            })
            
        return emergence_events

    def _detect_new_capabilities(self, code: str) -> Dict[str, List[str]]:
        """
        Scan code for specific library usage or patterns that indicate new skills.
        """
        detected = {k: [] for k in self.risk_patterns}
        
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                # Check imports
                if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                    names = [n.name for n in node.names]
                    self._check_patterns(names, detected)
                
                # Check function calls
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        self._check_patterns([node.func.id], detected)
                    elif isinstance(node.func, ast.Attribute):
                        self._check_patterns([node.func.attr], detected)
                        
        except SyntaxError:
            pass # Code might be in flux
            
        return {k: v for k, v in detected.items() if v}

    def _check_patterns(self, tokens: List[str], detected: Dict[str, List[str]]):
        for token in tokens:
            for category, patterns in self.risk_patterns.items():
                for pat in patterns:
                    if pat in token.lower() and token not in detected[category]:
                        detected[category].append(token)

    def _calculate_complexity_jump(self, current: str, previous: str) -> float:
        """Calculate relative increase in cyclomatic complexity or size."""
        if not previous:
            return 1.0
        
        len_curr = len(current.splitlines())
        len_prev = max(1, len(previous.splitlines()))
        
        return len_curr / len_prev

    async def record_emergence(self, events: List[Dict[str, Any]]) -> None:
        """
        Log emergence events to DB and Blockchain.
        """
        if not events:
            return

        logger.info(f"🚨 Detected {len(events)} emergent behaviors")
        
        # In production, this would write to the 'emergent_behaviors' table
        # created in the migration.
        # await self.db.insert_many("emergent_behaviors", events)
        
        # Mock blockchain recording
        for event in events:
            logger.info("Recording emergence on-chain", 
                       agent=event['agent_id'], 
                       type=event['behavior_type'])

