if 'transformer' not in globals():
    from mage_ai.data_preparation.decorators import transformer
import pandas as pd
import os

@transformer
def transform(data, *args, **kwargs):
    """
    Robustly handles input whether it is a single metadata dict
    OR a list of metadata dicts.
    Input format expected: {'type': '...', 'path': '...'}
    """
    
    # --- 1. Normalize Input (The Fix) ---
    # Mage Dynamic Blocks often pass a single item (dict) to each worker.
    # We ensure 'files_to_process' is always a LIST of file paths.
    files_to_process = []
    
    # Case A: Input is a single Dictionary (What you are currently receiving)
    if isinstance(data, dict):
        # Verify valid structure
        if 'path' in data:
            files_to_process.append(data['path'])
        else:
            print(f"Skipping invalid metadata dict: {data}")

    # Case B: Input is a List of Dictionaries (True Batching)
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and 'path' in item:
                files_to_process.append(item['path'])
            elif isinstance(item, str):
                # Fallback if input is just a list of string paths
                files_to_process.append(item)
    
    print(f"Worker started. Processing {len(files_to_process)} valid file paths.")

    # --- 2. Read and Combine ---
    dfs = []
    
    for file_path in files_to_process:
        try:
            print(f"Reading: {file_path}")
            
            # Low_memory=False handles mixed types in large files
            df = pd.read_csv(file_path, low_memory=False)
            
            # Track source for debugging/lineage
            df['source_file'] = os.path.basename(file_path)
            
            dfs.append(df)
            
        except Exception as e:
            print(f"FAILED to read {file_path}: {e}")
            continue

    if not dfs:
        print("No dataframes created. Returning empty.")
        return pd.DataFrame()

    # Combine all valid DFs for this batch
    batch_df = pd.concat(dfs, ignore_index=True)
    
    print(f"Batch complete. Total rows generated: {len(batch_df)}")
    return batch_df