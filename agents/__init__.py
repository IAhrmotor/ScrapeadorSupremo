"""Agents package for ScrapeadorSupremo."""

from .base_agent import BaseAgent, AgentCapability, AgentResponse
from .registry import AgentRegistry, get_registry
from .orchestrator import OrchestratorAgent, orchestrate
from .hierarchy import (
    AgentHierarchy,
    AgentProfile,
    Department,
    Rank,
    get_hierarchy,
    AGENT_PROFILES
)

__all__ = [
    # Base
    "BaseAgent",
    "AgentCapability",
    "AgentResponse",
    # Registry
    "AgentRegistry",
    "get_registry",
    # Orchestrator
    "OrchestratorAgent",
    "orchestrate",
    # Hierarchy
    "AgentHierarchy",
    "AgentProfile",
    "Department",
    "Rank",
    "get_hierarchy",
    "AGENT_PROFILES",
]
