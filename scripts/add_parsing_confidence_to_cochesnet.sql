-- Add parsing metadata columns to cochesnet table
-- Run this in Supabase SQL Editor

ALTER TABLE cochesnet
ADD COLUMN IF NOT EXISTS parsing_confidence DECIMAL(3,2),
ADD COLUMN IF NOT EXISTS parsing_method VARCHAR(50);

-- Add comments
COMMENT ON COLUMN cochesnet.parsing_confidence IS 'Confidence score from TitleParser (0.0-1.0)';
COMMENT ON COLUMN cochesnet.parsing_method IS 'Parsing method used: database or heuristic';

-- Create index for filtering by confidence
CREATE INDEX IF NOT EXISTS idx_cochesnet_parsing_confidence
ON cochesnet(parsing_confidence);

-- Verify columns were added
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'cochesnet'
AND column_name IN ('parsing_confidence', 'parsing_method');
