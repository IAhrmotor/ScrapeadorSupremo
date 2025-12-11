"""Data processing and storage agent."""

from typing import Any, Dict, Optional
from .base_agent import BaseAgent, AgentCapability, AgentResponse


class DataAgent(BaseAgent):
    """Agent specialized in data processing, transformation and storage."""

    def __init__(self):
        super().__init__(
            name="data",
            description="Handles data processing, transformation, and storage"
        )
        self._keywords = [
            "data", "save", "store", "database", "csv", "json", "excel",
            "transform", "clean", "process", "export", "import", "format"
        ]

    def get_capabilities(self) -> list[AgentCapability]:
        return [
            AgentCapability(
                name="data_storage",
                description="Save and store data in various formats",
                keywords=["save", "store", "database", "csv", "json"],
                priority=10
            ),
            AgentCapability(
                name="data_transformation",
                description="Transform and clean data",
                keywords=["transform", "clean", "process"],
                priority=8
            ),
        ]

    def can_handle(self, task: str, context: Optional[Dict[str, Any]] = None) -> float:
        task_lower = task.lower()

        matches = sum(1 for kw in self._keywords if kw in task_lower)

        if matches >= 3:
            return 0.9
        elif matches >= 2:
            return 0.7
        elif matches >= 1:
            return 0.4

        return 0.0

    async def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        return AgentResponse(
            success=True,
            result={"processed": True, "task": task},
            message=f"Data agent processed: {task[:50]}..."
        )
