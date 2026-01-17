INSERT INTO public.trips (started_at, ended_at, start_station_id, end_station_id, duration_minutes)
SELECT
    started_at,
    ended_at,
    start_station_id,
    end_station_id,
    -- Calculate duration in minutes
    EXTRACT(EPOCH FROM (ended_at - started_at)) / 60 as duration_minutes
FROM public.trips_data_raw
WHERE started_at IS NOT NULL;