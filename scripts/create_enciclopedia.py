"""Script to create Enciclopedia documentation in Obsidian."""

import httpx

OBSIDIAN_HOST = "https://127.0.0.1:27124"
API_KEY = "524c3217ec428edff081b6956d64ae2169bde68ade7814af8ab1fb12a0ffdd90"

client = httpx.Client(verify=False, timeout=30.0)
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "text/markdown"
}


def create_note(path: str, content: str) -> int:
    """Create or update a note in Obsidian."""
    resp = client.put(
        f"{OBSIDIAN_HOST}/vault/{path}",
        headers=headers,
        content=content.encode("utf-8")
    )
    return resp.status_code


# ============================================
# INDICE PRINCIPAL DE LA ENCICLOPEDIA
# ============================================
INDEX = """# Enciclopedia ScrapeadorSupremo

Glosario completo de conceptos, clases y patrones del proyecto.

## Por Categoria

### Agentes
- [[Enciclopedia/AgentCapability|AgentCapability]]
- [[Enciclopedia/AgentHierarchy|AgentHierarchy]]
- [[Enciclopedia/AgentProfile|AgentProfile]]
- [[Enciclopedia/AgentResponse|AgentResponse]]
- [[Enciclopedia/BaseAgent|BaseAgent]]
- [[Enciclopedia/Department|Department]]
- [[Enciclopedia/OrchestratorAgent|OrchestratorAgent]]
- [[Enciclopedia/Rank|Rank]]
- [[Enciclopedia/Registry|Registry]]

### Scraping
- [[Enciclopedia/BaseSite|BaseSite]]
- [[Enciclopedia/BaseParser|BaseParser]]
- [[Enciclopedia/CarListing|CarListing]]
- [[Enciclopedia/HeadlessX|HeadlessX]]
- [[Enciclopedia/SiteConfig|SiteConfig]]
- [[Enciclopedia/SiteRegistry|SiteRegistry]]

### Sitios Soportados
- [[Enciclopedia/CochesNet|Coches.net]]
- [[Enciclopedia/Autocasion|Autocasion]]
- [[Enciclopedia/Clicars|Clicars]]

### Debug y Utilidades
- [[Enciclopedia/Debug|Debug]]
- [[Enciclopedia/DebugLevel|DebugLevel]]
- [[Enciclopedia/FlowEntry|FlowEntry]]
- [[Enciclopedia/ExecutionContext|ExecutionContext]]
- [[Enciclopedia/debug_flow|@debug_flow]]

### Base de Datos
- [[Enciclopedia/SupabaseClient|SupabaseClient]]
- [[Enciclopedia/Upsert|Upsert]]
- [[Enciclopedia/Objetivos|Tablas de Objetivos]]

### Patrones de Diseno
- [[Enciclopedia/Singleton|Singleton]]
- [[Enciclopedia/AbstractFactory|Abstract Factory]]
- [[Enciclopedia/Strategy|Strategy]]
- [[Enciclopedia/ChainOfResponsibility|Chain of Responsibility]]

## Indice Alfabetico

| A-D | E-O | P-Z |
|-----|-----|-----|
| [[Enciclopedia/AbstractFactory|Abstract Factory]] | [[Enciclopedia/ExecutionContext|ExecutionContext]] | [[Enciclopedia/Rank|Rank]] |
| [[Enciclopedia/AgentCapability|AgentCapability]] | [[Enciclopedia/FlowEntry|FlowEntry]] | [[Enciclopedia/Registry|Registry]] |
| [[Enciclopedia/AgentHierarchy|AgentHierarchy]] | [[Enciclopedia/HeadlessX|HeadlessX]] | [[Enciclopedia/Singleton|Singleton]] |
| [[Enciclopedia/AgentProfile|AgentProfile]] | [[Enciclopedia/Objetivos|Objetivos]] | [[Enciclopedia/SiteConfig|SiteConfig]] |
| [[Enciclopedia/AgentResponse|AgentResponse]] | [[Enciclopedia/OrchestratorAgent|OrchestratorAgent]] | [[Enciclopedia/SiteRegistry|SiteRegistry]] |
| [[Enciclopedia/Autocasion|Autocasion]] | | [[Enciclopedia/Strategy|Strategy]] |
| [[Enciclopedia/BaseAgent|BaseAgent]] | | [[Enciclopedia/SupabaseClient|SupabaseClient]] |
| [[Enciclopedia/BaseParser|BaseParser]] | | [[Enciclopedia/Upsert|Upsert]] |
| [[Enciclopedia/BaseSite|BaseSite]] | | |
| [[Enciclopedia/CarListing|CarListing]] | | |
| [[Enciclopedia/ChainOfResponsibility|Chain of Responsibility]] | | |
| [[Enciclopedia/Clicars|Clicars]] | | |
| [[Enciclopedia/CochesNet|Coches.net]] | | |
| [[Enciclopedia/Debug|Debug]] | | |
| [[Enciclopedia/DebugLevel|DebugLevel]] | | |
| [[Enciclopedia/debug_flow|@debug_flow]] | | |
| [[Enciclopedia/Department|Department]] | | |

## Tags

#enciclopedia #glosario #referencia
"""

# ============================================
# CONCEPTOS DE AGENTES
# ============================================

AGENT_CAPABILITY = """# AgentCapability

[[Enciclopedia/Enciclopedia|← Volver a Enciclopedia]]

## Definicion

Dataclass que describe una capacidad especifica de un agente.

## Ubicacion

`agents/base_agent.py`

## Estructura

```python
@dataclass
class AgentCapability:
    name: str           # Nombre de la capacidad
    description: str    # Descripcion de que hace
    keywords: list[str] # Palabras clave para matching
    priority: int = 0   # Mayor prioridad = preferido
```

## Uso

```python
capability = AgentCapability(
    name="web_scraping",
    description="Extract data from websites",
    keywords=["scrape", "extract", "crawl", "fetch"],
    priority=10
)
```

## Proposito

- Permite al [[Enciclopedia/OrchestratorAgent|Orchestrator]] determinar que agente puede manejar una tarea
- Los `keywords` se usan para matching con la descripcion de la tarea
- El `priority` resuelve empates entre agentes

## Relacionado

- [[Enciclopedia/BaseAgent|BaseAgent]] - Clase que usa AgentCapability
- [[Enciclopedia/OrchestratorAgent|OrchestratorAgent]] - Quien evalua las capacidades

## Tags

#agentes #dataclass #capacidades
"""

AGENT_HIERARCHY = """# AgentHierarchy

[[Enciclopedia/Enciclopedia|← Volver a Enciclopedia]]

## Definicion

Clase que gestiona la organizacion jerarquica de todos los agentes.

## Ubicacion

`agents/hierarchy.py`

## Metodos Principales

| Metodo | Descripcion |
|--------|-------------|
| `get_agent(name)` | Obtener perfil por nombre |
| `get_department_agents(dept)` | Agentes de un departamento |
| `get_department_head(dept)` | Jefe del departamento |
| `get_by_rank(rank)` | Agentes de un rango |
| `get_subordinates(name)` | Subordinados de un agente |
| `get_supervisor(name)` | Supervisor de un agente |
| `get_chain_of_command(name)` | Cadena hasta el director |
| `find_by_specialty(spec)` | Buscar por especialidad |
| `get_org_chart()` | Organigrama completo |

## Uso

```python
from agents.hierarchy import get_hierarchy

hierarchy = get_hierarchy()

# Obtener agente
agent = hierarchy.get_agent("python-pro")

# Cadena de mando
chain = hierarchy.get_chain_of_command("python-pro")
# [backend-architect]

# Buscar expertos
experts = hierarchy.find_by_specialty("scraping")
```

## Singleton

La funcion `get_hierarchy()` retorna siempre la misma instancia.

## Relacionado

- [[Enciclopedia/AgentProfile|AgentProfile]] - Perfiles que gestiona
- [[Enciclopedia/Department|Department]] - Departamentos
- [[Enciclopedia/Rank|Rank]] - Rangos

## Tags

#agentes #jerarquia #singleton
"""

AGENT_PROFILE = """# AgentProfile

[[Enciclopedia/Enciclopedia|← Volver a Enciclopedia]]

## Definicion

Dataclass que contiene toda la informacion de un agente en la jerarquia.

## Ubicacion

`agents/hierarchy.py`

## Estructura

```python
@dataclass
class AgentProfile:
    name: str                    # Identificador unico
    department: Department       # Departamento al que pertenece
    rank: Rank                   # Rango en la jerarquia
    description: str             # Descripcion del rol
    specialties: List[str]       # Especialidades
    tools: List[str] = []        # Herramientas disponibles
    model: str = "sonnet"        # Modelo LLM a usar
    reports_to: Optional[str]    # Nombre del supervisor
    subordinates: List[str] = [] # Nombres de subordinados
```

## Propiedades

| Propiedad | Tipo | Descripcion |
|-----------|------|-------------|
| `full_id` | str | `"{department}/{name}"` |
| `authority_level` | int | Valor numerico del rango |

## Ejemplo

```python
profile = AgentProfile(
    name="python-pro",
    department=Department.DESARROLLO,
    rank=Rank.SENIOR,
    description="Advanced Python with async and testing",
    specialties=["Python", "async/await", "pytest"],
    tools=["Read", "Write", "Edit", "Bash"],
    model="sonnet",
    reports_to="backend-architect"
)
```

## Los 22 Agentes Definidos

El sistema define 22 perfiles predefinidos en `AGENT_PROFILES`.

## Relacionado

- [[Enciclopedia/Department|Department]] - Enum de departamentos
- [[Enciclopedia/Rank|Rank]] - Enum de rangos
- [[Enciclopedia/AgentHierarchy|AgentHierarchy]] - Quien gestiona los perfiles

## Tags

#agentes #dataclass #perfil
"""

AGENT_RESPONSE = """# AgentResponse

[[Enciclopedia/Enciclopedia|← Volver a Enciclopedia]]

## Definicion

Dataclass que representa la respuesta estandar de cualquier agente.

## Ubicacion

`agents/base_agent.py`

## Estructura

```python
@dataclass
class AgentResponse:
    success: bool                      # Si la tarea fue exitosa
    result: Any                        # Resultado de la tarea
    message: str                       # Mensaje descriptivo
    metadata: Optional[Dict[str, Any]] # Datos adicionales
```

## Uso

```python
# Respuesta exitosa
response = AgentResponse(
    success=True,
    result={"scraped": 150, "pages": 5},
    message="Scraping completed successfully",
    metadata={"duration_seconds": 45.2}
)

# Respuesta de error
response = AgentResponse(
    success=False,
    result=None,
    message="Failed to connect to target site"
)
```

## Convencion

- `success=True`: La tarea se completo correctamente
- `success=False`: Hubo un error o no se pudo completar
- `result`: Contiene los datos si `success=True`
- `message`: Siempre debe ser descriptivo

## Relacionado

- [[Enciclopedia/BaseAgent|BaseAgent]] - Metodo `execute()` retorna esto
- [[Enciclopedia/OrchestratorAgent|OrchestratorAgent]] - Propaga estas respuestas

## Tags

#agentes #dataclass #respuesta
"""

BASE_AGENT = """# BaseAgent

[[Enciclopedia/Enciclopedia|← Volver a Enciclopedia]]

## Definicion

Clase base abstracta (ABC) que define la interfaz para todos los agentes runtime.

## Ubicacion

`agents/base_agent.py`

## Interfaz

```python
class BaseAgent(ABC):
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    def get_capabilities(self) -> list[AgentCapability]:
        \"\"\"Retorna lista de capacidades.\"\"\"
        pass

    @abstractmethod
    def can_handle(self, task: str, context: Dict = None) -> float:
        \"\"\"Score de 0.0 a 1.0 indicando confianza.\"\"\"
        pass

    @abstractmethod
    async def execute(self, task: str, context: Dict = None) -> AgentResponse:
        \"\"\"Ejecuta la tarea y retorna resultado.\"\"\"
        pass
```

## Implementacion

```python
class ScraperAgent(BaseAgent):
    def __init__(self):
        super().__init__("scraper", "Web scraping agent")

    def get_capabilities(self):
        return [
            AgentCapability(
                name="scraping",
                description="Extract data from websites",
                keywords=["scrape", "extract", "crawl"]
            )
        ]

    def can_handle(self, task, context=None):
        keywords = ["scrape", "extract", "fetch"]
        return 0.8 if any(k in task.lower() for k in keywords) else 0.0

    async def execute(self, task, context=None):
        # ... implementacion
        return AgentResponse(success=True, result=data, message="Done")
```

## Metodo `can_handle`

El score de confianza determina si el agente deberia manejar la tarea:

| Score | Significado |
|-------|-------------|
| 0.0 | No puede manejar |
| 0.1-0.3 | Puede intentar pero no es ideal |
| 0.4-0.6 | Match moderado |
| 0.7-0.9 | Buen match |
| 1.0 | Match perfecto |

## Relacionado

- [[Enciclopedia/AgentCapability|AgentCapability]] - Define capacidades
- [[Enciclopedia/AgentResponse|AgentResponse]] - Tipo de retorno
- [[Enciclopedia/Registry|Registry]] - Donde se registran

## Tags

#agentes #abc #interfaz
"""

DEPARTMENT = """# Department

[[Enciclopedia/Enciclopedia|← Volver a Enciclopedia]]

## Definicion

Enum que define los departamentos organizacionales del sistema.

## Ubicacion

`agents/hierarchy.py`

## Valores

```python
class Department(str, Enum):
    IA = "departamento_ia"
    DESARROLLO = "departamento_desarrollo"
    CALIDAD = "departamento_calidad"
    DOCUMENTACION = "departamento_documentacion"
    OPERACIONES = "departamento_operaciones"
    DATOS = "departamento_datos"
```

## Descripcion de Departamentos

| Departamento | Responsabilidad | Jefe |
|--------------|-----------------|------|
| IA | Prompts, LLMs, RAG | prompt-engineer |
| DESARROLLO | Codigo, APIs, Frontend | backend-architect |
| CALIDAD | Testing, Reviews | qa-architect |
| DOCUMENTACION | Docs, OpenAPI | doc-architect |
| OPERACIONES | DevOps, Deploy | devops-architect |
| DATOS | Data, Scraping, DB | data-architect |

## Uso

```python
from agents.hierarchy import Department, get_hierarchy

# Obtener agentes de un departamento
hierarchy = get_hierarchy()
datos_team = hierarchy.get_department_agents(Department.DATOS)

# Obtener jefe
jefe = hierarchy.get_department_head(Department.DATOS)
# -> AgentProfile(name="data-architect", ...)
```

## Herencia de str

Al heredar de `str`, el enum se puede usar directamente como string:

```python
print(Department.DATOS)  # "departamento_datos"
```

## Relacionado

- [[Enciclopedia/Rank|Rank]] - Rangos dentro de departamentos
- [[Enciclopedia/AgentProfile|AgentProfile]] - Tiene campo department
- [[Enciclopedia/AgentHierarchy|AgentHierarchy]] - Organiza por departamento

## Tags

#agentes #enum #organizacion
"""

ORCHESTRATOR = """# OrchestratorAgent

[[Enciclopedia/Enciclopedia|← Volver a Enciclopedia]]

## Definicion

El agente maestro que identifica, evalua y rutea tareas a los agentes especializados.

## Ubicacion

`agents/orchestrator.py`

## Responsabilidades

1. Descubrir agentes disponibles
2. Analizar tareas entrantes
3. Evaluar (score) cada agente para la tarea
4. Delegar al agente mas apropiado
5. Manejar fallbacks y errores

## Metodos Principales

### Inicializacion y Descubrimiento

```python
orchestrator = OrchestratorAgent()
num_agents = orchestrator.initialize()  # Descubre agentes
agents = orchestrator.list_available_agents()
```

### Ruteo de Tareas

```python
# Seleccionar mejor agente
agent, confidence = orchestrator.select_agent(task)

# Rutear y ejecutar
response = await orchestrator.route(task, context, min_confidence=0.1)

# Rutear con fallback automatico
response = await orchestrator.route_with_fallback(task, max_attempts=3)
```

### Metodos de Jerarquia

```python
# Rutear a departamento especifico
agent = orchestrator.route_to_department(
    task="Build REST API",
    department=Department.DESARROLLO,
    min_rank=Rank.SENIOR
)

# Escalar a supervisor
supervisor = orchestrator.escalate("python-pro")
# -> AgentProfile(name="backend-architect")

# Delegar hacia abajo
delegate = orchestrator.delegate_down("data-architect", task)

# Buscar expertos
experts = orchestrator.find_expert("scraping")
```

## Scoring de Agentes

El orchestrator llama a `can_handle()` en cada agente y ordena por score:

```python
scores = self._score_agents(task, context)
# [AgentScore(agent=scraper, confidence=0.9),
#  AgentScore(agent=data, confidence=0.3), ...]
```

## Historial

```python
history = orchestrator.get_task_history()
# [{"task": "...", "agent": "scraper", "confidence": 0.9, "success": True}]
```

## Relacionado

- [[Enciclopedia/BaseAgent|BaseAgent]] - Agentes que orquesta
- [[Enciclopedia/Registry|Registry]] - De donde descubre agentes
- [[Enciclopedia/AgentHierarchy|AgentHierarchy]] - Jerarquia que usa

## Tags

#agentes #orchestrator #routing
"""

RANK = """# Rank

[[Enciclopedia/Enciclopedia|← Volver a Enciclopedia]]

## Definicion

Enum que define los rangos jerarquicos de los agentes.

## Ubicacion

`agents/hierarchy.py`

## Valores

```python
class Rank(IntEnum):
    JUNIOR = 1      # Tareas simples, ejecucion directa
    SENIOR = 2      # Tareas complejas, puede supervisar juniors
    LEAD = 3        # Lidera equipo, decisiones tecnicas
    ARCHITECT = 4   # Disena sistemas, arquitectura
    DIRECTOR = 5    # Dirige departamento, estrategia
```

## Uso en Filtrado

```python
from agents.hierarchy import Rank, get_hierarchy

hierarchy = get_hierarchy()

# Obtener todos los architects
architects = hierarchy.get_by_rank(Rank.ARCHITECT)

# Filtrar por rango minimo
dept_agents = hierarchy.get_department_agents(Department.DATOS)
seniors_plus = [a for a in dept_agents if a.rank >= Rank.SENIOR]
```

## Herencia de IntEnum

Al heredar de `IntEnum`, los rangos se pueden comparar numericamente:

```python
Rank.ARCHITECT > Rank.SENIOR  # True (4 > 2)
Rank.JUNIOR < Rank.LEAD       # True (1 < 3)
```

## Responsabilidades por Rango

| Rango | Responsabilidades |
|-------|-------------------|
| JUNIOR | Ejecutar tareas simples, seguir instrucciones |
| SENIOR | Tareas complejas, supervisar juniors, decisiones tacticas |
| LEAD | Liderar equipo, decisiones tecnicas, coordinar |
| ARCHITECT | Disenar sistemas, definir arquitectura, estandares |
| DIRECTOR | Estrategia departamental, vision, recursos |

## Relacionado

- [[Enciclopedia/Department|Department]] - Departamentos donde aplican
- [[Enciclopedia/AgentProfile|AgentProfile]] - Tiene campo rank
- [[Enciclopedia/OrchestratorAgent|OrchestratorAgent]] - Usa rangos para routing

## Tags

#agentes #enum #jerarquia
"""

REGISTRY = """# Registry (AgentRegistry)

[[Enciclopedia/Enciclopedia|← Volver a Enciclopedia]]

## Definicion

Clase que maneja el auto-descubrimiento y registro de agentes runtime.

## Ubicacion

`agents/registry.py`

## Funcionamiento

El Registry escanea el directorio `agents/` buscando clases que hereden de [[Enciclopedia/BaseAgent|BaseAgent]].

## Metodos

```python
from agents.registry import get_registry

registry = get_registry()

# Descubrir agentes automaticamente
discovered = registry.discover_agents()  # List[BaseAgent]

# Registrar manualmente
registry.register(my_agent)

# Obtener agente por nombre
agent = registry.get("scraper")

# Listar nombres
names = registry.list_agents()  # ["scraper", "data", "analysis"]

# Iterar
for agent in registry:
    print(agent.name)
```

## Auto-Descubrimiento

```python
def discover_agents(self) -> List[BaseAgent]:
    \"\"\"
    Busca en agents/ archivos *_agent.py
    Importa y busca clases que hereden de BaseAgent
    Instancia y registra cada una
    \"\"\"
```

## Patron Singleton

```python
_registry: Optional[AgentRegistry] = None

def get_registry() -> AgentRegistry:
    global _registry
    if _registry is None:
        _registry = AgentRegistry()
    return _registry
```

## Relacionado

- [[Enciclopedia/BaseAgent|BaseAgent]] - Tipo de agentes que registra
- [[Enciclopedia/OrchestratorAgent|OrchestratorAgent]] - Usa el registry
- [[Enciclopedia/Singleton|Singleton]] - Patron que implementa

## Tags

#agentes #registry #autodiscovery
"""

# ============================================
# CONCEPTOS DE SCRAPING
# ============================================

BASE_SITE = """# BaseSite

[[Enciclopedia/Enciclopedia|← Volver a Enciclopedia]]

## Definicion

Clase base abstracta que define la interfaz para cada sitio web soportado.

## Ubicacion

`scraping/base/site.py`

## Interfaz

```python
class BaseSite(ABC):
    config: SiteConfig
    parser: BaseParser

    def __init__(self):
        self.config = self._create_config()
        self.parser = self._create_parser()

    @abstractmethod
    def _create_config(self) -> SiteConfig:
        \"\"\"Crear configuracion del sitio.\"\"\"
        pass

    @abstractmethod
    def _create_parser(self) -> BaseParser:
        \"\"\"Crear parser para este sitio.\"\"\"
        pass

    @abstractmethod
    def build_search_url(self, marca: str, year: int = None, page: int = 1) -> str:
        \"\"\"Construir URL de busqueda.\"\"\"
        pass

    @abstractmethod
    def detect_block(self, html: str) -> tuple:
        \"\"\"Detectar si estamos bloqueados.\"\"\"
        pass

    def parse(self, html: str) -> List[CarListing]:
        return self.parser.parse(html)
```

## Implementaciones

- [[Enciclopedia/CochesNet|CochesNetSite]]
- [[Enciclopedia/Autocasion|AutocasionSite]]
- [[Enciclopedia/Clicars|ClicarsSite]]

## Patron Abstract Factory

BaseSite usa el patron [[Enciclopedia/AbstractFactory|Abstract Factory]]:
- `_create_config()` crea la configuracion
- `_create_parser()` crea el parser apropiado

## Relacionado

- [[Enciclopedia/SiteConfig|SiteConfig]] - Configuracion
- [[Enciclopedia/BaseParser|BaseParser]] - Parser
- [[Enciclopedia/SiteRegistry|SiteRegistry]] - Donde se registran

## Tags

#scraping #abc #sitio
"""

BASE_PARSER = """# BaseParser

[[Enciclopedia/Enciclopedia|← Volver a Enciclopedia]]

## Definicion

Clase base abstracta para parsers de HTML de cada sitio.

## Ubicacion

`scraping/base/parser.py`

## Interfaz

```python
class BaseParser(ABC):
    @abstractmethod
    def parse(self, html: str) -> List[CarListing]:
        \"\"\"Parsear HTML y extraer listings.\"\"\"
        pass

    @abstractmethod
    def get_total_count(self, html: str) -> Optional[int]:
        \"\"\"Obtener total de resultados.\"\"\"
        pass
```

## Estrategias de Parsing

Cada sitio usa una estrategia diferente:

| Sitio | Estrategia |
|-------|------------|
| Coches.net | `__INITIAL_PROPS__` JSON embebido |
| Autocasion | JSON-LD + scraping HTML |
| Clicars | API JSON directa |

## Implementacion Ejemplo

```python
class CochesNetParser(BaseParser):
    def parse(self, html: str) -> List[CarListing]:
        # Buscar script con __INITIAL_PROPS__
        match = re.search(r'__INITIAL_PROPS__\s*=\s*({.*?});', html)
        if match:
            data = json.loads(match.group(1))
            return self._extract_listings(data)
        return []
```

## Patron Strategy

Cada parser implementa una [[Enciclopedia/Strategy|estrategia]] diferente para el mismo objetivo.

## Relacionado

- [[Enciclopedia/CarListing|CarListing]] - Lo que produce
- [[Enciclopedia/BaseSite|BaseSite]] - Quien lo usa
- [[Enciclopedia/Strategy|Strategy]] - Patron que implementa

## Tags

#scraping #parser #abc
"""

CAR_LISTING = """# CarListing

[[Enciclopedia/Enciclopedia|← Volver a Enciclopedia]]

## Definicion

Dataclass que representa un anuncio de coche extraido.

## Ubicacion

`scraping/base/parser.py`

## Estructura

```python
@dataclass
class CarListing:
    ad_id: str                    # ID unico del anuncio
    url: str                      # URL completa
    title: str                    # Titulo del anuncio
    marca: str                    # Marca (BMW, Audi, etc.)
    modelo: str                   # Modelo (Serie 3, A4, etc.)
    version: Optional[str]        # Version/acabado
    year: Optional[int]           # Ano de matriculacion
    kilometers: Optional[str]     # Kilometraje (texto)
    fuel: Optional[str]           # Tipo de combustible
    price: Optional[str]          # Precio (texto)
    power: Optional[str]          # Potencia (texto)
    power_cv: Optional[int]       # Potencia en CV (numerico)
    transmission: Optional[str]   # Tipo de cambio
    location: Optional[str]       # Ubicacion
    provincia: Optional[str]      # Provincia
    source: str                   # "cochesnet", "autocasion", "clicars"
```

## Ejemplo

```python
listing = CarListing(
    ad_id="12345678",
    url="https://www.coches.net/...",
    title="BMW Serie 3 320d",
    marca="BMW",
    modelo="Serie 3",
    version="320d",
    year=2020,
    kilometers="45.000 km",
    fuel="Diesel",
    price="28.900 EUR",
    power="190 CV",
    power_cv=190,
    transmission="Automatico",
    location="Madrid",
    provincia="Madrid",
    source="cochesnet"
)
```

## Flujo

```
HTML → Parser → List[CarListing] → SupabaseClient → Database
```

## Relacionado

- [[Enciclopedia/BaseParser|BaseParser]] - Quien lo produce
- [[Enciclopedia/SupabaseClient|SupabaseClient]] - Quien lo persiste

## Tags

#scraping #dataclass #modelo
"""

HEADLESSX = """# HeadlessX

[[Enciclopedia/Enciclopedia|← Volver a Enciclopedia]]

## Definicion

Servicio externo de renderizado de JavaScript para evitar deteccion anti-bot.

## Ubicacion

`scraping/engine/headlessx.py`

## Proposito

Muchos sitios (especialmente Coches.net con Cloudflare) detectan scrapers.
HeadlessX proporciona:

1. Renderizado completo de JavaScript
2. Rotacion de IPs
3. Fingerprinting de navegador real
4. Bypass de CAPTCHAs

## Uso

```python
from scraping.engine.headlessx import HeadlessXClient

client = HeadlessXClient(api_key="...")

# Renderizar pagina
html = await client.render(
    url="https://www.coches.net/segunda-mano/",
    wait_for="networkidle"
)

# Con opciones
html = await client.render(
    url=url,
    wait_for_selector=".listing-card",
    timeout=30000
)
```

## Alternativas Locales

Para sitios menos protegidos se puede usar Playwright directo:

```python
from playwright.async_api import async_playwright

async with async_playwright() as p:
    browser = await p.chromium.launch()
    page = await browser.new_page()
    await page.goto(url)
    html = await page.content()
```

## Cuando Usar

| Sitio | HeadlessX | Playwright | Requests |
|-------|-----------|------------|----------|
| Coches.net | Si | No | No |
| Autocasion | Opcional | Si | No |
| Clicars | No | Si | Si (API) |

## Relacionado

- [[Enciclopedia/CochesNet|Coches.net]] - Principal usuario
- [[Enciclopedia/BaseSite|BaseSite]] - Lo integra

## Tags

#scraping #rendering #antibot
"""

SITE_CONFIG = """# SiteConfig

[[Enciclopedia/Enciclopedia|← Volver a Enciclopedia]]

## Definicion

Dataclass con la configuracion de un sitio web para scraping.

## Ubicacion

`scraping/base/site.py`

## Estructura

```python
@dataclass
class SiteConfig:
    name: str              # Identificador: "cochesnet"
    display_name: str      # Para UI: "Coches.net"
    base_url: str          # "https://www.coches.net"
    search_path: str       # "/segunda-mano"

    # Rate limiting
    delay_between_requests: float = 2.0  # segundos
    delay_between_pages: float = 1.0

    # Paginacion
    max_pages_per_search: int = 100
    items_per_page: int = 30
```

## Ejemplo

```python
config = SiteConfig(
    name="cochesnet",
    display_name="Coches.net",
    base_url="https://www.coches.net",
    search_path="/segunda-mano",
    delay_between_requests=3.0,  # Mas lento para evitar bloqueo
    max_pages_per_search=50,
    items_per_page=30
)
```

## Uso de Delays

```python
import asyncio

for page in range(1, config.max_pages_per_search + 1):
    html = await fetch_page(page)
    await asyncio.sleep(config.delay_between_pages)
```

## Relacionado

- [[Enciclopedia/BaseSite|BaseSite]] - Tiene un SiteConfig
- [[Enciclopedia/SiteRegistry|SiteRegistry]] - Registra sitios con config

## Tags

#scraping #configuracion #dataclass
"""

SITE_REGISTRY = """# SiteRegistry

[[Enciclopedia/Enciclopedia|← Volver a Enciclopedia]]

## Definicion

Registro central de todos los sitios de scraping disponibles.

## Ubicacion

`scraping/base/site.py`

## Interfaz

```python
class SiteRegistry:
    def register(self, site: BaseSite) -> None:
        \"\"\"Registrar un sitio.\"\"\"

    def get(self, name: str) -> Optional[BaseSite]:
        \"\"\"Obtener sitio por nombre.\"\"\"

    def list_sites(self) -> List[str]:
        \"\"\"Listar nombres de sitios.\"\"\"

    def get_all(self) -> Dict[str, BaseSite]:
        \"\"\"Obtener todos los sitios.\"\"\"
```

## Uso

```python
from scraping.base.site import get_site_registry

registry = get_site_registry()

# Registrar
registry.register(CochesNetSite())
registry.register(AutocasionSite())

# Obtener
site = registry.get("cochesnet")
url = site.build_search_url("bmw", page=1)

# Listar
print(registry.list_sites())  # ["cochesnet", "autocasion"]
```

## Patron Singleton

```python
_registry: Optional[SiteRegistry] = None

def get_site_registry() -> SiteRegistry:
    global _registry
    if _registry is None:
        _registry = SiteRegistry()
    return _registry
```

## Relacionado

- [[Enciclopedia/BaseSite|BaseSite]] - Lo que registra
- [[Enciclopedia/Registry|Registry]] - Similar para agentes
- [[Enciclopedia/Singleton|Singleton]] - Patron usado

## Tags

#scraping #registry #singleton
"""

# ============================================
# SITIOS SOPORTADOS
# ============================================

COCHES_NET = """# Coches.net

[[Enciclopedia/Enciclopedia|← Volver a Enciclopedia]]

## Descripcion

Portal lider de coches de segunda mano en Espana.

## URL Base

`https://www.coches.net`

## Caracteristicas Tecnicas

| Aspecto | Valor |
|---------|-------|
| Anti-bot | Cloudflare (agresivo) |
| Renderizado | JavaScript requerido |
| Datos | `__INITIAL_PROPS__` JSON |
| Paginacion | `?pg={page}` |
| Items/pagina | ~30 |

## Estrategia de Parsing

El sitio embebe los datos en un script JavaScript:

```html
<script>
window.__INITIAL_PROPS__ = {
  "searchResults": {
    "items": [
      {"id": "123", "title": "BMW Serie 3", ...},
      ...
    ]
  }
};
</script>
```

El parser extrae este JSON con regex:

```python
match = re.search(r'__INITIAL_PROPS__\s*=\s*({.*?});', html, re.DOTALL)
data = json.loads(match.group(1))
```

## URL de Busqueda

```
https://www.coches.net/segunda-mano/?marca={marca}&pg={page}
```

Ejemplo:
```
https://www.coches.net/segunda-mano/?marca=bmw&pg=1
```

## Deteccion de Bloqueo

```python
def detect_block(self, html: str) -> tuple:
    if "challenge-running" in html:
        return (True, "cloudflare", {"type": "challenge"})
    if "Access denied" in html:
        return (True, "blocked", {"type": "ip_ban"})
    return (False, None, {})
```

## Requiere

- [[Enciclopedia/HeadlessX|HeadlessX]] para bypass de Cloudflare

## Relacionado

- [[Enciclopedia/BaseSite|BaseSite]] - Clase padre
- [[Enciclopedia/Autocasion|Autocasion]] - Sitio alternativo
- [[Enciclopedia/SupabaseClient|SupabaseClient]] - Tabla `cochesnet`

## Tags

#scraping #sitio #cochesnet
"""

AUTOCASION = """# Autocasion

[[Enciclopedia/Enciclopedia|← Volver a Enciclopedia]]

## Descripcion

Portal de coches de ocasion, parte del grupo Vocento.

## URL Base

`https://www.autocasion.com`

## Caracteristicas Tecnicas

| Aspecto | Valor |
|---------|-------|
| Anti-bot | Moderado |
| Renderizado | JavaScript parcial |
| Datos | JSON-LD + HTML |
| Paginacion | `?pagina={page}` |

## Estrategia de Parsing

Combina dos fuentes:

### 1. JSON-LD (datos estructurados)

```html
<script type="application/ld+json">
{
  "@type": "Product",
  "name": "Audi A4",
  "offers": {"price": "25900"}
}
</script>
```

### 2. HTML scraping

```python
soup = BeautifulSoup(html, 'html.parser')
cards = soup.select('.listing-card')
for card in cards:
    title = card.select_one('.title').text
    price = card.select_one('.price').text
```

## URL de Busqueda

```
https://www.autocasion.com/coches-segunda-mano/{marca}.htm?pagina={page}
```

Ejemplo:
```
https://www.autocasion.com/coches-segunda-mano/audi.htm?pagina=1
```

## Puede usar

- Playwright (recomendado)
- [[Enciclopedia/HeadlessX|HeadlessX]] (opcional)

## Relacionado

- [[Enciclopedia/BaseSite|BaseSite]] - Clase padre
- [[Enciclopedia/CochesNet|Coches.net]] - Sitio principal
- [[Enciclopedia/SupabaseClient|SupabaseClient]] - Tabla `autocasion`

## Tags

#scraping #sitio #autocasion
"""

CLICARS = """# Clicars

[[Enciclopedia/Enciclopedia|← Volver a Enciclopedia]]

## Descripcion

Concesionario online de coches de ocasion con garantia.

## URL Base

`https://www.clicars.com`

## Caracteristicas Tecnicas

| Aspecto | Valor |
|---------|-------|
| Anti-bot | Bajo |
| Renderizado | SPA React |
| Datos | API JSON interna |
| Paginacion | API params |

## Estrategia de Parsing

Clicars usa una API interna que devuelve JSON directo:

```python
async def fetch_listings(self, marca: str, page: int):
    response = await self.client.get(
        "https://www.clicars.com/api/vehicles",
        params={
            "brand": marca,
            "page": page,
            "limit": 24
        }
    )
    return response.json()["vehicles"]
```

## Ventajas

- No necesita renderizado de JS para datos
- Rate limiting permisivo
- Datos estructurados y limpios

## Puede usar

- `httpx` / `requests` directo
- Playwright para validacion visual

## Relacionado

- [[Enciclopedia/BaseSite|BaseSite]] - Clase padre
- [[Enciclopedia/CochesNet|Coches.net]] - Sitio mas complejo
- [[Enciclopedia/SupabaseClient|SupabaseClient]] - Tabla `clicars`

## Tags

#scraping #sitio #clicars #api
"""

# ============================================
# DEBUG Y UTILIDADES
# ============================================

DEBUG = """# Debug

[[Enciclopedia/Enciclopedia|← Volver a Enciclopedia]]

## Definicion

Sistema centralizado de debug para tracking de flujo de ejecucion.

## Ubicacion

`core/debug.py`

## Caracteristicas

- Multi-nivel (OFF, ERROR, WARN, INFO, DEBUG, TRACE)
- Flow tracking con timing
- Decorators para tracing automatico
- Context management para tareas
- Reportes de ejecucion

## Singleton

```python
from core.debug import get_debugger

debug = get_debugger()  # Siempre la misma instancia
```

## Configuracion

```python
debug.set_level(DebugLevel.DEBUG)
debug.show_timestamps = True
debug.show_file_info = True
debug.show_call_stack = False
debug.colorize = True
```

## Logging por Nivel

```python
debug.error("component", "mensaje", {"data": "..."})
debug.warn("component", "mensaje")
debug.info("component", "mensaje")
debug.debug("component", "mensaje")
debug.trace("component", "mensaje")
```

## Flow Tracking

```python
start = debug.flow_start("scraper", "fetch_page")
# ... operacion ...
debug.flow_step("scraper", "parsing", "Extracting data")
# ... mas operacion ...
debug.flow_end("scraper", "fetch_page", start)  # Incluye duracion
```

## Relacionado

- [[Enciclopedia/DebugLevel|DebugLevel]] - Niveles
- [[Enciclopedia/FlowEntry|FlowEntry]] - Entradas de log
- [[Enciclopedia/debug_flow|@debug_flow]] - Decorator
- [[Enciclopedia/ExecutionContext|ExecutionContext]] - Contextos

## Tags

#debug #logging #tracing
"""

DEBUG_LEVEL = """# DebugLevel

[[Enciclopedia/Enciclopedia|← Volver a Enciclopedia]]

## Definicion

Enum que define los niveles de verbosidad del debug.

## Ubicacion

`core/debug.py`

## Valores

```python
class DebugLevel(IntEnum):
    OFF = 0      # Nada
    ERROR = 1    # Solo errores
    WARN = 2     # Errores + warnings
    INFO = 3     # Flujo normal
    DEBUG = 4    # Debug detallado
    TRACE = 5    # Todo (entry/exit de funciones)
```

## Jerarquia

Cada nivel incluye todos los anteriores:

```
TRACE (5) ⊃ DEBUG (4) ⊃ INFO (3) ⊃ WARN (2) ⊃ ERROR (1) ⊃ OFF (0)
```

## Uso

```python
from core.debug import get_debugger, DebugLevel

debug = get_debugger()

# En desarrollo
debug.set_level(DebugLevel.DEBUG)

# En produccion
debug.set_level(DebugLevel.WARN)

# Para troubleshooting profundo
debug.set_level(DebugLevel.TRACE)
```

## Comparacion

```python
if current_level >= DebugLevel.DEBUG:
    # Mostrar info de debug
```

## Relacionado

- [[Enciclopedia/Debug|Debug]] - Sistema que lo usa
- [[Enciclopedia/FlowEntry|FlowEntry]] - Tiene campo level

## Tags

#debug #enum #niveles
"""

FLOW_ENTRY = """# FlowEntry

[[Enciclopedia/Enciclopedia|← Volver a Enciclopedia]]

## Definicion

Dataclass que representa una entrada individual en el log de ejecucion.

## Ubicacion

`core/debug.py`

## Estructura

```python
@dataclass
class FlowEntry:
    timestamp: datetime          # Cuando ocurrio
    level: DebugLevel           # Nivel de debug
    component: str              # Componente que logeo
    action: str                 # Accion realizada
    message: str                # Mensaje descriptivo
    data: Optional[Dict]        # Datos adicionales
    duration_ms: Optional[float] # Duracion si aplica
    file_path: Optional[str]    # Archivo origen
    line_number: Optional[int]  # Linea origen
    call_stack: Optional[List]  # Stack trace
```

## Ejemplo de Output

```
[INFO] 14:32:15.234 [orchestrator] <route:START> Starting route {"task": "scrape bmw"}
[INFO] 14:32:15.456 [orchestrator] <step:scoring> Scoring all agents
[INFO] 14:32:16.789 [orchestrator] <route:END> Completed route (1555.00ms)
```

## Formateo

```python
def _format_message(self, entry: FlowEntry) -> str:
    parts = []
    parts.append(f"[{entry.level.name}]")
    if self.show_timestamps:
        parts.append(entry.timestamp.strftime("%H:%M:%S.%f")[:-3])
    parts.append(f"[{entry.component}]")
    parts.append(f"<{entry.action}>")
    parts.append(entry.message)
    if entry.duration_ms:
        parts.append(f"({entry.duration_ms:.2f}ms)")
    return " ".join(parts)
```

## Relacionado

- [[Enciclopedia/Debug|Debug]] - Sistema que lo genera
- [[Enciclopedia/DebugLevel|DebugLevel]] - Campo level
- [[Enciclopedia/ExecutionContext|ExecutionContext]] - Contiene lista de FlowEntry

## Tags

#debug #dataclass #logging
"""

EXECUTION_CONTEXT = """# ExecutionContext

[[Enciclopedia/Enciclopedia|← Volver a Enciclopedia]]

## Definicion

Dataclass que agrupa informacion sobre una tarea en ejecucion.

## Ubicacion

`core/debug.py`

## Estructura

```python
@dataclass
class ExecutionContext:
    task_id: str                    # Identificador de la tarea
    start_time: datetime            # Inicio de ejecucion
    agent_chain: List[str] = []     # Agentes que participaron
    department: Optional[str]       # Departamento si aplica
    flow: List[FlowEntry] = []      # Entradas de log
```

## Uso

```python
debug = get_debugger()

# Iniciar contexto
debug.start_context("task_123", department="datos")

# Durante la ejecucion
debug.add_to_agent_chain("scraper-specialist")
debug.add_to_agent_chain("data-cleaner")

# Finalizar y obtener
ctx = debug.end_context("task_123")

print(ctx.agent_chain)  # ["scraper-specialist", "data-cleaner"]
print(len(ctx.flow))    # Numero de log entries
```

## Proposito

- Aislar logs de diferentes tareas
- Rastrear que agentes participaron
- Calcular tiempos totales
- Debugging de flujos complejos

## Relacionado

- [[Enciclopedia/Debug|Debug]] - Sistema que lo gestiona
- [[Enciclopedia/FlowEntry|FlowEntry]] - Elementos del flow

## Tags

#debug #contexto #dataclass
"""

DEBUG_FLOW_DECORATOR = """# @debug_flow

[[Enciclopedia/Enciclopedia|← Volver a Enciclopedia]]

## Definicion

Decorator que automatiza el tracing de funciones.

## Ubicacion

`core/debug.py`

## Uso

```python
from core.debug import debug_flow

@debug_flow("my_component")
def my_function(x, y):
    return x + y

@debug_flow("scraper")
async def fetch_page(url):
    # ... async code
    return html
```

## Output Automatico

Con `DebugLevel.TRACE`:

```
[TRACE] ENTER my_function args=(1, 2) kwargs={}
[TRACE] EXIT my_function result=3 duration_ms=0.05
```

En caso de excepcion:

```
[ERROR] EXCEPTION in my_function: ValueError(...) duration_ms=1.23
```

## Implementacion

```python
def debug_flow(component: Optional[str] = None):
    def decorator(func: Callable) -> Callable:
        comp = component or func.__module__.split('.')[-1]

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            debugger = get_debugger()
            debugger.trace(comp, f"ENTER {func.__name__}", {...})
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                duration = (time.perf_counter() - start) * 1000
                debugger.trace(comp, f"EXIT {func.__name__}", {...})
                return result
            except Exception as e:
                debugger.error(comp, f"EXCEPTION in {func.__name__}: {e}")
                raise

        return wrapper
    return decorator
```

## Soporte Async

El decorator detecta si la funcion es async y usa el wrapper apropiado.

## Relacionado

- [[Enciclopedia/Debug|Debug]] - Sistema que usa
- [[Enciclopedia/DebugLevel|DebugLevel]] - Requiere TRACE para ver

## Tags

#debug #decorator #tracing
"""

# ============================================
# BASE DE DATOS
# ============================================

SUPABASE_CLIENT = """# SupabaseClient

[[Enciclopedia/Enciclopedia|← Volver a Enciclopedia]]

## Definicion

Cliente para persistir datos scrapeados en Supabase (PostgreSQL).

## Ubicacion

`scraping/storage/supabase_client.py`

## Configuracion

```python
# .env
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Singleton

```python
from scraping.storage.supabase_client import get_supabase_client

client = get_supabase_client()
```

## Metodos Principales

### Guardar Listings

```python
# Un listing
result = client.save_listing(listing)

# Multiples (batch)
stats = client.save_listings(listings)
# {"cochesnet": 30, "autocasion": 15, "errors": 0}
```

### Verificar Existentes

```python
existing = client.get_existing_ad_ids("cochesnet", ad_ids_list)
new_ads = [l for l in listings if l.ad_id not in existing]
```

### Estadisticas

```python
stats = client.get_stats()
# {"cochesnet": {"total": 15000}, "autocasion": {"total": 8000}}

count = client.count_by_source("cochesnet")
```

### Objetivos de Scraping

```python
# Obtener objetivos pendientes
objetivos = client.get_pending_objetivos("cochesnet", limit=10)

# Actualizar estado
client.update_objetivo_status(
    source="cochesnet",
    marca="bmw",
    status="success",
    cars_scraped=150
)
```

## Tablas

| Tabla | Contenido |
|-------|-----------|
| cochesnet | Anuncios de Coches.net |
| autocasion | Anuncios de Autocasion |
| clicars | Anuncios de Clicars |
| objetivo_coches_net | Marcas a scrapear |
| objetivo_autocasion | Marcas a scrapear |

## Relacionado

- [[Enciclopedia/CarListing|CarListing]] - Lo que persiste
- [[Enciclopedia/Upsert|Upsert]] - Estrategia de insert
- [[Enciclopedia/Objetivos|Objetivos]] - Tablas de control

## Tags

#database #supabase #storage
"""

UPSERT = """# Upsert

[[Enciclopedia/Enciclopedia|← Volver a Enciclopedia]]

## Definicion

Operacion de base de datos que inserta o actualiza segun exista el registro.

## Comportamiento

```
Si ad_id NO existe → INSERT
Si ad_id YA existe → UPDATE
```

## Implementacion en Supabase

```python
result = self.client.table("cochesnet").upsert(
    data,
    on_conflict="ad_id"  # Columna de conflicto
).execute()
```

## SQL Equivalente

```sql
INSERT INTO cochesnet (ad_id, title, price, ...)
VALUES ('123', 'BMW Serie 3', '25900', ...)
ON CONFLICT (ad_id) DO UPDATE SET
    title = EXCLUDED.title,
    price = EXCLUDED.price,
    ...
    updated_at = NOW();
```

## Ventajas

1. **Atomicidad**: Una sola operacion
2. **Idempotencia**: Se puede ejecutar multiples veces
3. **Actualizacion**: Mantiene datos frescos
4. **Sin duplicados**: Garantizado por constraint

## Uso en el Proyecto

Cada vez que se scrapea:
1. Se extraen listings
2. Se hace upsert por batch
3. Nuevos se insertan, existentes se actualizan

```python
def save_listings(self, listings: List[CarListing]):
    data = [self._listing_to_row(l) for l in listings]
    result = self.client.table(table).upsert(
        data,
        on_conflict="ad_id"
    ).execute()
```

## Relacionado

- [[Enciclopedia/SupabaseClient|SupabaseClient]] - Quien lo usa
- [[Enciclopedia/CarListing|CarListing]] - Datos que upsertea

## Tags

#database #operacion #upsert
"""

OBJETIVOS = """# Tablas de Objetivos

[[Enciclopedia/Enciclopedia|← Volver a Enciclopedia]]

## Definicion

Tablas que controlan que marcas scrapear y su estado.

## Tablas

| Tabla | Sitio |
|-------|-------|
| objetivo_coches_net | Coches.net |
| objetivo_autocasion | Autocasion |

## Esquema (objetivo_coches_net)

| Campo | Tipo | Descripcion |
|-------|------|-------------|
| marca | TEXT PK | Marca (bmw, audi, etc.) |
| url_general | TEXT | URL base de busqueda |
| last_scraped | TIMESTAMP | Ultima ejecucion |
| last_status | TEXT | success, error, blocked |
| total_cars_scraped | INT | Coches acumulados |
| total_pages_scraped | INT | Paginas acumuladas |
| scraping_attempts | INT | Intentos totales |
| last_scraping_duration_seconds | FLOAT | Duracion ultima |

## Uso

### Obtener Pendientes

```python
objetivos = client.get_pending_objetivos("cochesnet", limit=10)
for obj in objetivos:
    marca = obj["marca"]
    url = obj["url_general"]
    # Scrapear...
```

### Actualizar Estado

```python
client.update_objetivo_status(
    source="cochesnet",
    marca="bmw",
    status="success",
    cars_scraped=150,
    pages_scraped=5,
    duration_seconds=45.2
)
```

### Obtener URL

```python
url = client.get_objetivo_url("cochesnet", "audi")
# "https://www.coches.net/segunda-mano/?marca=audi"
```

## Prioridad (Autocasion)

La tabla de autocasion tiene campo `prioridad`:

```python
result = self.client.table("objetivo_autocasion").select("*")\\
    .order("prioridad", desc=True)\\
    .order("scraping_attempts")\\
    .limit(limit).execute()
```

## Relacionado

- [[Enciclopedia/SupabaseClient|SupabaseClient]] - Metodos de acceso
- [[Enciclopedia/CochesNet|Coches.net]] - Sitio objetivo
- [[Enciclopedia/Autocasion|Autocasion]] - Sitio objetivo

## Tags

#database #objetivos #control
"""

# ============================================
# PATRONES DE DISENO
# ============================================

SINGLETON = """# Singleton

[[Enciclopedia/Enciclopedia|← Volver a Enciclopedia]]

## Definicion

Patron que garantiza una unica instancia de una clase.

## Implementacion en el Proyecto

### Funcion get_*()

```python
_instance: Optional[MyClass] = None

def get_instance() -> MyClass:
    global _instance
    if _instance is None:
        _instance = MyClass()
    return _instance
```

### Clase con __new__

```python
class Debug:
    _instance: Optional['Debug'] = None

    def __new__(cls) -> 'Debug':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        # ... inicializacion ...
        self._initialized = True
```

## Usos en ScrapeadorSupremo

| Singleton | Funcion | Proposito |
|-----------|---------|-----------|
| Debug | `get_debugger()` | Un solo logger |
| AgentRegistry | `get_registry()` | Un registro de agentes |
| AgentHierarchy | `get_hierarchy()` | Una jerarquia |
| SiteRegistry | `get_site_registry()` | Un registro de sitios |
| SupabaseClient | `get_supabase_client()` | Una conexion DB |

## Ventajas

- Estado global controlado
- Inicializacion lazy
- Acceso desde cualquier parte

## Desventajas

- Dificulta testing (estado global)
- Puede ocultar dependencias

## Relacionado

- [[Enciclopedia/Debug|Debug]] - Ejemplo de singleton
- [[Enciclopedia/Registry|Registry]] - Ejemplo de singleton

## Tags

#patron #singleton #diseno
"""

ABSTRACT_FACTORY = """# Abstract Factory

[[Enciclopedia/Enciclopedia|← Volver a Enciclopedia]]

## Definicion

Patron que proporciona una interfaz para crear familias de objetos relacionados.

## Implementacion en el Proyecto

### BaseSite como Factory

```python
class BaseSite(ABC):
    config: SiteConfig
    parser: BaseParser

    def __init__(self):
        self.config = self._create_config()  # Factory method
        self.parser = self._create_parser()  # Factory method

    @abstractmethod
    def _create_config(self) -> SiteConfig:
        pass

    @abstractmethod
    def _create_parser(self) -> BaseParser:
        pass
```

### Implementacion Concreta

```python
class CochesNetSite(BaseSite):
    def _create_config(self) -> SiteConfig:
        return SiteConfig(
            name="cochesnet",
            display_name="Coches.net",
            base_url="https://www.coches.net",
            ...
        )

    def _create_parser(self) -> BaseParser:
        return CochesNetParser()
```

## Familia de Objetos

Cada sitio crea su propia "familia":

| Sitio | Config | Parser |
|-------|--------|--------|
| CochesNetSite | CochesNetConfig | CochesNetParser |
| AutocasionSite | AutocasionConfig | AutocasionParser |
| ClicarsSite | ClicarsConfig | ClicarsParser |

## Ventajas

- Consistencia entre objetos relacionados
- Facil agregar nuevos sitios
- Encapsula creacion

## Relacionado

- [[Enciclopedia/BaseSite|BaseSite]] - Abstract factory
- [[Enciclopedia/BaseParser|BaseParser]] - Producto abstracto
- [[Enciclopedia/SiteConfig|SiteConfig]] - Producto abstracto

## Tags

#patron #factory #diseno
"""

STRATEGY = """# Strategy

[[Enciclopedia/Enciclopedia|← Volver a Enciclopedia]]

## Definicion

Patron que permite seleccionar un algoritmo en tiempo de ejecucion.

## Implementacion en el Proyecto

### Parsers como Estrategias

```python
class BaseParser(ABC):
    @abstractmethod
    def parse(self, html: str) -> List[CarListing]:
        pass
```

Cada parser implementa una estrategia diferente:

```python
class CochesNetParser(BaseParser):
    def parse(self, html: str) -> List[CarListing]:
        # Estrategia: extraer __INITIAL_PROPS__
        data = extract_initial_props(html)
        return self._convert(data)

class AutocasionParser(BaseParser):
    def parse(self, html: str) -> List[CarListing]:
        # Estrategia: JSON-LD + HTML scraping
        json_ld = extract_json_ld(html)
        html_data = scrape_html(html)
        return self._merge(json_ld, html_data)

class ClicarsParser(BaseParser):
    def parse(self, html: str) -> List[CarListing]:
        # Estrategia: API JSON directa
        return json.loads(html)["vehicles"]
```

### Uso en Context (BaseSite)

```python
class BaseSite:
    parser: BaseParser  # Estrategia inyectada

    def parse(self, html: str) -> List[CarListing]:
        return self.parser.parse(html)  # Delega a estrategia
```

## Ventajas

- Intercambiar algoritmos facilmente
- Separar logica de parsing
- Testing individual de cada estrategia

## Relacionado

- [[Enciclopedia/BaseParser|BaseParser]] - Interfaz estrategia
- [[Enciclopedia/BaseSite|BaseSite]] - Context que usa estrategia
- [[Enciclopedia/CochesNet|Coches.net]] - Estrategia especifica

## Tags

#patron #strategy #diseno
"""

CHAIN_OF_RESPONSIBILITY = """# Chain of Responsibility

[[Enciclopedia/Enciclopedia|← Volver a Enciclopedia]]

## Definicion

Patron que permite pasar solicitudes a traves de una cadena de handlers.

## Implementacion en el Proyecto

### Escalacion de Agentes

```python
class OrchestratorAgent:
    def escalate(self, agent_name: str) -> Optional[AgentProfile]:
        \"\"\"Escala al supervisor.\"\"\"
        return self.hierarchy.get_supervisor(agent_name)
```

### Cadena de Mando

```
python-pro → backend-architect → (ninguno, es ARCHITECT)
```

```python
def get_chain_of_command(self, name: str) -> List[AgentProfile]:
    chain = []
    current = self.get_supervisor(name)
    while current:
        chain.append(current)
        current = self.get_supervisor(current.name)
    return chain
```

### Ejemplo de Uso

```python
# Tarea demasiado compleja para junior
agent = "test-writer"  # JUNIOR

# Escalar hasta encontrar quien pueda
supervisor = orchestrator.escalate(agent)
while supervisor:
    if supervisor.rank >= Rank.SENIOR:
        # Este puede manejarlo
        break
    supervisor = orchestrator.escalate(supervisor.name)
```

### Route with Fallback

```python
async def route_with_fallback(self, task, max_attempts=3):
    scores = self._score_agents(task)

    for score in scores[:max_attempts]:
        try:
            response = await score.agent.execute(task)
            if response.success:
                return response
        except Exception:
            continue  # Pasar al siguiente

    return AgentResponse(success=False, ...)
```

## Ventajas

- Desacoplamiento entre emisor y receptor
- Flexibilidad en la cadena
- Facil agregar/remover handlers

## Relacionado

- [[Enciclopedia/OrchestratorAgent|OrchestratorAgent]] - Implementa la cadena
- [[Enciclopedia/AgentHierarchy|AgentHierarchy]] - Define la estructura
- [[Enciclopedia/Rank|Rank]] - Determina capacidad

## Tags

#patron #chain #diseno
"""

# ============================================
# EJECUTAR
# ============================================
if __name__ == "__main__":
    notes = [
        # Indice
        ("Enciclopedia/Enciclopedia.md", INDEX),

        # Agentes
        ("Enciclopedia/AgentCapability.md", AGENT_CAPABILITY),
        ("Enciclopedia/AgentHierarchy.md", AGENT_HIERARCHY),
        ("Enciclopedia/AgentProfile.md", AGENT_PROFILE),
        ("Enciclopedia/AgentResponse.md", AGENT_RESPONSE),
        ("Enciclopedia/BaseAgent.md", BASE_AGENT),
        ("Enciclopedia/Department.md", DEPARTMENT),
        ("Enciclopedia/OrchestratorAgent.md", ORCHESTRATOR),
        ("Enciclopedia/Rank.md", RANK),
        ("Enciclopedia/Registry.md", REGISTRY),

        # Scraping
        ("Enciclopedia/BaseSite.md", BASE_SITE),
        ("Enciclopedia/BaseParser.md", BASE_PARSER),
        ("Enciclopedia/CarListing.md", CAR_LISTING),
        ("Enciclopedia/HeadlessX.md", HEADLESSX),
        ("Enciclopedia/SiteConfig.md", SITE_CONFIG),
        ("Enciclopedia/SiteRegistry.md", SITE_REGISTRY),

        # Sitios
        ("Enciclopedia/CochesNet.md", COCHES_NET),
        ("Enciclopedia/Autocasion.md", AUTOCASION),
        ("Enciclopedia/Clicars.md", CLICARS),

        # Debug
        ("Enciclopedia/Debug.md", DEBUG),
        ("Enciclopedia/DebugLevel.md", DEBUG_LEVEL),
        ("Enciclopedia/FlowEntry.md", FLOW_ENTRY),
        ("Enciclopedia/ExecutionContext.md", EXECUTION_CONTEXT),
        ("Enciclopedia/debug_flow.md", DEBUG_FLOW_DECORATOR),

        # Database
        ("Enciclopedia/SupabaseClient.md", SUPABASE_CLIENT),
        ("Enciclopedia/Upsert.md", UPSERT),
        ("Enciclopedia/Objetivos.md", OBJETIVOS),

        # Patrones
        ("Enciclopedia/Singleton.md", SINGLETON),
        ("Enciclopedia/AbstractFactory.md", ABSTRACT_FACTORY),
        ("Enciclopedia/Strategy.md", STRATEGY),
        ("Enciclopedia/ChainOfResponsibility.md", CHAIN_OF_RESPONSIBILITY),
    ]

    print("Creando Enciclopedia en Obsidian...")
    print("=" * 50)

    for path, content in notes:
        status = create_note(path, content)
        status_icon = "OK" if status in [200, 201, 204] else "ERR"
        print(f"[{status_icon}] {path}")

    print("=" * 50)
    print(f"Total: {len(notes)} notas creadas")
