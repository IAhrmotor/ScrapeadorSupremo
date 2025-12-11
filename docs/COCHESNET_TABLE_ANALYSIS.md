# Análisis y Mejoras de la Tabla Cochesnet

Este documento analiza la estructura actual de la tabla `cochesnet` y propone mejoras basadas en:
1. Patrones de parsing observados
2. Tabla de referencia `marca_modelos`
3. Best practices para búsqueda y análisis

---

## 1. Estructura Actual de la Tabla

```sql
CREATE TABLE cochesnet (
    id BIGSERIAL PRIMARY KEY,
    ad_id TEXT UNIQUE NOT NULL,
    url TEXT,
    title TEXT,

    -- Marca y modelo (parsing básico)
    marca TEXT,
    marca_normalizada TEXT,
    modelo TEXT,
    modelo_base TEXT,
    modelo_completo TEXT,
    version TEXT,

    -- Características
    year TEXT,  -- ⚠️ Debería ser INTEGER
    kilometers TEXT,
    kilometers_numeric INTEGER,
    fuel TEXT,
    combustible_normalizado TEXT,
    price TEXT,
    price_numeric INTEGER,
    power TEXT,
    power_numeric INTEGER,
    location TEXT,
    provincia TEXT,

    -- Metadata
    scraped_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    activo BOOLEAN,
    parsing_version INTEGER
);
```

---

## 2. Problemas Identificados

### A) Campo `year` como TEXT en vez de INTEGER

**❌ Problema actual:**
```sql
year TEXT  -- "2021", "2020", etc.
```

**Impacto:**
- No se pueden hacer comparaciones numéricas eficientes
- Queries como `WHERE year > 2020` requieren CAST
- Ordenamiento alfabético vs numérico

**✅ Solución propuesta:**
```sql
year INTEGER  -- 2021, 2020, etc.
```

### B) Redundancia en campos de marca/modelo

**Campos actuales:**
- `marca` - Original del parsing
- `marca_normalizada` - Lowercase
- `modelo` - Primera palabra del modelo
- `modelo_base` - ¿?
- `modelo_completo` - ¿Incluye versión?

**❓ Preguntas:**
- ¿`modelo_base` vs `modelo_completo` - cuál es la diferencia?
- ¿Por qué tres campos de marca/modelo?

**✅ Propuesta simplificada:**
```sql
-- Campos originales del parsing
title TEXT NOT NULL,           -- "OPEL Corsa 1.5D DT 74kW 100CV Edition 5p."
marca TEXT,                    -- "OPEL"
modelo TEXT,                   -- "Corsa"
version TEXT,                  -- "1.5D DT 74kW 100CV Edition 5p."

-- Campos normalizados para búsqueda
marca_normalized TEXT,         -- "opel" (índice)
modelo_normalized TEXT,        -- "corsa" (índice)

-- Confidence del parsing (NUEVO)
parsing_confidence REAL,       -- 0.0-1.0
parsing_method TEXT,           -- "db_exact", "db_fuzzy", "heuristic"
```

### C) Falta campo `transmission`

**Observación:**
- Autocasion y Clicars tienen `transmission` (Manual/Automático)
- Cochesnet NO lo tiene

**✅ Agregar:**
```sql
transmission TEXT,  -- "Manual", "Automático", "Semiautomático"
```

### D) No hay tracking de cambios de precio

**Problema:**
- Si un coche baja de precio, perdemos el histórico
- No podemos detectar "buenas ofertas" (bajadas recientes)

**✅ Propuesta:**
```sql
-- Tabla separada para tracking de precios
CREATE TABLE cochesnet_price_history (
    id BIGSERIAL PRIMARY KEY,
    ad_id TEXT REFERENCES cochesnet(ad_id),
    price_numeric INTEGER NOT NULL,
    scraped_at TIMESTAMPTZ NOT NULL,

    INDEX idx_ad_id_date (ad_id, scraped_at DESC)
);
```

### E) No hay índices optimizados para búsquedas comunes

**Búsquedas típicas:**
1. Por marca + modelo
2. Por rango de precio
3. Por año
4. Por ubicación
5. Por combustible

**✅ Índices recomendados:**
```sql
-- Búsquedas por marca/modelo
CREATE INDEX idx_cochesnet_marca_modelo
    ON cochesnet(marca_normalized, modelo_normalized);

-- Búsquedas por precio
CREATE INDEX idx_cochesnet_price
    ON cochesnet(price_numeric) WHERE price_numeric IS NOT NULL;

-- Búsquedas por año
CREATE INDEX idx_cochesnet_year
    ON cochesnet(year) WHERE year IS NOT NULL;

-- Búsquedas compuestas (marca + año + precio)
CREATE INDEX idx_cochesnet_search
    ON cochesnet(marca_normalized, year DESC, price_numeric);

-- Búsquedas por ubicación
CREATE INDEX idx_cochesnet_location
    ON cochesnet(location) WHERE location IS NOT NULL;

-- Full-text search en título
CREATE INDEX idx_cochesnet_title_fts
    ON cochesnet USING gin(to_tsvector('spanish', title));
```

---

## 3. Propuesta de Mejora Completa

### A) Nueva Estructura (Versión 2)

```sql
-- Drop old table (BACKUP FIRST!)
-- CREATE TABLE cochesnet_backup AS SELECT * FROM cochesnet;

DROP TABLE IF EXISTS cochesnet CASCADE;

CREATE TABLE cochesnet (
    -- Identificación
    id BIGSERIAL PRIMARY KEY,
    ad_id TEXT UNIQUE NOT NULL,
    url TEXT,

    -- Título original
    title TEXT NOT NULL,

    -- Parsing de título (con TitleParser + marca_modelos)
    marca TEXT,
    modelo TEXT,
    version TEXT,

    -- Campos normalizados (para búsqueda/filtrado)
    marca_normalized TEXT GENERATED ALWAYS AS (lower(marca)) STORED,
    modelo_normalized TEXT GENERATED ALWAYS AS (lower(modelo)) STORED,

    -- Metadata de parsing (NUEVO)
    parsing_confidence REAL DEFAULT 0.5,  -- 0.0-1.0
    parsing_method TEXT DEFAULT 'heuristic',  -- 'db_exact', 'db_fuzzy', 'heuristic'

    -- Características del vehículo
    year INTEGER,  -- ✅ Cambiado de TEXT a INTEGER
    kilometers_numeric INTEGER,
    kilometers_text TEXT,  -- "137.000 km" (display)

    fuel TEXT,
    fuel_normalized TEXT,  -- "diesel", "gasolina", "electrico", "hibrido"

    transmission TEXT,  -- ✅ NUEVO

    power_numeric INTEGER,  -- CV
    power_text TEXT,  -- "100 CV" (display)

    -- Precio
    price_numeric INTEGER,
    price_text TEXT,  -- "9.950 €" (display)

    -- Ubicación
    location TEXT,
    provincia TEXT,

    -- Dealer info (si está disponible en JSON)
    dealer_name TEXT,
    dealer_type TEXT,  -- "professional", "particular"

    -- Metadata de scraping
    scraped_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Estado
    is_active BOOLEAN DEFAULT TRUE,
    last_seen_at TIMESTAMPTZ,  -- Última vez que se vio el anuncio

    -- Version del parser usado
    parser_version INTEGER DEFAULT 2,

    -- Raw data (para debugging)
    raw_json JSONB
);

-- Índices optimizados
CREATE INDEX idx_cochesnet_ad_id ON cochesnet(ad_id);
CREATE INDEX idx_cochesnet_marca_modelo ON cochesnet(marca_normalized, modelo_normalized);
CREATE INDEX idx_cochesnet_price ON cochesnet(price_numeric) WHERE price_numeric IS NOT NULL;
CREATE INDEX idx_cochesnet_year ON cochesnet(year) WHERE year IS NOT NULL;
CREATE INDEX idx_cochesnet_fuel ON cochesnet(fuel_normalized);
CREATE INDEX idx_cochesnet_location ON cochesnet(location);
CREATE INDEX idx_cochesnet_active ON cochesnet(is_active, scraped_at DESC);

-- Índice compuesto para búsquedas comunes
CREATE INDEX idx_cochesnet_search ON cochesnet(
    marca_normalized,
    modelo_normalized,
    year DESC,
    price_numeric
) WHERE is_active = TRUE;

-- Full-text search
CREATE INDEX idx_cochesnet_title_fts ON cochesnet
    USING gin(to_tsvector('spanish', title));

-- Trigger para actualizar updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_cochesnet_updated_at
    BEFORE UPDATE ON cochesnet
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

### B) Tabla de Historial de Precios

```sql
CREATE TABLE cochesnet_price_history (
    id BIGSERIAL PRIMARY KEY,
    ad_id TEXT NOT NULL,
    price_numeric INTEGER NOT NULL,
    scraped_at TIMESTAMPTZ NOT NULL,

    FOREIGN KEY (ad_id) REFERENCES cochesnet(ad_id) ON DELETE CASCADE
);

CREATE INDEX idx_price_history_ad_id ON cochesnet_price_history(ad_id, scraped_at DESC);
CREATE INDEX idx_price_history_date ON cochesnet_price_history(scraped_at DESC);

-- Trigger para insertar en history cuando cambia el precio
CREATE OR REPLACE FUNCTION track_price_change()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'INSERT') OR
       (TG_OP = 'UPDATE' AND OLD.price_numeric != NEW.price_numeric) THEN
        INSERT INTO cochesnet_price_history (ad_id, price_numeric, scraped_at)
        VALUES (NEW.ad_id, NEW.price_numeric, NEW.scraped_at);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_track_price_change
    AFTER INSERT OR UPDATE ON cochesnet
    FOR EACH ROW
    WHEN (NEW.price_numeric IS NOT NULL)
    EXECUTE FUNCTION track_price_change();
```

### C) Vista para Búsquedas Comunes

```sql
CREATE OR REPLACE VIEW cochesnet_search AS
SELECT
    id,
    ad_id,
    url,
    title,
    marca,
    modelo,
    version,
    year,
    kilometers_numeric,
    fuel,
    transmission,
    power_numeric,
    price_numeric,
    location,
    scraped_at,
    is_active,
    parsing_confidence,

    -- Precio por año (valor relativo)
    CASE
        WHEN year IS NOT NULL AND price_numeric IS NOT NULL
        THEN ROUND(price_numeric::NUMERIC / year, 2)
        ELSE NULL
    END AS price_per_year,

    -- Edad del coche
    EXTRACT(YEAR FROM CURRENT_DATE) - year AS car_age,

    -- Días desde último scraping
    EXTRACT(DAY FROM (CURRENT_TIMESTAMP - scraped_at)) AS days_since_scraped,

    -- Formato display
    marca || ' ' || modelo || ' ' || COALESCE(version, '') AS full_title,
    price_text,
    kilometers_text,
    power_text

FROM cochesnet
WHERE is_active = TRUE;

-- Índice materializado para búsquedas MUY rápidas (opcional)
-- CREATE MATERIALIZED VIEW cochesnet_search_mat AS
-- SELECT * FROM cochesnet_search;
-- CREATE INDEX idx_search_mat_marca ON cochesnet_search_mat(marca);
-- REFRESH MATERIALIZED VIEW cochesnet_search_mat;  -- Actualizar periódicamente
```

---

## 4. Scripts de Migración

### A) Migración de datos existentes

```sql
-- Backup
CREATE TABLE cochesnet_v1_backup AS
SELECT * FROM cochesnet;

-- Crear tabla v2 (ver sección 3.A)

-- Migrar datos
INSERT INTO cochesnet (
    ad_id, url, title,
    marca, modelo, version,
    year,
    kilometers_numeric, kilometers_text,
    fuel, fuel_normalized,
    transmission,  -- NULL por ahora
    power_numeric, power_text,
    price_numeric, price_text,
    location, provincia,
    scraped_at, created_at,
    is_active, parser_version,
    parsing_confidence,
    parsing_method
)
SELECT
    ad_id,
    url,
    title,
    marca,
    modelo,
    version,

    -- year: TEXT → INTEGER
    CASE
        WHEN year ~ '^\d{4}$' THEN year::INTEGER
        ELSE NULL
    END,

    kilometers_numeric,
    kilometers,

    fuel,
    combustible_normalizado,

    NULL,  -- transmission (no disponible en v1)

    power_numeric,
    power,

    price_numeric,
    price,

    location,
    provincia,

    scraped_at,
    created_at,

    activo,
    2,  -- parser_version = 2

    -- parsing_confidence: basado en parsing_version
    CASE
        WHEN parsing_version >= 1 THEN 0.7
        ELSE 0.5
    END,

    'heuristic'  -- Todos los v1 usaron heurística

FROM cochesnet_v1_backup;

-- Verificar migración
SELECT
    COUNT(*) as total,
    COUNT(DISTINCT ad_id) as unique_ads,
    COUNT(*) - COUNT(year) as missing_year,
    COUNT(*) - COUNT(price_numeric) as missing_price,
    COUNT(*) - COUNT(marca) as missing_marca
FROM cochesnet;
```

### B) Re-parsear con TitleParser

```python
# Script para re-parsear títulos con TitleParser + marca_modelos
from scraping.base.title_parser import get_title_parser
from scraping.storage.supabase_client import get_supabase_client

supabase = get_supabase_client()
parser = get_title_parser(supabase)

# Load all cochesnet records
result = supabase.client.table('cochesnet').select('ad_id, title').execute()

updates = []
for row in result.data:
    ad_id = row['ad_id']
    title = row['title']

    # Parse with new parser
    parsed = parser.parse(title)

    # Prepare update
    updates.append({
        'ad_id': ad_id,
        'marca': parsed.marca,
        'modelo': parsed.modelo,
        'version': parsed.version,
        'parsing_confidence': parsed.confidence,
        'parsing_method': 'db_exact' if parsed.confidence >= 0.9 else 'db_fuzzy' if parsed.confidence >= 0.7 else 'heuristic',
        'parser_version': 3
    })

    # Batch update every 100 records
    if len(updates) >= 100:
        supabase.client.table('cochesnet').upsert(
            updates,
            on_conflict='ad_id'
        ).execute()
        print(f"Updated {len(updates)} records")
        updates = []

# Final batch
if updates:
    supabase.client.table('cochesnet').upsert(updates, on_conflict='ad_id').execute()
    print(f"Updated {len(updates)} records")

print("Re-parsing complete!")
```

---

## 5. Queries de Ejemplo con Nueva Estructura

### A) Búsqueda por marca y modelo

```sql
-- ANTES (lento sin índice correcto)
SELECT * FROM cochesnet
WHERE LOWER(marca) = 'opel'
  AND LOWER(modelo) LIKE 'corsa%'
ORDER BY price_numeric;

-- DESPUÉS (rápido con índice marca_normalized)
SELECT * FROM cochesnet
WHERE marca_normalized = 'opel'
  AND modelo_normalized = 'corsa'
  AND is_active = TRUE
ORDER BY price_numeric;
```

### B) Coches con alta confidence de parsing

```sql
SELECT
    marca,
    modelo,
    COUNT(*) as total,
    AVG(parsing_confidence) as avg_confidence
FROM cochesnet
WHERE parsing_confidence >= 0.9
GROUP BY marca, modelo
ORDER BY total DESC
LIMIT 20;
```

### C) Detectar bajadas de precio

```sql
WITH price_changes AS (
    SELECT
        ad_id,
        price_numeric,
        LAG(price_numeric) OVER (PARTITION BY ad_id ORDER BY scraped_at) as prev_price,
        scraped_at
    FROM cochesnet_price_history
)
SELECT
    c.*,
    pc.prev_price,
    pc.prev_price - pc.price_numeric as price_drop,
    ROUND((pc.prev_price - pc.price_numeric)::NUMERIC / pc.prev_price * 100, 2) as price_drop_percent
FROM cochesnet c
JOIN price_changes pc ON c.ad_id = pc.ad_id
WHERE pc.prev_price IS NOT NULL
  AND pc.price_numeric < pc.prev_price
  AND c.is_active = TRUE
ORDER BY price_drop DESC
LIMIT 50;
```

### D) Full-text search en título

```sql
-- Buscar "BMW X5 diesel"
SELECT
    marca,
    modelo,
    version,
    year,
    price_numeric,
    ts_rank(to_tsvector('spanish', title), query) as relevance
FROM cochesnet,
     to_tsquery('spanish', 'bmw & x5 & diesel') query
WHERE to_tsvector('spanish', title) @@ query
  AND is_active = TRUE
ORDER BY relevance DESC, price_numeric
LIMIT 20;
```

---

## 6. Resumen de Mejoras

| Aspecto | Antes | Después | Beneficio |
|---------|-------|---------|-----------|
| **year** | TEXT | INTEGER | Queries numéricas, ordenamiento |
| **marca/modelo** | 5 campos confusos | 4 campos claros | Simplicidad |
| **transmission** | ❌ No existe | ✅ Existe | Paridad con otros scrapers |
| **Parsing metadata** | ❌ No existe | ✅ confidence + method | Auditoría |
| **Price history** | ❌ Perdido | ✅ Tracking completo | Detectar ofertas |
| **Índices** | Básicos | Optimizados | Búsquedas 10-100x más rápidas |
| **Full-text search** | ❌ No | ✅ GIN index | Búsquedas de texto |
| **Normalization** | Manual | GENERATED ALWAYS | Consistencia automática |

---

## 7. Próximos Pasos

1. ✅ **Crear tabla `marca_modelos`** con top 500 marcas/modelos
2. ✅ **Integrar `TitleParser`** en `CochesNetParser`
3. ⚠️ **Migrar tabla `cochesnet`** a estructura v2
4. ⚠️ **Re-parsear** todos los títulos existentes
5. ⚠️ **Poblar `price_history`** con datos actuales
6. ⚠️ **Crear índices** optimizados
7. ✅ **Testing** de queries comunes

**Orden recomendado:**
1. Crear `marca_modelos` y poblarla
2. Probar `TitleParser` con muestra de 100 títulos
3. Revisar resultados y ajustar
4. Migrar tabla completa
5. Re-parsear con nuevo parser
