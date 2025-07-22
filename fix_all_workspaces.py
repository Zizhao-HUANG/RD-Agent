import pandas as pd
import os

# --- [重要] 将 diagnose_all_workspaces.py 发现的损坏文件完整路径填入此列表 ---
FILES_TO_FIX = [
    "git_ignore_folder/RD-Agent_workspace/2ff6a0e566b64b0e9b9af418de6eacef/result.h5",
    "git_ignore_folder/RD-Agent_workspace/3a22cad2ea654c87bf86c117b53abb7a/result.h5",
    "git_ignore_folder/RD-Agent_workspace/ea2df69abb5546849cb5e378fa3d5645/result.h5",
    "git_ignore_folder/RD-Agent_workspace/fe10e88769d24975ba8fde927ef7d54a/result.h5"
    # 如有更多，继续补充
]

print("[*] Starting index repair process...")

if not FILES_TO_FIX:
    print("[!] No file paths specified in FILES_TO_FIX list. Exiting.")
    exit()

for file_path in FILES_TO_FIX:
    if not os.path.exists(file_path):
        print(f"\n[!] File not found: {file_path}. Skipping.")
        continue

    print(f"\n--- Processing: {file_path} ---")
    try:
        # 读取损坏的文件
        df_original = pd.read_hdf(file_path, key="data")
        print(f"    - Before: Index levels={df_original.index.nlevels}, Names={df_original.index.names}")

        # 修复索引：重置索引，然后重新设置为标准的 ('datetime', 'instrument')
        df_fixed = df_original.reset_index()

        # 检查必要的列是否存在
        if 'datetime' not in df_fixed.columns or 'instrument' not in df_fixed.columns:
             print(f"    [!] FATAL ERROR: 'datetime' or 'instrument' column missing after reset_index(). Cannot fix this file automatically.")
             continue

        df_fixed = df_fixed.set_index(['datetime', 'instrument'])
        df_fixed = df_fixed.sort_index()

        print(f"    - After:  Index levels={df_fixed.index.nlevels}, Names={df_fixed.index.names}")

        # 覆盖保存修复后的文件
        df_fixed.to_hdf(file_path, key="data", mode="w", format="table")
        print(f"    - [SUCCESS] File has been repaired and overwritten.")

    except Exception as e:
        print(f"    - [FAILURE] An error occurred while fixing {file_path}: {e}")

print("\n[*] Repair process finished.") 