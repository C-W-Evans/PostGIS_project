if 'transformer' not in globals():
    from mage_ai.data_preparation.decorators import transformer
import pandas as pd
import numpy as np

@transformer
def standardize_columns(df, *args, **kwargs):
    """
    1. Renames 'Old' columns to 'New' schema.
    2. Converts time columns to datetime objects.
    3. CLEANS IDs to remove '.0' decimals and mixed types.
    """
    print(f"--- INPUT START ---")
    print(f"Initial Shape: {df.shape}")
    print(f"Initial Columns: {df.columns.tolist()}")

    # --- 1. Normalize Column Names ---
    rename_map = {
        'Start time': 'started_at',
        'End time': 'ended_at',
        'Start station': 'start_station_id',
        'End station': 'end_station_id',
        'Start station number': 'start_station_id',
        'Start station name': 'start_station_name',
        # Added explicit check for Latitude/Longitude if they appear in 'New' data
        'Start Lat': 'start_station_latitude', 
        'Start Lng': 'start_station_longitude'
    }
    df = df.rename(columns=rename_map)

    # --- 2. Ensure All Expected Columns Exist ---
    expected_cols = [
        'started_at', 'ended_at', 
        'start_station_id', 'end_station_id',
        'start_station_name', 'start_station_latitude', 'start_station_longitude'
    ]
    
    for col in expected_cols:
        if col not in df.columns:
            df[col] = np.nan

    # --- 3. FIX: Robust ID Standardization ---
    # This fixes the "3100.0" (float) vs "3100" (string) issue
    id_cols = ['start_station_id', 'end_station_id']
    for col in id_cols:
        # Force numeric first to handle '3100.0' strings or floats
        # errors='coerce' turns non-numeric junk into NaN temporarily
        df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Convert to nullable integer (Int64), then to string
        # This removes the decimal point: 3100.0 -> 3100 -> "3100"
        df[col] = df[col].astype('Int64').astype(str)
        
        # 'astype(str)' turns NaNs into the string "<NA>". We must revert that.
        df[col] = df[col].replace('<NA>', np.nan)

    # --- 4. Convert Types (Dates) ---
    df['started_at'] = pd.to_datetime(df['started_at'], errors='coerce')
    df['ended_at'] = pd.to_datetime(df['ended_at'], errors='coerce')

    # --- 5. EXTENSIVE LOGGING ---
    print(f"--- DATA INSPECTION ---")
    
    # Check 1: How many rows have valid Station IDs?
    valid_ids = df['start_station_id'].notna().sum()
    print(f"Rows with Valid Start Station IDs: {valid_ids} / {len(df)}")
    
    # Check 2: Sample what the IDs actually look like
    print("Sample Station IDs (Head):")
    print(df['start_station_id'].dropna().head(5).tolist())

    # Check 3: Check Lat/Lon availability (Crucial for transform_stations)
    valid_locs = df[['start_station_latitude', 'start_station_longitude']].dropna().shape[0]
    print(f"Rows with Valid Lat/Lon: {valid_locs} / {len(df)}")
    
    # Check 4: Check Date parsing success
    valid_dates = df['started_at'].notna().sum()
    print(f"Rows with Valid Dates: {valid_dates} / {len(df)}")

    if valid_ids == 0:
        print("🚨 CRITICAL: No valid station IDs found. Check input column names!")
    
    return df