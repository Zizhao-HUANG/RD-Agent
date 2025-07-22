import pandas as pd
import os
import warnings

# Suppress specific pandas warnings for cleaner output
warnings.filterwarnings("ignore", category=pd.errors.PerformanceWarning)

ROOT_WORKSPACE_PATH = "git_ignore_folder/RD-Agent_workspace/"
TARGET_FILENAME = "result.h5"

print(f"[*] Starting comprehensive diagnosis of '{TARGET_FILENAME}' in all subdirectories of '{ROOT_WORKSPACE_PATH}'\n")

corrupted_files_paths = []
checked_files_count = 0

if not os.path.isdir(ROOT_WORKSPACE_PATH):
    print(f"[!] Error: Root workspace directory not found at '{ROOT_WORKSPACE_PATH}'")
    exit()

# Iterate through all items in the root workspace directory
for workspace_id in os.listdir(ROOT_WORKSPACE_PATH):
    workspace_path = os.path.join(ROOT_WORKSPACE_PATH, workspace_id)
    
    # Ensure it's a directory
    if os.path.isdir(workspace_path):
        target_file_path = os.path.join(workspace_path, TARGET_FILENAME)
        
        if os.path.exists(target_file_path):
            checked_files_count += 1
            try:
                df = pd.read_hdf(target_file_path, key="data")
                if df.index.nlevels != 2:
                    print(f"[!!!] CORRUPTED FILE FOUND: {target_file_path}")
                    print(f"    - Index levels: {df.index.nlevels} (Expected: 2)")
                    print(f"    - Index names: {df.index.names}\n")
                    corrupted_files_paths.append(target_file_path)
                else:
                    # This file is OK
                    pass
            except Exception as e:
                print(f"[!] Error reading or processing {target_file_path}: {e}\n")

print("\n--- Diagnosis Summary ---")
print(f"Checked {checked_files_count} '{TARGET_FILENAME}' files in total.")
if corrupted_files_paths:
    print(f"Found {len(corrupted_files_paths)} file(s) with incorrect index levels:")
    for f_path in corrupted_files_paths:
        print(f"  - {f_path}")
else:
    print("All checked files have the correct 2-level index. No corruption found.") 