#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析$factor字段对量化研究的影响
"""

import pandas as pd
import numpy as np

def analyze_factor_impact():
    """分析$factor字段的影响"""
    print("=== $factor字段影响分析 ===\n")
    
    # 读取原始数据
    original_file = "/home/shenzi/RD-Agent/git_ignore_folder/factor_implementation_source_data/daily_pv.h5"
    original_df = pd.read_hdf(original_file, key="data")
    
    # 读取转换后数据
    converted_file = "/home/shenzi/RD-Agent/qlib_converted_daily_pv.h5"
    converted_df = pd.read_hdf(converted_file, key="data")
    
    print("1. 原始数据$factor字段统计:")
    print(f"   最小值: {original_df['$factor'].min():.6f}")
    print(f"   最大值: {original_df['$factor'].max():.6f}")
    print(f"   平均值: {original_df['$factor'].mean():.6f}")
    print(f"   中位数: {original_df['$factor'].median():.6f}")
    print(f"   标准差: {original_df['$factor'].std():.6f}")
    print(f"   非零值数量: {(original_df['$factor'] != 0).sum()}")
    print(f"   零值数量: {(original_df['$factor'] == 0).sum()}")
    
    print("\n2. 转换后数据$factor字段统计:")
    print(f"   最小值: {converted_df['$factor'].min():.6f}")
    print(f"   最大值: {converted_df['$factor'].max():.6f}")
    print(f"   平均值: {converted_df['$factor'].mean():.6f}")
    print(f"   中位数: {converted_df['$factor'].median():.6f}")
    print(f"   标准差: {converted_df['$factor'].std():.6f}")
    
    print("\n3. $factor字段变化分析:")
    print("   ❌ 原始数据: $factor包含真实的复权因子值")
    print("   ❌ 转换后数据: $factor全部设为1.0（默认值）")
    print("   ❌ 这意味着复权信息完全丢失！")
    
    print("\n4. 对量化研究的影响:")
    print("   🔴 价格数据可能不准确:")
    print("      - 原始数据中的价格可能已经过复权处理")
    print("      - 转换后数据中的价格是原始价格，未复权")
    print("      - 这会导致价格序列的不一致性")
    
    print("\n   🔴 因子计算可能错误:")
    print("      - 基于价格的因子（如收益率、动量等）会受影响")
    print("      - 技术指标计算可能不准确")
    print("      - 回测结果可能失真")
    
    print("\n   🔴 数据一致性问题:")
    print("      - 新旧数据之间的价格基准不同")
    print("      - 可能导致策略表现差异")
    print("      - 历史数据对比困难")
    
    print("\n5. 解决方案建议:")
    print("   ✅ 方案1: 使用adjclose字段作为复权价格")
    print("      - Qlib数据中的adjclose是复权收盘价")
    print("      - 可以替代$close字段")
    
    print("\n   ✅ 方案2: 重新计算复权因子")
    print("      - 基于adjclose和close计算复权因子")
    print("      - 公式: factor = adjclose / close")
    
    print("\n   ✅ 方案3: 统一使用复权价格")
    print("      - 将所有价格字段都转换为复权价格")
    print("      - 确保数据一致性")
    
    # 计算复权因子
    print("\n6. 复权因子计算示例:")
    sample_stock = 'sh600000'
    if sample_stock in converted_df.index.get_level_values(1):
        stock_data = converted_df.loc[converted_df.index.get_level_values(1) == sample_stock]
        if len(stock_data) > 0:
            # 假设adjclose字段存在，计算复权因子
            print(f"   股票: {sample_stock}")
            print(f"   数据点数量: {len(stock_data)}")
            print(f"   收盘价范围: {stock_data['$close'].min():.4f} - {stock_data['$close'].max():.4f}")
            print(f"   注意: 需要adjclose字段来计算真实的复权因子")
    
    print("\n⚠️  重要提醒:")
    print("   在修复$factor字段之前，请谨慎使用转换后的数据进行量化研究！")
    print("   建议先解决复权问题，确保数据质量。")

if __name__ == "__main__":
    analyze_factor_impact() 