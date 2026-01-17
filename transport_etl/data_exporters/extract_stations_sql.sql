INSERT INTO public.stations (station_id, name, latitude, longitude, geometry)
SELECT
    start_station_id as station_id,
    
    -- Pick the most common name (alphabetically last) to settle variations
    MAX(start_station_name) as name,
    
    -- Average the coordinates to eliminate GPS drift/jitter
    AVG(start_station_latitude) as latitude,
    AVG(start_station_longitude) as longitude,
    
    -- Create point from the Averaged coordinates
    ST_SetSRID(ST_MakePoint(AVG(start_station_longitude), AVG(start_station_latitude)), 4326) as geometry

FROM public.trips_data_raw
WHERE start_station_id IS NOT NULL 
  AND start_station_latitude IS NOT NULL
  AND start_station_longitude IS NOT NULL

-- 🚨 CRITICAL FIX: Collapse duplicates into one row per ID
GROUP BY start_station_id

ON CONFLICT (station_id) 
DO UPDATE SET
    name = EXCLUDED.name,
    latitude = EXCLUDED.latitude,
    longitude = EXCLUDED.longitude;