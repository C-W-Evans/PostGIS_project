if 'transformer' not in globals():
    from mage_ai.data_preparation.decorators import transformer
if 'test' not in globals():
    from mage_ai.data_preparation.decorators import test

@transformer
def transform_stations(df, *args, **kwargs):
    # 1. Select only station columns
    station_cols = [
        'start_station_id', 
        'start_station_name', 
        'start_station_latitude', 
        'start_station_longitude'
    ]
    
    # Copy to avoid warnings
    stations_df = df[station_cols].copy()

    # 2. Rename for DB
    stations_df.rename(columns={
        'start_station_id': 'station_id',
        'start_station_name': 'station_name',
        'start_station_latitude': 'latitude',
        'start_station_longitude': 'longitude'
    }, inplace=True)

    # 3. Drop rows that have no location (The "Old" data)
    stations_df = stations_df.dropna(subset=['latitude', 'longitude'])

    # 4. Drop Duplicates (Keep 1 row per station ID)
    unique_stations = stations_df.drop_duplicates(subset=['station_id'])
    
    print(f"Unique stations found: {len(unique_stations)}")
    return unique_stations

@test
def test_output(output, *args) -> None:
    assert output is not None, 'The output is undefined'
    assert 'station_id' in output.columns, 'Missing station_id'