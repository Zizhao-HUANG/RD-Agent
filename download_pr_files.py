#!/usr/bin/env python3
"""
下载PR中的文件并覆盖本地文件
"""

import requests
import sys
import os

def download_file_from_pr(owner, repo, pr_number, file_path, branch_name):
    """从PR分支下载文件"""
    url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch_name}/{file_path}"
    print(f"正在下载: {url}")
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # 写入文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        print(f"✅ 成功覆盖文件: {file_path}")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 下载失败: {e}")
        return False

def main():
    # PR信息
    owner = "Zizhao-HUANG"
    repo = "RD-Agent"
    pr_number = 4
    branch_name = "codex/fix-data-passing-and-feedback-generation-in-rd-agent"
    
    # 需要下载的文件列表
    files_to_download = [
        "rdagent/core/experiment.py",
        "rdagent/components/workflow/rd_loop.py", 
        "rdagent/scenarios/qlib/developer/feedback.py"
    ]
    
    print(f"正在从PR #{pr_number}下载文件...")
    print(f"分支: {branch_name}")
    print()
    
    success_count = 0
    for file_path in files_to_download:
        if download_file_from_pr(owner, repo, pr_number, file_path, branch_name):
            success_count += 1
        print()
    
    print(f"完成! 成功下载了 {success_count}/{len(files_to_download)} 个文件")

if __name__ == "__main__":
    main() 