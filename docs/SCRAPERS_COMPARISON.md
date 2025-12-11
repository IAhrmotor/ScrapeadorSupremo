# Comparación de Scrapers: Autocasion vs Clicars

Este documento explica el funcionamiento de ambos scrapers y sus diferencias arquitectónicas.

---

## 1. Scraper de Autocasion

### 1.1 Patrón de Scraping: **PAGINACIÓN TRADICIONAL**

Autocasion usa URLs con parámetros de página para navegar por los resultados:
```
https://www.autocasion.com/coches-segunda-mano/audi?p=1
https://www.autocasion.com/coches-segunda-mano/audi?p=2
https://www.autocasion.com/coches-segunda-mano/audi?p=3
...
```

### 1.2 Arquitectura

```
scraping/sites/autocasion/
├── site.py              # Configuración y detección de páginas
├── parser.py            # Extracción de datos del HTML
└── app/
    ├── headlessx_client.py    # Cliente anti-detección
    └── scraper_agent.py       # Agente runtime con lógica principal
```

### 1.3 Flujo de Scraping

```
┌─────────────────────────────────────────────────────────────┐
│ 1. INICIALIZACIÓN                                           │
│    - Crear agente AutocasionScraperAgent                   │
│    - Configurar HeadlessX con profile rotation             │
│    - Conectar a Supabase                                    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. SCRAPING POR MARCA (ejemplo: "audi")                    │
│                                                              │
│    page = 1                                                 │
│    while page <= max_pages OR all_pages_mode:               │
│                                                              │
│      ┌──────────────────────────────────────┐              │
│      │ 2.1 Construir URL                     │              │
│      │  url = build_search_url(marca, page)  │              │
│      │  → /coches-segunda-mano/audi?p=1     │              │
│      └──────────────────────────────────────┘              │
│                     ↓                                        │
│      ┌──────────────────────────────────────┐              │
│      │ 2.2 Fetch con HeadlessX               │              │
│      │  - Rotar profile (device/geo/behavior)│              │
│      │  - render_stealth() si es necesario   │              │
│      │  - Verificar bloqueos (Cloudflare)    │              │
│      └──────────────────────────────────────┘              │
│                     ↓                                        │
│      ┌──────────────────────────────────────┐              │
│      │ 2.3 Parsear HTML                      │              │
│      │  - Extraer listings con BeautifulSoup │              │
│      │  - Detectar total_pages (página 1)    │              │
│      │  - Verificar next_page_url            │              │
│      └──────────────────────────────────────┘              │
│                     ↓                                        │
│      ┌──────────────────────────────────────┐              │
│      │ 2.4 Guardar en Supabase (incremental) │              │
│      │  - save_listings(listings)            │              │
│      │  - Tabla: autocasion                  │              │
│      │  - Upsert por ad_id                   │              │
│      └──────────────────────────────────────┘              │
│                     ↓                                        │
│      page += 1                                              │
│      await asyncio.sleep(delay_between_pages)               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. FINALIZACIÓN                                             │
│    - update_objetivo_status()                               │
│    - Retornar ScrapeResult con estadísticas                 │
└─────────────────────────────────────────────────────────────┘
```

### 1.4 Componentes Clave

#### A) HeadlessX Client (headlessx_client.py)

**Anti-detección avanzada:**
```python
HeadlessXConfig(
    timeout=60000,
    wait_until="networkidle",

    # Profiles para rotation
    device_profile="mid-range-desktop",    # 7 opciones
    geo_profile="spain",                   # 6 países
    behavior_profile="natural",            # 3 patrones

    # Spoofing
    enable_canvas_spoofing=True,
    enable_webgl_spoofing=True,
    enable_audio_spoofing=True,
    enable_webrtc_blocking=True,

    # Comportamiento humano
    simulate_mouse_movement=True,
    simulate_scrolling=True,
    human_delays=True,
    randomize_timings=True
)
```

**Métodos principales:**
- `render(url, config)` - Renderizado normal
- `render_stealth(url, config)` - Modo stealth máximo
- `get_status()` - Estado del servidor
- `is_available()` - Verificar disponibilidad

#### B) Site Configuration (site.py)

```python
@dataclass
class AutocasionConfig:
    base_url: str = "https://www.autocasion.com"

    # Delays para comportamiento humano
    delay_between_requests: float = 2.0
    delay_between_pages: float = 3.0

    # Timeouts
    request_timeout: int = 30
    max_retries: int = 3
```

**Detección de páginas totales:**
```python
def get_total_pages(self, html: str) -> int:
    """
    Detecta total de páginas desde:
    1. Botones de paginación (<a href="?p=23">)
    2. Metadata JSON-LD
    3. Patrón: "Mostrando X de Y resultados"
    """
```

#### C) Parser (parser.py)

**Extracción de datos:**
```python
def parse(self, html: str) -> List[CarListing]:
    soup = BeautifulSoup(html, 'lxml')

    # Encontrar tarjetas de coches
    car_cards = soup.find_all('div', class_='listing-card')

    for card in car_cards:
        listing = CarListing(
            ad_id=extract_ad_id(card),
            marca=card.get('data-brand'),
            modelo=card.get('data-model'),
            year=extract_year(card),
            kilometers=extract_km(card),
            price=extract_price(card),
            # ... más campos
        )
```

**Campos extraídos:**
- `ad_id` - Identificador único
- `marca` - Marca normalizada
- `modelo` - Modelo del coche
- `version` - Versión específica
- `year` - Año de fabricación (int)
- `kilometers` - Kilometraje (int)
- `power_cv` - Potencia en CV (int)
- `transmission` - Manual/Automático
- `fuel` - Tipo de combustible
- `price` - Precio (int)
- `location` - Ubicación del vendedor
- `url` - URL del anuncio

#### D) Scraper Agent (scraper_agent.py)

**Profile Rotation:**
```python
def _rotate_profile(self) -> HeadlessXConfig:
    """Rota perfiles entre marcas para evitar detección."""
    device = random.choice(DEVICE_PROFILES)
    geo = random.choice(GEO_PROFILES)
    behavior = random.choice(BEHAVIOR_PROFILES)

    return replace(self._headlessx_config,
                   device_profile=device,
                   geo_profile=geo,
                   behavior_profile=behavior)
```

**Métodos principales:**
```python
async def scrape_marca(
    marca: str,
    max_pages: int = 10,      # 0 = todas las páginas
    save_to_db: bool = True,
    stealth: bool = False
) -> ScrapeResult

async def scrape_batch(
    marcas: List[str],
    max_pages: int = 5
) -> List[ScrapeResult]

async def scrape_from_objetivos(
    limit: int = 10
) -> List[ScrapeResult]
```

### 1.5 Guardado en Supabase

**Tabla: `autocasion`**
```sql
CREATE TABLE autocasion (
    id BIGSERIAL PRIMARY KEY,
    ad_id TEXT UNIQUE NOT NULL,
    url TEXT,
    title TEXT,
    marca TEXT,
    modelo TEXT,
    version TEXT,
    year INTEGER,

    -- Kilometraje (dual format)
    kilometers TEXT,              -- "119.763 km"
    kilometers_numeric INTEGER,   -- 119763

    -- Potencia (dual format)
    power TEXT,                   -- "110 CV"
    power_numeric INTEGER,        -- 110

    -- Precio (dual format)
    price TEXT,                   -- "23.490 €"
    price_numeric INTEGER,        -- 23490

    fuel TEXT,
    transmission TEXT,
    location TEXT,

    scraped_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Guardado incremental:**
```python
# Guardar cada página inmediatamente (no esperar al final)
for page in range(1, total_pages + 1):
    listings = fetch_and_parse(page)

    # Guardar inmediatamente
    stats = supabase.save_listings(listings)
    saved += stats["autocasion"]
```

---

## 2. Scraper de Clicars

### 2.1 Patrón de Scraping: **INFINITE SCROLL**

Clicars usa una **sola URL** con carga dinámica mediante JavaScript:
```
https://www.clicars.com/coches-segunda-mano-ocasion
```

Los coches se cargan progresivamente haciendo **scroll + click** en el botón "Ver más":
```
Página inicial: 12 coches
↓ Scroll + Click "Ver más"
24 coches
↓ Scroll + Click "Ver más"
36 coches
↓ Scroll + Click "Ver más"
48 coches
...hasta 300+ coches
```

### 2.2 Arquitectura

```
scraping/sites/clicars/
├── site.py                # Configuración para infinite scroll
├── parser.py              # Extracción de datos del HTML
└── app/
    ├── playwright_scraper.py    # Playwright para JS execution
    └── scraper_agent.py         # Agente runtime
```

### 2.3 Flujo de Scraping

```
┌─────────────────────────────────────────────────────────────┐
│ 1. INICIALIZACIÓN                                           │
│    - Crear agente ClicarsScraperAgent                      │
│    - Inicializar Playwright con stealth                     │
│    - Conectar a Supabase                                    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. INICIO DE PLAYWRIGHT BROWSER                             │
│                                                              │
│    ┌──────────────────────────────────────┐                │
│    │ playwright.chromium.launch()          │                │
│    │  - Headless mode                      │                │
│    │  - Args anti-detection:               │                │
│    │    --disable-blink-features           │                │
│    │    --no-sandbox                       │                │
│    │  - Viewport: 1920x1080                │                │
│    │  - User-Agent: Chrome 120             │                │
│    │  - Locale: es-ES                      │                │
│    │  - Timezone: Europe/Madrid            │                │
│    └──────────────────────────────────────┘                │
│                     ↓                                        │
│    ┌──────────────────────────────────────┐                │
│    │ Inyectar scripts anti-detección       │                │
│    │  - navigator.webdriver = false        │                │
│    │  - window.chrome = {runtime: {}}      │                │
│    │  - Mock plugins, languages            │                │
│    └──────────────────────────────────────┘                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. CARGA INICIAL                                            │
│                                                              │
│    ┌──────────────────────────────────────┐                │
│    │ page.goto(url)                        │                │
│    │  wait_until='networkidle'             │                │
│    │  timeout=60000                        │                │
│    └──────────────────────────────────────┘                │
│                     ↓                                        │
│    ┌──────────────────────────────────────┐                │
│    │ Esperar selector inicial               │                │
│    │  wait_for_selector(                   │                │
│    │    'a[data-vehicle-web-id]'           │                │
│    │  )                                    │                │
│    └──────────────────────────────────────┘                │
│                     ↓                                        │
│    ┌──────────────────────────────────────┐                │
│    │ Contar coches iniciales                │                │
│    │  initial_count = 12-14 coches         │                │
│    └──────────────────────────────────────┘                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. LOOP DE INFINITE SCROLL                                  │
│                                                              │
│    iteration = 1                                            │
│    total_loaded = initial_count                             │
│                                                              │
│    while iteration <= max_iterations:                       │
│                                                              │
│      ┌──────────────────────────────────────┐              │
│      │ 4.1 Scroll to Bottom                  │              │
│      │  page.evaluate(                       │              │
│      │    "window.scrollTo(0,                │              │
│      │     document.body.scrollHeight)"      │              │
│      │  )                                    │              │
│      │  await sleep(2.0s)                    │              │
│      └──────────────────────────────────────┘              │
│                     ↓                                        │
│      ┌──────────────────────────────────────┐              │
│      │ 4.2 Buscar Botón "Ver más"            │              │
│      │  button = page.locator(               │              │
│      │    "button[data-action='next-page']"  │              │
│      │  )                                    │              │
│      │                                       │              │
│      │  if not button.is_visible():          │              │
│      │    break  # No más coches             │              │
│      └──────────────────────────────────────┘              │
│                     ↓                                        │
│      ┌──────────────────────────────────────┐              │
│      │ 4.3 Click en Botón                    │              │
│      │  button.click()                       │              │
│      │  await sleep(3.0s)                    │              │
│      │  wait_for_load_state('networkidle')   │              │
│      └──────────────────────────────────────┘              │
│                     ↓                                        │
│      ┌──────────────────────────────────────┐              │
│      │ 4.4 Contar Nuevos Coches              │              │
│      │  current_count = page.locator(        │              │
│      │    'a[data-vehicle-web-id]'           │              │
│      │  ).count()                            │              │
│      │                                       │              │
│      │  new_cars = current_count - total_loaded            │
│      │  total_loaded = current_count         │              │
│      │                                       │              │
│      │  if new_cars == 0:                    │              │
│      │    break  # No se cargaron más        │              │
│      └──────────────────────────────────────┘              │
│                     ↓                                        │
│      iteration += 1                                         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. EXTRACCIÓN FINAL                                         │
│                                                              │
│    ┌──────────────────────────────────────┐                │
│    │ Obtener HTML completo                 │                │
│    │  html = page.content()                │                │
│    │  → HTML con 60, 100, 200+ coches     │                │
│    └──────────────────────────────────────┘                │
│                     ↓                                        │
│    ┌──────────────────────────────────────┐                │
│    │ Parsear todos los coches              │                │
│    │  listings = parser.parse(html)        │                │
│    │  → List[CarListing]                   │                │
│    └──────────────────────────────────────┘                │
│                     ↓                                        │
│    ┌──────────────────────────────────────┐                │
│    │ Guardar en Supabase (batch único)     │                │
│    │  supabase.save_listings(listings)     │                │
│    │  → Tabla: clicars                     │                │
│    └──────────────────────────────────────┘                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. FINALIZACIÓN                                             │
│    - Cerrar Playwright browser                              │
│    - Retornar ScrapeResult                                  │
└─────────────────────────────────────────────────────────────┘
```

### 2.4 Componentes Clave

#### A) Playwright Scraper (playwright_scraper.py)

```python
class PlaywrightClicarsScaper:
    """Maneja Playwright con stealth para infinite scroll."""

    async def start(self):
        """Inicia browser con configuración anti-detección."""
        self.browser = await playwright.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-web-security'
            ]
        )

        # Inyectar scripts anti-detección
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => false
            });
            window.chrome = {runtime: {}};
        """)

    async def scrape_with_infinite_scroll(
        url: str,
        button_selector: str,
        max_iterations: int = 200,
        scroll_delay: float = 2.0,
        click_delay: float = 3.0
    ) -> str:
        """
        Scraping con infinite scroll.

        Returns:
            HTML completo con todos los coches cargados
        """
```

**Diferencias vs HeadlessX:**
- ✅ Puede ejecutar JavaScript
- ✅ Puede hacer click en botones
- ✅ Puede detectar eventos DOM
- ✅ Maneja infinite scroll nativo
- ⚠️ Menos anti-detección que HeadlessX (pero suficiente)

#### B) Site Configuration (site.py)

```python
@dataclass
class ClicarsConfig:
    base_url: str = "https://www.clicars.com"

    # ¡UNA SOLA URL!
    search_url: str = "https://www.clicars.com/coches-segunda-mano-ocasion"

    # Delays para infinite scroll
    delay_between_scrolls: float = 2.0
    delay_between_clicks: float = 3.0
    delay_after_load: float = 2.0

    # Configuración de scroll
    scroll_step: int = 500
    max_scroll_attempts: int = 100

    # Botón "Ver más"
    load_more_button_selector: str = "button[data-action='next-page']"

    # Estimación de coches por carga
    listings_per_load: int = 12
    expected_total_listings: int = 300
```

#### C) Parser (parser.py)

**Estructura HTML de Clicars:**
```html
<a data-vehicle-web-id="121906"
   data-analytics-vehicle-maker="Audi"
   data-analytics-vehicle-model="A3"
   href="/coches-segunda-mano-ocasion/comprar-audi-a3-...">

  <h2 class="maker">
    <strong>Audi A3</strong>
    <span class="version">Sportback 30 TFSI S tronic</span>
  </h2>

  <span class="info">2021 | 119.763km | 110CV | Automático</span>

  <div class="trigger-modal-price" data-price-web="23490€">
    <span class="price">23.490€</span>
  </div>

  <span class="fuelName">Mild hybrid</span>

  <img class="vehicle-img" src="...">
</a>
```

**Extracción:**
```python
def parse(self, html: str) -> List[CarListing]:
    soup = BeautifulSoup(html, 'lxml')

    # Encontrar todas las tarjetas con data-vehicle-web-id
    car_cards = soup.find_all('a', attrs={'data-vehicle-web-id': True})

    for card in car_cards:
        # Extraer desde data-attributes
        ad_id = card.get('data-vehicle-web-id')
        marca = card.get('data-analytics-vehicle-maker')
        modelo = card.get('data-analytics-vehicle-model')

        # Extraer desde HTML
        version = card.find('span', class_='version').text

        # Parsear "2021 | 119.763km | 110CV | Automático"
        info = card.find('span', class_='info').text
        year, km, cv, trans = parse_info_string(info)

        # Precio desde data-attribute
        price = card.find('div', class_='trigger-modal-price')
        price_int = clean_price(price.get('data-price-web'))
```

#### D) Scraper Agent (scraper_agent.py)

```python
class ClicarsScraperAgent(BaseAgent):

    async def scrape_all(
        max_iterations: int = 200,
        save_to_db: bool = True
    ) -> ScrapeResult:
        """
        Scraping completo con Playwright.

        Args:
            max_iterations: Máximo de clicks en "Ver más"
                          (200 * 12 ≈ 2400 coches)
        """

        # 1. Iniciar Playwright
        scraper = PlaywrightClicarsScaper(headless=True)
        await scraper.start()

        # 2. Scrape con infinite scroll
        html = await scraper.scrape_with_infinite_scroll(
            url=self.site.get_search_url(),
            button_selector=self.site.config.load_more_button_selector,
            max_iterations=max_iterations
        )

        # 3. Parsear HTML completo
        listings = self.parser.parse(html)

        # 4. Guardar en batch (una sola vez al final)
        if save_to_db:
            stats = self.supabase.save_listings(listings)

        # 5. Cerrar Playwright
        await scraper.close()
```

### 2.5 Guardado en Supabase

**Tabla: `clicars`** (mismo formato que `autocasion`)
```sql
CREATE TABLE clicars (
    id BIGSERIAL PRIMARY KEY,
    ad_id TEXT UNIQUE NOT NULL,
    url TEXT,
    title TEXT,
    marca TEXT,
    modelo TEXT,
    version TEXT,
    year INTEGER,
    kilometers TEXT,
    kilometers_numeric INTEGER,
    power TEXT,
    power_numeric INTEGER,
    transmission TEXT,
    price TEXT,
    price_numeric INTEGER,
    fuel TEXT,
    location TEXT,
    scraped_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Guardado en batch:**
```python
# Clicars: guardar TODO al final (no incremental)
all_listings = scrape_with_infinite_scroll()
supabase.save_listings(all_listings)  # Una sola llamada
```

---

## 3. Comparación Detallada

### 3.1 Patrón de Navegación

| Aspecto | Autocasion | Clicars |
|---------|-----------|---------|
| **Patrón** | Paginación tradicional | Infinite scroll |
| **URLs** | Múltiples (`?p=1`, `?p=2`, ...) | Una sola URL |
| **Navegación** | GET requests a diferentes URLs | Scroll + Click en botón |
| **Tecnología** | HTTP requests (HeadlessX) | JavaScript execution (Playwright) |
| **Total páginas** | Detectado en página 1 | No hay "páginas" |
| **Progreso** | Por página (1/23, 2/23, ...) | Por iteración (click count) |

### 3.2 Tecnología de Scraping

| Aspecto | Autocasion | Clicars |
|---------|-----------|---------|
| **Motor principal** | HeadlessX v1.3.0 | Playwright + stealth |
| **Anti-detección** | Máxima (fingerprinting completo) | Media-alta (scripts básicos) |
| **Profile rotation** | 126 combinaciones (7×6×3) | User-agent fijo |
| **JavaScript** | No ejecutado | Totalmente ejecutado |
| **Click eventos** | No soportado | Soportado nativamente |
| **Velocidad** | 3-5s por página | 2-3s por iteración |

### 3.3 Extracción de Datos

| Aspecto | Autocasion | Clicars |
|---------|-----------|---------|
| **HTML parsing** | BeautifulSoup (ambos) | BeautifulSoup (ambos) |
| **Selectores** | `<div class="listing-card">` | `<a data-vehicle-web-id>` |
| **Data attributes** | Pocos | Muchos (`data-analytics-*`) |
| **Info parsing** | Distribuida en HTML | Concentrada en `<span class="info">` |
| **Precio** | Parseado desde texto | `data-price-web` attribute |
| **Campos totales** | 14 campos | 14 campos (iguales) |

### 3.4 Guardado en Database

| Aspecto | Autocasion | Clicars |
|---------|-----------|---------|
| **Estrategia** | Incremental (por página) | Batch (al final) |
| **Frecuencia** | Cada página | Una vez |
| **Ventajas** | Datos parciales si falla | Más rápido (menos queries) |
| **Desventajas** | Más queries a DB | Pierde todo si falla |
| **Upsert** | Por ad_id (ambos) | Por ad_id (ambos) |

### 3.5 Manejo de Errores

| Aspecto | Autocasion | Clicars |
|---------|-----------|---------|
| **Bloqueos** | Retry con stealth mode | Retry con delays |
| **Timeouts** | Por página (60s) | Por operación (10s) |
| **Fallback** | HeadlessX → requests | No hay fallback |
| **Recovery** | Continúa siguiente página | Retorna HTML parcial |
| **Datos parciales** | Guardados en DB | Perdidos si falla |

### 3.6 Performance

| Aspecto | Autocasion | Clicars |
|---------|-----------|---------|
| **Audi (23 páginas)** | ~2-3 minutos | N/A (no por marca) |
| **10 marcas** | ~30-40 minutos | N/A |
| **300 coches** | Depende de páginas | ~2-3 minutos |
| **2000+ coches** | N/A (filtro por marca) | ~15-20 minutos |
| **Overhead** | Profile rotation | Browser startup |

---

## 4. Resumen Ejecutivo

### Autocasion: "Paginador Sigiloso"
- ✅ Anti-detección máxima con HeadlessX
- ✅ Profile rotation sofisticada
- ✅ Guardado incremental seguro
- ✅ Filtrado por marca
- ⚠️ No puede ejecutar JavaScript
- ⚠️ Lento con muchas páginas

### Clicars: "Scrolleador Dinámico"
- ✅ Soporta infinite scroll nativo
- ✅ Ejecuta JavaScript completo
- ✅ Una sola URL simplifica lógica
- ✅ Batch saving más rápido
- ⚠️ Anti-detección más básica
- ⚠️ Todo-o-nada (no guardado parcial)

---

## 5. Uso Práctico

### Autocasion

```python
# Por marca
agent = AutocasionScraperAgent()
result = await agent.scrape_marca(
    marca="audi",
    max_pages=0,      # Todas las páginas
    save_to_db=True,
    stealth=True      # Modo sigiloso
)

# Batch de marcas
results = await agent.scrape_batch(
    marcas=["audi", "bmw", "mercedes"],
    max_pages=10
)

# Desde objetivos
results = await agent.scrape_from_objetivos(limit=5)
```

### Clicars

```python
# Scraping completo
agent = ClicarsScraperAgent(headless=True)
result = await agent.scrape_all(
    max_iterations=200,  # 200 clicks ≈ 2400 coches
    save_to_db=True
)

# Menos coches (testing)
result = await agent.scrape_all(
    max_iterations=5,   # 5 clicks ≈ 60 coches
    save_to_db=True
)
```

---

## 6. Conclusión

**¿Cuándo usar cada uno?**

**Autocasion:**
- Sitios con paginación tradicional
- Necesitas máxima anti-detección
- Filtrado por marca/categoría
- Scraping largo (recovery importante)

**Clicars:**
- Sitios con infinite scroll
- Necesitas ejecutar JavaScript
- Click en botones/interacción DOM
- Scraping rápido de volumen completo

Ambos scrapers comparten:
- Misma estructura de datos (`CarListing`)
- Mismo parser base (`BeautifulSoup`)
- Misma DB (`Supabase`)
- Mismo sistema de agentes (`BaseAgent`)
