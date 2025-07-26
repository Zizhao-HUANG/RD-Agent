#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查股票数据的实际长度和时间范围
"""

import numpy as np
import pandas as pd
from pathlib import Path

def check_data_length():
    """检查股票数据的实际长度"""
    print("=== 检查股票数据长度和时间范围 ===\n")
    
    qlib_dir = Path("/home/shenzi/.qlib/qlib_data/cn_data")
    
    # 读取日历
    calendar_file = qlib_dir / "calendars" / "day.txt"
    with open(calendar_file, 'r') as f:
        calendar = [line.strip() for line in f.readlines() if line.strip()]
    
    print(f"1. 交易日历信息:")
    print(f"   总交易日数: {len(calendar)}")
    print(f"   开始日期: {calendar[0]}")
    print(f"   结束日期: {calendar[-1]}")
    
    # 读取股票列表
    instruments_file = qlib_dir / "instruments" / "all.txt"
    df_instruments = pd.read_csv(instruments_file, header=None)
    instruments = df_instruments[0].tolist()
    
    print(f"\n2. 股票列表信息:")
    print(f"   股票数量: {len(instruments)}")
    
    # 检查几个样本股票的数据长度
    sample_stocks = ['sh600000', 'sz000001', 'sh000300']
    
    print(f"\n3. 样本股票数据长度检查:")
    min_length = float('inf')
    max_length = 0
    
    for stock in sample_stocks:
        stock_dir = qlib_dir / "features" / stock
        if stock_dir.exists():
            # 读取收盘价数据来获取长度
            close_file = stock_dir / "close.day.bin"
            if close_file.exists():
                data = np.fromfile(close_file, dtype=np.float32)
                length = len(data)
                min_length = min(min_length, length)
                max_length = max(max_length, length)
                
                print(f"   {stock}: {length} 个数据点")
                
                # 计算对应的日期范围
                if length <= len(calendar):
                    start_date = calendar[0]
                    end_date = calendar[length-1] if length > 0 else calendar[0]
                    print(f"     日期范围: {start_date} 到 {end_date}")
                else:
                    print(f"     警告: 数据长度({length})超过日历长度({len(calendar)})")
        else:
            print(f"   {stock}: 目录不存在")
    
    print(f"\n4. 数据长度统计:")
    print(f"   最小长度: {min_length}")
    print(f"   最大长度: {max_length}")
    print(f"   日历长度: {len(calendar)}")
    
    # 检查所有股票的数据长度分布
    print(f"\n5. 检查所有股票的数据长度...")
    lengths = []
    for i, stock in enumerate(instruments[:100]):  # 只检查前100只股票作为样本
        stock_dir = qlib_dir / "features" / stock
        if stock_dir.exists():
            close_file = stock_dir / "close.day.bin"
            if close_file.exists():
                data = np.fromfile(close_file, dtype=np.float32)
                lengths.append(len(data))
        
        if (i + 1) % 20 == 0:
            print(f"   已检查 {i + 1} 只股票...")
    
    if lengths:
        print(f"\n6. 前100只股票的数据长度统计:")
        print(f"   平均长度: {np.mean(lengths):.1f}")
        print(f"   中位数长度: {np.median(lengths):.1f}")
        print(f"   最小长度: {min(lengths)}")
        print(f"   最大长度: {max(lengths)}")
        print(f"   标准差: {np.std(lengths):.1f}")
        
        # 检查有多少股票数据不完整
        incomplete_stocks = sum(1 for l in lengths if l < len(calendar))
        print(f"   数据不完整的股票数量: {incomplete_stocks}/{len(lengths)} ({incomplete_stocks/len(lengths)*100:.1f}%)")

if __name__ == "__main__":
    check_data_length() 