if 'transformer' not in globals():
    from mage_ai.data_preparation.decorators import transformer
from mage_ai.settings.repo import get_repo_path
from mage_ai.io.config import ConfigFileLoader
from mage_ai.io.postgres import Postgres
import pandas as pd
import os
import gc
import traceback # <--- Added for detailed error tracking
import ctypes

# --- DEFINE MEMORY TRIMMER ---
def trim_memory():
    try:
        libc = ctypes.CDLL("libc.so.6")
        libc.malloc_trim(0)
    except Exception:
        pass # Ignore if not on Linux


@transformer
def transform(*args, **kwargs):
    """
    HARDENED BATCH ETL:
    - Wraps every batch in a safety block.
    - Skips bad batches instead of crashing.
    - Aggressively manages memory.
    """
    
    # --- 1. INPUT DETECTION ---
    batches = []
    mapping_df = None

    for arg in args:
        if isinstance(arg, list):
            batches = arg
        elif isinstance(arg, pd.DataFrame):
            if 'legacy_id' in arg.columns:
                mapping_df = arg

    if not batches:
        print("🚨 ERROR: No batch list received.")
        return pd.DataFrame()

    # --- 2. SETUP MAPPING & DB ---
    map_dict = {}
    if mapping_df is not None:
        map_dict = dict(zip(mapping_df['legacy_id'].astype(str), mapping_df['new_id'].astype(str)))

    config_path = os.path.join(get_repo_path(), 'io_config.yaml')
    config_profile = 'default'
    table_name = 'trips_data_raw'

    total_batches = len(batches)
    print(f"--- Starting Processing for {total_batches} batches ---")

    # --- 3. THE SAFE LOOP ---
    for i, batch in enumerate(batches):
        batch_num = i + 1
        print(f"Processing Batch {batch_num}/{total_batches}...")
        
        # Explicit GC before starting new batch
        gc.collect() 

        try:
            # --- PHASE A: READ FILES ---
            dfs = []
            files_in_batch = batch.get('batch_files', [])
            
            for item in files_in_batch:
                try:
                    f_path = item.get('path')
                    f_type = item.get('type', 'new')
                    
                    if f_type == 'old':
                        df = pd.read_csv(f_path, compression='zip', low_memory=False)
                    else:
                        df = pd.read_csv(f_path, low_memory=False)
                    
                    df['source_file'] = os.path.basename(f_path)
                    dfs.append(df)
                except Exception as read_err:
                    print(f"  ⚠️ Skipped corrupt file {item}: {read_err}")

            if not dfs:
                print(f"  ⚠️ Batch {batch_num} is empty (no readable files). Skipping.")
                continue

            # --- PHASE B: MERGE & CLEAN (The Danger Zone) ---
            # concat can spike memory, so we do it inside the safety try block
            batch_df = pd.concat(dfs, ignore_index=True)
            
            # Clean headers
            batch_df.columns = [str(c).strip() for c in batch_df.columns]
            
            rename_map = {
                'Start time': 'started_at', 'Start Time': 'started_at', 'start time': 'started_at',
                'End time': 'ended_at', 'End Time': 'ended_at',
                'Start station': 'start_station_id', 'End station': 'end_station_id',
                'Start station number': 'start_station_id', 'End station number': 'end_station_id'
            }
            batch_df = batch_df.rename(columns=rename_map)


            # --- NEW FIX: FORCE DURATION TO FLOAT ---
            # This prevents the "smallint" error by forcing a larger data type
            if 'duration' in batch_df.columns:
                batch_df['duration'] = batch_df['duration'].astype(float)
            # ----------------------------------------
            

            # Convert Dates
            if 'started_at' in batch_df.columns:
                batch_df['started_at'] = pd.to_datetime(batch_df['started_at'], errors='coerce')
            if 'ended_at' in batch_df.columns:
                batch_df['ended_at'] = pd.to_datetime(batch_df['ended_at'], errors='coerce')

            # Map IDs
            if map_dict:
                def safe_map(series, mapping):
                    return series.astype(str).map(mapping).fillna(series)

                if 'start_station_id' in batch_df.columns:
                    batch_df['start_station_id'] = safe_map(batch_df['start_station_id'], map_dict)
                if 'end_station_id' in batch_df.columns:
                    batch_df['end_station_id'] = safe_map(batch_df['end_station_id'], map_dict)

            # Force IDs to string and strip trailing '.0'
            def clean_id(val):
                s = str(val)
                if s.endswith('.0'):
                    return s[:-2]
                return s

            if 'start_station_id' in batch_df.columns:
                batch_df['start_station_id'] = batch_df['start_station_id'].apply(clean_id)
            if 'end_station_id' in batch_df.columns:
                batch_df['end_station_id'] = batch_df['end_station_id'].apply(clean_id)


            # --- PHASE C: EXPORT ---
            print(f"  Exporting {len(batch_df)} rows to Postgres...")
            with Postgres.with_config(ConfigFileLoader(config_path, config_profile)) as loader:
                loader.export(
                    batch_df,
                    schema_name='public',
                    table_name=table_name,
                    index=False,
                    if_exists='append',
                    allow_reserved_words_in_column_names=True
                )
            print(f"  ✅ Batch {batch_num} Success.")

        except Exception as e:
            # THIS IS THE CRITICAL FIX:
            # Instead of crashing the whole pipeline, we print the error and move to Batch 9
            print(f"  ❌ CRITICAL FAILURE IN BATCH {batch_num}. SKIPPING.")
            print(f"  Error details: {e}")
            # print(traceback.format_exc()) # Uncomment if you need deep debug
        
        finally:
            # --- PHASE D: CLEANUP ---
            # Ensure memory is freed even if the batch failed
            if 'batch_df' in locals(): del batch_df
            if 'dfs' in locals(): del dfs
            
            # STANDARD PYTHON CLEANUP
            gc.collect()
            
            # SYSTEM LEVEL CLEANUP (The Fix)
            trim_memory()

    print("--- Pipeline Run Complete (Check logs for skipped batches) ---")
    return pd.DataFrame()