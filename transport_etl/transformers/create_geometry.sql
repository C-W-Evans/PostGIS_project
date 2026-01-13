-- Docs: https://docs.mage.ai/guides/sql-blocks
-- 1. Create the geometry column (safe to run even if column exists)
ALTER TABLE public.stations 
ADD COLUMN IF NOT EXISTS geom geometry(Point, 4326);

-- 2. Update the geometry column using the existing Lat/Long columns
-- Note: We cast to numeric/float just to be safe, though likely already float
UPDATE public.stations
SET geom = ST_SetSRID(ST_MakePoint(longitude::float, latitude::float), 4326)
WHERE latitude IS NOT NULL AND longitude IS NOT NULL;

-- 3. Create the spatial index (Critical for map performance)
CREATE INDEX IF NOT EXISTS idx_stations_geom ON public.stations USING GIST (geom);