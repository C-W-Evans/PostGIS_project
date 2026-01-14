from mage_ai.data_preparation.repo_manager import get_repo_path
from mage_ai.io.config import ConfigFileLoader
from pandas import DataFrame
import psycopg2
import os

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
    
    print(f"📦 Received {len(df)} stations to export.")

    db_kwargs = {
        'host': config['POSTGRES_HOST'],
        'port': config['POSTGRES_PORT'],
        'user': config['POSTGRES_USER'],
        'password': config['POSTGRES_PASSWORD'],
        'dbname': config['POSTGRES_DBNAME']
    }

    try:
        with psycopg2.connect(**db_kwargs) as conn:
            with conn.cursor() as cursor:
                # SQL Query
                insert_query = """
                INSERT INTO public.stations (station_id, name, latitude, longitude, geometry)
                VALUES (%s, %s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326))
                ON CONFLICT (station_id) DO NOTHING;
                """
                
                data_to_insert = []
                
                # --- THIS IS THE FIX ---
                # We use row.station_name because transform_stations renamed it.
                # If we use row.name, it crashes.
                for row in df.itertuples(index=False):
                    data_to_insert.append((
                        str(row.station_id), 
                        row.station_name,    # <--- MUST BE 'station_name'
                        row.latitude, 
                        row.longitude, 
                        row.longitude,       # For ST_MakePoint (x)
                        row.latitude         # For ST_MakePoint (y)
                    ))
                
                cursor.executemany(insert_query, data_to_insert)
                conn.commit()
                print(f"✅ COMMIT EXECUTED. Processed {len(data_to_insert)} rows.")
                
    except Exception as e:
        print(f"❌ DATABASE ERROR: {e}")
        # Print the first row's attributes to help debug if it fails again
        if not df.empty:
            print(f"DEBUG: First row columns available: {df.iloc[0].index.tolist()}")
        raise e