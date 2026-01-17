-- 1. Ensure PostGIS is enabled
CREATE EXTENSION IF NOT EXISTS postgis;

-- 2. RESET STAGING AREA (The "Raw" Dump)
-- We drop this so colossal_inventor (Python) can auto-create it fresh 
-- with the exact columns from the first CSV batch.
DROP TABLE IF EXISTS trips_data_raw;

-- 3. RESET DESTINATION TABLES (The "Clean" Data)
DROP TABLE IF EXISTS trips;
DROP TABLE IF EXISTS stations;

CREATE TABLE stations (
    id SERIAL PRIMARY KEY,
    station_id VARCHAR(255) UNIQUE NOT NULL, -- INCREASED SIZE
    name VARCHAR(255),
    latitude FLOAT,
    longitude FLOAT,
    geometry GEOMETRY(POINT, 4326),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Create Trips Table (Clean Schema)
CREATE TABLE trips (
    trip_id SERIAL PRIMARY KEY,
    started_at TIMESTAMP,
    ended_at TIMESTAMP,
    start_station_id VARCHAR(255),
    end_station_id VARCHAR(255),
    duration_minutes FLOAT
);

-- 6. Create Indexes
-- Spatial index for finding stations by location
CREATE INDEX idx_stations_geom ON stations USING GIST (geometry);
-- Index for faster trip lookups
CREATE INDEX idx_trips_start_station ON trips (start_station_id);
CREATE INDEX idx_trips_end_station ON trips (end_station_id);