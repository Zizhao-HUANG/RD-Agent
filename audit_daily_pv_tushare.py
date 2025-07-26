#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
极为详细地审核 daily_pv_tushare.h5 文件，确保其完全符合 Qlib 要求
"""

import pandas as pd
import h5py
import numpy as np
from collections import Counter

FILE_PATH = "/home/shenzi/RD-Agent/daily_pv_tushare_rebuilt_v4.h5"

print("=== 1. HDF5 文件结构检查 ===")
with h5py.File(FILE_PATH, 'r') as f:
    print(f"顶级 keys: {list(f.keys())}")
    if 'data' in f:
        data_group = f['data']
        print(f"data 组 keys: {list(data_group.keys())}")
        for k in data_group.keys():
            d = data_group[k]
            print(f"  {k}: shape={d.shape}, dtype={d.dtype}")

print("\n=== 2. 用 pandas 读取数据结构 ===")
df = pd.read_hdf(FILE_PATH, key="data")
print(f"DataFrame 形状: {df.shape}")
print(f"索引类型: {type(df.index)}")
print(f"索引名称: {df.index.names}")
print(f"列名: {list(df.columns)}")
print(f"列数据类型: {df.dtypes.to_dict()}")

print("\n=== 3. MultiIndex 结构与范围 ===")
if hasattr(df.index, 'levels'):
    for i, level in enumerate(df.index.levels):
        print(f"Level {i} ({df.index.names[i]}): {level.min()} ~ {level.max()} (共{len(level)}个)")
    print(f"索引样例: {df.index[:5].tolist()}")
else:
    print(f"单层索引样例: {df.index[:5].tolist()}")

print("\n=== 4. 股票与指数代码检查 ===")
instruments = df.index.levels[1]
stock_codes = [x for x in instruments if (x.startswith('SH') or x.startswith('SZ')) and not x.startswith(('SH000','SZ000'))]
index_codes = [x for x in instruments if x.startswith(('SH000','SZ000'))]
print(f"股票数量: {len(stock_codes)}")
print(f"指数数量: {len(index_codes)}")
print(f"股票样例: {stock_codes[:10]}")
print(f"指数样例: {index_codes}")

print("\n=== 5. 日期范围与缺失检查 ===")
dates = df.index.levels[0]
print(f"日期数量: {len(dates)}")
print(f"最早日期: {dates.min()} 最晚日期: {dates.max()}")

print("\n=== 6. 复权正确性抽查 ===")
# 随机抽查5只股票和1个指数
import random
random.seed(42)
check_stocks = random.sample(stock_codes, min(5, len(stock_codes)))
check_indices = random.sample(index_codes, min(1, len(index_codes)))
for code in check_stocks + check_indices:
    sub = df.xs(code, level='instrument')
    print(f"\n-- {code} --")
    print(sub.head(3))
    print(sub.tail(3))
    # 检查复权因子是否单调递增（股票）
    if code in check_stocks:
        factor = sub['$factor']
        print(f"  $factor 最小: {factor.min():.6f} 最大: {factor.max():.6f}")
        if not (factor.is_monotonic_increasing or factor.is_monotonic_decreasing):
            print("  [警告] $factor 不是单调的！")
    else:
        # 指数应恒为1
        factor = sub['$factor']
        if not np.allclose(factor, 1.0):
            print("  [警告] 指数 $factor 不全为1！")

print("\n=== 7. 成交量单位与极值检查 ===")
print("成交量统计:")
print(df['$volume'].describe())
print("成交量最小值(非零):", df['$volume'][df['$volume']>0].min())
print("成交量最大值:", df['$volume'].max())

print("\n=== 8. 缺失值检查 ===")
print(df.isnull().sum())

print("\n=== 9. 数据样本 ===")
print(df.head(10))
print(df.tail(10))

print("\n=== 10. 关键字段分布 ===")
for col in ['$open', '$close', '$high', '$low', '$factor']:
    print(f"{col} min: {df[col].min()}, max: {df[col].max()}, mean: {df[col].mean()}, std: {df[col].std()}")

print("\n=== 审核完成 ===") 