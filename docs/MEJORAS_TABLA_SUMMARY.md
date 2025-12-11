# Resumen Ejecutivo: Mejoras en Tabla Cochesnet

## 🎯 Cambios Críticos

### 1. Estructura de Campos

| Campo | Antes | Después | Motivo |
|-------|-------|---------|--------|
| `year` | TEXT | **INTEGER** | Queries numéricas, ordenamiento |
| `marca/modelo` | 5 campos | **4 campos claros** | Eliminardundancia |
| `transmission` | ❌ | **✅ TEXT** | Paridad con otros scrapers |
| `parsing_confidence` | ❌ | **✅ REAL (0-1)** | Auditar calidad |
| `parsing_method` | ❌ | **✅ TEXT** | Saber origen del parsing |

### 2. Nueva Tabla: `cochesnet_price_history`

```sql
CREATE TABLE cochesnet_price_history (
    id BIGSERIAL PRIMARY KEY,
    ad_id TEXT NOT NULL,
    price_numeric INTEGER NOT NULL,
    scraped_at TIMESTAMPTZ NOT NULL
);
```

**Beneficios:**
- 📊 Detectar bajadas de precio automáticamente
- 📈 Análisis de tendencias de mercado
- 🎯 Alertas de "buenas ofertas"

### 3. Índices Optimizados

```sql
-- Búsquedas por marca/modelo (10-100x más rápido)
CREATE INDEX idx_cochesnet_marca_modelo
    ON cochesnet(marca_normalized, modelo_normalized);

-- Búsquedas por precio
CREATE INDEX idx_cochesnet_price
    ON cochesnet(price_numeric);

-- Índice compuesto (búsqueda común)
CREATE INDEX idx_cochesnet_search
    ON cochesnet(marca_normalized, year DESC, price_numeric)
    WHERE is_active = TRUE;

-- Full-text search en español
CREATE INDEX idx_cochesnet_title_fts
    ON cochesnet USING gin(to_tsvector('spanish', title));
```

## 📋 Plan de Implementación

### Fase 1: Preparación (1 día)
1. ✅ Crear tabla `marca_modelos` con top 500 marcas/modelos
2. ✅ Integrar `TitleParser` en `CochesNetParser`
3. ✅ Probar con muestra de 100 anuncios

### Fase 2: Migración (2-3 horas)
1. Backup completo: `CREATE TABLE cochesnet_v1_backup AS SELECT * FROM cochesnet;`
2. Crear nueva estructura con ALTER TABLE o CREATE + INSERT
3. Migrar datos existentes con transformaciones:
   - `year::TEXT` → `year::INTEGER`
   - Agregar `transmission` = NULL
   - Calcular `parsing_confidence` basado en método usado

### Fase 3: Re-parsing (variable)
1. Re-parsear todos los títulos con `TitleParser + marca_modelos`
2. Actualizar campos `marca`, `modelo`, `version`
3. Actualizar `parsing_confidence` y `parsing_method`
4. Validar resultados (comparar con parsing anterior)

### Fase 4: Optimización (1 hora)
1. Crear todos los índices
2. Crear tabla `price_history`
3. Crear triggers automáticos
4. Crear vistas para búsquedas comunes

## 🚀 Beneficios Esperados

| Métrica | Antes | Después | Mejora |
|---------|-------|---------|--------|
| **Precisión parsing** | 60-70% | 95-98% | +35% |
| **Velocidad búsqueda** | 500-2000ms | 10-50ms | **50-200x** |
| **Tracking precio** | ❌ | ✅ | Detectar ofertas |
| **Consistencia** | ⚠️ Variable | ✅ Alta | Tabla referencia |
| **Full-text search** | ❌ | ✅ | Búsquedas naturales |

## 📝 Scripts SQL Listos

Todos los scripts están en [COCHESNET_TABLE_ANALYSIS.md](./COCHESNET_TABLE_ANALYSIS.md):
- ✅ Nueva estructura completa
- ✅ Tabla price_history con triggers
- ✅ Todos los índices optimizados
- ✅ Script de migración paso a paso
- ✅ Queries de ejemplo
- ✅ Script Python para re-parsing

## ⚠️ Consideraciones

**Tiempo de ejecución:**
- Migración estructura: ~5 minutos
- Re-parsing 10,000 anuncios: ~10-20 minutos
- Re-parsing 100,000 anuncios: ~2-3 horas
- Creación índices: ~5-10 minutos

**Downtime:**
- Opción A: Crear tabla nueva → 0 downtime
- Opción B: ALTER TABLE → 5-30 minutos downtime

**Rollback:**
- Backup completo antes de empezar
- Tabla `cochesnet_v1_backup` con todos los datos
- Restauración: 1-2 minutos

## 🎯 Recomendación Final

**HACER AHORA:**
1. Crear `marca_modelos` con top 100 marcas/modelos manualmente
2. Integrar `TitleParser` en nuevo scraping (NO tocar datos antiguos)
3. Probar con nuevos anuncios durante 1 semana

**HACER DESPUÉS (cuando TitleParser esté validado):**
4. Migrar tabla completa con nueva estructura
5. Re-parsear anuncios antiguos
6. Crear índices y price_history

**Orden seguro:**
```
Nuevo scraping con TitleParser → Validar 1 semana → Migrar tabla → Re-parsear histórico
```

Esto minimiza riesgo y permite validar antes de tocar datos existentes.
