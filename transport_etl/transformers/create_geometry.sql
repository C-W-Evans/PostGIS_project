-- 1. Deduplicate (Safe method)
-- Only run if you are sure you want to delete data. 
-- This keeps the row with the HIGHEST ctid (usually the latest inserted) or lowest, depending on preference.
-- Here we keep the "min" ctid (the oldest row loaded) for stability.
DELETE FROM public.stations a USING public.stations b
WHERE a.ctid > b.ctid 
AND a.station_id = b.station_id;

-- 2. Create Geometry Column (Idempotent)
ALTER TABLE public.stations 
ADD COLUMN IF NOT EXISTS geom geometry(Point, 4326);

-- 3. Update Geometry (Optimized)
-- ONLY update rows that haven't been calculated yet (WHERE geom IS NULL)
UPDATE public.stations
SET geom = ST_SetSRID(ST_MakePoint(longitude::float, latitude::float), 4326)
WHERE latitude IS NOT NULL 
  AND longitude IS NOT NULL 
  AND geom IS NULL;

-- 4. Index
-- DROP index first to ensure a clean rebuild, or use IF NOT EXISTS
CREATE INDEX IF NOT EXISTS idx_stations_geom ON public.stations USING GIST (geom);