# ScrapeadorSupremo

Sistema completo de scraping de coches de segunda mano con aplicaciones de escritorio, parsing optimizado y bypass anti-bot.

## 🎯 Características Principales

- ✅ **Scraping Autocasion**: Por marca (23 marcas comunes)
- ✅ **Scraping Cochesnet**: Por año (2007-2025) con HeadlessX
- ✅ **Parsing Optimizado**: TitleParser con 73 marcas y 24,930+ modelos
- ✅ **Bypass Anti-Bot**: HeadlessX API con stealth completo
- ✅ **Aplicaciones Desktop**: 3 apps tkinter con GUI completa
- ✅ **Confidence Scoring**: Metrics de calidad de parsing
- ✅ **Base de Datos**: Integración Supabase

## 🚀 Quick Start

### 1. Instalación

```bash
# Clonar repositorio
cd ScrapeadorSupremo

# Instalar dependencias
pip install -r requirements.txt

# Configurar .env
cp .env.example .env
# Editar .env con tus credenciales
```

### 2. Configurar Variables de Entorno

```bash
# .env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
HEADLESSX_URL=http://localhost:3000
HEADLESSX_TOKEN=your_token
```

### 3. Iniciar Servidor HeadlessX

```bash
# En terminal separada
cd ../HeadlessX
npm start
```

### 4. Ejecutar Aplicaciones

```bash
# Opción 1: Doble click en accesos directos del escritorio
Cochesnet Scraper.lnk
Autocasion Scraper.lnk
Unified Scraper.lnk

# Opción 2: Desde command line
python scraping/sites/cochesnet/app/main.py
python scraping/sites/autocasion/app/main.py
python scraping/unified_app/main.py

# Opción 3: Usando launchers
launch_cochesnet_app.bat
launch_autocasion_app.bat
launch_unified_app.bat
```

## 📁 Estructura del Proyecto

```
ScrapeadorSupremo/
├── scraping/
│   ├── base/
│   │   ├── parser.py                   # CarListing dataclass base
│   │   └── title_parser.py             # Parser optimizado con DB
│   ├── sites/
│   │   ├── cochesnet/
│   │   │   ├── parser.py               # Parser JSON de Cochesnet
│   │   │   ├── site.py                 # URL builder
│   │   │   └── app/
│   │   │       ├── main.py             # Entry point GUI
│   │   │       ├── gui.py              # Desktop app (tkinter)
│   │   │       └── scraper_agent.py    # Agent con HeadlessX
│   │   └── autocasion/
│   │       ├── parser.py               # Parser HTML de Autocasion
│   │       └── app/
│   │           ├── main.py             # Entry point GUI
│   │           ├── gui.py              # Desktop app
│   │           └── scraper_agent.py    # Scraping agent
│   ├── unified_app/
│   │   ├── main.py                     # Entry point unified
│   │   └── gui.py                      # Manager unificado
│   └── storage/
│       └── supabase_client.py          # Supabase integration
├── scripts/
│   ├── test_headlessx_cochesnet.py     # Test HeadlessX
│   ├── test_title_parser.py            # Test parsing
│   ├── populate_marca_modelos.py       # Populate DB
│   └── add_parsing_confidence_to_cochesnet.sql
├── docs/
│   ├── COCHESNET_HEADLESSX_INTEGRATION.md   # 📘 Guía completa HeadlessX
│   ├── TITLE_PARSER_INTEGRATION.md          # 📘 Parser documentation
│   ├── RESUMEN_FISURAS_Y_TEST_REAL.md       # 📘 Bugs históricos
│   ├── COCHESNET_APP_README.md              # 📘 App Cochesnet
│   ├── UNIFIED_APP_README.md                # 📘 App unificada
│   └── DESKTOP_SHORTCUTS_GUIDE.md           # 📘 Accesos directos
├── launch_cochesnet_app.bat            # Launcher Windows
├── launch_autocasion_app.bat           # Launcher Windows
├── launch_unified_app.bat              # Launcher Windows
├── create_desktop_shortcuts.bat        # Script shortcuts
├── create_shortcuts.ps1                # PowerShell shortcuts
└── README.md                           # Este archivo
```

## 🎨 Aplicaciones de Escritorio

### 1. Cochesnet Scraper

**Función**: Scraping de Cochesnet por año

**Características**:
- Selección de años 2007-2025
- Botones rápidos: "2020-2025", "2015-2025"
- HeadlessX bypass anti-bot
- Parsing con confidence scoring
- Progress bars en tiempo real
- Logs en vivo

**Ejecutar**:
```bash
python scraping/sites/cochesnet/app/main.py
```

### 2. Autocasion Scraper

**Función**: Scraping de Autocasion por marca

**Características**:
- Selección de 23 marcas comunes
- Max páginas configurable
- Scraping desde objetivos
- Estadísticas por marca
- Export JSON/CSV

**Ejecutar**:
```bash
python scraping/sites/autocasion/app/main.py
```

### 3. Unified Scraper

**Función**: Manager unificado para ambos scrapers

**Características**:
- 5 tabs: Autocasion, Cochesnet, Stats, Export, Logs
- Ejecución paralela de ambos scrapers
- Estadísticas unificadas
- Export centralizado
- Logs combinados

**Ejecutar**:
```bash
python scraping/unified_app/main.py
```

## 🔧 Tecnologías Utilizadas

### Core
- **Python 3.8+**: Lenguaje principal
- **tkinter**: GUI de escritorio
- **asyncio**: Operaciones asíncronas
- **requests**: HTTP client

### Scraping
- **HeadlessX API**: Bypass anti-bot avanzado
- **BeautifulSoup**: Parsing HTML
- **lxml**: Parser rápido

### Database
- **Supabase**: PostgreSQL cloud
- **python-supabase**: Client oficial

### Anti-Detection
- **Canvas Spoofing**: Fingerprint falsification
- **WebGL Spoofing**: GPU fingerprint
- **Behavioral Simulation**: Mouse/scroll humanos
- **Device Profiles**: Emulación de dispositivos

## 📊 Rendimiento

### Cochesnet con HeadlessX

| Metric | Value |
|--------|-------|
| Fetch time (1 página) | ~40-45s |
| Parsing (35 listings) | <1s |
| Save to DB | ~2-3s |
| **Total por página** | **~48s** |
| **Páginas/hora** | ~75 |
| **Listings/hora** | ~2,625 |

### Parsing Quality

| Metric | Value |
|--------|-------|
| Perfect matches (conf=1.0) | 91.4% |
| DB matches (conf≥0.7) | 95.7% |
| Average confidence | 0.95 |

## 🗄️ Base de Datos

### Tablas

#### `cochesnet`
```sql
CREATE TABLE cochesnet (
    ad_id VARCHAR PRIMARY KEY,
    source VARCHAR NOT NULL,
    url TEXT,
    title TEXT,
    marca VARCHAR,
    modelo VARCHAR,
    year INTEGER,
    kilometers INTEGER,
    fuel VARCHAR,
    power_cv INTEGER,
    price INTEGER,
    price_text VARCHAR,
    location VARCHAR,
    parsing_confidence DECIMAL(3,2),  -- 0.00 - 1.00
    parsing_method VARCHAR(50),        -- 'database' | 'heuristic'
    scraped_at TIMESTAMP
);
```

#### `marcas_modelos_validos`
```sql
CREATE TABLE marcas_modelos_validos (
    id SERIAL PRIMARY KEY,
    marca VARCHAR NOT NULL,
    modelo VARCHAR NOT NULL
);

-- 73 marcas, 24,930+ modelos
```

### Migración Requerida

Para agregar campos de parsing confidence:

```bash
# Ejecutar en Supabase SQL Editor
scripts/add_parsing_confidence_to_cochesnet.sql
```

## 🐛 Troubleshooting

### Error: "HEADLESSX_TOKEN not set"

```bash
# Agregar al .env
HEADLESSX_TOKEN=your_token_here
```

### Error: "Connection refused to localhost:3000"

```bash
# Iniciar servidor HeadlessX
cd ../HeadlessX
npm start
```

### Error: "Could not find the 'parsing_confidence' column"

```bash
# Ejecutar migración SQL
# En Supabase SQL Editor:
scripts/add_parsing_confidence_to_cochesnet.sql
```

### Parser devuelve 0 listings

1. Verificar que HeadlessX está corriendo:
   ```bash
   curl http://localhost:3000/api/health
   ```

2. Verificar HTML size (debe ser >1MB):
   ```python
   # En logs debe aparecer:
   # HeadlessX: Page loaded successfully
   ```

3. Verificar campo `extra_fields` existe en CarListing

## 📖 Documentación Completa

- **[COCHESNET_HEADLESSX_INTEGRATION.md](docs/COCHESNET_HEADLESSX_INTEGRATION.md)**: Guía completa de HeadlessX integration
- **[TITLE_PARSER_INTEGRATION.md](docs/TITLE_PARSER_INTEGRATION.md)**: Sistema de parsing optimizado
- **[RESUMEN_FISURAS_Y_TEST_REAL.md](docs/RESUMEN_FISURAS_Y_TEST_REAL.md)**: Bugs históricos y fixes
- **[UNIFIED_APP_README.md](docs/UNIFIED_APP_README.md)**: Guía de la app unificada
- **[DESKTOP_SHORTCUTS_GUIDE.md](docs/DESKTOP_SHORTCUTS_GUIDE.md)**: Crear accesos directos

## 🔗 Referencias

### Proyecto Relacionado: PruebaScrapeador

Este proyecto sirvió como referencia para la implementación de HeadlessX.

**Características útiles**:
- 10+ tipos de scrapers diferentes
- Proxy rotation y management
- Advanced error recovery
- Dashboard web con React
- WAF bypass extensions

**Consultar**:
- `PruebaScrapeador/src/scrapers/headlessx_scraper.py`
- `PruebaScrapeador/docs/`

## 📈 Roadmap

### v1.0.0 (Actual) ✅
- [x] Scraper Cochesnet con HeadlessX
- [x] Scraper Autocasion
- [x] TitleParser optimizado
- [x] 3 aplicaciones desktop
- [x] Accesos directos en escritorio
- [x] Documentación completa

### v1.1.0 (Próximo)
- [ ] Proxy support en Cochesnet
- [ ] Retry logic mejorado
- [ ] Cache de resultados (24h)
- [ ] Notificaciones de errores
- [ ] Logs persistentes

### v1.2.0 (Futuro)
- [ ] Browser rotation
- [ ] Scraping multi-marca paralelo
- [ ] Detección de cambios de precio
- [ ] Dashboard web analytics
- [ ] API REST

### v2.0.0 (Visión)
- [ ] ML para predicción de precios
- [ ] Análisis de tendencias
- [ ] Alertas personalizadas
- [ ] Mobile app
- [ ] Integración con marketplaces

## 👥 Contribución

Este es un proyecto interno. Para consultas:
- Ver documentación en `docs/`
- Revisar scripts de test en `scripts/`
- Consultar PruebaScrapeador para features avanzados

## 📝 Licencia

Proyecto interno - Todos los derechos reservados

---

**Version**: 1.0.0
**Última actualización**: 2025-12-05
**Status**: ✅ PRODUCTION READY
**Powered by**: HeadlessX v1.3.0
