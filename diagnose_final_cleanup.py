import pandas as pd
import os
import warnings

# Suppress specific pandas warnings for cleaner output
warnings.filterwarnings("ignore", category=pd.errors.PerformanceWarning)

ROOT_WORKSPACE_PATH = "git_ignore_folder/RD-Agent_workspace/"
TARGET_FILENAME = "result.h5"

print(f"[*] Starting FINAL diagnosis of '{TARGET_FILENAME}' in all subdirectories of '{ROOT_WORKSPACE_PATH}'")
print("[*] This script will identify files with wrong index levels OR any loading errors.\n")

corrupted_files_paths = []
checked_files_count = 0

if not os.path.isdir(ROOT_WORKSPACE_PATH):
    print(f"[!] Error: Root workspace directory not found at '{ROOT_WORKSPACE_PATH}'")
    exit()

for workspace_id in os.listdir(ROOT_WORKSPACE_PATH):
    workspace_path = os.path.join(ROOT_WORKSPACE_PATH, workspace_id)
    
    if os.path.isdir(workspace_path):
        target_file_path = os.path.join(workspace_path, TARGET_FILENAME)
        
        if os.path.exists(target_file_path):
            checked_files_count += 1
            is_corrupted = False
            try:
                # Attempt to load the file
                df = pd.read_hdf(target_file_path, key="data")
                # Check index levels ONLY if loading succeeds
                if df.index.nlevels != 2:
                    print(f"[!!!] CORRUPTION (Wrong Level): {target_file_path}")
                    print(f"    - Reason: Index levels = {df.index.nlevels} (Expected: 2)\n")
                    is_corrupted = True
            except Exception as e:
                # ANY exception during loading means the file is corrupt
                print(f"[!!!] CORRUPTION (Load Error): {target_file_path}")
                print(f"    - Reason: {type(e).__name__} - {e}\n")
                is_corrupted = True
            
            if is_corrupted:
                corrupted_files_paths.append(target_file_path)

print("\n--- FINAL Diagnosis Summary ---")
print(f"Checked {checked_files_count} '{TARGET_FILENAME}' files in total.")
if corrupted_files_paths:
    print(f"Found {len(corrupted_files_paths)} corrupted file(s) that must be deleted:")
    for f_path in corrupted_files_paths:
        print(f"  - {f_path}")
else:
    print("✅ SUCCESS: All checked files are clean and have the correct 2-level index. No corruption found.") 