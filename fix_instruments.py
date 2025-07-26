#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复instruments文件格式
"""

import pandas as pd
from pathlib import Path

def fix_instruments_file():
    """修复instruments文件格式"""
    instruments_file = Path("/home/shenzi/.qlib/qlib_data/cn_data/instruments/all.txt")
    
    # 读取现有的股票列表
    with open(instruments_file, 'r') as f:
        symbols = [line.strip() for line in f.readlines() if line.strip()]
    
    # 创建正确格式的DataFrame
    # qlib期望的格式: symbol, start_date, end_date
    df = pd.DataFrame({
        'symbol': symbols,
        'start_date': '1999-12-07',  # 数据开始日期
        'end_date': '2025-07-15'     # 数据结束日期
    })
    
    # 保存为CSV格式
    df.to_csv(instruments_file, index=False, header=False)
    
    print(f"已修复instruments文件，包含 {len(symbols)} 个股票")
    print(f"格式: symbol, start_date, end_date")

if __name__ == "__main__":
    fix_instruments_file() 