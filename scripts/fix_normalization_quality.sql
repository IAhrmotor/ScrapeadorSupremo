-- ============================================================================
-- SCRIPT DE CORRECCIÓN DE CALIDAD DE NORMALIZACIÓN
-- Tabla: vehiculos_combinados_v4
-- Fecha: 2025-12-17
-- ============================================================================

-- ============================================================================
-- PARTE 1: CORRECCIONES DE marca_norm
-- ============================================================================

-- 1.1 Land Rover (espacio → guión)
UPDATE vehiculos_combinados_v4
SET marca_norm = 'land-rover', updated_at = NOW()
WHERE marca_norm = 'land rover';

-- 1.2 Alfa Romeo (espacio → guión)
UPDATE vehiculos_combinados_v4
SET marca_norm = 'alfa-romeo', updated_at = NOW()
WHERE marca_norm = 'alfa romeo';

-- 1.3 DS → DS Automobiles
UPDATE vehiculos_combinados_v4
SET marca_norm = 'ds-automobiles', updated_at = NOW()
WHERE marca_norm = 'ds';

-- 1.4 Aston Martin (espacio → guión)
UPDATE vehiculos_combinados_v4
SET marca_norm = 'aston-martin', updated_at = NOW()
WHERE marca_norm IN ('aston martin', 'aston');

-- 1.5 Lynk & Co (todas las variaciones)
UPDATE vehiculos_combinados_v4
SET marca_norm = 'lynk-&-co', updated_at = NOW()
WHERE marca_norm IN ('lynk & co', 'lynk  co', 'lynk');

-- 1.6 KGM (antes Ssangyong)
UPDATE vehiculos_combinados_v4
SET marca_norm = 'kgm', updated_at = NOW()
WHERE marca_norm = 'kgm  ssangyong';

-- 1.7 Land Rover con modelo mezclado en marca (extraer modelo)
-- Range Rover
UPDATE vehiculos_combinados_v4
SET
    marca_norm = 'land-rover',
    modelo_norm = CASE
        WHEN modelo_norm IS NULL OR modelo_norm = '' THEN 'range rover'
        ELSE modelo_norm
    END,
    updated_at = NOW()
WHERE marca_norm = 'land-rover range';

-- Discovery
UPDATE vehiculos_combinados_v4
SET
    marca_norm = 'land-rover',
    modelo_norm = CASE
        WHEN modelo_norm IS NULL OR modelo_norm = '' THEN 'discovery'
        ELSE modelo_norm
    END,
    updated_at = NOW()
WHERE marca_norm = 'land-rover discovery';

-- Defender
UPDATE vehiculos_combinados_v4
SET
    marca_norm = 'land-rover',
    modelo_norm = CASE
        WHEN modelo_norm IS NULL OR modelo_norm = '' THEN 'defender'
        ELSE modelo_norm
    END,
    updated_at = NOW()
WHERE marca_norm = 'land-rover defender';

-- Freelander
UPDATE vehiculos_combinados_v4
SET
    marca_norm = 'land-rover',
    modelo_norm = CASE
        WHEN modelo_norm IS NULL OR modelo_norm = '' THEN 'freelander'
        ELSE modelo_norm
    END,
    updated_at = NOW()
WHERE marca_norm = 'land-rover freelander';

-- ============================================================================
-- PARTE 2: CORRECCIONES DE modelo_norm (Mercedes-Benz)
-- Normalizar "clase X" → "clase x" (mantener prefijo pero consistente)
-- ============================================================================

-- Mercedes: Unificar modelos - usar formato "clase x" para clases principales
-- Los modelos tipo CLA, GLC, GLA se convierten a "clase cla", "clase glc", etc.

-- 2.1 CLA → clase cla
UPDATE vehiculos_combinados_v4
SET modelo_norm = 'clase cla', updated_at = NOW()
WHERE marca_norm = 'mercedes-benz' AND modelo_norm = 'cla';

-- 2.2 GLC → clase glc
UPDATE vehiculos_combinados_v4
SET modelo_norm = 'clase glc', updated_at = NOW()
WHERE marca_norm = 'mercedes-benz' AND modelo_norm = 'glc';

-- 2.3 GLA → clase gla
UPDATE vehiculos_combinados_v4
SET modelo_norm = 'clase gla', updated_at = NOW()
WHERE marca_norm = 'mercedes-benz' AND modelo_norm = 'gla';

-- 2.4 GLE → clase gle
UPDATE vehiculos_combinados_v4
SET modelo_norm = 'clase gle', updated_at = NOW()
WHERE marca_norm = 'mercedes-benz' AND modelo_norm = 'gle';

-- 2.5 GLB → clase glb
UPDATE vehiculos_combinados_v4
SET modelo_norm = 'clase glb', updated_at = NOW()
WHERE marca_norm = 'mercedes-benz' AND modelo_norm = 'glb';

-- 2.6 CLS → clase cls
UPDATE vehiculos_combinados_v4
SET modelo_norm = 'clase cls', updated_at = NOW()
WHERE marca_norm = 'mercedes-benz' AND modelo_norm = 'cls';

-- 2.7 GLK → clase glk
UPDATE vehiculos_combinados_v4
SET modelo_norm = 'clase glk', updated_at = NOW()
WHERE marca_norm = 'mercedes-benz' AND modelo_norm = 'glk';

-- 2.8 SLK → clase slk
UPDATE vehiculos_combinados_v4
SET modelo_norm = 'clase slk', updated_at = NOW()
WHERE marca_norm = 'mercedes-benz' AND modelo_norm = 'slk';

-- 2.9 CLE → clase cle
UPDATE vehiculos_combinados_v4
SET modelo_norm = 'clase cle', updated_at = NOW()
WHERE marca_norm = 'mercedes-benz' AND modelo_norm = 'cle';

-- 2.10 CLC → clase clc
UPDATE vehiculos_combinados_v4
SET modelo_norm = 'clase clc', updated_at = NOW()
WHERE marca_norm = 'mercedes-benz' AND modelo_norm = 'clc';

-- 2.11 GLS → clase gls
UPDATE vehiculos_combinados_v4
SET modelo_norm = 'clase gls', updated_at = NOW()
WHERE marca_norm = 'mercedes-benz' AND modelo_norm = 'gls';

-- 2.12 SL → clase sl
UPDATE vehiculos_combinados_v4
SET modelo_norm = 'clase sl', updated_at = NOW()
WHERE marca_norm = 'mercedes-benz' AND modelo_norm = 'sl';

-- 2.13 GL → clase gl
UPDATE vehiculos_combinados_v4
SET modelo_norm = 'clase gl', updated_at = NOW()
WHERE marca_norm = 'mercedes-benz' AND modelo_norm = 'gl';

-- 2.14 SLC → clase slc
UPDATE vehiculos_combinados_v4
SET modelo_norm = 'clase slc', updated_at = NOW()
WHERE marca_norm = 'mercedes-benz' AND modelo_norm = 'slc';

-- 2.15 CL → clase cl
UPDATE vehiculos_combinados_v4
SET modelo_norm = 'clase cl', updated_at = NOW()
WHERE marca_norm = 'mercedes-benz' AND modelo_norm = 'cl';

-- ============================================================================
-- PARTE 3: MARCAS ADICIONALES QUE FALTAN EN vehicle_brands (agregar al catálogo)
-- ============================================================================

-- Estas marcas existen en los datos pero no están en vehicle_brands:
-- ferrari, bentley, lamborghini, iveco, dfsk, swm, rover, bestune, livan,
-- mahindra, mclaren, ram, maxus, seres, baic, hummer, gmc

-- Se pueden agregar al catálogo si se desea:
/*
INSERT INTO vehicle_brands (canonical_name, display_name, is_active, source)
VALUES
    ('ferrari', 'Ferrari', true, 'manual'),
    ('bentley', 'Bentley', true, 'manual'),
    ('lamborghini', 'Lamborghini', true, 'manual'),
    ('iveco', 'Iveco', true, 'manual'),
    ('dfsk', 'DFSK', true, 'manual'),
    ('swm', 'SWM', true, 'manual'),
    ('rover', 'Rover', true, 'manual'),
    ('bestune', 'Bestune', true, 'manual'),
    ('livan', 'Livan', true, 'manual'),
    ('mahindra', 'Mahindra', true, 'manual'),
    ('mclaren', 'McLaren', true, 'manual'),
    ('ram', 'RAM', true, 'manual'),
    ('maxus', 'Maxus', true, 'manual'),
    ('seres', 'Seres', true, 'manual'),
    ('baic', 'BAIC', true, 'manual'),
    ('hummer', 'Hummer', true, 'manual'),
    ('gmc', 'GMC', true, 'manual')
ON CONFLICT (canonical_name) DO NOTHING;
*/

-- ============================================================================
-- PARTE 4: VERIFICACIÓN POST-CORRECCIÓN
-- ============================================================================

-- Verificar marcas corregidas
SELECT marca_norm, COUNT(*) as total
FROM vehiculos_combinados_v4
WHERE marca_norm IN ('land-rover', 'alfa-romeo', 'ds-automobiles', 'aston-martin', 'lynk-&-co', 'kgm')
GROUP BY marca_norm
ORDER BY total DESC;

-- Verificar modelos Mercedes corregidos
SELECT modelo_norm, COUNT(*) as total
FROM vehiculos_combinados_v4
WHERE marca_norm = 'mercedes-benz'
  AND modelo_norm LIKE 'clase %'
GROUP BY modelo_norm
ORDER BY total DESC;

-- Verificar que no quedan variaciones problemáticas
SELECT marca_norm, COUNT(*) as total
FROM vehiculos_combinados_v4
WHERE marca_norm IN ('land rover', 'alfa romeo', 'ds', 'aston martin', 'aston',
                     'lynk & co', 'lynk  co', 'lynk', 'kgm  ssangyong',
                     'land-rover range', 'land-rover discovery', 'land-rover defender', 'land-rover freelander')
GROUP BY marca_norm;
-- Debería devolver 0 filas si todo se corrigió correctamente
