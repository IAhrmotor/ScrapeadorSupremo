-- Add normalized columns to cochesnet table
-- Run this in Supabase SQL Editor

-- Add marca_normalizada for standardized brand names
ALTER TABLE cochesnet
ADD COLUMN IF NOT EXISTS marca_normalizada VARCHAR(100);

-- Add modelo_completo for full model name from TitleParser
ALTER TABLE cochesnet
ADD COLUMN IF NOT EXISTS modelo_completo VARCHAR(200);

-- Add modelo_variante for version/variant from title
ALTER TABLE cochesnet
ADD COLUMN IF NOT EXISTS modelo_variante TEXT;

-- Add transmision for gearbox type
ALTER TABLE cochesnet
ADD COLUMN IF NOT EXISTS transmision VARCHAR(50);

-- Add combustible_normalizado for standardized fuel type
ALTER TABLE cochesnet
ADD COLUMN IF NOT EXISTS combustible_normalizado VARCHAR(50);

-- Add comments
COMMENT ON COLUMN cochesnet.marca_normalizada IS 'Normalized brand name (uppercase, standard format)';
COMMENT ON COLUMN cochesnet.modelo_completo IS 'Full model name from TitleParser';
COMMENT ON COLUMN cochesnet.modelo_variante IS 'Model variant/version from title parsing';
COMMENT ON COLUMN cochesnet.transmision IS 'Transmission type (manual/automatic)';
COMMENT ON COLUMN cochesnet.combustible_normalizado IS 'Normalized fuel type (DIESEL, GASOLINA, ELECTRICO, etc.)';

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_cochesnet_marca_normalizada ON cochesnet(marca_normalizada);
CREATE INDEX IF NOT EXISTS idx_cochesnet_combustible_normalizado ON cochesnet(combustible_normalizado);

-- Verify columns were added
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'cochesnet'
AND column_name IN ('marca_normalizada', 'modelo_completo', 'modelo_variante', 'transmision', 'combustible_normalizado')
ORDER BY column_name;
