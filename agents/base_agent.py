"""Base agent interface for all agents in the system."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from dataclasses import dataclass


@dataclass
class AgentCapability:
    """Describes what an agent can do."""
    name: str
    description: str
    keywords: list[str]
    priority: int = 0  # Higher priority agents are preferred when multiple match


@dataclass
class AgentResponse:
    """Standard response from an agent."""
    success: bool
    result: Any
    message: str
    metadata: Optional[Dict[str, Any]] = None


class BaseAgent(ABC):
    """Abstract base class for all agents."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    def get_capabilities(self) -> list[AgentCapability]:
        """Return list of capabilities this agent provides."""
        pass

    @abstractmethod
    def can_handle(self, task: str, context: Optional[Dict[str, Any]] = None) -> float:
        """
        Determine if this agent can handle the given task.

        Returns a confidence score between 0.0 and 1.0.
        0.0 = cannot handle
        1.0 = perfect match
        """
        pass

    @abstractmethod
    async def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """Execute the given task and return the result."""
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"
