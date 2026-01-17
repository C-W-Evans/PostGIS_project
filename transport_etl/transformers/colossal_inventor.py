if 'transformer' not in globals():
    from mage_ai.data_preparation.decorators import transformer
from mage_ai.settings.repo import get_repo_path
from mage_ai.io.config import ConfigFileLoader
from mage_ai.io.postgres import Postgres
import pandas as pd
import os
import gc
import ctypes

def trim_memory():
    try:
        libc = ctypes.CDLL("libc.so.6")
        libc.malloc_trim(0)
    except Exception:
        pass

@transformer
def transform(batches, *args, **kwargs):
    # 1. SETUP & CONFIG
    config_path = os.path.join(get_repo_path(), 'io_config.yaml')
    config_profile = 'default'
    table_name = 'trips_data_raw'
    
    # 2. CHECKPOINTING: Find out what is already in DB
    print("Checking for existing files in DB to avoid duplicates...")
    existing_files = set()
    try:
        query = f"SELECT DISTINCT source_file FROM {table_name}"
        with Postgres.with_config(ConfigFileLoader(config_path, config_profile)) as loader:
            # Load existing filenames into a set for fast lookup
            df_existing = loader.load(query)
            if not df_existing.empty:
                existing_files = set(df_existing['source_file'].tolist())
        print(f"Found {len(existing_files)} files already processed. Resuming...")
    except Exception as e:
        print("Table might not exist yet or empty. Starting fresh.")

    # 3. PROCESSING LOOP
    total_batches = len(batches)
    
    for i, batch in enumerate(batches):
        # We need to peek at the filename inside the batch to see if we should skip
        # Since batch size is 1, we can just look at the first item
        files_in_batch = batch.get('batch_files', [])
        if not files_in_batch: continue
        
        current_file_path = files_in_batch[0].get('path')
        current_filename = os.path.basename(current_file_path)

        # --- THE CHECKPOINT LOGIC ---
        if current_filename in existing_files:
            print(f"⏩ Skipping Batch {i+1}/{total_batches} ({current_filename}) - Already in DB.")
            continue
        # ----------------------------

        print(f"Processing Batch {i+1}/{total_batches} ({current_filename})...")
        gc.collect() 

        try:
            # --- PHASE A: READ FILES ---
            dfs = []
            for item in files_in_batch:
                try:
                    f_path = item.get('path')
                    f_type = item.get('type', 'new')
                    
                    if f_type == 'old':
                        df = pd.read_csv(f_path, compression='zip', low_memory=False)
                    else:
                        df = pd.read_csv(f_path, low_memory=False)
                    
                    df['source_file'] = os.path.basename(f_path)
                    
                    # Force duration to float immediately to save memory/schema
                    if 'duration' in df.columns:
                        df['duration'] = pd.to_numeric(df['duration'], errors='coerce')
                        
                    dfs.append(df)
                except Exception as read_err:
                    print(f"  ⚠️ Skipped corrupt file {item}: {read_err}")

            if not dfs: continue

            # --- PHASE B: MERGE & CLEAN ---
            batch_df = pd.concat(dfs, ignore_index=True)
            
            # Standardization Logic
            batch_df.columns = [str(c).strip() for c in batch_df.columns]
            rename_map = {
                'Start time': 'started_at', 'Start Time': 'started_at', 'start time': 'started_at',
                'End time': 'ended_at', 'End Time': 'ended_at',
                'Start station': 'start_station_id', 'End station': 'end_station_id',
                'Start station number': 'start_station_id', 'End station number': 'end_station_id'
            }
            batch_df = batch_df.rename(columns=rename_map)

            # Fix Dates
            if 'started_at' in batch_df.columns:
                batch_df['started_at'] = pd.to_datetime(batch_df['started_at'], errors='coerce')
            if 'ended_at' in batch_df.columns:
                batch_df['ended_at'] = pd.to_datetime(batch_df['ended_at'], errors='coerce')

            # Fix IDs (Remove '.0')
            def clean_id(val):
                s = str(val)
                if s.endswith('.0'): return s[:-2]
                return s

            if 'start_station_id' in batch_df.columns:
                batch_df['start_station_id'] = batch_df['start_station_id'].apply(clean_id)
            if 'end_station_id' in batch_df.columns:
                batch_df['end_station_id'] = batch_df['end_station_id'].apply(clean_id)

            # --- PHASE C: EXPORT ---
            # Safety Check: If batch is huge, print warning
            if len(batch_df) > 200000:
                print(f"⚠️ LARGE BATCH DETECTED: {len(batch_df)} rows. Memory spike expected.")

            with Postgres.with_config(ConfigFileLoader(config_path, config_profile)) as loader:
                loader.export(
                    batch_df,
                    schema_name='public',
                    table_name=table_name,
                    index=False,
                    if_exists='append',
                    allow_reserved_words_in_column_names=True
                )
            print(f"  ✅ Batch {i+1} Success.")
            
            # Add to set so we don't process it again if loop continues
            existing_files.add(current_filename)

        except Exception as e:
            print(f"  ❌ CRITICAL FAILURE IN BATCH {i+1}. SKIPPING.")
            print(f"  Error: {e}")
        
        finally:
            if 'batch_df' in locals(): del batch_df
            if 'dfs' in locals(): del dfs
            gc.collect()
            trim_memory()

    return pd.DataFrame()