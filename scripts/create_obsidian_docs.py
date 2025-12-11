"""Script to create ScrapeadorSupremo documentation in Obsidian."""

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
# NOTA 1: Index Principal
# ============================================
INDEX_CONTENT = """# ScrapeadorSupremo

Sistema multi-agente con organizacion jerarquica por departamentos y rangos para scraping de coches.

## Quick Links

- [[ScrapeadorSupremo/Arquitectura|Arquitectura General]]
- [[ScrapeadorSupremo/Jerarquia-Agentes|Sistema de Jerarquia]]
- [[ScrapeadorSupremo/Sistema-Debug|Sistema de Debug]]
- [[ScrapeadorSupremo/Modulo-Scraping|Modulo de Scraping]]
- [[ScrapeadorSupremo/Supabase-Storage|Storage con Supabase]]

## Estructura del Proyecto

```
ScrapeadorSupremo/
├── main.py                 # Entry point
├── core/                   # Core utilities
│   └── debug.py           # Debug system
├── agents/                 # Runtime Python agents
│   ├── base_agent.py      # BaseAgent ABC
│   ├── registry.py        # Agent auto-discovery
│   ├── hierarchy.py       # Departments, Ranks (22 agents)
│   └── orchestrator.py    # OrchestratorAgent
└── scraping/              # Web scraping module
    ├── base/              # Abstract classes
    ├── engine/            # HeadlessX engine
    ├── sites/             # Site implementations
    └── storage/           # Supabase persistence
```

## Comando Principal

```bash
python main.py  # Run orchestrator demo
```

## Tags

#proyecto #scraping #multi-agente #python
"""

# ============================================
# NOTA 2: Arquitectura
# ============================================
ARQUITECTURA_CONTENT = """# Arquitectura - ScrapeadorSupremo

[[ScrapeadorSupremo/ScrapeadorSupremo|← Volver al indice]]

## Vision General

ScrapeadorSupremo es un sistema multi-agente disenado para scraping de anuncios de coches de segunda mano en Espana. Combina:

1. **Sistema de agentes con jerarquia organizacional**
2. **Motor de scraping con HeadlessX**
3. **Persistencia en Supabase**

## Componentes Principales

### 1. Core (`core/`)

| Archivo | Descripcion |
|---------|-------------|
| `debug.py` | Sistema de debug con niveles (OFF, ERROR, WARN, INFO, DEBUG, TRACE) |

### 2. Agentes (`agents/`)

| Archivo | Descripcion |
|---------|-------------|
| `base_agent.py` | Clase base abstracta `BaseAgent` |
| `registry.py` | Auto-descubrimiento de agentes |
| `hierarchy.py` | Departamentos, Rangos, 22 perfiles de agentes |
| `orchestrator.py` | Orquestador que rutea tareas |

### 3. Scraping (`scraping/`)

| Carpeta | Descripcion |
|---------|-------------|
| `base/` | Clases abstractas (`BaseSite`, `BaseParser`) |
| `engine/` | Motor HeadlessX para renderizado |
| `sites/` | Implementaciones por sitio |
| `storage/` | Cliente Supabase |

## Flujo de Datos

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│ Orchestrator│────▶│  Site Agent  │────▶│  HeadlessX  │
└─────────────┘     └──────────────┘     └─────────────┘
                           │                    │
                           ▼                    ▼
                    ┌──────────────┐     ┌─────────────┐
                    │   Parser     │◀────│    HTML     │
                    └──────────────┘     └─────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │   Supabase   │
                    └──────────────┘
```

## Patrones de Diseno

- **Abstract Factory**: `BaseSite` y `BaseParser`
- **Singleton**: Debug, Registry, Hierarchy
- **Strategy**: Parsers especificos por sitio
- **Chain of Responsibility**: Escalation en jerarquia

## Tags

#arquitectura #diseno #patrones
"""

# ============================================
# NOTA 3: Jerarquia de Agentes
# ============================================
JERARQUIA_CONTENT = """# Sistema de Jerarquia de Agentes

[[ScrapeadorSupremo/ScrapeadorSupremo|← Volver al indice]]

## Rangos (de menor a mayor autoridad)

| Rank | Valor | Descripcion |
|------|-------|-------------|
| JUNIOR | 1 | Tareas simples, ejecucion directa |
| SENIOR | 2 | Tareas complejas, supervisa juniors |
| LEAD | 3 | Lidera equipo, decisiones tecnicas |
| ARCHITECT | 4 | Disena sistemas, arquitectura |
| DIRECTOR | 5 | Dirige departamento, estrategia |

## Departamentos

### IA (`departamento_ia`)

| Agente | Rango | Especialidades |
|--------|-------|----------------|
| prompt-engineer | ARCHITECT | prompt optimization, chain-of-thought |
| ai-engineer | LEAD | LLM integration, RAG systems, embeddings |
| task-decomposition-expert | SENIOR | task decomposition, workflow design |
| prompt-assistant | JUNIOR | prompt formatting, templates |

### Desarrollo (`departamento_desarrollo`)

| Agente | Rango | Especialidades |
|--------|-------|----------------|
| backend-architect | ARCHITECT | REST APIs, microservices, databases |
| frontend-developer | SENIOR | React, CSS, accessibility |
| python-pro | SENIOR | Python, async/await, pytest |
| javascript-pro | SENIOR | ES6+, Node.js, TypeScript |
| code-formatter | JUNIOR | formatting, linting |

### Calidad (`departamento_calidad`)

| Agente | Rango | Especialidades |
|--------|-------|----------------|
| qa-architect | ARCHITECT | test architecture, QA strategy |
| code-reviewer | LEAD | code review, security |
| error-detective | SENIOR | log analysis, debugging |
| test-writer | JUNIOR | unit tests, pytest |

### Documentacion (`departamento_documentacion`)

| Agente | Rango | Especialidades |
|--------|-------|----------------|
| doc-architect | ARCHITECT | documentation architecture |
| api-documenter | SENIOR | OpenAPI, SDK generation |
| readme-writer | JUNIOR | README, markdown |

### Operaciones (`departamento_operaciones`)

| Agente | Rango | Especialidades |
|--------|-------|----------------|
| devops-architect | ARCHITECT | DevOps, CI/CD, Docker |
| deploy-engineer | SENIOR | deployment, releases |
| monitor-agent | JUNIOR | monitoring, alerts |

### Datos (`departamento_datos`)

| Agente | Rango | Especialidades |
|--------|-------|----------------|
| data-architect | ARCHITECT | data architecture, ETL |
| data-engineer | SENIOR | data pipelines, pandas |
| scraper-specialist | SENIOR | web scraping, HeadlessX |
| supabase-engineer | SENIOR | Supabase, PostgreSQL, RLS |
| cochesnet-scraper | JUNIOR | coches.net parsing |
| autocasion-scraper | JUNIOR | autocasion.com parsing |
| data-cleaner | JUNIOR | data cleaning, validation |

## Metodos del Orchestrator

```python
# Rutear a departamento
agent = orchestrator.route_to_department(task, Department.DATOS, Rank.SENIOR)

# Escalar a supervisor
supervisor = orchestrator.escalate("python-pro")  # → backend-architect

# Delegar hacia abajo
delegate = orchestrator.delegate_down("data-architect", task)

# Buscar experto
experts = orchestrator.find_expert("scraping")  # → [scraper-specialist]
```

## Tags

#agentes #jerarquia #organizacion
"""

# ============================================
# NOTA 4: Sistema de Debug
# ============================================
DEBUG_CONTENT = """# Sistema de Debug

[[ScrapeadorSupremo/ScrapeadorSupremo|← Volver al indice]]

## Niveles de Debug

| Nivel | Valor | Descripcion |
|-------|-------|-------------|
| OFF | 0 | Desactivado |
| ERROR | 1 | Solo errores |
| WARN | 2 | Errores + warnings |
| INFO | 3 | Flujo normal |
| DEBUG | 4 | Debug detallado |
| TRACE | 5 | Todo incluyendo entry/exit |

## Uso Basico

```python
from core.debug import get_debugger, DebugLevel

debug = get_debugger()
debug.set_level(DebugLevel.DEBUG)
debug.show_timestamps = True

# Logging por nivel
debug.error("component", "Error message", {"key": "value"})
debug.warn("component", "Warning message")
debug.info("component", "Info message")
debug.debug("component", "Debug message")
debug.trace("component", "Trace message")
```

## Flow Tracking

```python
# Marcar inicio/fin de operaciones
start_time = debug.flow_start("component", "action")
# ... codigo ...
debug.flow_end("component", "action", start_time)

# Pasos intermedios
debug.flow_step("component", "step_name", "description")
```

## Decorator @debug_flow

```python
from core.debug import debug_flow

@debug_flow("my_component")
def my_function(x, y):
    return x + y

# Automaticamente logea:
# [TRACE] ENTER my_function
# [TRACE] EXIT my_function (duration_ms)
```

## Context Management

```python
# Iniciar contexto de tarea
debug.start_context("task_123", department="datos")

# Agregar agente a la cadena
debug.add_to_agent_chain("scraper-specialist")

# Finalizar contexto
ctx = debug.end_context("task_123")
```

## Reporte de Flujo

```python
debug.print_flow_report()

# Output:
# ============================================================
# EXECUTION FLOW REPORT
# ============================================================
# Total entries: 42
# Total time: 3.25s
# Components: orchestrator, scraper, parser
# Level breakdown:
#   INFO: 30
#   DEBUG: 10
#   ERROR: 2
# ============================================================
```

## Tags

#debug #logging #tracing
"""

# ============================================
# NOTA 5: Modulo de Scraping
# ============================================
SCRAPING_CONTENT = """# Modulo de Scraping

[[ScrapeadorSupremo/ScrapeadorSupremo|← Volver al indice]]

## Estructura

```
scraping/
├── base/
│   ├── site.py          # BaseSite, SiteConfig, SiteRegistry
│   ├── parser.py        # BaseParser, CarListing
│   └── title_parser.py  # Parsing de titulos
├── engine/
│   └── headlessx.py     # Cliente HeadlessX
├── sites/
│   ├── cochesnet/       # Coches.net implementation
│   ├── autocasion/      # Autocasion implementation
│   └── clicars/         # Clicars implementation
└── storage/
    └── supabase_client.py
```

## BaseSite

Clase abstracta que define la interfaz para cada sitio:

```python
class BaseSite(ABC):
    config: SiteConfig
    parser: BaseParser

    @abstractmethod
    def build_search_url(self, marca: str, year: int = None, page: int = 1) -> str:
        pass

    @abstractmethod
    def detect_block(self, html: str) -> tuple:
        pass

    def parse(self, html: str) -> List[CarListing]:
        return self.parser.parse(html)
```

## SiteConfig

```python
@dataclass
class SiteConfig:
    name: str                      # "cochesnet"
    display_name: str              # "Coches.net"
    base_url: str                  # "https://www.coches.net"
    search_path: str               # "/segunda-mano"
    delay_between_requests: float  # 2.0 segundos
    max_pages_per_search: int      # 100
    items_per_page: int            # 30
```

## CarListing (dataclass)

```python
@dataclass
class CarListing:
    ad_id: str
    url: str
    title: str
    marca: str
    modelo: str
    version: Optional[str]
    year: Optional[int]
    kilometers: Optional[str]
    fuel: Optional[str]
    price: Optional[str]
    power: Optional[str]
    location: Optional[str]
    source: str  # "cochesnet", "autocasion", "clicars"
```

## Sitios Soportados

### Coches.net
- Parser: `__INITIAL_PROPS__` JSON embedding
- Anti-bot: Cloudflare
- URL pattern: `/segunda-mano/?marca={marca}&pg={page}`

### Autocasion
- Parser: JSON-LD + HTML
- Anti-bot: Moderate
- URL pattern: `/coches-segunda-mano/{marca}.htm?pagina={page}`

### Clicars
- Parser: API JSON + Playwright
- Anti-bot: Low
- URL pattern: API-based

## HeadlessX Engine

Servicio externo para renderizado de JavaScript:

```python
from scraping.engine.headlessx import HeadlessXClient

client = HeadlessXClient()
html = await client.render("https://www.coches.net/...")
```

## Tags

#scraping #parser #sites
"""

# ============================================
# NOTA 6: Supabase Storage
# ============================================
SUPABASE_CONTENT = """# Storage con Supabase

[[ScrapeadorSupremo/ScrapeadorSupremo|← Volver al indice]]

## Configuracion

Variables de entorno requeridas:
```
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=eyJhbG...
```

## Tablas de Datos

| Tabla | Descripcion |
|-------|-------------|
| cochesnet | Anuncios de Coches.net |
| autocasion | Anuncios de Autocasion |
| clicars | Anuncios de Clicars |

## Tablas de Objetivos

| Tabla | Descripcion |
|-------|-------------|
| objetivo_coches_net | Marcas a scrapear en Coches.net |
| objetivo_autocasion | Marcas a scrapear en Autocasion |

## Uso del Cliente

```python
from scraping.storage.supabase_client import get_supabase_client

client = get_supabase_client()

# Guardar listings
stats = client.save_listings(listings)
# {"cochesnet": 30, "autocasion": 0, "errors": 0}

# Obtener objetivos pendientes
objetivos = client.get_pending_objetivos("cochesnet", limit=10)

# Actualizar estado
client.update_objetivo_status(
    source="cochesnet",
    marca="audi",
    status="success",
    cars_scraped=150,
    pages_scraped=5
)

# Estadisticas
stats = client.get_stats()
```

## Esquema de Datos (cochesnet)

| Campo | Tipo | Descripcion |
|-------|------|-------------|
| ad_id | TEXT PK | ID del anuncio |
| url | TEXT | URL completa |
| title | TEXT | Titulo |
| marca | TEXT | Marca |
| modelo | TEXT | Modelo |
| version | TEXT | Version/acabado |
| year | TEXT | Ano |
| kilometers | TEXT | Kilometraje texto |
| kilometers_numeric | INT | Kilometraje numerico |
| price | TEXT | Precio texto |
| price_numeric | INT | Precio numerico |
| fuel | TEXT | Combustible |
| power | TEXT | Potencia |
| location | TEXT | Ubicacion |
| scraped_at | TIMESTAMP | Fecha scraping |
| activo | BOOLEAN | Esta activo |

## Upsert por ad_id

El cliente usa upsert con `on_conflict="ad_id"` para evitar duplicados:

```python
result = self.client.table(table_name).upsert(
    data,
    on_conflict="ad_id"
).execute()
```

## Tags

#supabase #database #storage #postgresql
"""

# ============================================
# EJECUTAR
# ============================================
if __name__ == "__main__":
    notes = [
        ("ScrapeadorSupremo/ScrapeadorSupremo.md", INDEX_CONTENT),
        ("ScrapeadorSupremo/Arquitectura.md", ARQUITECTURA_CONTENT),
        ("ScrapeadorSupremo/Jerarquia-Agentes.md", JERARQUIA_CONTENT),
        ("ScrapeadorSupremo/Sistema-Debug.md", DEBUG_CONTENT),
        ("ScrapeadorSupremo/Modulo-Scraping.md", SCRAPING_CONTENT),
        ("ScrapeadorSupremo/Supabase-Storage.md", SUPABASE_CONTENT),
    ]

    for path, content in notes:
        status = create_note(path, content)
        print(f"{path}: {status}")

    print("\nDocumentacion creada en Obsidian!")
