from mage_ai.data_preparation.repo_manager import get_repo_path
from mage_ai.io.config import ConfigFileLoader
from pandas import DataFrame
import psycopg2
import psycopg2.errors  # <--- NEW IMPORT
import os
import time             # <--- NEW IMPORT

if 'data_exporter' not in globals():
    from mage_ai.data_preparation.decorators import data_exporter

@data_exporter
def export_stations_atomic(df: DataFrame, **kwargs):
    if df is None or df.empty: 
        print("⚠️ DataFrame is empty. Nothing to export.")
        return
    
    config_path = os.path.join(get_repo_path(), 'io_config.yaml')
    config_profile = 'default'
    config = ConfigFileLoader(config_path, config_profile).config
    
    db_kwargs = {
        'host': config['POSTGRES_HOST'],
        'port': config['POSTGRES_PORT'],
        'user': config['POSTGRES_USER'],
        'password': config['POSTGRES_PASSWORD'],
        'dbname': config['POSTGRES_DBNAME']
    }

    # --- RETRY LOGIC STARTS HERE ---
    max_retries = 5
    retry_delay = 2  # seconds

    for attempt in range(max_retries):
        try:
            with psycopg2.connect(**db_kwargs) as conn:
                with conn.cursor() as cursor:
                    insert_query = """
                    INSERT INTO public.stations (station_id, name, latitude, longitude, geometry)
                    VALUES (%s, %s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326))
                    ON CONFLICT (station_id) DO NOTHING;
                    """
                    
                    data_to_insert = []
                    for row in df.itertuples(index=False):
                        data_to_insert.append((
                            str(row.station_id), 
                            row.station_name,
                            row.latitude, 
                            row.longitude, 
                            row.longitude,
                            row.latitude
                        ))
                    
                    cursor.executemany(insert_query, data_to_insert)
                    conn.commit()
                    print(f"✅ COMMIT EXECUTED. Processed {len(data_to_insert)} rows.")
                    
                    # If we succeed, BREAK the loop so we don't retry
                    break 

        except psycopg2.errors.DeadlockDetected:
            # specifically catch Deadlocks
            print(f"⚠️ Deadlock detected on attempt {attempt + 1}. Retrying in {retry_delay}s...")
            time.sleep(retry_delay)
            continue  # Go to next attempt
            
        except Exception as e:
            # Catch other real errors (like syntax, connection lost) and fail
            print(f"❌ DATABASE ERROR: {e}")
            raise e
    else:
        # This runs if the loop finishes all retries without breaking
        raise Exception(f"❌ Failed to export stations after {max_retries} attempts due to deadlocks.")