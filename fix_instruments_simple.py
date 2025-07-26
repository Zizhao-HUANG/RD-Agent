#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复instruments文件格式
"""

import pandas as pd

def fix_instruments():
    """修复instruments文件格式"""
    print("修复instruments文件格式...")
    
    # 读取现有的股票列表
    instruments_file = "/home/shenzi/.qlib/qlib_data/cn_data/instruments/all.txt"
    
    try:
        # 读取文件
        with open(instruments_file, 'r') as f:
            symbols = [line.strip() for line in f.readlines() if line.strip()]
        
        print(f"读取到 {len(symbols)} 个股票代码")
        
        # 创建正确格式的DataFrame
        df = pd.DataFrame({
            'symbol': symbols,
            'start_date': '1999-12-07',
            'end_date': '2025-07-15'
        })
        
        # 保存为CSV格式
        df.to_csv(instruments_file, index=False, header=False)
        
        print(f"已修复instruments文件，包含 {len(symbols)} 个股票")
        print("格式: symbol, start_date, end_date")
        
        # 验证修复结果
        df_check = pd.read_csv(instruments_file, header=None)
        print(f"验证: 列数={len(df_check.columns)}, 行数={len(df_check)}")
        
        return True
        
    except Exception as e:
        print(f"修复失败: {e}")
        return False

if __name__ == "__main__":
    success = fix_instruments()
    if success:
        print("✅ instruments文件修复成功！")
    else:
        print("❌ instruments文件修复失败！") 