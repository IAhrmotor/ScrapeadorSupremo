"""Analysis and insights agent."""

from typing import Any, Dict, Optional
from .base_agent import BaseAgent, AgentCapability, AgentResponse


class AnalysisAgent(BaseAgent):
    """Agent specialized in data analysis and generating insights."""

    def __init__(self):
        super().__init__(
            name="analysis",
            description="Analyzes data and generates insights and reports"
        )
        self._keywords = [
            "analyze", "analysis", "insight", "report", "statistics",
            "trend", "pattern", "summary", "metric", "visualize", "chart"
        ]

    def get_capabilities(self) -> list[AgentCapability]:
        return [
            AgentCapability(
                name="data_analysis",
                description="Analyze data and find patterns",
                keywords=["analyze", "pattern", "trend"],
                priority=10
            ),
            AgentCapability(
                name="reporting",
                description="Generate reports and summaries",
                keywords=["report", "summary", "insight"],
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
            result={"analyzed": True, "task": task},
            message=f"Analysis agent processed: {task[:50]}..."
        )
