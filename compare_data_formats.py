#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对比RD Agent和Qlib的数据格式
"""

import pandas as pd
import numpy as np
from pathlib import Path

def compare_data_formats():
    """对比两种数据格式"""
    print("=== RD Agent vs Qlib 数据格式对比 ===\n")
    
    # 1. RD Agent数据格式
    print("1. RD Agent数据格式 (HDF5):")
    print("-" * 50)
    
    rd_agent_file = "/home/shenzi/RD-Agent/git_ignore_folder/factor_implementation_source_data/daily_pv.h5"
    rd_df = pd.read_hdf(rd_agent_file, key="data")
    
    print(f"文件格式: HDF5 (.h5)")
    print(f"数据形状: {rd_df.shape}")
    print(f"列名: {list(rd_df.columns)}")
    print(f"数据类型: {rd_df.dtypes}")
    print(f"时间范围: {rd_df.index.get_level_values(0).min()} 到 {rd_df.index.get_level_values(0).max()}")
    print(f"股票数量: {rd_df.index.get_level_values(1).nunique()}")
    print(f"总数据点: {len(rd_df)}")
    print(f"索引结构: MultiIndex (datetime, instrument)")
    print(f"数据字段: {list(rd_df.columns)}")
    
    # 2. Qlib数据格式
    print("\n2. Qlib数据格式 (二进制):")
    print("-" * 50)
    
    qlib_dir = Path("/home/shenzi/.qlib/qlib_data/cn_data")
    
    # 读取交易日历
    calendar_file = qlib_dir / "calendars" / "day.txt"
    with open(calendar_file, 'r') as f:
        dates = [line.strip() for line in f.readlines() if line.strip()]
    
    # 读取股票列表
    instruments_file = qlib_dir / "instruments" / "all.txt"
    df_instruments = pd.read_csv(instruments_file, header=None)
    
    print(f"文件格式: 二进制 (.bin) + 文本文件")
    print(f"目录结构: {qlib_dir}")
    print(f"交易日历文件: {calendar_file}")
    print(f"股票列表文件: {instruments_file}")
    print(f"交易日数量: {len(dates)}")
    print(f"时间范围: {dates[0]} 到 {dates[-1]}")
    print(f"股票数量: {len(df_instruments)}")
    print(f"股票列表前5个: {df_instruments[0].head().tolist()}")
    
    # 检查一个股票的数据文件
    test_stock = "sh600000"
    test_stock_dir = qlib_dir / "features" / test_stock
    if test_stock_dir.exists():
        data_files = list(test_stock_dir.glob("*.bin"))
        print(f"数据文件示例 ({test_stock}): {[f.name for f in data_files]}")
        
        # 读取一个数据文件
        close_file = test_stock_dir / "close.day.bin"
        if close_file.exists():
            data = np.fromfile(close_file, dtype=np.float32)
            print(f"单个股票数据点数量: {len(data)}")
    
    # 3. 格式对比总结
    print("\n3. 格式对比总结:")
    print("-" * 50)
    print("RD Agent格式特点:")
    print("  ✓ 单一HDF5文件，包含所有数据")
    print("  ✓ MultiIndex结构 (datetime, instrument)")
    print("  ✓ 包含$factor字段")
    print("  ✓ 数据范围: 2008-2020")
    print("  ✓ 股票数量: 3875")
    print("  ✓ 总数据点: 7,584,444")
    
    print("\nQlib格式特点:")
    print("  ✓ 目录结构，每个股票单独目录")
    print("  ✓ 二进制文件存储，高性能")
    print("  ✓ 分离的日历和股票列表文件")
    print("  ✓ 数据范围: 1999-2025")
    print("  ✓ 股票数量: 5179")
    print("  ✓ 每个股票6329个交易日")
    
    print("\n主要差异:")
    print("  1. 存储格式: HDF5 vs 二进制文件")
    print("  2. 数据结构: 单一文件 vs 目录结构")
    print("  3. 时间范围: 2008-2020 vs 1999-2025")
    print("  4. 股票数量: 3875 vs 5179")
    print("  5. 数据字段: 包含$factor vs 标准OHLCV")
    print("  6. 索引结构: MultiIndex vs 文件系统索引")

if __name__ == "__main__":
    compare_data_formats() 