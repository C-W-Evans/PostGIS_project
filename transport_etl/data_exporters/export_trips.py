from mage_ai.settings.repo import get_repo_path
from mage_ai.io.config import ConfigFileLoader
from pandas import DataFrame
from os import path
import psycopg2
import psycopg2.extras

if 'data_exporter' not in globals():
    from mage_ai.data_preparation.decorators import data_exporter

@data_exporter
def export_trips_atomic(df: DataFrame, **kwargs):
    # 1. Guard against empty batches
    if df is None or df.empty:
        print("Trip batch is empty. Skipping.")
        return

    config_path = path.join(get_repo_path(), 'io_config.yaml')
    config_profile = 'default'
    config = ConfigFileLoader(config_path, config_profile).config

    # --- UPDATE STARTS HERE ---
    # We must map the Mage configuration keys to what psycopg2 expects
    db_kwargs = {
        'host': config['POSTGRES_HOST'],
        'port': config['POSTGRES_PORT'],
        'user': config['POSTGRES_USER'],
        'password': config['POSTGRES_PASSWORD'],
        'dbname': config['POSTGRES_DBNAME']
    }

    # 2. Connect using the MAPPED arguments (not raw config)
    with psycopg2.connect(**db_kwargs) as conn:
    # --- UPDATE ENDS HERE ---
    
        with conn.cursor() as cursor:
            
            # 3. Align DataFrame Columns
            cols_to_export = [
                'started_at', 
                'ended_at', 
                'start_station_id', 
                'end_station_id', 
                'duration_minutes'
            ]
            
            df_final = df[cols_to_export]

            # 4. Prepare Data
            rows_to_insert = list(df_final.itertuples(index=False, name=None))
            
            # 5. Fast Insert
            insert_query = """
            INSERT INTO public.trips 
            (started_at, ended_at, start_station_id, end_station_id, duration_minutes)
            VALUES %s
            """
            
            # 6. Execute Values
            psycopg2.extras.execute_values(
                cursor, 
                insert_query, 
                rows_to_insert,
                page_size=1000
            )
            
            # Context manager auto-commits here if no error occurs
            print(f"Successfully inserted {len(rows_to_insert)} trip rows.")