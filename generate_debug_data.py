#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成调试数据
使用2018-2019年的数据和前100只股票
"""

import qlib
import pandas as pd
from pathlib import Path

def generate_debug_data():
    """生成调试数据"""
    print("开始生成调试数据...")
    
    # 初始化qlib
    qlib.init(provider_uri="~/.qlib/qlib_data/cn_data")
    from qlib.data import D
    
    # 获取股票列表
    instruments = D.instruments()
    print(f"总股票数量: {len(instruments)}")
    
    # 定义字段
    fields = ["$open", "$close", "$high", "$low", "$volume", "$factor"]
    
    # 获取完整数据以确定前100只股票
    print("获取完整数据以确定股票列表...")
    full_data = D.features(instruments, fields, freq="day").swaplevel().sort_index()
    
    # 获取前100只股票
    top_100_instruments = full_data.reset_index()["instrument"].unique()[:100]
    print(f"选择前100只股票: {len(top_100_instruments)}")
    
    # 生成调试数据
    print("生成调试数据...")
    debug_data = (
        (
            D.features(top_100_instruments, fields, start_time="2018-01-01", end_time="2019-12-31", freq="day")
            .swaplevel()
            .sort_index()
        )
        .swaplevel()
        .loc[top_100_instruments]
        .swaplevel()
        .sort_index()
    )
    
    # 保存调试数据
    debug_file = Path("git_ignore_folder/factor_implementation_source_data_debug/daily_pv.h5")
    debug_file.parent.mkdir(parents=True, exist_ok=True)
    debug_data.to_hdf(debug_file, key="data")
    
    print(f"调试数据已保存到: {debug_file}")
    print(f"调试数据形状: {debug_data.shape}")
    print(f"调试数据时间范围: {debug_data.index.get_level_values(0).min()} 到 {debug_data.index.get_level_values(0).max()}")
    print(f"调试数据股票数量: {debug_data.index.get_level_values(1).nunique()}")
    
    return debug_data

if __name__ == "__main__":
    debug_data = generate_debug_data()
    print("✅ 调试数据生成完成！") 