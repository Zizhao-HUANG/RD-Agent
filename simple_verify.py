#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单验证最终数据
"""

import pandas as pd

def simple_verify():
    """简单验证数据"""
    print("=== 验证最终数据 ===\n")
    
    try:
        # 读取数据
        df = pd.read_hdf('/home/shenzi/RD-Agent/git_ignore_folder/factor_implementation_source_data/daily_pv.h5', key='data')
        
        print("✅ 数据加载成功！")
        print(f"数据形状: {df.shape}")
        print(f"时间范围: {df.index.get_level_values(0).min()} 到 {df.index.get_level_values(0).max()}")
        print(f"股票数量: {df.index.get_level_values(1).nunique()}")
        print(f"数据字段: {list(df.columns)}")
        
        # 检查复权因子
        factor_col = '$factor'
        if factor_col in df.columns:
            print(f"复权因子范围: {df[factor_col].min():.6f} - {df[factor_col].max():.6f}")
            print(f"复权因子平均值: {df[factor_col].mean():.6f}")
        else:
            print("❌ 复权因子字段不存在")
        
        print("\n🎉 数据验证完成！")
        
    except Exception as e:
        print(f"❌ 验证失败: {e}")

if __name__ == "__main__":
    simple_verify() 