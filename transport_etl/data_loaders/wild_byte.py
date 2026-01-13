import iostart
import pandas as pd
import zipfile
import os
from mage_ai.settings.repo import get_repo_path

if 'data_loader' not in globals():
    from mage_ai.data_preparation.decorators import data_loader
if 'test' not in globals():
    from mage_ai.data_preparation.decorators import test

@data_loader
def load_data_from_file(*args, **kwargs):
    """
    Loads data from 'old' and 'new' folders.
    Crucially, it KEEPS station metadata (lat/long/name) from the new files
    so we can extract a Stations table in the next step.
    """
    project_root = get_repo_path()
    data_path = os.path.join(project_root, 'data')
    old_folder = os.path.join(data_path, 'old')
    new_folder = os.path.join(data_path, 'new')

    dfs = []
    
    # --- DEV MODE: Change this from True to False for Production! ---
    DEV_MODE = False 

    # 1. Process 'Old' Folder (Zipped CSVs)
    if os.path.exists(old_folder):
        files = [f for f in os.listdir(old_folder) if f.endswith('.zip')]
        if DEV_MODE: files = files[:2] # Only load 2 files
        
        print(f"Processing {len(files)} files in 'old'...")

        for filename in files:
            zip_path = os.path.join(old_folder, filename)
            try:
                with zipfile.ZipFile(zip_path, 'r') as z:
                    for csv_name in z.namelist():
                        if csv_name.endswith('.csv'):
                            with z.open(csv_name) as f:
                                df = pd.read_csv(f)
                                df = df.rename(columns={
                                    'Start time': 'started_at',
                                    'End time': 'ended_at',
                                    'Start station': 'start_station_id',
                                    'End station': 'end_station_id'
                                    # Old data has no Lat/Long, so we stop here
                                })
                                dfs.append(df[['started_at', 'ended_at', 'start_station_id', 'end_station_id']])
            except Exception as e:
                print(f"Error reading zip {filename}: {e}")

    # 2. Process 'New' Folder (Standard CSVs)
    if os.path.exists(new_folder):
        files = [f for f in os.listdir(new_folder) if f.endswith('.csv')]
        if DEV_MODE: files = files[:2] # Only load 2 files
        
        print(f"Processing {len(files)} files in 'new'...")

        for filename in files:
            file_path = os.path.join(new_folder, filename)
            try:
                df = pd.read_csv(file_path)
                
                # WE MUST KEEP THESE COLUMNS NOW to create the Stations table later.
                # Even though the 'Old' data above doesn't have them.
                cols_to_keep = [
                    'started_at', 'ended_at', 
                    'start_station_id', 'end_station_id',
                    'start_station_name', 'start_station_latitude', 'start_station_longitude'
                ]
                
                # Select only columns that exist (safe selection)
                existing = [c for c in cols_to_keep if c in df.columns]
                dfs.append(df[existing])
                
            except Exception as e:
                print(f"Error reading csv {filename}: {e}")

    # 3. Merge
    if not dfs: raise ValueError("No data loaded.")

    print("Concatenating...")
    # This automatically creates NaN (empty) values for Lat/Long in the 'Old' rows
    total_df = pd.concat(dfs, ignore_index=True)
    
    # Cleanup timestamps
    total_df['started_at'] = pd.to_datetime(total_df['started_at'])
    total_df['ended_at'] = pd.to_datetime(total_df['ended_at'])

    print(f"Loaded {len(total_df)} rows. Columns available for next step:")
    print(list(total_df.columns))
    
    return total_df