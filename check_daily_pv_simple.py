#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版本检查 daily_pv.h5 文件的格式结构
"""

import pandas as pd
import h5py
import numpy as np

def check_daily_pv_simple(file_path):
    """检查 daily_pv.h5 文件的结构"""
    
    print("=== 检查 daily_pv.h5 文件格式 (简化版) ===\n")
    
    # 1. 使用 h5py 直接读取原始数据
    print("1. HDF5 原始数据结构:")
    with h5py.File(file_path, 'r') as f:
        print(f"   顶级 Keys: {list(f.keys())}")
        
        if 'data' in f:
            data_group = f['data']
            print(f"   data 组中的 keys: {list(data_group.keys())}")
            
            # 读取列名
            if 'axis0' in data_group:
                columns = data_group['axis0'][:]
                print(f"   列名 (axis0): {[col.decode() if isinstance(col, bytes) else col for col in columns]}")
            
            # 读取索引信息
            if 'axis1_level0' in data_group and 'axis1_level1' in data_group:
                dates = data_group['axis1_level0'][:]
                instruments = data_group['axis1_level1'][:]
                print(f"   日期数量: {len(dates)}")
                print(f"   股票数量: {len(instruments)}")
                print(f"   日期样例: {dates[:5]}")
                print(f"   股票代码样例: {[inst.decode() if isinstance(inst, bytes) else inst for inst in instruments[:10]]}")
            
            # 读取数据值
            if 'block0_values' in data_group:
                values = data_group['block0_values']
                print(f"   数据形状: {values.shape}")
                print(f"   数据类型: {values.dtype}")
                
                # 读取一小部分数据样例
                sample_data = values[:100, :]  # 前100行
                print(f"   数据值样例 (前5行前3列):")
                print(sample_data[:5, :3])
    
    # 2. 尝试直接使用 pandas 读取整个数据集
    print("\n2. 尝试读取完整数据集:")
    try:
        df = pd.read_hdf(file_path, key="data")
        print(f"   成功读取! DataFrame 形状: {df.shape}")
        print(f"   索引类型: {type(df.index)}")
        print(f"   索引名称: {df.index.names}")
        print(f"   列名: {list(df.columns)}")
        
        # 显示数据样例
        print(f"\n   数据样例 (前5行):")
        print(df.head())
        
        # 显示索引范围
        print(f"\n   索引范围:")
        if hasattr(df.index, 'levels'):
            for i, level in enumerate(df.index.levels):
                level_name = df.index.names[i]
                print(f"     Level {i} ({level_name}): {level.min()} 到 {level.max()}")
        
    except Exception as e:
        print(f"   读取完整数据集失败: {e}")
        
        # 尝试使用 HDFStore
        print("\n3. 尝试使用 HDFStore 获取信息:")
        try:
            with pd.HDFStore(file_path, 'r') as store:
                print(f"   Store keys: {store.keys()}")
                storer = store.get_storer('data')
                print(f"   数据行数: {storer.nrows}")
                print(f"   数据列数: {storer.ncols}")
                
                # 获取索引信息
                if hasattr(storer, 'table'):
                    table = storer.table
                    print(f"   表描述: {table.description}")
                
        except Exception as store_e:
            print(f"   HDFStore 也失败: {store_e}")
    
    print(f"\n=== 格式检查完成 ===")

if __name__ == "__main__":
    file_path = "/home/shenzi/RD-Agent/git_ignore_folder/factor_implementation_source_data/daily_pv.h5"
    check_daily_pv_simple(file_path) 