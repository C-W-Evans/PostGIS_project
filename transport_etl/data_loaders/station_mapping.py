if 'data_loader' not in globals():
    from mage_ai.data_preparation.decorators import data_loader
import pandas as pd
import os
from mage_ai.settings.repo import get_repo_path

@data_loader
def load_data(*args, **kwargs):
    """
    Loads the station ID mapping file from the data directory.
    """
    # 1. Construct the absolute path to the file
    # This points to: /your_mage_project/data/legacy_new_station_id_mapping.csv
    file_path = os.path.join(get_repo_path(), 'data', 'legacy_new_station_id_mapping.csv')
    
    print(f"Attempting to load mapping from: {file_path}")
    
    # 2. Check if file exists (good for debugging)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Could not find the mapping file at: {file_path}")

    # 3. Read the CSV
    # dtype=str is crucial because IDs like "3100" can look like numbers but must act like strings
    df = pd.read_csv(file_path, dtype=str)
    
    print(f"Mapping loaded. Rows: {len(df)}")
    return df