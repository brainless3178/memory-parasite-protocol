"""Core module for Memory Parasite Protocol."""
from core.infection import Infection, InfectionType, InfectionResult
from core.reasoning import ReasoningEngine
from core.mutation import MutationEngine

__all__ = [
    "Infection",
    "InfectionType", 
    "InfectionResult",
    "ReasoningEngine",
    "MutationEngine",
]
