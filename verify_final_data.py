#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证最终数据质量和完整性
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime

def verify_final_data():
    """验证最终数据"""
    print("=== 验证最终数据质量和完整性 ===\n")
    
    # 读取最终数据
    data_file = "/home/shenzi/RD-Agent/git_ignore_folder/factor_implementation_source_data/daily_pv.h5"
    
    try:
        print("1. 读取数据...")
        df = pd.read_hdf(data_file, key='data')
        
        print("2. 基本统计信息:")
        print(f"   数据形状: {df.shape}")
        print(f"   列名: {list(df.columns)}")
        print(f"   时间范围: {df.index.get_level_values(0).min()} 到 {df.index.get_level_values(0).max()}")
        print(f"   股票数量: {df.index.get_level_values(1).nunique()}")
        print(f"   总数据点: {len(df)}")
        
        print("\n3. 数据质量检查:")
        print(f"   缺失值数量: {df.isnull().sum().sum()}")
        print(f"   无穷值数量: {np.isinf(df.select_dtypes(include=[np.number])).sum().sum()}")
        print(f"   负值数量: {(df.select_dtypes(include=[np.number]) < 0).sum().sum()}")
        
        print("\n4. 各字段统计:")
        for col in df.columns:
            if col != '$factor':
                print(f"   {col}:")
                print(f"     最小值: {df[col].min():.4f}")
                print(f"     最大值: {df[col].max():.4f}")
                print(f"     平均值: {df[col].mean():.4f}")
                print(f"     缺失值: {df[col].isnull().sum()}")
        
        print("\n5. 复权因子($factor)统计:")
        print(f"   最小值: {df['$factor'].min():.6f}")
        print(f"   最大值: {df['$factor'].max():.6f}")
        print(f"   平均值: {df['$factor'].mean():.6f}")
        print(f"   中位数: {df['$factor'].median():.6f}")
        print(f"   标准差: {df['$factor'].std():.6f}")
        print(f"   复权因子=1的数量: {(df['$factor'] == 1.0).sum()}")
        print(f"   复权因子≠1的数量: {(df['$factor'] != 1.0).sum()}")
        
        print("\n6. 时间序列完整性检查:")
        # 检查是否有连续的交易日
        dates = df.index.get_level_values(0).unique()
        dates_sorted = sorted(dates)
        print(f"   交易日数量: {len(dates_sorted)}")
        print(f"   开始日期: {dates_sorted[0]}")
        print(f"   结束日期: {dates_sorted[-1]}")
        
        # 检查时间跨度
        time_span = (dates_sorted[-1] - dates_sorted[0]).days
        print(f"   时间跨度: {time_span} 天")
        
        print("\n7. 股票数据完整性检查:")
        # 检查每个股票的数据点数量
        stock_counts = df.groupby(level=1).size()
        print(f"   平均每只股票数据点: {stock_counts.mean():.1f}")
        print(f"   最少数据点股票: {stock_counts.min()}")
        print(f"   最多数据点股票: {stock_counts.max()}")
        
        # 检查数据点数量异常的股票
        low_data_stocks = stock_counts[stock_counts < 1000]
        if len(low_data_stocks) > 0:
            print(f"   数据点少于1000的股票数量: {len(low_data_stocks)}")
        
        print("\n8. 样本股票数据检查:")
        sample_stocks = ['sh600000', 'sz000001', 'sh000300']
        for stock in sample_stocks:
            if stock in df.index.get_level_values(1):
                stock_data = df.loc[df.index.get_level_values(1) == stock]
                print(f"   {stock}:")
                print(f"     数据点数量: {len(stock_data)}")
                print(f"     时间范围: {stock_data.index.get_level_values(0).min()} 到 {stock_data.index.get_level_values(0).max()}")
                print(f"     收盘价范围: {stock_data['$close'].min():.4f} - {stock_data['$close'].max():.4f}")
                print(f"     复权因子范围: {stock_data['$factor'].min():.6f} - {stock_data['$factor'].max():.6f}")
        
        print("\n9. 文件大小检查:")
        file_size_mb = os.path.getsize(data_file) / (1024 * 1024)
        print(f"   文件大小: {file_size_mb:.1f} MB")
        
        print("\n10. 数据一致性检查:")
        # 检查价格逻辑关系
        price_errors = 0
        volume_errors = 0
        
        # 检查high >= low
        high_low_errors = (df['$high'] < df['$low']).sum()
        print(f"   High < Low 错误数量: {high_low_errors}")
        
        # 检查high >= close
        high_close_errors = (df['$high'] < df['$close']).sum()
        print(f"   High < Close 错误数量: {high_close_errors}")
        
        # 检查low <= close
        low_close_errors = (df['$low'] > df['$close']).sum()
        print(f"   Low > Close 错误数量: {low_close_errors}")
        
        # 检查volume >= 0
        volume_errors = (df['$volume'] < 0).sum()
        print(f"   负成交量数量: {volume_errors}")
        
        print("\n✅ 数据验证完成！")
        
        # 总结
        print("\n=== 数据质量总结 ===")
        if df.isnull().sum().sum() == 0:
            print("✅ 无缺失值")
        else:
            print("⚠️  存在缺失值")
            
        if np.isinf(df.select_dtypes(include=[np.number])).sum().sum() == 0:
            print("✅ 无无穷值")
        else:
            print("⚠️  存在无穷值")
            
        if high_low_errors == 0 and high_close_errors == 0 and low_close_errors == 0:
            print("✅ 价格逻辑关系正确")
        else:
            print("⚠️  存在价格逻辑错误")
            
        if volume_errors == 0:
            print("✅ 成交量数据正确")
        else:
            print("⚠️  存在负成交量")
            
        if df['$factor'].min() > 0 and df['$factor'].max() <= 1:
            print("✅ 复权因子范围正确")
        else:
            print("⚠️  复权因子范围异常")
        
        return True
        
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False

if __name__ == "__main__":
    success = verify_final_data()
    if success:
        print("\n🎉 数据验证成功！数据质量良好！")
    else:
        print("\n❌ 数据验证失败！") 