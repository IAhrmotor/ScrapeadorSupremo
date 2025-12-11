"""Script to create changelog note in Obsidian."""

import httpx
from datetime import datetime

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
# CHANGELOG 2025-12-05
# ============================================
CHANGELOG = """# Changelog - 5 Diciembre 2025

[[ScrapeadorSupremo/ScrapeadorSupremo|← Volver al proyecto]]

## Resumen del Dia

Mejoras significativas en el sistema de scraping con tres lineas principales de trabajo:

1. **Paralelismo en Cochesnet** - Scraping simultaneo de multiples anos
2. **Scraper de Autocasion** - Implementacion completa con anti-deteccion
3. **Nuevo sitio: OcasionPlus** - Arquitectura y parser para infinite scroll

---

## 1. Paralelismo en Cochesnet

### Problema
El scraping secuencial de anos (2007-2025) era muy lento, tardando horas en completar.

### Solucion Implementada

Se agrego **scraping paralelo real** usando `httpx.AsyncClient` con las siguientes caracteristicas:

#### Nuevos Metodos en `CochesnetScraperAgent`

```python
# Cliente async reutilizable con connection pooling
async def _get_async_client(self) -> httpx.AsyncClient

# Fetch async con reintentos y backoff exponencial
async def _fetch_with_headlessx_async(url, log_callback, max_retries=3) -> str

# Scraping paralelo con semaforo de concurrencia
async def _scrape_years_parallel(years, progress_callback, log_callback, max_workers=2)
```

#### Caracteristicas del Paralelismo

| Caracteristica | Implementacion |
|----------------|----------------|
| **Concurrencia controlada** | `asyncio.Semaphore(max_workers)` limita workers simultaneos |
| **Connection pooling** | `httpx.AsyncClient` reutilizado para todas las requests |
| **Thread-safe counters** | `asyncio.Lock()` para contadores de progreso |
| **Rotacion de perfiles** | Round-robin en lugar de aleatorio para mejor distribucion |
| **Retry con backoff** | Reintentos 1s, 2s, 4s en caso de timeout |
| **Cleanup automatico** | `_close_async_client()` al finalizar |

#### Uso

```python
# Scraping secuencial (por defecto)
await agent.scrape_years([2020, 2021, 2022])

# Scraping paralelo (2 workers simultaneos)
await agent.scrape_years([2020, 2021, 2022], parallel=True, max_workers=2)
```

#### Mejora de Rendimiento

Con `max_workers=2`:
- **~2x mas rapido** que secuencial
- Con `max_workers=3`: ~3x mas rapido
- Limitado por rate limiting del servidor HeadlessX

### Archivos Modificados

- `scraping/sites/cochesnet/app/scraper_agent.py` - Metodos paralelos

---

## 2. Scraper de Autocasion

### Implementacion Completa

Se implemento el scraper completo para **Autocasion.com** con las siguientes caracteristicas:

#### Arquitectura

```
scraping/sites/autocasion/
├── site.py              # AutocasionSite con configuracion
├── parser.py            # AutocasionParser (JSON-LD + HTML)
└── app/
    ├── scraper_agent.py # AutocasionScraperAgent
    ├── headlessx_client.py # Cliente HeadlessX encapsulado
    ├── runner.py        # CLI runner
    └── gui.py           # Interfaz grafica
```

#### Caracteristicas del Scraper

| Caracteristica | Valor |
|----------------|-------|
| **Anti-deteccion** | HeadlessX con fingerprint spoofing completo |
| **Rotacion de perfiles** | device/geo/behavior profiles aleatorios |
| **Fallback** | HeadlessX stealth → HeadlessX normal → requests |
| **Modo ALL PAGES** | `max_pages=0` scrapea todas las paginas |
| **Guardado incremental** | Cada pagina se guarda inmediatamente |

#### Perfiles Disponibles

```python
DEVICE_PROFILES = [
    "high-end-desktop", "mid-range-desktop", "low-end-desktop",
    "high-end-laptop", "mid-range-laptop", "macbook-pro", "macbook-air"
]
GEO_PROFILES = ["spain", "us-east", "us-west", "uk", "germany", "france"]
BEHAVIOR_PROFILES = ["natural", "cautious", "confident"]
```

#### HeadlessX Config Optimizada

```python
HeadlessXConfig(
    timeout=60000,
    extra_wait_time=3000,
    wait_until="networkidle",
    enable_canvas_spoofing=True,
    enable_webgl_spoofing=True,
    enable_audio_spoofing=True,
    enable_webrtc_blocking=True,
    enable_advanced_stealth=True,
    simulate_mouse_movement=True,
    simulate_scrolling=True,
    human_delays=True,
    randomize_timings=True,
    scroll_to_bottom=True
)
```

#### Uso

```python
agent = AutocasionScraperAgent()

# Scrapear una marca (todas las paginas)
result = await agent.scrape_marca("audi", max_pages=0)

# Scrapear multiples marcas
results = await agent.scrape_batch(["audi", "bmw", "mercedes"])

# Scrapear desde objetivos en Supabase
results = await agent.scrape_from_objetivos(limit=10)
```

### Archivos Creados/Modificados

- `scraping/sites/autocasion/app/scraper_agent.py` - Agente completo
- `scraping/sites/autocasion/app/headlessx_client.py` - Cliente encapsulado

---

## 3. Nuevo Sitio: OcasionPlus

### Planteamiento

**OcasionPlus.com** usa un patron diferente: **Infinite Scroll** en lugar de paginacion tradicional.

#### Diferencias con otros sitios

| Aspecto | Cochesnet/Autocasion | OcasionPlus |
|---------|----------------------|-------------|
| **Patron** | Paginacion `?pg=N` | Infinite scroll |
| **Carga** | Nueva pagina | Mismo DOM, mas items |
| **Scraping** | Request por pagina | Scroll + wait + parse |

### Arquitectura Implementada

```
scraping/sites/ocasionplus/
├── site.py              # OcasionPlusSite con config de scroll
├── parser.py            # OcasionPlusParser con selectores CSS
└── app/
    ├── scraper_agent.py       # OcasionPlusScraperAgent
    ├── headlessx_scraper.py   # Scraper con HeadlessX
    ├── playwright_scraper.py  # Scraper con Playwright (scroll real)
    └── gui.py                 # Interfaz grafica
```

### Modelo de Datos: OcasionPlusListing

```python
@dataclass
class OcasionPlusListing:
    # Identificacion
    url: str
    listing_id: str

    # Vehiculo
    marca: str
    modelo: str
    version: str
    potencia_cv: Optional[int]
    titulo_completo: str

    # Precios (3 tipos!)
    precio_contado: Optional[int]      # 39990
    precio_financiado: Optional[int]   # 36355
    cuota_mensual: Optional[int]       # 559/mes

    # Caracteristicas
    year: Optional[int]
    kilometros: Optional[int]
    combustible: str
    transmision: str
    etiqueta_ambiental: str  # C, B, ECO, 0

    # Ubicacion
    ubicacion: str

    # Media
    imagen_url: str
```

### Parser con Selectores data-test

```python
SELECTORS = {
    "card": "div.cardVehicle_card__LwFCi",
    "brand_model": "[data-test='span-brand-model']",
    "version": "[data-test='span-version']",
    "price": "[data-test='span-price']",
    "finance_price": "[data-test='span-finance']",
    "year": "[data-test='span-registration-date']",
    "km": "[data-test='span-km']",
    "fuel": "[data-test='span-fuel-type']",
    "transmission": "[data-test='span-engine-transmission']",
}
```

### Estrategia de Scraping

```python
# Para pocas iteraciones (quick scrape)
if max_iterations <= 5:
    use HeadlessX (scrollToBottom: true)

# Para muchas iteraciones (full scrape)
else:
    use Playwright con scroll loop real
```

### Tabla Supabase

```sql
CREATE TABLE ocasionplus (
    id BIGSERIAL PRIMARY KEY,
    listing_id TEXT UNIQUE NOT NULL,
    url TEXT,
    marca TEXT,
    modelo TEXT,
    version TEXT,
    titulo_completo TEXT,
    potencia TEXT,
    potencia_cv INTEGER,
    precio TEXT,
    precio_contado INTEGER,
    precio_financiado INTEGER,
    cuota_mensual INTEGER,
    year INTEGER,
    kilometros TEXT,
    kilometros_numeric INTEGER,
    combustible TEXT,
    transmision TEXT,
    etiqueta_ambiental TEXT,
    ubicacion TEXT,
    imagen_url TEXT,
    scraped_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Supabase Client Actualizado

Se agrego soporte para OcasionPlus en `SupabaseClient`:

```python
TABLE_MAPPING = {
    "cochesnet": "cochesnet",
    "autocasion": "autocasion",
    "clicars": "clicars",
    "ocasionplus": "ocasionplus"  # NUEVO
}

def _dict_to_ocasionplus(self, data: Dict) -> Dict:
    \"\"\"Convert OcasionPlusListing.to_dict() to table format.\"\"\"
    ...

def save_ocasionplus_listings(self, listings_data: List[Dict]) -> Dict:
    \"\"\"Save OcasionPlus listings to database.\"\"\"
    ...
```

### Archivos Creados

- `scraping/sites/ocasionplus/site.py`
- `scraping/sites/ocasionplus/parser.py`
- `scraping/sites/ocasionplus/app/scraper_agent.py`
- `scraping/sites/ocasionplus/app/headlessx_scraper.py`
- `scraping/sites/ocasionplus/app/playwright_scraper.py`
- `scraping/sites/ocasionplus/app/gui.py`
- `scripts/create_table_ocasionplus.sql`
- `scraping/storage/supabase_client.py` (actualizado)

---

## Resumen de Cambios

### Archivos Nuevos (14)

| Archivo | Descripcion |
|---------|-------------|
| `ocasionplus/site.py` | Configuracion del sitio |
| `ocasionplus/parser.py` | Parser HTML con data-test |
| `ocasionplus/app/scraper_agent.py` | Agente de scraping |
| `ocasionplus/app/headlessx_scraper.py` | Scraper HeadlessX |
| `ocasionplus/app/playwright_scraper.py` | Scraper Playwright |
| `ocasionplus/app/gui.py` | Interfaz grafica |
| `scripts/create_table_ocasionplus.sql` | Schema SQL |
| `Enciclopedia/*.md` | 31 notas de documentacion |

### Archivos Modificados (3)

| Archivo | Cambio |
|---------|--------|
| `cochesnet/app/scraper_agent.py` | Metodos de paralelismo async |
| `autocasion/app/scraper_agent.py` | Implementacion completa |
| `storage/supabase_client.py` | Soporte OcasionPlus |

---

## Proximos Pasos

1. **OcasionPlus**: Testear scraper en produccion
2. **Paralelismo**: Optimizar max_workers segun capacidad de HeadlessX
3. **Monitoreo**: Agregar metricas de rendimiento
4. **GUI Unificada**: Panel para controlar todos los scrapers

---

## Tags

#changelog #desarrollo #2025-12-05 #scraping #paralelismo
"""

# ============================================
# EJECUTAR
# ============================================
if __name__ == "__main__":
    today = datetime.now().strftime("%Y-%m-%d")
    path = f"ScrapeadorSupremo/Changelog-{today}.md"

    status = create_note(path, CHANGELOG)

    if status in [200, 201, 204]:
        print(f"Changelog creado: {path}")
    else:
        print(f"Error creando changelog: {status}")
