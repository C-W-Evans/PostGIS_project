-- 1. Ensure PostGIS is enabled
CREATE EXTENSION IF NOT EXISTS postgis;

-- 2. Drop tables to start fresh
DROP TABLE IF EXISTS trips;
DROP TABLE IF EXISTS stations;

-- 3. Create Stations Table (Now with Lat/Lon columns)
CREATE TABLE stations (
    id SERIAL PRIMARY KEY,
    station_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255),
    latitude FLOAT,   -- Added
    longitude FLOAT,  -- Added
    geometry GEOMETRY(POINT, 4326),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Create Trips Table
CREATE TABLE trips (
    trip_id SERIAL PRIMARY KEY,
    started_at TIMESTAMP,
    ended_at TIMESTAMP,
    start_station_id VARCHAR(50),
    end_station_id VARCHAR(50),
    duration_minutes FLOAT
);

-- 5. Create Spatial Index (Crucial for PostGIS performance)
CREATE INDEX idx_stations_geom ON stations USING GIST (geometry);