if 'transformer' not in globals():
    from mage_ai.data_preparation.decorators import transformer
import pandas as pd

@transformer
def transform_stations(df, *args, **kwargs):
    # 1. Define the Mapping (CSV Header -> Database Column)
    # This ensures we renamed 'start_station_name' to 'station_name'
    rename_map = {
        'start_station_id': 'station_id',
        'start_station_name': 'station_name',
        'start_station_latitude': 'latitude',
        'start_station_longitude': 'longitude'
    }
    
    # 2. Safety Check: Create missing columns with None
    # This prevents crashes if the "New" CSV is missing the name column
    for source_col in rename_map.keys():
        if source_col not in df.columns:
            print(f"⚠️ Warning: '{source_col}' missing in input. Filling with None.")
            df[source_col] = None

    # 3. Rename and Select Columns
    stations_df = df.rename(columns=rename_map)
    
    # Only keep the columns we want for the DB
    # We use the VALUES of the map (station_id, station_name, etc.)
    keep_cols = list(rename_map.values())
    stations_df = stations_df[keep_cols].copy()

    # 4. Clean Data (Drop rows without location, Drop duplicates)
    stations_df = stations_df.dropna(subset=['latitude', 'longitude'])
    stations_df = stations_df.drop_duplicates(subset=['station_id'])
    
    print(f"✅ Transform Complete. Output Columns: {stations_df.columns.tolist()}")
    return stations_df