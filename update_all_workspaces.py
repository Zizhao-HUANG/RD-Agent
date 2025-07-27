#!/usr/bin/env python3

import os
import shutil
from pathlib import Path

def update_all_workspaces():
    """更新所有工作区目录中的daily_pv.h5文件"""
    
    # 源文件路径
    source_file = "./git_ignore_folder/factor_implementation_source_data/daily_pv.h5"
    source_file_debug = "./git_ignore_folder/factor_implementation_source_data_debug/daily_pv.h5"
    
    # 检查源文件是否存在
    if not os.path.exists(source_file):
        print(f"错误：源文件不存在: {source_file}")
        return
    
    if not os.path.exists(source_file_debug):
        print(f"错误：debug源文件不存在: {source_file_debug}")
        return
    
    # 工作区根目录
    workspace_root = "./git_ignore_folder/RD-Agent_workspace"
    
    # 统计信息
    total_dirs = 0
    updated_files = 0
    created_files = 0
    
    print("开始更新所有工作区目录中的daily_pv.h5文件...")
    
    # 遍历所有工作区目录
    for root, dirs, files in os.walk(workspace_root):
        # 只处理直接子目录（避免处理子目录的子目录）
        if root == workspace_root:
            for dir_name in dirs:
                workspace_dir = os.path.join(root, dir_name)
                total_dirs += 1
                
                # 检查是否需要daily_pv.h5文件
                target_file = os.path.join(workspace_dir, "daily_pv.h5")
                
                # 如果目录中有factor.py文件，说明这是一个需要数据的工作区
                factor_file = os.path.join(workspace_dir, "factor.py")
                if os.path.exists(factor_file):
                    try:
                        # 复制文件
                        shutil.copy2(source_file, target_file)
                        updated_files += 1
                        if total_dirs % 100 == 0:
                            print(f"已处理 {total_dirs} 个目录，更新了 {updated_files} 个文件...")
                    except Exception as e:
                        print(f"更新 {workspace_dir} 时出错: {e}")
    
    print(f"\n更新完成！")
    print(f"总目录数: {total_dirs}")
    print(f"更新的文件数: {updated_files}")
    
    # 同时更新模板目录中的文件
    template_dirs = [
        "./rdagent/scenarios/qlib/experiment/factor_data_template",
        "./git_ignore_folder/factor_implementation_source_data",
        "./git_ignore_folder/factor_implementation_source_data_debug"
    ]
    
    print("\n更新模板目录...")
    for template_dir in template_dirs:
        if os.path.exists(template_dir):
            target_file = os.path.join(template_dir, "daily_pv.h5")
            try:
                if "debug" in template_dir:
                    shutil.copy2(source_file_debug, target_file)
                else:
                    shutil.copy2(source_file, target_file)
                print(f"已更新: {template_dir}")
            except Exception as e:
                print(f"更新 {template_dir} 时出错: {e}")

if __name__ == "__main__":
    update_all_workspaces() 