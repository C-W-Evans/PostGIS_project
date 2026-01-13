if 'transformer' not in globals():
    from mage_ai.data_preparation.decorators import transformer
if 'test' not in globals():
    from mage_ai.data_preparation.decorators import test

@transformer
def transform_trips(df, *args, **kwargs):
    """
    Cleans and selects only the trip data (Old + New mixed).
    """
    
    # 1. Select the core columns we want for the trips table
    # We ignore the lat/long columns here because we already extracted them 
    # in the other branch.
    trip_cols = [
        'started_at', 
        'ended_at', 
        'start_station_id', 
        'end_station_id'
    ]
    
    # 2. Create the clean dataframe
    trips_df = df[trip_cols].copy()
    
    # 3. Clean IDs (Optional but recommended)
    # Sometimes IDs are mixed strings/ints. Let's force them to strings to be safe,
    # or drop rows where the Station ID is missing (can't link them anyway).
    trips_df = trips_df.dropna(subset=['start_station_id', 'end_station_id'])
    
    # 4. Calculate Duration (Optional, useful for analysis)
    # PostGIS can do this, but Pandas is often faster to pre-calc
    trips_df['duration_minutes'] = (trips_df['ended_at'] - trips_df['started_at']).dt.total_seconds() / 60

    print(f"Total trips processed: {len(trips_df)}")
    return trips_df

@test
def test_output(output, *args) -> None:
    assert output is not None, 'The output is undefined'
    assert 'started_at' in output.columns, 'Missing started_at'
    assert len(output) > 0, 'No trips returned'