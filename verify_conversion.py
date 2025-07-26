#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证Qlib到RD Agent格式转换结果
"""

import pandas as pd
import numpy as np

def verify_conversion():
    """验证转换结果"""
    print("=== 验证转换结果 ===\n")
    
    # 读取转换后的数据
    converted_file = "/home/shenzi/RD-Agent/qlib_converted_daily_pv.h5"
    df = pd.read_hdf(converted_file, key='data')
    
    print("1. 基本统计信息:")
    print(f"   数据形状: {df.shape}")
    print(f"   列名: {list(df.columns)}")
    print(f"   时间范围: {df.index.get_level_values(0).min()} 到 {df.index.get_level_values(0).max()}")
    print(f"   股票数量: {df.index.get_level_values(1).nunique()}")
    print(f"   总数据点: {len(df)}")
    
    print("\n2. 数据质量检查:")
    print(f"   缺失值数量: {df.isnull().sum().sum()}")
    print(f"   无穷值数量: {np.isinf(df.select_dtypes(include=[np.number])).sum().sum()}")
    
    print("\n3. 数据范围检查:")
    for col in df.columns:
        if col != '$factor':  # 跳过因子列
            print(f"   {col}: {df[col].min():.4f} - {df[col].max():.4f}")
    
    print("\n4. 前5行数据:")
    print(df.head())
    
    print("\n5. 索引结构:")
    print(f"   索引名称: {df.index.names}")
    print(f"   索引级别数: {df.index.nlevels}")
    
    # 检查特定股票的数据
    print("\n6. 特定股票数据检查 (sh600000):")
    stock_data = df.loc[df.index.get_level_values(1) == 'sh600000']
    if len(stock_data) > 0:
        print(f"   sh600000数据点数量: {len(stock_data)}")
        print(f"   时间范围: {stock_data.index.get_level_values(0).min()} 到 {stock_data.index.get_level_values(0).max()}")
        print(f"   收盘价范围: {stock_data['$close'].min():.4f} - {stock_data['$close'].max():.4f}")
    else:
        print("   未找到sh600000的数据")
    
    print("\n✅ 验证完成！")

if __name__ == "__main__":
    verify_conversion() 