-- ============================================
-- Tabla: ocasionplus
-- Fuente: https://www.ocasionplus.com
-- Patrón: Infinite Scroll (similar a Clicars)
-- ============================================

CREATE TABLE ocasionplus (
    id BIGSERIAL PRIMARY KEY,

    -- Identificación
    listing_id TEXT UNIQUE NOT NULL,
    url TEXT,

    -- Vehículo
    marca TEXT,
    modelo TEXT,
    version TEXT,
    titulo_completo TEXT,

    -- Potencia (dual format)
    potencia TEXT,                -- "245 CV"
    potencia_cv INTEGER,          -- 245

    -- Precio (triple format: contado, financiado, cuota)
    precio TEXT,                  -- "39.990€"
    precio_contado INTEGER,       -- 39990
    precio_financiado INTEGER,    -- 36355
    cuota_mensual INTEGER,        -- 559

    -- Año
    year INTEGER,

    -- Kilometraje (dual format)
    kilometros TEXT,              -- "24.228 Km"
    kilometros_numeric INTEGER,   -- 24228

    -- Características
    combustible TEXT,             -- "Gasolina", "Diésel", "Híbrido", "Eléctrico"
    transmision TEXT,             -- "Manual", "Automático"
    etiqueta_ambiental TEXT,      -- "C", "B", "ECO", "0"

    -- Ubicación
    ubicacion TEXT,               -- "Cádiz - Jerez"

    -- Media
    imagen_url TEXT,

    -- Timestamps
    scraped_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- Índices para búsquedas frecuentes
-- ============================================

-- Índice único por listing_id (ya definido en columna)
CREATE INDEX idx_ocasionplus_marca ON ocasionplus(marca);
CREATE INDEX idx_ocasionplus_modelo ON ocasionplus(modelo);
CREATE INDEX idx_ocasionplus_year ON ocasionplus(year);
CREATE INDEX idx_ocasionplus_precio ON ocasionplus(precio_contado);
CREATE INDEX idx_ocasionplus_km ON ocasionplus(kilometros_numeric);
CREATE INDEX idx_ocasionplus_combustible ON ocasionplus(combustible);
CREATE INDEX idx_ocasionplus_ubicacion ON ocasionplus(ubicacion);

-- Índice compuesto para búsquedas comunes
CREATE INDEX idx_ocasionplus_marca_modelo ON ocasionplus(marca, modelo);
CREATE INDEX idx_ocasionplus_marca_year ON ocasionplus(marca, year);

-- ============================================
-- Trigger para updated_at automático
-- ============================================

CREATE OR REPLACE FUNCTION update_ocasionplus_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_ocasionplus_updated_at
    BEFORE UPDATE ON ocasionplus
    FOR EACH ROW
    EXECUTE FUNCTION update_ocasionplus_updated_at();

-- ============================================
-- Comentarios descriptivos
-- ============================================

COMMENT ON TABLE ocasionplus IS 'Listados de coches de segunda mano de OcasionPlus.com';
COMMENT ON COLUMN ocasionplus.listing_id IS 'ID único del anuncio en OcasionPlus';
COMMENT ON COLUMN ocasionplus.potencia_cv IS 'Potencia en CV extraída de la versión';
COMMENT ON COLUMN ocasionplus.precio_contado IS 'Precio de contado en euros';
COMMENT ON COLUMN ocasionplus.precio_financiado IS 'Precio con financiación en euros';
COMMENT ON COLUMN ocasionplus.cuota_mensual IS 'Cuota mensual de financiación en euros';
COMMENT ON COLUMN ocasionplus.etiqueta_ambiental IS 'Etiqueta DGT: 0, ECO, C, B';
