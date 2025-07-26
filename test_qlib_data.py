#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试qlib数据加载
"""

import numpy as np
import pandas as pd
from pathlib import Path

def test_qlib_data():
    """测试qlib数据"""
    print("=== 测试qlib数据 ===")
    
    # 1. 检查目录结构
    qlib_dir = Path("/home/shenzi/.qlib/qlib_data/cn_data")
    print(f"qlib数据目录: {qlib_dir}")
    print(f"目录存在: {qlib_dir.exists()}")
    
    # 2. 检查features目录
    features_dir = qlib_dir / "features"
    print(f"features目录: {features_dir}")
    print(f"features目录存在: {features_dir.exists()}")
    
    # 3. 统计股票数量
    stock_dirs = list(features_dir.glob("*"))
    print(f"股票数量: {len(stock_dirs)}")
    
    # 4. 检查一个具体股票的数据
    test_stock = "sh600000"
    test_stock_dir = features_dir / test_stock
    print(f"\n测试股票: {test_stock}")
    print(f"股票目录存在: {test_stock_dir.exists()}")
    
    if test_stock_dir.exists():
        # 检查数据文件
        data_files = list(test_stock_dir.glob("*.bin"))
        print(f"数据文件数量: {len(data_files)}")
        for file in data_files:
            print(f"  - {file.name}")
        
        # 读取收盘价数据
        close_file = test_stock_dir / "close.day.bin"
        if close_file.exists():
            data = np.fromfile(close_file, dtype=np.float32)
            print(f"收盘价数据点数量: {len(data)}")
            print(f"数据范围: {data.min():.2f} - {data.max():.2f}")
            print(f"非零数据点: {np.count_nonzero(data)}")
    
    # 5. 检查日历文件
    calendar_file = qlib_dir / "calendars" / "day.txt"
    print(f"\n交易日历文件: {calendar_file}")
    print(f"日历文件存在: {calendar_file.exists()}")
    
    if calendar_file.exists():
        with open(calendar_file, 'r') as f:
            dates = [line.strip() for line in f.readlines() if line.strip()]
        print(f"交易日数量: {len(dates)}")
        print(f"开始日期: {dates[0]}")
        print(f"结束日期: {dates[-1]}")
    
    # 6. 检查instruments文件
    instruments_file = qlib_dir / "instruments" / "all.txt"
    print(f"\n股票列表文件: {instruments_file}")
    print(f"股票列表文件存在: {instruments_file.exists()}")
    
    if instruments_file.exists():
        df = pd.read_csv(instruments_file, header=None)
        print(f"股票列表列数: {len(df.columns)}")
        print(f"股票列表行数: {len(df)}")
        print(f"前5个股票: {df[0].head().tolist()}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_qlib_data() 