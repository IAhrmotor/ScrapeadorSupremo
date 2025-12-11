"""Agent registry for discovering and managing agents."""

import importlib
import pkgutil
from pathlib import Path
from typing import Dict, List, Optional, Type
from .base_agent import BaseAgent


class AgentRegistry:
    """Registry that discovers and manages all available agents."""

    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}

    def register(self, agent: BaseAgent) -> None:
        """Register an agent instance."""
        self._agents[agent.name] = agent

    def unregister(self, name: str) -> bool:
        """Unregister an agent by name."""
        if name in self._agents:
            del self._agents[name]
            return True
        return False

    def get_agent(self, name: str) -> Optional[BaseAgent]:
        """Get a specific agent by name."""
        return self._agents.get(name)

    def list_agents(self) -> List[BaseAgent]:
        """List all registered agents."""
        return list(self._agents.values())

    def discover_agents(self, package_path: str = "agents") -> List[BaseAgent]:
        """
        Auto-discover agents from the agents package.

        Scans all Python modules in the agents directory and registers
        any class that inherits from BaseAgent.
        """
        discovered = []
        agents_dir = Path(__file__).parent

        for module_info in pkgutil.iter_modules([str(agents_dir)]):
            if module_info.name in ("base_agent", "registry", "orchestrator", "__init__"):
                continue

            try:
                module = importlib.import_module(f".{module_info.name}", package="agents")

                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (
                        isinstance(attr, type)
                        and issubclass(attr, BaseAgent)
                        and attr is not BaseAgent
                    ):
                        # Instantiate and register the agent
                        agent_instance = attr()
                        self.register(agent_instance)
                        discovered.append(agent_instance)

            except Exception as e:
                print(f"Error loading agent from {module_info.name}: {e}")

        return discovered

    def __len__(self) -> int:
        return len(self._agents)

    def __iter__(self):
        return iter(self._agents.values())


# Global registry instance
_global_registry: Optional[AgentRegistry] = None


def get_registry() -> AgentRegistry:
    """Get the global agent registry."""
    global _global_registry
    if _global_registry is None:
        _global_registry = AgentRegistry()
    return _global_registry
