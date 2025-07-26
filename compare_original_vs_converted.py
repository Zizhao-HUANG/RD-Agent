#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对比原始RD Agent数据和转换后的数据
"""

import pandas as pd
import numpy as np

def compare_data():
    """对比原始数据和转换后的数据"""
    print("=== 原始RD Agent数据 vs 转换后数据对比 ===\n")
    
    # 读取原始RD Agent数据
    original_file = "/home/shenzi/RD-Agent/git_ignore_folder/factor_implementation_source_data/daily_pv.h5"
    original_df = pd.read_hdf(original_file, key="data")
    
    # 读取转换后的数据
    converted_file = "/home/shenzi/RD-Agent/qlib_converted_daily_pv.h5"
    converted_df = pd.read_hdf(converted_file, key="data")
    
    print("1. 原始RD Agent数据:")
    print(f"   数据形状: {original_df.shape}")
    print(f"   时间范围: {original_df.index.get_level_values(0).min()} 到 {original_df.index.get_level_values(0).max()}")
    print(f"   股票数量: {original_df.index.get_level_values(1).nunique()}")
    print(f"   总数据点: {len(original_df)}")
    print(f"   列名: {list(original_df.columns)}")
    
    print("\n2. 转换后的数据:")
    print(f"   数据形状: {converted_df.shape}")
    print(f"   时间范围: {converted_df.index.get_level_values(0).min()} 到 {converted_df.index.get_level_values(0).max()}")
    print(f"   股票数量: {converted_df.index.get_level_values(1).nunique()}")
    print(f"   总数据点: {len(converted_df)}")
    print(f"   列名: {list(converted_df.columns)}")
    
    print("\n3. 数据对比:")
    print(f"   数据点增长: {len(converted_df) - len(original_df):,} ({((len(converted_df) - len(original_df)) / len(original_df) * 100):.1f}%)")
    print(f"   股票数量增长: {converted_df.index.get_level_values(1).nunique() - original_df.index.get_level_values(1).nunique()} ({((converted_df.index.get_level_values(1).nunique() - original_df.index.get_level_values(1).nunique()) / original_df.index.get_level_values(1).nunique() * 100):.1f}%)")
    
    # 计算时间范围扩展
    original_start = original_df.index.get_level_values(0).min()
    original_end = original_df.index.get_level_values(0).max()
    converted_start = converted_df.index.get_level_values(0).min()
    converted_end = converted_df.index.get_level_values(0).max()
    
    print(f"   时间范围扩展: {original_start} - {original_end} → {converted_start} - {converted_end}")
    
    # 检查共同股票的数据
    print("\n4. 共同股票数据对比 (sh600000):")
    if 'sh600000' in original_df.index.get_level_values(1):
        original_stock = original_df.loc[original_df.index.get_level_values(1) == 'sh600000']
        print(f"   原始数据sh600000: {len(original_stock)} 个数据点")
        print(f"   原始数据时间范围: {original_stock.index.get_level_values(0).min()} 到 {original_stock.index.get_level_values(0).max()}")
    
    if 'sh600000' in converted_df.index.get_level_values(1):
        converted_stock = converted_df.loc[converted_df.index.get_level_values(1) == 'sh600000']
        print(f"   转换后数据sh600000: {len(converted_stock)} 个数据点")
        print(f"   转换后数据时间范围: {converted_stock.index.get_level_values(0).min()} 到 {converted_stock.index.get_level_values(0).max()}")
    
    print("\n5. 数据质量对比:")
    print(f"   原始数据缺失值: {original_df.isnull().sum().sum()}")
    print(f"   转换后数据缺失值: {converted_df.isnull().sum().sum()}")
    print(f"   原始数据无穷值: {np.isinf(original_df.select_dtypes(include=[np.number])).sum().sum()}")
    print(f"   转换后数据无穷值: {np.isinf(converted_df.select_dtypes(include=[np.number])).sum().sum()}")
    
    print("\n6. 文件大小对比:")
    import os
    original_size = os.path.getsize(original_file) / (1024 * 1024)  # MB
    converted_size = os.path.getsize(converted_file) / (1024 * 1024)  # MB
    print(f"   原始文件大小: {original_size:.1f} MB")
    print(f"   转换后文件大小: {converted_size:.1f} MB")
    print(f"   文件大小变化: {converted_size - original_size:.1f} MB ({((converted_size - original_size) / original_size * 100):.1f}%)")
    
    print("\n✅ 对比完成！")

if __name__ == "__main__":
    compare_data() 