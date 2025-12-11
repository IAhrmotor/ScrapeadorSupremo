# Cochesnet Desktop Scraper

Aplicación de escritorio para scrapear Coches.net por años (2007-2025).

## Características

- ✅ Selección de años con checkboxes (2007-2025)
- ✅ Botones rápidos (Todos, Ninguno, 2020-2025)
- ✅ Barra de progreso en tiempo real
- ✅ Logs detallados
- ✅ Estadísticas de base de datos
- ✅ Exportación a CSV/JSON/Excel
- ✅ Parsing optimizado con confidence scoring

## Uso

### Ejecución

```bash
python scraping/sites/cochesnet/app/main.py
```

### Interfaz

#### Tab 1: Scraping
- **Panel izquierdo**: Checkboxes para seleccionar años (2007-2025)
- **Botones**:
  - `Select All`: Seleccionar todos los años
  - `Deselect All`: Deseleccionar todos
  - `2020-2025`: Selección rápida de años recientes
- **Panel derecho**:
  - Barra de progreso
  - Botones Start/Stop
  - Logs en tiempo real

#### Tab 2: Statistics
- Total de anuncios
- Desglose por año
- Calidad de parsing (confidence promedio)
- Botón `Refresh Statistics`

#### Tab 3: Export
- Exportar a CSV
- Exportar a JSON
- Exportar a Excel (requiere pandas)

## URL Pattern

```
https://www.coches.net/segunda-mano/{year}/?pg={page}
```

Ejemplos:
- `https://www.coches.net/segunda-mano/2024/` - Año 2024, página 1
- `https://www.coches.net/segunda-mano/2024/?pg=2` - Año 2024, página 2

## Arquitectura

```
scraping/sites/cochesnet/app/
├── __init__.py           # Exports
├── main.py               # Entry point
├── gui.py                # GUI con tkinter
└── scraper_agent.py      # Lógica de scraping
```

### Componentes

#### CochesnetApp (gui.py)
- Interfaz gráfica con tkinter
- 3 tabs: Scraping, Statistics, Export
- Callbacks para progreso y logs
- Threading para evitar bloqueo de UI

#### CochesnetScraperAgent (scraper_agent.py)
- Hereda de `BaseAgent`
- Scraping asíncrono por año
- Integración con Supabase
- Manejo de errores robusto

## Flujo de Scraping

1. Usuario selecciona años
2. Click en "Start Scraping"
3. Para cada año:
   - Itera páginas hasta no encontrar más
   - Parsea anuncios con TitleParser (confidence scoring)
   - Guarda en Supabase con upsert
   - Actualiza progreso
4. Muestra resumen al finalizar

## Base de Datos

### Tabla: `cochesnet`

Campos principales:
- `ad_id` (PK): ID único del anuncio
- `marca`, `modelo`: Parseados con TitleParser
- `year`: Año del vehículo
- `price`: Precio numérico
- `kilometers`: Kilómetros
- `parsing_confidence`: Score 0.0-1.0
- `parsing_method`: "database" o "heuristic"
- `version`: Versión del modelo
- `scraped_at`: Timestamp

## Dependencias

```python
# Core
tkinter  # GUI (incluido en Python)
asyncio  # Async scraping

# HTTP
requests  # Fetch pages

# Database
supabase  # Supabase client

# Parsing
beautifulsoup4  # HTML parsing
lxml  # Parser backend

# Export (opcional)
pandas  # Para Excel export
openpyxl  # Excel backend
```

## Notas Técnicas

### Parsing
- Usa TitleParser optimizado con tabla de referencia
- Carga 73 marcas y 24,930+ modelos
- Confidence perfecto (1.0) para marcas/modelos conocidos

### Rate Limiting
- Delay de 1s entre páginas
- Delay de 2s entre años
- Max 50 páginas por año (configurable)

### Error Handling
- Reintentos automáticos
- Log de errores detallado
- Continúa si una página falla
- Máximo 5 errores consecutivos por año

## Comparación vs Autocasion

| Feature | Autocasion | Cochesnet |
|---------|------------|-----------|
| **Selector** | Marcas | **Años** |
| **Patrón URL** | Por marca | Por año |
| **Anti-detección** | HeadlessX | **requests simple** |
| **Parsing** | CSS + heurística | **JSON + TitleParser** |
| **Confidence** | No | **Sí (0.0-1.0)** |

## Ejemplo de Uso

```python
from scraping.sites.cochesnet.app import CochesnetApp

# Crear app
app = CochesnetApp()

# Run
app.run()
```

O desde línea de comandos:
```bash
cd scraping/sites/cochesnet/app
python main.py
```

## Próxima Versión

Ver: **Unified Scraper App** - Gestiona tanto Autocasion como Cochesnet en una sola interfaz.
