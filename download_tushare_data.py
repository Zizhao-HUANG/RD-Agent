#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 Tushare 下载 A 股日线行情数据 (最终修正版 - 并行优化)
目标：生成一个与 Qlib 原始 daily_pv.h5 文件在数据结构和数值逻辑上
      都高度兼容，同时扩展了股票池和时间范围的高质量数据文件。

核心修正：
1. 使用 pro_bar 接口同时获取后复权(hfq)和不复权(None)数据。
2. 通过 (后复权价 / 不复权价) 的方式精确反向计算出 Qlib 兼容的 $factor。
3. 使用计算出的 $factor 对不复权成交量进行复权，得到 $volume。
4. 将指数数据作为特殊情况独立处理，精确设置其 $factor (包括 NaN)。
5. 保留数据中的 NaN 值，与原始文件格式保持一致。
6. [新增] 使用多线程并行下载，大幅提升下载效率。
"""

import tushare as ts
import pandas as pd
import numpy as np
import time
from datetime import datetime
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import tqdm # 引入tqdm来显示进度条

# --- 配置区 ---
# Tushare Token - 请替换为您自己的Token
TUSHARE_TOKEN = "4e231cd75686342a6b80f13b2d8c5ca8c682cdeb9b668830dc97fc0d"
# 数据时间范围
START_DATE = '19990101'
END_DATE = datetime.now().strftime('%Y%m%d') # 动态获取当前日期
# 输出文件名
OUTPUT_FILENAME = "daily_pv_tushare_corrected_parallel.h5"
# API调用延时（秒），保护Tushare积分
API_DELAY = 0.3
# 并行下载的线程数 (根据你的Tushare积分限制调整，200次/分钟，建议5-8个线程)
MAX_WORKERS = 8

def setup_tushare():
    """初始化 Tushare"""
    ts.set_token(TUSHARE_TOKEN)
    pro = ts.pro_api()
    return pro

def get_all_stocks_and_indices(pro):
    """获取所有 A 股股票和【指定】的指数列表"""
    print("正在获取所有A股股票列表...")
    stocks = pro.stock_basic(exchange='', list_status='L', 
                             fields='ts_code,symbol,name,list_date')
    
    print("正在构建目标指数列表...")
    target_indices_codes = ['000300.SH', '000903.SH', '000905.SH']
    indices = pd.DataFrame({
        'ts_code': target_indices_codes,
        'name': ['CSI 300', 'CSI 100', 'CSI 500']
    })
    
    print(f"获取到 {len(stocks)} 只股票，{len(indices)} 个目标指数")
    return stocks, indices

def convert_ts_code_to_qlib_format(ts_code):
    """将 Tushare 股票代码 '000001.SZ' 转换为 Qlib 格式 'SZ000001'"""
    symbol, exchange = ts_code.split('.')
    return f"{exchange}{symbol}"

def download_stock_data(pro, ts_code, start_date, end_date):
    """
    [重构] 下载单只股票的后复权和不复权数据，用于计算$factor
    """
    try:
        # 1. 获取后复权数据 (hfq)
        df_hfq = ts.pro_bar(ts_code=ts_code, adj='hfq', start_date=start_date, end_date=end_date, asset='E', freq='D')
        time.sleep(API_DELAY)
        
        if df_hfq.empty:
            # 在并行模式下，减少不必要的打印
            # print(f"  {ts_code}: 无数据")
            return None

        # 2. 获取不复权数据 (None)
        df_unadj = ts.pro_bar(ts_code=ts_code, adj=None, start_date=start_date, end_date=end_date, asset='E', freq='D')
        time.sleep(API_DELAY)

        if df_unadj.empty:
            # print(f"  {ts_code}: 警告！有后复权数据但无不复权数据")
            return None

        # 3. 合并数据
        df_merged = pd.merge(
            df_hfq, df_unadj,
            on=['ts_code', 'trade_date'],
            suffixes=('_hfq', '_unadj'),
            how='inner'
        )
        
        # print(f"  {ts_code}: 下载了 {len(df_merged)} 条记录")
        return df_merged
        
    except Exception as e:
        # 在并行模式下，错误信息可能会交错，但仍然需要打印
        print(f"  {ts_code}: 下载失败 - {e}")
        return None

def download_index_data(pro, ts_code, start_date, end_date):
    """
    [重构] 独立下载并处理指数数据
    """
    try:
        df = ts.pro_bar(ts_code=ts_code, asset='I', start_date=start_date, end_date=end_date, freq='D')
        time.sleep(API_DELAY)
        if df.empty:
            print(f"  {ts_code}: 无数据")
            return None
        
        df = df.rename(columns={'open': '$open', 'close': '$close', 'high': '$high', 'low': '$low'})
        
        # 指数成交量使用成交额（千元 -> 元）
        df['$volume'] = df['amount'] * 1000

        # [关键修正] 根据指数代码精确设置 $factor
        if ts_code == '000905.SH':
            df['$factor'] = np.nan
        else: # SH000300, SH000903
            df['$factor'] = 1.0
        
        df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
        df['instrument'] = df['ts_code'].apply(convert_ts_code_to_qlib_format)
        df = df.rename(columns={'trade_date': 'datetime'})
        
        columns_needed = ['datetime', 'instrument', '$open', '$close', '$high', '$low', '$volume', '$factor']
        print(f"  {ts_code}: 下载了 {len(df)} 条记录")
        return df[columns_needed]
        
    except Exception as e:
        print(f"  {ts_code}: 指数下载失败 - {e}")
        return None

def process_stock_data(raw_stock_list):
    """
    [重构] 处理合并后的股票数据，精确计算 $factor 和 $volume
    """
    print("\n正在处理股票数据...")
    if not raw_stock_list:
        print("没有需要处理的股票数据。")
        return pd.DataFrame()

    all_data = pd.concat(raw_stock_list, ignore_index=True)
    print(f"合并后总股票记录数: {len(all_data)}")
    
    # 1. 计算 $factor
    all_data['$factor'] = np.where(
        all_data['close_unadj'] != 0,
        all_data['close_hfq'] / all_data['close_unadj'],
        np.nan 
    )

    # 2. 计算 $volume (成交量复权)
    all_data['$volume'] = np.where(
        (all_data['$factor'].notna()) & (all_data['$factor'] != 0),
        (all_data['vol_unadj'] * 100) / all_data['$factor'],
        0
    )

    # 3. 准备最终列 (价格字段使用后复权数据)
    all_data['$open'] = all_data['open_hfq']
    all_data['$close'] = all_data['close_hfq']
    all_data['$high'] = all_data['high_hfq']
    all_data['$low'] = all_data['low_hfq']
    
    all_data['trade_date'] = pd.to_datetime(all_data['trade_date'], format='%Y%m%d')
    all_data['instrument'] = all_data['ts_code'].apply(convert_ts_code_to_qlib_format)
    
    columns_needed = ['trade_date', 'instrument', '$open', '$close', '$high', '$low', '$volume', '$factor']
    final_data = all_data[columns_needed].rename(columns={'trade_date': 'datetime'})
    
    print("股票数据处理完成。")
    return final_data

def save_to_hdf5(data, filename):
    """保存数据到 HDF5 文件"""
    print(f"\n正在保存到 {filename}...")
    os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else '.', exist_ok=True)
    
    data.to_hdf(filename, key='data', mode='w', complevel=9, complib='zlib')
    print(f"数据已保存到 {filename}")
    
    print("\n验证保存的数据:")
    try:
        with pd.HDFStore(filename, 'r') as store:
            df_verify = store['data']
            print(f"  文件读取成功。")
            print(f"  形状: {df_verify.shape}")
            print(f"  索引: {df_verify.index.names}")
            print(f"  列名: {list(df_verify.columns)}")
            print(f"  数据类型: \n{df_verify.dtypes}")
            print(f"\n  数据样例 (头部):\n{df_verify.head()}")
            print(f"\n  数据样例 (尾部):\n{df_verify.tail()}")
    except Exception as e:
        print(f"  验证失败: {e}")

def main():
    """主函数 - 并行优化版"""
    print("=== Tushare A股数据下载脚本 (最终修正版 - 并行优化) ===")
    print(f"数据范围: {START_DATE} to {END_DATE}")
    print(f"Tushare Token: {TUSHARE_TOKEN[:10]}...")
    
    pro = setup_tushare()
    stocks, indices = get_all_stocks_and_indices(pro)
    
    raw_stock_list = []
    raw_index_list = []
    failed_stocks = []
    failed_indices = []
    
    # --- [核心修改] 并行下载股票数据 ---
    print(f"\n开始并行下载 {len(stocks)} 只股票的数据 (使用 {MAX_WORKERS} 个线程)...")
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # 创建future任务列表
        future_to_stock = {executor.submit(download_stock_data, pro, row['ts_code'], START_DATE, END_DATE): row['ts_code'] for _, row in stocks.iterrows()}
        
        # 使用tqdm显示进度条，并收集结果
        for future in tqdm.tqdm(as_completed(future_to_stock), total=len(stocks), desc="下载股票"):
            ts_code = future_to_stock[future]
            try:
                data = future.result()
                if data is not None:
                    raw_stock_list.append(data)
                else:
                    # download_stock_data内部已经处理了失败情况，这里只记录失败的ts_code
                    failed_stocks.append(ts_code)
            except Exception as exc:
                print(f'\n{ts_code} 在主线程中生成了异常: {exc}')
                failed_stocks.append(ts_code)

    # --- 下载指数数据 (串行，因为数量少) ---
    print(f"\n开始下载 {len(indices)} 个指数的数据...")
    for i, row in indices.iterrows():
        ts_code = row['ts_code']
        print(f"[指数 {i+1}/{len(indices)}] {ts_code}")
        data = download_index_data(pro, ts_code, START_DATE, END_DATE)
        if data is not None:
            raw_index_list.append(data)
        else:
            failed_indices.append(ts_code)

    print("\n--- 下载总结 ---")
    print(f"股票成功: {len(raw_stock_list)}, 失败: {len(failed_stocks)}")
    print(f"指数成功: {len(raw_index_list)}, 失败: {len(failed_indices)}")
    if failed_stocks: print(f"失败的股票 (前10个): {failed_stocks[:10]}")
    if failed_indices: print(f"失败的指数: {failed_indices}")
    
    # --- 数据处理与合并 ---
    processed_stocks = process_stock_data(raw_stock_list)
    
    print("\n正在合并股票和指数数据...")
    if not raw_index_list:
        final_df = processed_stocks
    else:
        processed_indices = pd.concat(raw_index_list, ignore_index=True)
        final_df = pd.concat([processed_stocks, processed_indices], ignore_index=True)

    if final_df.empty:
        print("没有生成任何数据，程序退出。")
        return

    # --- 最终格式化 ---
    print("\n正在进行最终格式化...")
    final_df = final_df.set_index(['datetime', 'instrument']).sort_index()
    
    # 转换数据类型为 float32
    for col in final_df.columns:
        final_df[col] = final_df[col].astype('float32')
    
    # 应用日期过滤，与原始Qlib脚本保持一致
    final_df = final_df.loc[final_df.index.get_level_values('datetime') >= '2008-12-29']
    final_df = final_df.sort_index()
    
    print(f"最终数据形状: {final_df.shape}")
    if not final_df.empty:
        print(f"日期范围: {final_df.index.levels[0].min()} 到 {final_df.index.levels[0].max()}")
        print(f"股票/指数数量: {len(final_df.index.levels[1])}")

    # --- 保存文件 ---
    save_to_hdf5(final_df, OUTPUT_FILENAME)
    
    print(f"\n=== 任务完成 ===")
    print(f"输出文件: {OUTPUT_FILENAME}")
    print("请使用审计脚本检查数据质量，然后用此文件替换原有的 daily_pv.h5")

if __name__ == "__main__":
    main()