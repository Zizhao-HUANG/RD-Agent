#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接使用HDF5数据生成调试数据
"""

import pandas as pd
from pathlib import Path

def generate_debug_data_direct():
    """直接使用HDF5数据生成调试数据"""
    print("开始生成调试数据...")
    
    # 读取完整数据
    full_data_file = Path("git_ignore_folder/factor_implementation_source_data/daily_pv.h5")
    print(f"读取完整数据: {full_data_file}")
    
    df = pd.read_hdf(full_data_file, key="data")
    print(f"完整数据形状: {df.shape}")
    
    # 获取前100只股票
    all_instruments = df.index.get_level_values(1).unique()
    top_100_instruments = all_instruments[:100]
    print(f"选择前100只股票: {len(top_100_instruments)}")
    
    # 筛选2018-2019年的数据
    start_date = "2018-01-01"
    end_date = "2019-12-31"
    
    # 筛选数据
    debug_data = df.loc[(slice(start_date, end_date), top_100_instruments), :]
    
    print(f"调试数据形状: {debug_data.shape}")
    print(f"调试数据时间范围: {debug_data.index.get_level_values(0).min()} 到 {debug_data.index.get_level_values(0).max()}")
    print(f"调试数据股票数量: {debug_data.index.get_level_values(1).nunique()}")
    
    # 保存调试数据
    debug_file = Path("git_ignore_folder/factor_implementation_source_data_debug/daily_pv.h5")
    debug_file.parent.mkdir(parents=True, exist_ok=True)
    debug_data.to_hdf(debug_file, key="data")
    
    print(f"调试数据已保存到: {debug_file}")
    print(f"文件大小: {debug_file.stat().st_size / 1024 / 1024:.1f} MB")
    
    return debug_data

if __name__ == "__main__":
    debug_data = generate_debug_data_direct()
    print("✅ 调试数据生成完成！") 