#!/usr/bin/env python3

import os
import shutil
from pathlib import Path

def replace_daily_pv_all_files():
    """替换所有daily_pv_all.h5文件的内容为daily_pv.h5的内容"""
    
    # 源文件路径（最新的daily_pv.h5）
    source_file = "./git_ignore_folder/factor_implementation_source_data/daily_pv.h5"
    
    # 检查源文件是否存在
    if not os.path.exists(source_file):
        print(f"错误：源文件不存在: {source_file}")
        return
    
    # 找到所有daily_pv_all.h5文件
    daily_pv_all_files = [
        "./rdagent/scenarios/qlib/experiment/factor_data_template/daily_pv_all.h5",
        "./daily_pv_all.h5"
    ]
    
    print("开始替换daily_pv_all.h5文件的内容...")
    
    for target_file in daily_pv_all_files:
        if os.path.exists(target_file):
            try:
                # 备份原文件
                backup_file = target_file + ".backup"
                shutil.copy2(target_file, backup_file)
                print(f"已备份: {target_file} -> {backup_file}")
                
                # 替换文件内容
                shutil.copy2(source_file, target_file)
                print(f"已替换: {target_file}")
                
                # 验证文件大小
                source_size = os.path.getsize(source_file)
                target_size = os.path.getsize(target_file)
                print(f"  源文件大小: {source_size:,} bytes")
                print(f"  目标文件大小: {target_size:,} bytes")
                
                if source_size == target_size:
                    print(f"  ✅ 替换成功，文件大小一致")
                else:
                    print(f"  ❌ 替换失败，文件大小不一致")
                    
            except Exception as e:
                print(f"替换 {target_file} 时出错: {e}")
        else:
            print(f"文件不存在，跳过: {target_file}")
    
    print("\n替换完成！")

if __name__ == "__main__":
    replace_daily_pv_all_files() 