-- Add missing columns to cochesnet table
-- Run this in Supabase SQL Editor

-- Add power_cv column (potencia en CV)
ALTER TABLE cochesnet
ADD COLUMN IF NOT EXISTS power_cv INTEGER;

-- Add other potentially missing columns
ALTER TABLE cochesnet
ADD COLUMN IF NOT EXISTS transmission VARCHAR(50),
ADD COLUMN IF NOT EXISTS version TEXT,
ADD COLUMN IF NOT EXISTS provincia VARCHAR(100);

-- Add comments
COMMENT ON COLUMN cochesnet.power_cv IS 'Engine power in CV (horsepower)';
COMMENT ON COLUMN cochesnet.transmission IS 'Transmission type: manual/automatic';
COMMENT ON COLUMN cochesnet.version IS 'Vehicle version/trim level';
COMMENT ON COLUMN cochesnet.provincia IS 'Province/region';

-- Verify all columns exist
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'cochesnet'
ORDER BY ordinal_position;
