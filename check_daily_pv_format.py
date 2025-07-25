#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查现有 daily_pv.h5 文件的格式结构
"""

import pandas as pd
import h5py
import numpy as np

def check_daily_pv_format(file_path):
    """检查 daily_pv.h5 文件的结构"""
    
    print("=== 检查 daily_pv.h5 文件格式 ===\n")
    
    # 1. 使用 h5py 查看文件基本信息
    print("1. HDF5 文件基本信息:")
    with h5py.File(file_path, 'r') as f:
        print(f"   Keys: {list(f.keys())}")
        
        def print_h5_structure(name, obj):
            print(f"   {name}: {type(obj)}")
            if hasattr(obj, 'shape'):
                print(f"     形状: {obj.shape}")
            if hasattr(obj, 'dtype'):
                print(f"     数据类型: {obj.dtype}")
        
        f.visititems(print_h5_structure)
    
    # 2. 使用 pandas 读取小样本数据
    print("\n2. 使用 pandas 读取数据结构:")
    try:
        # 读取前100行查看结构
        df_sample = pd.read_hdf(file_path, key="data", start=0, stop=100)
        
        print(f"   DataFrame 形状 (前100行): {df_sample.shape}")
        print(f"   索引类型: {type(df_sample.index)}")
        print(f"   索引名称: {df_sample.index.names}")
        print(f"   列名: {list(df_sample.columns)}")
        print(f"   列数据类型:")
        for col in df_sample.columns:
            print(f"     {col}: {df_sample[col].dtype}")
        
        print(f"\n   索引结构详情:")
        if hasattr(df_sample.index, 'levels'):
            print(f"     MultiIndex levels: {len(df_sample.index.levels)}")
            for i, level in enumerate(df_sample.index.levels):
                level_type = type(level[0]) if len(level) > 0 else "Empty"
                level_sample = level[:3].tolist() if len(level) >= 3 else level.tolist()
                print(f"     Level {i} ({df_sample.index.names[i]}): {level_type} - 样例: {level_sample}")
        else:
            print(f"     Single Index: {type(df_sample.index[0])} - 样例: {df_sample.index[:3].tolist()}")
        
        print(f"\n   数据样例 (前5行):")
        print(df_sample.head())
        
        # 3. 查看完整的索引范围
        print(f"\n3. 查看完整索引范围:")
        
        # 只读取索引信息，不读取数据
        try:
            with pd.HDFStore(file_path, 'r') as store:
                storer = store.get_storer('data')
                print(f"   总行数: {storer.nrows}")
        except Exception as e:
            print(f"   获取总行数失败: {e}")
            
        # 读取第一行和最后一行的索引
        df_first = pd.read_hdf(file_path, key="data", start=0, stop=1)
        try:
            df_last = pd.read_hdf(file_path, key="data", start=-1)
            print(f"   第一个索引: {df_first.index[0]}")
            print(f"   最后一个索引: {df_last.index[0]}")
        except Exception as e:
            print(f"   第一个索引: {df_first.index[0]}")
            print(f"   获取最后一个索引失败: {e}")
        
        # 4. 检查日期范围
        if hasattr(df_sample.index, 'levels') and len(df_sample.index.levels) >= 1:
            # MultiIndex的情况，假设第一个level是日期
            date_level = df_sample.index.levels[0]
            if hasattr(date_level, 'min') and len(date_level) > 0:
                print(f"\n4. 日期范围信息:")
                print(f"   样例中最早日期: {date_level.min()}")
                print(f"   样例中最晚日期: {date_level.max()}")
        
        # 5. 检查股票代码
        if hasattr(df_sample.index, 'levels') and len(df_sample.index.levels) >= 2:
            instrument_level = df_sample.index.levels[1]
            print(f"\n5. 股票代码信息:")
            print(f"   样例中股票数量: {len(instrument_level)}")
            if len(instrument_level) >= 10:
                print(f"   股票代码样例: {instrument_level[:10].tolist()}")
            else:
                print(f"   股票代码样例: {instrument_level.tolist()}")
            if len(instrument_level) > 0:
                print(f"   股票代码格式: {type(instrument_level[0])}")
        
        # 6. 检查数据值的范围
        print(f"\n6. 数据值范围:")
        for col in df_sample.columns:
            if df_sample[col].dtype in ['float32', 'float64', 'int32', 'int64']:
                print(f"   {col}: min={df_sample[col].min():.6f}, max={df_sample[col].max():.6f}")
            else:
                print(f"   {col}: 非数值类型 ({df_sample[col].dtype})")
        
    except Exception as e:
        print(f"   读取数据时出错: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n=== 格式检查完成 ===")

if __name__ == "__main__":
    file_path = "/home/shenzi/RD-Agent/git_ignore_folder/factor_implementation_source_data/daily_pv.h5"
    check_daily_pv_format(file_path) 