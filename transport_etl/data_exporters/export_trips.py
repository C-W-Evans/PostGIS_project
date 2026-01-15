if 'data_exporter' not in globals():
    from mage_ai.data_preparation.decorators import data_exporter
from mage_ai.settings.repo import get_repo_path
from mage_ai.io.config import ConfigFileLoader
from pandas import DataFrame
from os import path
import psycopg2
import psycopg2.extras
import time

@data_exporter
def export_trips_atomic(df: DataFrame, **kwargs):
    # 1. Guard against empty batches
    if df is None or df.empty:
        print("Trip batch is empty. Skipping.")
        return

    config_path = path.join(get_repo_path(), 'io_config.yaml')
    config_profile = 'default'
    config = ConfigFileLoader(config_path, config_profile).config

    db_kwargs = {
        'host': config['POSTGRES_HOST'],
        'port': config['POSTGRES_PORT'],
        'user': config['POSTGRES_USER'],
        'password': config['POSTGRES_PASSWORD'],
        'dbname': config['POSTGRES_DBNAME']
    }

    # 2. Retry Logic (Handles intermittent connection failures)
    max_retries = 3
    for attempt in range(max_retries):
        try:
            with psycopg2.connect(**db_kwargs) as conn:
                with conn.cursor() as cursor:
                    # 3. Align Columns
                    cols_to_export = [
                        'started_at', 'ended_at', 
                        'start_station_id', 'end_station_id', 
                        'duration_minutes'
                    ]
                    # Ensure columns exist to avoid KeyError
                    missing_cols = [c for c in cols_to_export if c not in df.columns]
                    if missing_cols:
                        raise ValueError(f"Missing columns in dataframe: {missing_cols}")

                    df_final = df[cols_to_export]
                    rows_to_insert = list(df_final.itertuples(index=False, name=None))
                    
                    insert_query = """
                    INSERT INTO public.trips 
                    (started_at, ended_at, start_station_id, end_station_id, duration_minutes)
                    VALUES %s
                    """
                    
                    psycopg2.extras.execute_values(
                        cursor, insert_query, rows_to_insert, page_size=1000
                    )
                    
                    conn.commit()  # <--- CRITICAL COMMIT
                    print(f"✅ Batch Success: Inserted {len(rows_to_insert)} rows.")
                    return # Exit function on success

        except (psycopg2.OperationalError, psycopg2.errors.DeadlockDetected) as e:
            print(f"⚠️ Connection error on attempt {attempt+1}: {e}")
            time.sleep(2) # Wait before retrying
        except Exception as e:
            print(f"❌ FATAL ERROR: {e}")
            raise e # Crash the pipeline for non-connection errors (like bad data)
            
    raise Exception("Failed to export batch after retries.")