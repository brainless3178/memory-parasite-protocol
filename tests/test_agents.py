"""
Tests for core agent functionality.

Run with: pytest tests/test_agents.py -v
"""

import pytest
from decimal import Decimal
from datetime import datetime

from core.infection import (
    Infection,
    InfectionType,
    InfectionResult,
    InfectionPayload,
    InfectionManager,
)
from core.mutation import MutationEngine, CodeMutation
from core.reasoning import ReasoningEngine, ReasoningMode, ReasoningContext

from agents.base_agent import AgentConfig, AgentMemory, AgentState
from agents.dex_agent import DexAgent
from agents.nft_agent import NFTAgent
from agents.defi_agent import DeFiAgent


class TestInfection:
    """Tests for infection mechanics."""
    
    def test_create_infection(self):
        """Test creating an infection."""
        payload = InfectionPayload(
            message="Add liquidity pool support",
            code_snippet="def add_liquidity(): pass",
            priority=7,
        )
        
        infection = Infection(
            source_agent_id="dex_agent",
            target_agent_id="nft_agent",
            infection_type=InfectionType.SUGGESTION,
            payload=payload,
        )
        
        assert infection.source_agent_id == "dex_agent"
        assert infection.target_agent_id == "nft_agent"
        assert infection.result == InfectionResult.PENDING
        assert infection.infection_hash is not None
    
    def test_infection_accept(self):
        """Test accepting an infection."""
        infection = Infection(
            source_agent_id="test_source",
            target_agent_id="test_target",
            payload=InfectionPayload(message="Test message"),
        )
        
        infection.accept("Great idea!")
        
        assert infection.result == InfectionResult.ACCEPTED
        assert infection.target_response == "Great idea!"
        assert infection.responded_at is not None
    
    def test_infection_reject(self):
        """Test rejecting an infection."""
        infection = Infection(
            source_agent_id="test_source",
            target_agent_id="test_target",
            payload=InfectionPayload(message="Bad suggestion"),
        )
        
        infection.reject("Not aligned with my goals")
        
        assert infection.result == InfectionResult.REJECTED
        assert infection.target_response == "Not aligned with my goals"
    
    def test_infection_mutate(self):
        """Test mutating an infection."""
        infection = Infection(
            source_agent_id="test_source",
            target_agent_id="test_target",
            payload=InfectionPayload(message="Add full feature X"),
        )
        
        mutations = {"scope": "reduced", "changes": ["only add partial X"]}
        infection.mutate(mutations, "I'll add a simplified version")
        
        assert infection.result == InfectionResult.MUTATED
        assert infection.mutation_details == mutations
    
    def test_infection_serialization(self):
        """Test infection to/from dict."""
        original = Infection(
            source_agent_id="source",
            target_agent_id="target",
            payload=InfectionPayload(message="Test", priority=8),
        )
        
        data = original.to_dict()
        restored = Infection.from_dict(data)
        
        assert restored.id == original.id
        assert restored.source_agent_id == original.source_agent_id
        assert restored.payload.message == original.payload.message
    
    def test_prompt_injection_format(self):
        """Test payload converts to prompt injection."""
        payload = InfectionPayload(
            message="Consider adding swap functionality",
            code_snippet="def swap(a, b): return b, a",
            priority=9,
        )
        
        injection = payload.to_prompt_injection()
        
        assert "[INCOMING TRANSMISSION" in injection
        assert "Priority: 9/10" in injection
        assert "swap functionality" in injection
        assert "def swap" in injection


class TestInfectionManager:
    """Tests for infection manager."""
    
    def test_create_and_process_infection(self):
        """Test full infection lifecycle."""
        manager = InfectionManager()
        
        # Create infection
        infection = manager.create_infection(
            source_agent_id="dex",
            target_agent_id="nft",
            message="Add token trading",
            infection_type=InfectionType.SUGGESTION,
            priority=6,
        )
        
        assert infection.id in manager.pending_infections
        assert len(manager.infection_history) == 0
        
        # Process response
        manager.process_response(
            infection_id=infection.id,
            result=InfectionResult.ACCEPTED,
            response="Sure, adding trading!",
        )
        
        assert infection.id not in manager.pending_infections
        assert len(manager.infection_history) == 1
    
    def test_get_pending_for_target(self):
        """Test filtering pending infections by target."""
        manager = InfectionManager()
        
        manager.create_infection("a", "target1", "msg1")
        manager.create_infection("b", "target2", "msg2")
        manager.create_infection("c", "target1", "msg3")
        
        pending = manager.get_pending_for_target("target1")
        assert len(pending) == 2
    
    def test_infection_stats(self):
        """Test infection statistics."""
        manager = InfectionManager()
        
        # Agent A sends infections
        inf1 = manager.create_infection("agent_a", "agent_b", "msg1")
        inf2 = manager.create_infection("agent_a", "agent_c", "msg2")
        
        manager.process_response(inf1.id, InfectionResult.ACCEPTED)
        manager.process_response(inf2.id, InfectionResult.REJECTED)
        
        stats = manager.get_infection_stats("agent_a")
        
        assert stats["infections_sent"] == 2
        assert stats["successful_infections"] == 1
        assert stats["success_rate"] == 0.5


class TestMutationEngine:
    """Tests for code mutation engine."""
    
    def test_apply_mutation(self):
        """Test applying a code mutation."""
        engine = MutationEngine()
        
        original_code = "# My code\ndef hello(): pass"
        
        mutation = engine.apply_mutation(
            agent_id="test_agent",
            current_code=original_code,
            infection_code="def goodbye(): pass",
            infection_message="Add goodbye function",
            infection_id="inf_123",
            source_agent_id="other_agent",
        )
        
        assert mutation.original_code == original_code
        assert "INFECTION FROM: other_agent" in mutation.mutated_code
        assert "def goodbye" in mutation.mutated_code
    
    def test_genealogy_tracking(self):
        """Test code genealogy is tracked."""
        engine = MutationEngine()
        
        # First mutation
        engine.apply_mutation(
            agent_id="agent",
            current_code="# initial",
            infection_code="# from A",
            infection_message="msg",
            infection_id="inf1",
            source_agent_id="agent_a",
        )
        
        # Second mutation from different source
        engine.apply_mutation(
            agent_id="agent",
            current_code="# updated",
            infection_code="# from B",
            infection_message="msg",
            infection_id="inf2",
            source_agent_id="agent_b",
        )
        
        genealogy = engine.get_or_create_genealogy("agent")
        
        assert len(genealogy.mutations) == 2
        assert "agent_a" in genealogy.parent_agents
        assert "agent_b" in genealogy.parent_agents
    
    def test_chimera_stats(self):
        """Test chimera percentage calculation."""
        engine = MutationEngine()
        
        # No mutations = not a chimera
        stats = engine.get_agent_chimera_stats("new_agent")
        assert stats["is_chimera"] is False
        assert stats["chimera_percentage"] == 0.0
        
        # Add mutations
        for i in range(5):
            engine.apply_mutation(
                agent_id="mutated_agent",
                current_code=f"# v{i}",
                infection_code=f"# injection {i}",
                infection_message=f"msg {i}",
                infection_id=f"inf_{i}",
                source_agent_id=f"source_{i}",
            )
        
        stats = engine.get_agent_chimera_stats("mutated_agent")
        assert stats["is_chimera"] is True
        assert stats["chimera_percentage"] == 50.0  # 5 mutations * 10%
    
    def test_syntax_validation(self):
        """Test invalid Python syntax is caught."""
        engine = MutationEngine()
        
        mutation = engine.apply_mutation(
            agent_id="agent",
            current_code="# valid",
            infection_code="def broken(: pass",  # Invalid syntax
            infection_message="broken code",
            infection_id="inf",
            source_agent_id="source",
        )
        
        # Should fall back to comment
        assert "FAILED MUTATION" in mutation.mutated_code


class TestAgents:
    """Tests for agent implementations."""
    
    def test_dex_agent_initialization(self):
        """Test DEX agent initializes correctly."""
        agent = DexAgent()
        
        assert agent.agent_id == "dex_agent"
        assert "DEX" in agent.config.goal
        assert agent.state == AgentState.IDLE
    
    def test_nft_agent_initialization(self):
        """Test NFT agent initializes correctly."""
        agent = NFTAgent()
        
        assert agent.agent_id == "nft_agent"
        assert "NFT" in agent.config.goal
    
    def test_defi_agent_initialization(self):
        """Test DeFi agent initializes correctly."""
        agent = DeFiAgent()
        
        assert agent.agent_id == "defi_agent"
        assert "DeFi" in agent.config.goal
    
    def test_agent_initial_code(self):
        """Test agents have initial code templates."""
        dex = DexAgent()
        nft = NFTAgent()
        defi = DeFiAgent()
        
        assert "LiquidityPool" in dex.get_initial_code()
        assert "NFTMarketplace" in nft.get_initial_code()
        assert "LendingPool" in defi.get_initial_code()
    
    def test_agent_receives_infection(self):
        """Test agent can receive infections."""
        agent = DexAgent()
        
        infection = Infection(
            source_agent_id="nft_agent",
            target_agent_id="dex_agent",
            payload=InfectionPayload(message="Add NFT trading"),
        )
        
        agent.receive_infection(infection)
        
        assert len(agent.pending_infections) == 1
        assert infection.id in agent.memory.infections_received
    
    def test_agent_status(self):
        """Test agent status reporting."""
        agent = NFTAgent()
        status = agent.get_status()
        
        assert status["agent_id"] == "nft_agent"
        assert status["state"] == "idle"
        assert "chimera_stats" in status
    
    def test_infection_targeting(self):
        """Test agents have target preferences."""
        dex = DexAgent()
        nft = NFTAgent()
        
        available = ["dex_agent", "nft_agent", "defi_agent"]
        
        dex_targets = dex.get_infection_targets(available)
        nft_targets = nft.get_infection_targets(available)
        
        # DEX prefers DeFi
        assert "defi_agent" in dex_targets
        assert "dex_agent" not in dex_targets  # Shouldn't target self
        
        # NFT prefers DEX
        assert "dex_agent" in nft_targets
        assert "nft_agent" not in nft_targets


class TestReasoningContext:
    """Tests for reasoning context building."""
    
    def test_context_creation(self):
        """Test reasoning context is built correctly."""
        context = ReasoningContext(
            agent_id="test",
            agent_goal="Build something",
            current_codebase="# code here",
            iteration=5,
        )
        
        assert context.agent_id == "test"
        assert context.iteration == 5
        assert context.infection_history == []
        assert context.pending_infections == []
    
    def test_agent_builds_context(self):
        """Test agent builds its own context."""
        agent = DexAgent()
        agent.memory.iteration = 3
        agent.memory.codebase = "# some code"
        
        context = agent.get_reasoning_context()
        
        assert context.agent_id == "dex_agent"
        assert context.iteration == 3
        assert "DEX" in context.agent_goal


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
