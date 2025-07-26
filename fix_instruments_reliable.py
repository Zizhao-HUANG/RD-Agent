#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
可靠地修复instruments文件格式
"""

import os
import re

def fix_instruments_reliable():
    """可靠地修复instruments文件格式"""
    print("开始修复instruments文件格式...")
    
    instruments_file = "/home/shenzi/.qlib/qlib_data/cn_data/instruments/all.txt"
    
    try:
        # 备份原文件
        backup_file = instruments_file + ".backup"
        if not os.path.exists(backup_file):
            os.system(f"cp {instruments_file} {backup_file}")
            print(f"已备份原文件到: {backup_file}")
        
        # 读取文件并提取股票代码
        with open(instruments_file, 'r') as f:
            content = f.read()
        
        # 使用正则表达式提取股票代码
        # 匹配类似 sh600000, sh600004 等格式
        pattern = r'[a-z]{2}\d{6}'
        symbols = list(set(re.findall(pattern, content)))
        symbols.sort()
        
        print(f"提取到 {len(symbols)} 个唯一股票代码")
        
        # 创建正确格式的内容
        new_content = ""
        for symbol in symbols:
            new_content += f"{symbol},1999-12-07,2025-07-15\n"
        
        # 写入新文件
        with open(instruments_file, 'w') as f:
            f.write(new_content)
        
        print(f"已修复instruments文件，包含 {len(symbols)} 个股票")
        print("格式: symbol, start_date, end_date")
        
        # 验证修复结果
        with open(instruments_file, 'r') as f:
            lines = f.readlines()
        
        print(f"验证: 文件行数={len(lines)}")
        print("前5行内容:")
        for i, line in enumerate(lines[:5]):
            print(f"  {i+1}: {line.strip()}")
        
        return True
        
    except Exception as e:
        print(f"修复失败: {e}")
        return False

if __name__ == "__main__":
    success = fix_instruments_reliable()
    if success:
        print("✅ instruments文件修复成功！")
    else:
        print("❌ instruments文件修复失败！") 