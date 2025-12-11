"""Orchestrator agent that routes tasks to the appropriate specialized agents."""

import asyncio
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Awaitable
from dataclasses import dataclass

# Add parent to path for core imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from .base_agent import BaseAgent, AgentCapability, AgentResponse
from .registry import AgentRegistry, get_registry
from .hierarchy import AgentHierarchy, AgentProfile, Department, Rank, get_hierarchy
from core.debug import get_debugger, debug_flow, DebugLevel
from core.network import ScrapingCoordinator, CoordinatorConfig
from core.dns import DNSHealthStatus


@dataclass
class AgentScore:
    """Represents an agent's score for handling a task."""
    agent: BaseAgent
    confidence: float
    reason: str


class OrchestratorAgent:
    """
    Master orchestrator that identifies all agents and decides which one should act.

    The orchestrator:
    1. Discovers all available agents in the project
    2. Analyzes incoming tasks
    3. Scores each agent's ability to handle the task
    4. Delegates to the most appropriate agent
    5. Handles fallbacks and error cases
    """

    def __init__(self, registry: Optional[AgentRegistry] = None, hierarchy: Optional[AgentHierarchy] = None):
        self.registry = registry or get_registry()
        self.hierarchy = hierarchy or get_hierarchy()
        self.name = "orchestrator"
        self.description = "Routes tasks to specialized agents"
        self._task_history: List[Dict[str, Any]] = []
        self._debug = get_debugger()
        self._coordinator: Optional[ScrapingCoordinator] = None

    @debug_flow("orchestrator")
    def initialize(self) -> int:
        """
        Initialize the orchestrator by discovering all agents.

        Returns the number of agents discovered.
        """
        self._debug.flow_start("orchestrator", "initialize")
        discovered = self.registry.discover_agents()
        self._debug.info("orchestrator", f"Discovered {len(discovered)} agents")
        for agent in discovered:
            self._debug.debug("orchestrator", f"Agent: {agent.name}", {"description": agent.description})
        self._debug.flow_step("orchestrator", "discovery", f"Found {len(discovered)} runtime agents")
        return len(discovered)

    def list_available_agents(self) -> List[Dict[str, Any]]:
        """List all available agents with their capabilities."""
        agents_info = []
        for agent in self.registry:
            capabilities = agent.get_capabilities()
            agents_info.append({
                "name": agent.name,
                "description": agent.description,
                "capabilities": [
                    {
                        "name": cap.name,
                        "description": cap.description,
                        "keywords": cap.keywords
                    }
                    for cap in capabilities
                ]
            })
        return agents_info

    def _score_agents(
        self, task: str, context: Optional[Dict[str, Any]] = None
    ) -> List[AgentScore]:
        """
        Score all agents for their ability to handle the task.

        Returns sorted list of AgentScore (highest confidence first).
        """
        scores = []

        for agent in self.registry:
            try:
                confidence = agent.can_handle(task, context)
                scores.append(AgentScore(
                    agent=agent,
                    confidence=confidence,
                    reason=f"Confidence score: {confidence:.2f}"
                ))
            except Exception as e:
                scores.append(AgentScore(
                    agent=agent,
                    confidence=0.0,
                    reason=f"Error scoring: {e}"
                ))

        # Sort by confidence descending
        scores.sort(key=lambda x: x.confidence, reverse=True)
        return scores

    def select_agent(
        self, task: str, context: Optional[Dict[str, Any]] = None
    ) -> Optional[Tuple[BaseAgent, float]]:
        """
        Select the best agent for the given task.

        Returns tuple of (agent, confidence) or None if no suitable agent found.
        """
        scores = self._score_agents(task, context)

        if not scores:
            return None

        best = scores[0]
        if best.confidence > 0:
            return (best.agent, best.confidence)

        return None

    @debug_flow("orchestrator")
    async def route(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        min_confidence: float = 0.1
    ) -> AgentResponse:
        """
        Route a task to the most appropriate agent.

        Args:
            task: The task description
            context: Optional context for the task
            min_confidence: Minimum confidence required to delegate

        Returns:
            AgentResponse from the selected agent
        """
        task_id = f"task_{id(task)}"
        self._debug.start_context(task_id)
        start_time = self._debug.flow_start("orchestrator", "route")

        self._debug.info("orchestrator", f"Received task: {task[:100]}...")

        # Score all agents
        self._debug.flow_step("orchestrator", "scoring", "Scoring all agents")
        scores = self._score_agents(task, context)

        if not scores:
            self._debug.warn("orchestrator", "No agents available")
            self._debug.end_context(task_id)
            return AgentResponse(
                success=False,
                result=None,
                message="No agents available to handle this task"
            )

        # Log scores for debugging
        self._debug.debug("orchestrator", "Agent scores calculated", {
            "top_agents": [(s.agent.name, s.confidence) for s in scores[:5]]
        })

        # Select best agent
        best = scores[0]

        if best.confidence < min_confidence:
            self._debug.warn("orchestrator", f"No confident agent found", {
                "best_match": best.agent.name,
                "confidence": best.confidence,
                "min_required": min_confidence
            })
            self._debug.end_context(task_id)
            return AgentResponse(
                success=False,
                result=None,
                message=f"No agent confident enough to handle this task. "
                        f"Best match: {best.agent.name} ({best.confidence:.2f})"
            )

        # Delegate to selected agent
        self._debug.flow_step("orchestrator", "delegation", f"Delegating to {best.agent.name}")
        self._debug.add_to_agent_chain(best.agent.name)

        try:
            response = await best.agent.execute(task, context)

            # Record in history
            self._task_history.append({
                "task": task,
                "agent": best.agent.name,
                "confidence": best.confidence,
                "success": response.success
            })

            self._debug.info("orchestrator", f"Task completed by {best.agent.name}", {
                "success": response.success
            })
            self._debug.flow_end("orchestrator", "route", start_time)
            self._debug.end_context(task_id)

            return response

        except Exception as e:
            self._debug.error("orchestrator", f"Agent {best.agent.name} failed", {
                "exception": str(e)
            })
            self._debug.end_context(task_id)
            return AgentResponse(
                success=False,
                result=None,
                message=f"Agent {best.agent.name} failed: {e}"
            )

    async def route_with_fallback(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        max_attempts: int = 3
    ) -> AgentResponse:
        """
        Route a task with automatic fallback to next-best agent on failure.
        """
        scores = self._score_agents(task, context)
        attempted = set()

        for i, score in enumerate(scores[:max_attempts]):
            if score.confidence <= 0:
                break

            if score.agent.name in attempted:
                continue

            attempted.add(score.agent.name)
            print(f"[Orchestrator] Attempt {i+1}: {score.agent.name}")

            try:
                response = await score.agent.execute(task, context)
                if response.success:
                    return response
                print(f"[Orchestrator] Agent {score.agent.name} reported failure, "
                      f"trying next...")
            except Exception as e:
                print(f"[Orchestrator] Agent {score.agent.name} raised error: {e}")

        return AgentResponse(
            success=False,
            result=None,
            message=f"All {len(attempted)} attempted agents failed"
        )

    def get_task_history(self) -> List[Dict[str, Any]]:
        """Get history of routed tasks."""
        return self._task_history.copy()

    # === HIERARCHY METHODS ===

    def get_department(self, department: Department) -> List[AgentProfile]:
        """Get all agents in a department."""
        return self.hierarchy.get_department_agents(department)

    def get_department_head(self, department: Department) -> Optional[AgentProfile]:
        """Get the head of a department."""
        return self.hierarchy.get_department_head(department)

    def route_to_department(
        self,
        task: str,
        department: Department,
        min_rank: Rank = Rank.JUNIOR
    ) -> Optional[AgentProfile]:
        """
        Route task to the best agent in a specific department.

        Args:
            task: Task description
            department: Target department
            min_rank: Minimum rank required

        Returns:
            Best matching agent profile or None
        """
        dept_agents = self.hierarchy.get_department_agents(department)
        eligible = [a for a in dept_agents if a.rank >= min_rank]

        if not eligible:
            return None

        # Score by specialty match
        task_lower = task.lower()
        scored = []
        for agent in eligible:
            score = sum(1 for s in agent.specialties if s.lower() in task_lower)
            # Bonus for higher rank
            score += agent.rank.value * 0.1
            scored.append((agent, score))

        scored.sort(key=lambda x: -x[1])
        return scored[0][0] if scored else None

    def escalate(self, agent_name: str) -> Optional[AgentProfile]:
        """Escalate task to the supervisor of an agent."""
        return self.hierarchy.get_supervisor(agent_name)

    def delegate_down(self, agent_name: str, task: str) -> Optional[AgentProfile]:
        """Delegate task to a subordinate of an agent."""
        subordinates = self.hierarchy.get_subordinates(agent_name)
        if not subordinates:
            return None

        # Find best matching subordinate
        task_lower = task.lower()
        scored = []
        for sub in subordinates:
            score = sum(1 for s in sub.specialties if s.lower() in task_lower)
            scored.append((sub, score))

        scored.sort(key=lambda x: -x[1])
        return scored[0][0] if scored else subordinates[0]

    def find_expert(self, specialty: str) -> List[AgentProfile]:
        """Find agents with a specific specialty."""
        return self.hierarchy.find_by_specialty(specialty)

    def get_org_chart(self) -> Dict[str, Any]:
        """Get the organizational chart."""
        return self.hierarchy.get_org_chart()

    def print_hierarchy(self) -> str:
        """Print the agent hierarchy."""
        return self.hierarchy.print_org_chart()

    # === SCRAPER COORDINATION METHODS ===

    def setup_coordinator(
        self,
        max_global_connections: int = 6,
        dns_providers: Optional[List[str]] = None,
        scraper_slots: Optional[Dict[str, int]] = None
    ) -> ScrapingCoordinator:
        """
        Setup the scraping coordinator with DNS protection.

        Args:
            max_global_connections: Maximum total connections across all scrapers
            dns_providers: List of DNS servers to use (defaults to Cloudflare, Google, Quad9, OpenDNS)
            scraper_slots: Dict mapping scraper name to max concurrent slots

        Returns:
            Configured ScrapingCoordinator

        Example:
            orchestrator.setup_coordinator(
                max_global_connections=6,
                scraper_slots={"cochesnet": 3, "autocasion": 2, "ocasionplus": 1}
            )
        """
        config = CoordinatorConfig(
            max_global_connections=max_global_connections,
            dns_providers=dns_providers or [
                "1.1.1.1",        # Cloudflare
                "8.8.8.8",        # Google
                "9.9.9.9",        # Quad9
                "208.67.222.222"  # OpenDNS
            ],
            scraper_defaults=scraper_slots or {
                "cochesnet": 3,
                "autocasion": 2,
                "ocasionplus": 1
            }
        )

        self._coordinator = ScrapingCoordinator(config)

        # Register scrapers from config
        for name, slots in config.scraper_defaults.items():
            self._coordinator.register_scraper(name, slots)

        self._debug.info("orchestrator", "Coordinator setup complete", {
            "max_connections": max_global_connections,
            "scrapers": list(config.scraper_defaults.keys())
        })

        return self._coordinator

    @property
    def coordinator(self) -> Optional[ScrapingCoordinator]:
        """Get the scraping coordinator."""
        return self._coordinator

    async def coordinate_scrapers(
        self,
        scrapers: List[str],
        scraper_funcs: Dict[str, Callable[[], Awaitable[Any]]],
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute multiple scrapers in a coordinated manner with DNS protection.

        Args:
            scrapers: List of scraper names to run
            scraper_funcs: Dict mapping scraper name to async function to execute
            config: Optional configuration overrides

        Returns:
            Dict with results from each scraper

        Example:
            results = await orchestrator.coordinate_scrapers(
                scrapers=["cochesnet", "autocasion", "ocasionplus"],
                scraper_funcs={
                    "cochesnet": lambda: coches_scraper.run(),
                    "autocasion": lambda: auto_scraper.run(),
                    "ocasionplus": lambda: ocasion_scraper.run()
                }
            )
        """
        if not self._coordinator:
            self.setup_coordinator()

        start_time = time.time()
        self._debug.info("orchestrator", f"Starting coordinated scrape of {len(scrapers)} scrapers")

        # Start DNS monitoring
        await self._coordinator.start_monitoring()

        results = {}
        errors = {}

        try:
            # Create tasks for each scraper
            async def run_scraper(name: str) -> Tuple[str, Any]:
                if name not in scraper_funcs:
                    return (name, {"error": f"No function provided for {name}"})

                try:
                    self._debug.info("orchestrator", f"Starting scraper: {name}")
                    result = await scraper_funcs[name]()
                    self._debug.info("orchestrator", f"Scraper {name} completed")
                    return (name, result)
                except Exception as e:
                    self._debug.error("orchestrator", f"Scraper {name} failed: {e}")
                    return (name, {"error": str(e)})

            # Run all scrapers concurrently (coordinator handles limits)
            tasks = [run_scraper(name) for name in scrapers]
            task_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            for item in task_results:
                if isinstance(item, Exception):
                    errors["unknown"] = str(item)
                else:
                    name, result = item
                    if isinstance(result, dict) and "error" in result:
                        errors[name] = result["error"]
                    else:
                        results[name] = result

        finally:
            await self._coordinator.stop_monitoring()

        duration = time.time() - start_time

        return {
            "success": len(errors) == 0,
            "duration_seconds": duration,
            "results": results,
            "errors": errors,
            "coordinator_stats": self._coordinator.get_stats()
        }

    def get_dns_status(self) -> Optional[DNSHealthStatus]:
        """Get current DNS health status."""
        if self._coordinator:
            return self._coordinator.dns_status
        return None

    def get_coordinator_stats(self) -> Optional[Dict]:
        """Get coordinator statistics."""
        if self._coordinator:
            return self._coordinator.get_stats()
        return None

    async def close_coordinator(self):
        """Clean up coordinator resources."""
        if self._coordinator:
            await self._coordinator.close()
            self._coordinator = None


# Convenience function for quick usage
async def orchestrate(task: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
    """Quick function to orchestrate a task."""
    orchestrator = OrchestratorAgent()
    orchestrator.initialize()
    return await orchestrator.route(task, context)
