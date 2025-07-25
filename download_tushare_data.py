#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 Tushare 下载 A 股日线行情数据
严格按照现有 daily_pv.h5 的格式要求
"""

import tushare as ts
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta
import os

# Tushare Token
TUSHARE_TOKEN = "6f8cc83f22acc925e65adf42cc5427a79f4954ca72eb66d844ce2d00"

def setup_tushare():
    """初始化 Tushare"""
    ts.set_token(TUSHARE_TOKEN)
    pro = ts.pro_api()
    return pro

def get_all_stocks(pro):
    """获取所有 A 股股票列表"""
    print("正在获取股票列表...")
    
    # 获取主板、中小板、创业板股票
    stocks_main = pro.stock_basic(exchange='', list_status='L', 
                                 fields='ts_code,symbol,name,area,industry,list_date')
    
    print(f"获取到 {len(stocks_main)} 只股票")
    return stocks_main

def convert_ts_code_to_qlib_format(ts_code):
    """
    将 Tushare 股票代码转换为 Qlib 格式
    例如: '000001.SZ' -> 'SZ000001'
    """
    symbol, exchange = ts_code.split('.')
    return f"{exchange}{symbol}"

def download_stock_data(pro, ts_code, start_date='19990101', end_date='20241231'):
    """下载单只股票的日线数据"""
    try:
        # 下载日线行情
        df = pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date,
                      fields='ts_code,trade_date,open,high,low,close,vol,amount')
        
        if df.empty:
            print(f"  {ts_code}: 无数据")
            return None
        
        # 获取复权因子
        adj_factor = pro.adj_factor(ts_code=ts_code, start_date=start_date, end_date=end_date,
                                   fields='ts_code,trade_date,adj_factor')
        
        # 合并数据
        if not adj_factor.empty:
            df = pd.merge(df, adj_factor, on=['ts_code', 'trade_date'], how='left')
        else:
            df['adj_factor'] = np.nan
        
        print(f"  {ts_code}: {len(df)} 条记录")
        return df
        
    except Exception as e:
        print(f"  {ts_code}: 下载失败 - {e}")
        return None

def process_raw_data(raw_data_list):
    """
    处理原始数据，转换为 Qlib 格式
    """
    print("\n正在处理和转换数据格式...")
    
    # 合并所有数据
    all_data = pd.concat(raw_data_list, ignore_index=True)
    print(f"合并后总记录数: {len(all_data)}")
    
    # 数据预处理
    all_data['trade_date'] = pd.to_datetime(all_data['trade_date'], format='%Y%m%d')
    all_data['instrument'] = all_data['ts_code'].apply(convert_ts_code_to_qlib_format)
    
    # 重命名列以符合 Qlib 格式
    all_data = all_data.rename(columns={
        'trade_date': 'datetime',
        'open': '$open',
        'close': '$close', 
        'high': '$high',
        'low': '$low',
        'vol': '$volume',  # Tushare 的 vol 是成交量(万手)，需要转换
        'adj_factor': '$factor'
    })
    
    # 转换成交量单位：Tushare 是万手，Qlib 需要股
    all_data['$volume'] = all_data['$volume'] * 10000  # 万手转为手
    
    # 只保留需要的列
    columns_needed = ['datetime', 'instrument', '$open', '$close', '$high', '$low', '$volume', '$factor']
    all_data = all_data[columns_needed]
    
    # 删除空值行
    all_data = all_data.dropna(subset=['$open', '$close', '$high', '$low'])
    
    # 设置 MultiIndex
    all_data = all_data.set_index(['datetime', 'instrument']).sort_index()
    
    # 转换数据类型为 float32 (与原 daily_pv.h5 一致)
    for col in ['$open', '$close', '$high', '$low', '$volume', '$factor']:
        all_data[col] = all_data[col].astype('float32')
    
    print(f"处理后数据形状: {all_data.shape}")
    print(f"日期范围: {all_data.index.levels[0].min()} 到 {all_data.index.levels[0].max()}")
    print(f"股票数量: {len(all_data.index.levels[1])}")
    
    return all_data

def save_to_hdf5(data, filename):
    """保存数据到 HDF5 文件"""
    print(f"\n正在保存到 {filename}...")
    
    # 确保目录存在
    os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else '.', exist_ok=True)
    
    # 保存到 HDF5
    data.to_hdf(filename, key='data', mode='w', complevel=9, complib='zlib')
    print(f"数据已保存到 {filename}")
    
    # 验证保存的数据
    print("验证保存的数据:")
    df_verify = pd.read_hdf(filename, key='data')
    print(f"  形状: {df_verify.shape}")
    print(f"  索引: {df_verify.index.names}")
    print(f"  列名: {list(df_verify.columns)}")
    print(f"  数据类型: {df_verify.dtypes.to_dict()}")

def main():
    """主函数"""
    print("=== Tushare A股数据下载脚本 ===")
    print("目标格式：与现有 daily_pv.h5 完全一致")
    print(f"Tushare Token: {TUSHARE_TOKEN[:10]}...")
    
    # 初始化 Tushare
    pro = setup_tushare()
    
    # 获取股票列表
    stocks = get_all_stocks(pro)
    
    # 下载数据
    print(f"\n开始下载 {len(stocks)} 只股票的数据...")
    print("注意：Tushare 有访问频率限制，请耐心等待...")
    
    raw_data_list = []
    failed_stocks = []
    
    for i, row in stocks.iterrows():
        ts_code = row['ts_code']
        print(f"[{i+1}/{len(stocks)}] 下载 {ts_code}...")
        
        data = download_stock_data(pro, ts_code)
        if data is not None:
            raw_data_list.append(data)
        else:
            failed_stocks.append(ts_code)
        
        # 控制访问频率 (120积分约束：200次/分钟)
        time.sleep(0.3)  # 每次请求间隔0.3秒，约每分钟200次
        
        # 每100只股票保存一次进度
        if (i + 1) % 100 == 0:
            print(f"已完成 {i+1} 只股票，成功 {len(raw_data_list)} 只，失败 {len(failed_stocks)} 只")
    
    print(f"\n下载完成！成功: {len(raw_data_list)}, 失败: {len(failed_stocks)}")
    if failed_stocks:
        print(f"失败的股票: {failed_stocks[:10]}..." if len(failed_stocks) > 10 else f"失败的股票: {failed_stocks}")
    
    if not raw_data_list:
        print("没有成功下载任何数据，程序退出")
        return
    
    # 处理数据
    processed_data = process_raw_data(raw_data_list)
    
    # 保存数据
    output_file = "daily_pv_tushare.h5"
    save_to_hdf5(processed_data, output_file)
    
    print(f"\n=== 下载完成 ===")
    print(f"输出文件: {output_file}")
    print("请检查数据质量，然后用此文件替换原有的 daily_pv.h5")

if __name__ == "__main__":
    main() 