# Unified Scraper Application

Aplicación de escritorio unificada para gestionar scraping de **Autocasion** y **Cochesnet**.

## Características

### Gestión Dual de Scrapers
- **Autocasion**: Scraping por marca (23 marcas comunes)
- **Cochesnet**: Scraping por año (2007-2025)

### 5 Pestañas Funcionales

1. **Autocasion** - Gestión de scraping por marca
   - Selección múltiple de marcas
   - Botones rápidos: Todas, Ninguna, Top 10
   - Progreso en tiempo real
   - Estadísticas mini por marca

2. **Cochesnet** - Gestión de scraping por año
   - Selección múltiple de años (2007-2025)
   - Botones rápidos: Todos, Ninguno, 2020-2025, 2015-2025
   - Progreso en tiempo real
   - Estadísticas mini por año

3. **Estadísticas Unificadas** - Visión global
   - Total anuncios de ambas fuentes
   - Anuncios por fuente (Autocasion / Cochesnet)
   - Confianza promedio de parsing
   - Perfect DB matches
   - Refrescar estadísticas en vivo

4. **Exportar** - Exportación de datos
   - Formato CSV
   - Selección de fuente: Autocasion, Cochesnet o Ambos
   - Filtros personalizados
   - Exportación directa

5. **Logs** - Monitoreo en tiempo real
   - Mensajes de ambos scrapers
   - Auto-scroll
   - Timestamps
   - Niveles: INFO, WARNING, ERROR

## Instalación

### Requisitos
```bash
pip install tkinter
pip install requests
pip install beautifulsoup4
pip install lxml
```

### Variables de Entorno
Crear `.env` en la raíz del proyecto:
```bash
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

## Uso

### Ejecutar Aplicación
```bash
python scraping/unified_app/main.py
```

### Scraping con Autocasion

1. Ir a pestaña **Autocasion**
2. Seleccionar marcas:
   - Click individual en marcas
   - "Select All" para todas
   - "Select None" para limpiar
   - "Top 10" para marcas más populares
3. Click en **Start Scraping**
4. Ver progreso en barra y logs
5. Click en **Stop Scraping** para cancelar (opcional)

### Scraping con Cochesnet

1. Ir a pestaña **Cochesnet**
2. Seleccionar años:
   - Click individual en años
   - "Select All" para todos
   - "2020-2025" para últimos 5 años
   - "2015-2025" para última década
3. Click en **Start Scraping**
4. Ver progreso en barra y logs
5. Click en **Stop Scraping** para cancelar (opcional)

### Ver Estadísticas

1. Ir a pestaña **Unified Statistics**
2. Ver totales globales y por fuente
3. Click en **Refresh Stats** para actualizar

### Exportar Datos

1. Ir a pestaña **Export**
2. Seleccionar fuente: Autocasion, Cochesnet o Both
3. (Opcional) Configurar filtros
4. Click en **Export CSV**
5. Seleccionar ubicación de archivo

## Arquitectura

### Estructura de Archivos
```
scraping/unified_app/
├── __init__.py          # Module exports
├── main.py              # Entry point
└── gui.py               # UnifiedScraperApp class
```

### Agentes Integrados

**AutocasionScraperAgent**
- Ubicación: `scraping/sites/autocasion/agent/scraper_agent.py`
- Método: `scrape_brands(brands: List[str])`

**CochesnetScraperAgent**
- Ubicación: `scraping/sites/cochesnet/app/scraper_agent.py`
- Método: `scrape_years(years: List[int])`

### Sistema de Parsing Optimizado

Ambos scrapers usan **TitleParser** con database-driven matching:
- 73 marcas
- 24,930+ modelos
- Confidence scoring: 1.0 (DB exact), 0.7 (DB marca), 0.5 (heuristic)
- Parsing accuracy: ~100% para títulos comunes

## Aplicaciones Individuales

Si solo necesitas un scraper específico:

### Solo Autocasion
```bash
python scraping/sites/autocasion/agent/main.py
```

### Solo Cochesnet
```bash
python scraping/sites/cochesnet/app/main.py
```

## Características Técnicas

### Threading
- Cada scraper corre en thread separado
- UI no se bloquea durante scraping
- Progress callbacks en tiempo real

### Logging Unificado
- Todos los mensajes centralizados
- Timestamps automáticos
- Color-coded por nivel

### Estado de Scraping
- Track independiente: `self.is_running["autocasion"]` y `self.is_running["cochesnet"]`
- Botones habilitados/deshabilitados automáticamente
- Previene múltiples ejecuciones concurrentes del mismo scraper

### Manejo de Errores
- Try-catch en operaciones críticas
- Mensajes de error en logs
- UI responde incluso en caso de error

## Ejemplos de Uso

### Caso 1: Scraping Masivo de Ambos
1. Autocasion: Seleccionar "Top 10" marcas
2. Cochesnet: Seleccionar "2020-2025" años
3. Ejecutar ambos simultáneamente
4. Monitorear en logs
5. Ver estadísticas unificadas

### Caso 2: Actualización Rápida
1. Cochesnet: Solo "2025" (año actual)
2. Ejecutar scraping
3. Exportar CSV para análisis

### Caso 3: Análisis Histórico
1. Cochesnet: "2015-2025" (última década)
2. Ejecutar scraping completo
3. Ver estadísticas de evolución

## Troubleshooting

### No se conecta a Supabase
- Verificar `.env` con credenciales correctas
- Revisar conexión a internet
- Ver logs para error específico

### Scraping muy lento
- Normal: Autocasion ~5 min por marca, Cochesnet ~2 min por año
- Pausar/reanudar con Stop/Start buttons
- Revisar límites de rate en websites

### UI se congela
- Threading debería evitarlo
- Si ocurre, reiniciar aplicación
- Reportar bug con logs

### Parsing confidence baja
- Verificar que `marcas_modelos_validos` tenga 24,930+ rows
- Ejecutar `scripts/populate_marca_modelos.py`
- Ver `docs/TITLE_PARSER_INTEGRATION.md`

## Próximas Mejoras

- [ ] Implementar scraping multi-marca en Autocasion
- [ ] Agregar filtros por precio/año en export
- [ ] Gráficas de estadísticas históricas
- [ ] Notificaciones cuando termina scraping
- [ ] Scheduling automático (cron-like)
- [ ] Comparación side-by-side Autocasion vs Cochesnet

## Referencias

- [COCHESNET_APP_README.md](COCHESNET_APP_README.md) - App individual de Cochesnet
- [TITLE_PARSER_INTEGRATION.md](TITLE_PARSER_INTEGRATION.md) - Sistema de parsing optimizado
- [RESUMEN_FISURAS_Y_TEST_REAL.md](RESUMEN_FISURAS_Y_TEST_REAL.md) - Bugs corregidos y tests

---

**Version**: 1.0.0
**Date**: 2025-12-05
**Status**: ✅ Listo para producción (Cochesnet completo, Autocasion en desarrollo)
