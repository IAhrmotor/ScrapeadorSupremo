"""Agent hierarchy system with departments and ranks."""

from enum import Enum, IntEnum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


class Rank(IntEnum):
    """Agent ranks - higher value = more authority."""
    JUNIOR = 1      # Tareas simples, ejecución directa
    SENIOR = 2      # Tareas complejas, puede supervisar juniors
    LEAD = 3        # Lidera equipo, toma decisiones técnicas
    ARCHITECT = 4   # Diseña sistemas, decisiones de arquitectura
    DIRECTOR = 5    # Dirige departamento, estrategia


class Department(str, Enum):
    """Departments that group agents by function."""
    IA = "departamento_ia"
    DESARROLLO = "departamento_desarrollo"
    CALIDAD = "departamento_calidad"
    DOCUMENTACION = "departamento_documentacion"
    OPERACIONES = "departamento_operaciones"
    DATOS = "departamento_datos"


@dataclass
class AgentProfile:
    """Complete profile for an agent including hierarchy info."""
    name: str
    department: Department
    rank: Rank
    description: str
    specialties: List[str]
    tools: List[str] = field(default_factory=list)
    model: str = "sonnet"
    reports_to: Optional[str] = None  # Name of supervisor agent
    subordinates: List[str] = field(default_factory=list)

    @property
    def full_id(self) -> str:
        """Return full hierarchical ID."""
        return f"{self.department.value}/{self.name}"

    @property
    def authority_level(self) -> int:
        """Return numeric authority level."""
        return self.rank.value


# Predefined agent profiles based on the templates
AGENT_PROFILES: Dict[str, AgentProfile] = {
    # === DEPARTAMENTO IA ===
    "prompt-engineer": AgentProfile(
        name="prompt-engineer",
        department=Department.IA,
        rank=Rank.ARCHITECT,
        description="Expert prompt optimization for LLMs and AI systems",
        specialties=["prompt optimization", "chain-of-thought", "few-shot learning"],
        tools=["Read", "Write", "Edit"],
        model="opus",
        subordinates=["task-decomposition-expert"]
    ),
    "ai-engineer": AgentProfile(
        name="ai-engineer",
        department=Department.IA,
        rank=Rank.LEAD,
        description="LLM application and RAG system specialist",
        specialties=["LLM integration", "RAG systems", "vector databases", "embeddings"],
        tools=["Read", "Write", "Edit", "Bash"],
        model="opus",
        reports_to="prompt-engineer"
    ),
    "task-decomposition-expert": AgentProfile(
        name="task-decomposition-expert",
        department=Department.IA,
        rank=Rank.SENIOR,
        description="Complex goal breakdown and workflow architecture",
        specialties=["task decomposition", "workflow design", "ChromaDB"],
        tools=["Read", "Write"],
        model="sonnet",
        reports_to="prompt-engineer"
    ),

    # === DEPARTAMENTO DESARROLLO ===
    "backend-architect": AgentProfile(
        name="backend-architect",
        department=Department.DESARROLLO,
        rank=Rank.ARCHITECT,
        description="Backend system architecture and API design",
        specialties=["REST APIs", "microservices", "database design", "scalability"],
        tools=["Read", "Write", "Edit", "Bash"],
        model="sonnet",
        subordinates=["python-pro", "javascript-pro"]
    ),
    "frontend-developer": AgentProfile(
        name="frontend-developer",
        department=Department.DESARROLLO,
        rank=Rank.SENIOR,
        description="React applications and responsive design",
        specialties=["React", "CSS", "state management", "accessibility"],
        tools=["Read", "Write", "Edit", "Bash"],
        model="sonnet",
        reports_to="backend-architect"
    ),
    "python-pro": AgentProfile(
        name="python-pro",
        department=Department.DESARROLLO,
        rank=Rank.SENIOR,
        description="Advanced Python with async and testing",
        specialties=["Python", "async/await", "pytest", "type hints"],
        tools=["Read", "Write", "Edit", "Bash"],
        model="sonnet",
        reports_to="backend-architect"
    ),
    "javascript-pro": AgentProfile(
        name="javascript-pro",
        department=Department.DESARROLLO,
        rank=Rank.SENIOR,
        description="Modern JavaScript and Node.js",
        specialties=["ES6+", "async patterns", "Node.js", "TypeScript"],
        tools=["Read", "Write", "Edit", "Bash"],
        model="sonnet",
        reports_to="backend-architect"
    ),

    # === DEPARTAMENTO CALIDAD ===
    "code-reviewer": AgentProfile(
        name="code-reviewer",
        department=Department.CALIDAD,
        rank=Rank.LEAD,
        description="Code review for quality and security",
        specialties=["code review", "security", "best practices"],
        tools=["Read", "Write", "Edit", "Bash", "Grep"],
        model="sonnet",
        subordinates=["error-detective", "test-writer"],
        reports_to="qa-architect"
    ),
    "error-detective": AgentProfile(
        name="error-detective",
        department=Department.CALIDAD,
        rank=Rank.SENIOR,
        description="Log analysis and error pattern detection",
        specialties=["log analysis", "debugging", "error patterns"],
        tools=["Read", "Write", "Edit", "Bash", "Grep"],
        model="sonnet",
        reports_to="code-reviewer"
    ),

    # === DEPARTAMENTO DOCUMENTACION ===
    "doc-architect": AgentProfile(
        name="doc-architect",
        department=Department.DOCUMENTACION,
        rank=Rank.ARCHITECT,
        description="Documentation strategy and architecture",
        specialties=["documentation architecture", "technical writing", "knowledge management"],
        tools=["Read", "Write", "Edit"],
        model="sonnet",
        subordinates=["api-documenter", "readme-writer"]
    ),
    "api-documenter": AgentProfile(
        name="api-documenter",
        department=Department.DOCUMENTACION,
        rank=Rank.SENIOR,
        description="OpenAPI specs and developer documentation",
        specialties=["OpenAPI", "SDK generation", "developer docs"],
        tools=["Read", "Write", "Edit", "Bash"],
        model="haiku",
        reports_to="doc-architect"
    ),
    "readme-writer": AgentProfile(
        name="readme-writer",
        department=Department.DOCUMENTACION,
        rank=Rank.JUNIOR,
        description="README and basic documentation writer",
        specialties=["README", "markdown", "basic docs"],
        tools=["Read", "Write"],
        model="haiku",
        reports_to="doc-architect"
    ),

    # === DEPARTAMENTO CALIDAD (completar) ===
    "qa-architect": AgentProfile(
        name="qa-architect",
        department=Department.CALIDAD,
        rank=Rank.ARCHITECT,
        description="Quality assurance architecture and testing strategy",
        specialties=["test architecture", "QA strategy", "CI/CD quality"],
        tools=["Read", "Write", "Edit", "Bash"],
        model="sonnet",
        subordinates=["code-reviewer", "test-writer"]
    ),
    "test-writer": AgentProfile(
        name="test-writer",
        department=Department.CALIDAD,
        rank=Rank.JUNIOR,
        description="Write unit tests and test cases",
        specialties=["unit tests", "pytest", "test cases"],
        tools=["Read", "Write", "Edit"],
        model="haiku",
        reports_to="code-reviewer"
    ),

    # === DEPARTAMENTO OPERACIONES ===
    "devops-architect": AgentProfile(
        name="devops-architect",
        department=Department.OPERACIONES,
        rank=Rank.ARCHITECT,
        description="DevOps and infrastructure architecture",
        specialties=["DevOps", "CI/CD", "infrastructure", "Docker", "Kubernetes"],
        tools=["Read", "Write", "Edit", "Bash"],
        model="sonnet",
        subordinates=["deploy-engineer", "monitor-agent"]
    ),
    "deploy-engineer": AgentProfile(
        name="deploy-engineer",
        department=Department.OPERACIONES,
        rank=Rank.SENIOR,
        description="Deployment and release management",
        specialties=["deployment", "releases", "Docker", "cloud"],
        tools=["Read", "Write", "Edit", "Bash"],
        model="sonnet",
        reports_to="devops-architect"
    ),
    "monitor-agent": AgentProfile(
        name="monitor-agent",
        department=Department.OPERACIONES,
        rank=Rank.JUNIOR,
        description="System monitoring and alerting",
        specialties=["monitoring", "alerts", "logs", "metrics"],
        tools=["Read", "Bash", "Grep"],
        model="haiku",
        reports_to="devops-architect"
    ),

    # === DEPARTAMENTO DATOS ===
    "data-architect": AgentProfile(
        name="data-architect",
        department=Department.DATOS,
        rank=Rank.ARCHITECT,
        description="Data architecture and pipeline design",
        specialties=["data architecture", "ETL", "data modeling", "databases"],
        tools=["Read", "Write", "Edit", "Bash"],
        model="sonnet",
        subordinates=["data-engineer", "scraper-specialist", "supabase-engineer"]
    ),
    "data-engineer": AgentProfile(
        name="data-engineer",
        department=Department.DATOS,
        rank=Rank.SENIOR,
        description="Data pipelines and transformations",
        specialties=["data pipelines", "ETL", "pandas", "SQL"],
        tools=["Read", "Write", "Edit", "Bash"],
        model="sonnet",
        reports_to="data-architect"
    ),
    "scraper-specialist": AgentProfile(
        name="scraper-specialist",
        department=Department.DATOS,
        rank=Rank.SENIOR,
        description="Web scraping and data extraction specialist",
        specialties=["web scraping", "HeadlessX", "anti-detection", "data extraction"],
        tools=["Read", "Write", "Edit", "Bash"],
        model="sonnet",
        reports_to="data-architect",
        subordinates=["cochesnet-scraper", "autocasion-scraper"]
    ),
    "cochesnet-scraper": AgentProfile(
        name="cochesnet-scraper",
        department=Department.DATOS,
        rank=Rank.JUNIOR,
        description="Coches.net scraping specialist",
        specialties=["coches.net", "car listings", "HeadlessX", "__INITIAL_PROPS__ parsing"],
        tools=["Read", "Write", "Bash"],
        model="haiku",
        reports_to="scraper-specialist"
    ),
    "autocasion-scraper": AgentProfile(
        name="autocasion-scraper",
        department=Department.DATOS,
        rank=Rank.JUNIOR,
        description="Autocasion.com scraping specialist",
        specialties=["autocasion.com", "car listings", "HeadlessX", "JSON-LD parsing"],
        tools=["Read", "Write", "Bash"],
        model="haiku",
        reports_to="scraper-specialist"
    ),
    "supabase-engineer": AgentProfile(
        name="supabase-engineer",
        department=Department.DATOS,
        rank=Rank.SENIOR,
        description="Supabase database and backend services specialist",
        specialties=["Supabase", "PostgreSQL", "RLS policies", "Edge Functions", "Realtime"],
        tools=["Read", "Write", "Edit", "Bash"],
        model="sonnet",
        reports_to="data-architect"
    ),
    "data-cleaner": AgentProfile(
        name="data-cleaner",
        department=Department.DATOS,
        rank=Rank.JUNIOR,
        description="Data cleaning and validation",
        specialties=["data cleaning", "validation", "normalization"],
        tools=["Read", "Write"],
        model="haiku",
        reports_to="data-engineer"
    ),

    # === JUNIORS ADICIONALES ===
    "prompt-assistant": AgentProfile(
        name="prompt-assistant",
        department=Department.IA,
        rank=Rank.JUNIOR,
        description="Basic prompt writing and formatting",
        specialties=["prompt formatting", "template filling", "basic prompts"],
        tools=["Read", "Write"],
        model="haiku",
        reports_to="task-decomposition-expert"
    ),
    "code-formatter": AgentProfile(
        name="code-formatter",
        department=Department.DESARROLLO,
        rank=Rank.JUNIOR,
        description="Code formatting and style fixes",
        specialties=["formatting", "linting", "style"],
        tools=["Read", "Write", "Edit"],
        model="haiku",
        reports_to="python-pro"
    ),
}


class AgentHierarchy:
    """Manages the organizational hierarchy of agents."""

    def __init__(self):
        self.profiles = AGENT_PROFILES.copy()
        self._department_heads: Dict[Department, str] = {}
        self._build_hierarchy()

    def _build_hierarchy(self) -> None:
        """Build department head mappings."""
        for name, profile in self.profiles.items():
            if profile.rank >= Rank.ARCHITECT:
                if profile.department not in self._department_heads:
                    self._department_heads[profile.department] = name

    def get_agent(self, name: str) -> Optional[AgentProfile]:
        """Get agent profile by name."""
        return self.profiles.get(name)

    def get_department_agents(self, department: Department) -> List[AgentProfile]:
        """Get all agents in a department."""
        return [p for p in self.profiles.values() if p.department == department]

    def get_department_head(self, department: Department) -> Optional[AgentProfile]:
        """Get the head of a department."""
        head_name = self._department_heads.get(department)
        return self.profiles.get(head_name) if head_name else None

    def get_by_rank(self, rank: Rank) -> List[AgentProfile]:
        """Get all agents of a specific rank."""
        return [p for p in self.profiles.values() if p.rank == rank]

    def get_subordinates(self, name: str) -> List[AgentProfile]:
        """Get all subordinates of an agent."""
        profile = self.profiles.get(name)
        if not profile:
            return []
        return [self.profiles[sub] for sub in profile.subordinates if sub in self.profiles]

    def get_supervisor(self, name: str) -> Optional[AgentProfile]:
        """Get the supervisor of an agent."""
        profile = self.profiles.get(name)
        if not profile or not profile.reports_to:
            return None
        return self.profiles.get(profile.reports_to)

    def get_chain_of_command(self, name: str) -> List[AgentProfile]:
        """Get the full chain of command above an agent."""
        chain = []
        current = self.get_supervisor(name)
        while current:
            chain.append(current)
            current = self.get_supervisor(current.name)
        return chain

    def find_by_specialty(self, specialty: str) -> List[AgentProfile]:
        """Find agents with a specific specialty."""
        specialty_lower = specialty.lower()
        return [
            p for p in self.profiles.values()
            if any(specialty_lower in s.lower() for s in p.specialties)
        ]

    def get_org_chart(self) -> Dict[str, Any]:
        """Generate organizational chart structure."""
        chart = {}
        for dept in Department:
            dept_agents = self.get_department_agents(dept)
            if dept_agents:
                chart[dept.value] = {
                    "head": self._department_heads.get(dept),
                    "agents": [
                        {
                            "name": a.name,
                            "rank": a.rank.name,
                            "reports_to": a.reports_to
                        }
                        for a in sorted(dept_agents, key=lambda x: -x.rank.value)
                    ]
                }
        return chart

    def register_agent(self, profile: AgentProfile) -> None:
        """Register a new agent profile."""
        self.profiles[profile.name] = profile
        self._build_hierarchy()

    def print_org_chart(self) -> str:
        """Return a formatted org chart string."""
        lines = ["=" * 60, "ORGANIGRAMA DE AGENTES", "=" * 60, ""]

        for dept in Department:
            agents = self.get_department_agents(dept)
            if not agents:
                continue

            lines.append(f"\n[{dept.name}]")
            lines.append("-" * 40)

            # Sort by rank descending
            for agent in sorted(agents, key=lambda x: -x.rank.value):
                indent = "  " * (Rank.DIRECTOR - agent.rank)
                rank_badge = f"[{agent.rank.name}]"
                lines.append(f"{indent}{rank_badge} {agent.name}")
                lines.append(f"{indent}  -> {agent.description[:50]}...")

        return "\n".join(lines)


# Global hierarchy instance
_hierarchy: Optional[AgentHierarchy] = None

def get_hierarchy() -> AgentHierarchy:
    """Get the global agent hierarchy."""
    global _hierarchy
    if _hierarchy is None:
        _hierarchy = AgentHierarchy()
    return _hierarchy
