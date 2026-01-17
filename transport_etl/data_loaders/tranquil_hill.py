if 'data_loader' not in globals():
    from mage_ai.data_preparation.decorators import data_loader
import os
from mage_ai.settings.repo import get_repo_path

@data_loader
def load_data(*args, **kwargs):
    project_root = get_repo_path()
    old_folder = os.path.join(project_root, 'data', 'old')
    new_folder = os.path.join(project_root, 'data', 'new')
    
    all_files = []

    # 1. Find Old Files (.zip)
    if os.path.exists(old_folder):
        print(f"Scanning: {old_folder}")
        files = [f for f in os.listdir(old_folder) if f.endswith('.zip')]
        for f in files:
            all_files.append({'type': 'old', 'path': os.path.join(old_folder, f)})

    # 2. Find New Files (.csv)
    if os.path.exists(new_folder):
        print(f"Scanning: {new_folder}")
        files = [f for f in os.listdir(new_folder) if f.endswith('.csv')]
        for f in files:
            all_files.append({'type': 'new', 'path': os.path.join(new_folder, f)})


    all_files = sorted(all_files, key=lambda x: x['path'])


    BATCH_SIZE = 1
    batches = []
    
    for i in range(0, len(all_files), BATCH_SIZE):
        batch_chunk = all_files[i : i + BATCH_SIZE]
        # WRAPPER TRICK: Wrap the list in a dict key 'batch_files'
        # This prevents Mage from flattening the list!
        batches.append({'batch_files': batch_chunk})

    print(f"DEBUG: Created {len(batches)} batches.") 
    print(batches)
    # Now returns: [{'batch_files': [f1, f2, f3, f4, f5]}, {'batch_files': [f6...]} ...]
    return batches