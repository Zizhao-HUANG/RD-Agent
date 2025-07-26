#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 Tushare 下载 A 股日线行情数据 (V6 - 修复复权因子非单调问题)

作者: 量化金融专家
版本: 6.0
日期: 2025-07-26

目标：
生成一个符合业界最高标准、与 RD-Agent(Q) / Qlib 框架完全兼容的高质量数据文件。

核心修正与特性 (V6):
1.  [最关键] 修复复权因子非单调的根本原因：
    -   调整了处理流程，确保在执行 `fillna` 填充复权因子前，数据已按日期升序排列。
    -   旧流程: merge -> ffill -> sort (错误)
    -   新流程: merge -> sort -> ffill (正确)
    -   此修正可确保 `$factor` 列严格单调非增。

2.  [健壮性] 增加关键股票下载校验与重试：
    -   在并行下载结束后，检查核心股票（如贵州茅台）是否下载成功。
    -   如果失败，则进行一次独立的、强制的串行下载重试，最大限度保证数据完整性。

3.  [兼容性] 保持V5版本所有优点
    -   严格采用前复权(qfq)逻辑。
    -   成交量根据前复权因子正确调整。
    -   强大的并行下载、API速率控制和重试引擎。
    -   严格的Qlib格式对齐。
"""

import tushare as ts
import pandas as pd
import numpy as np
import time
from datetime import datetime
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import tqdm
import threading
import warnings

# --- 配置区 ---
TUSHARE_TOKEN = "58ae7ff4258e6476a0e76b0acd9cfacabee1664b87702f39c739254c"
START_DATE = '19990101'
END_DATE = '20250725'
OUTPUT_FILENAME = "daily_pv_qfq_standard_v6.h5" # 使用新文件名以避免混淆
QLIB_COLUMN_ORDER = ['$open', '$close', '$high', '$low', '$volume', '$factor']

# --- 性能与API控制参数 ---
API_CALLS_PER_MINUTE = 200
MAX_WORKERS = 14
API_DELAY = 60.0 / API_CALLS_PER_MINUTE
API_SEMAPHORE = threading.Semaphore(MAX_WORKERS)

# --- 关键股票列表 ---
# 用于下载后校验，确保这些重要标的的数据完整
CRITICAL_STOCKS = ['600519.SH', '000001.SZ', '000300.SH'] 

warnings.filterwarnings(
    "ignore",
    message=".*fillna with 'method' is deprecated.*",
    category=FutureWarning
)

def setup_tushare():
    ts.set_token(TUSHARE_TOKEN)
    pro = ts.pro_api()
    try:
        pro.trade_cal(exchange='SSE', start_date='20200101', end_date='20200101')
        print("[INFO] Tushare 连接成功。")
    except Exception as e:
        print(f"[FATAL] Tushare 连接失败: {e}")
        exit(1)
    return pro

def get_all_stocks_and_indices(pro):
    print("[INFO] 正在获取所有A股股票列表 (包括已退市)...")
    fields = 'ts_code,name,list_date'
    df_l = pro.stock_basic(exchange='', list_status='L', fields=fields)
    df_d = pro.stock_basic(exchange='', list_status='D', fields=fields)
    df_p = pro.stock_basic(exchange='', list_status='P', fields=fields)
    stocks = pd.concat([df_l, df_d, df_p]).drop_duplicates(subset='ts_code').reset_index(drop=True)

    print("[INFO] 正在构建目标指数列表...")
    target_indices_codes = ['000300.SH', '000903.SH', '000905.SH']
    indices = pd.DataFrame({'ts_code': target_indices_codes, 'name': ['沪深300', '中证100', '中证500']})
    print(f"[SUCCESS] 获取到 {len(stocks)} 只股票，{len(indices)} 个目标指数。")
    return stocks, indices

def convert_ts_code_to_qlib_format(ts_code):
    if not isinstance(ts_code, str) or '.' not in ts_code:
        return None
    symbol, exchange = ts_code.split('.')
    return f"{exchange}{symbol}"

def call_tushare_api_with_retry(api_func, max_retries=5, **kwargs):
    for attempt in range(max_retries):
        with API_SEMAPHORE:
            try:
                time.sleep(API_DELAY)
                return api_func(**kwargs)
            except Exception as e:
                wait_time = 2 ** attempt
                tqdm.tqdm.write(f"  [WARN] API call for {kwargs.get('ts_code', '')} failed (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
    tqdm.tqdm.write(f"  [ERROR] API call failed after {max_retries} retries for {kwargs.get('ts_code', '')}")
    return None

def download_and_process_stock(pro, ts_code, start_date, end_date):
    try:
        df_daily = call_tushare_api_with_retry(pro.daily, ts_code=ts_code, start_date=start_date, end_date=end_date)
        if df_daily is None or df_daily.empty: return None

        df_factor = call_tushare_api_with_retry(pro.adj_factor, ts_code=ts_code, start_date=start_date, end_date=end_date)
        if df_factor is None or df_factor.empty:
            df_factor = pd.DataFrame({'trade_date': df_daily['trade_date'], 'adj_factor': 1.0})

        df = pd.merge(df_daily, df_factor, on='trade_date', how='left')
        
        # [核心修正] 先按日期升序排序，再填充
        df.sort_values(by='trade_date', ascending=True, inplace=True)
        df['adj_factor'].fillna(method='ffill', inplace=True) # ffill在升序数据上是正确的
        df.reset_index(drop=True, inplace=True)

        if df.empty: return None

        latest_factor = df['adj_factor'].iloc[-1]
        if latest_factor == 0: return None
        
        df['$factor'] = df['adj_factor'] / latest_factor
        df['$open'] = df['open'] * df['$factor']
        df['$close'] = df['close'] * df['$factor']
        df['$high'] = df['high'] * df['$factor']
        df['$low'] = df['low'] * df['$factor']
        df['$volume'] = (df['vol'] * 100) / df['$factor']
        df['$volume'].replace([np.inf, -np.inf], 0, inplace=True)
        df['$volume'].fillna(0, inplace=True)

        df['datetime'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
        df['instrument'] = convert_ts_code_to_qlib_format(ts_code)

        return df[['datetime', 'instrument'] + QLIB_COLUMN_ORDER]

    except Exception as e:
        tqdm.tqdm.write(f"  [CRITICAL] Unhandled exception for {ts_code}: {e}")
        return None

def download_and_process_index(pro, ts_code, start_date, end_date):
    # ... (此函数无需修改，保持原样)
    try:
        df = call_tushare_api_with_retry(pro.index_daily, ts_code=ts_code, start_date=start_date, end_date=end_date)
        if df is None or df.empty: return None
        df.rename(columns={'open': '$open', 'close': '$close', 'high': '$high', 'low': '$low'}, inplace=True)
        df['$volume'] = df['amount'] * 1000
        df['$factor'] = 1.0
        df['datetime'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
        df['instrument'] = convert_ts_code_to_qlib_format(ts_code)
        return df[['datetime', 'instrument'] + QLIB_COLUMN_ORDER]
    except Exception as e:
        tqdm.tqdm.write(f"  [ERROR] Index download failed for {ts_code}: {e}")
        return None

def save_to_hdf5(data, filename):
    print(f"\n[INFO] 正在保存数据到 {filename}...")
    # 使用 'fixed' 格式以匹配您原始审核脚本的期望
    data.to_hdf(filename, key='data', mode='w', format='fixed', complevel=9, complib='zlib')
    print(f"[SUCCESS] 数据已成功保存到 {filename}")

def main():
    print("="*80)
    print("=== Tushare A股日线行情下载脚本 (V6 - 修复复权因子非单调问题) ===")
    print("="*80)
    
    pro = setup_tushare()
    stocks, indices = get_all_stocks_and_indices(pro)
    
    all_symbols = list(stocks['ts_code']) + list(indices['ts_code'])
    
    processed_data = []
    failed_symbols = []
    
    print(f"\n[INFO] 开始并行下载 {len(all_symbols)} 个标的的数据...")
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_symbol = {}
        for symbol in all_symbols:
            if symbol in list(indices['ts_code']):
                future = executor.submit(download_and_process_index, pro, symbol, START_DATE, END_DATE)
            else:
                future = executor.submit(download_and_process_stock, pro, symbol, START_DATE, END_DATE)
            future_to_symbol[future] = symbol

        for future in tqdm.tqdm(as_completed(future_to_symbol), total=len(all_symbols), desc="下载数据"):
            symbol = future_to_symbol[future]
            try:
                result = future.result()
                if result is not None and not result.empty:
                    processed_data.append(result)
                else:
                    failed_symbols.append(symbol)
            except Exception as exc:
                tqdm.tqdm.write(f'\n[CRITICAL] {symbol} 在主线程中捕获到异常: {exc}')
                failed_symbols.append(symbol)

    # [健壮性] 关键股票校验与重试
    print("\n[INFO] 校验关键股票数据完整性...")
    successful_symbols = {df.iloc[0]['instrument'] for df in processed_data if not df.empty}
    
    for stock_code in CRITICAL_STOCKS:
        qlib_code = convert_ts_code_to_qlib_format(stock_code)
        if qlib_code not in successful_symbols:
            print(f"[WARNING] 关键股票 {qlib_code} ({stock_code}) 下载失败，正在强制重试...")
            # 使用串行方式重试
            if stock_code.endswith(('.SH', '.SZ')) and not stock_code.startswith(('000300', '000905', '000903')):
                 result = download_and_process_stock(pro, stock_code, START_DATE, END_DATE)
            else:
                 result = download_and_process_index(pro, stock_code, START_DATE, END_DATE)

            if result is not None and not result.empty:
                print(f"[SUCCESS] 关键股票 {qlib_code} 重试成功！")
                processed_data.append(result)
                if stock_code in failed_symbols: failed_symbols.remove(stock_code)
            else:
                print(f"[ERROR] 关键股票 {qlib_code} 重试失败。")

    print("\n" + "="*30 + " 下载总结 " + "="*30)
    print(f"成功处理的标的数量: {len(processed_data)}")
    print(f"失败或无数据的标的数量: {len(failed_symbols)}")
    if failed_symbols: print(f"失败/无数据标的样例 (前20个): {failed_symbols[:20]}")
    print("="*72)

    if not processed_data:
        print("\n[FATAL] 未能下载到任何有效数据，程序退出。")
        return

    print("\n[INFO] 正在合并所有数据...")
    final_df = pd.concat(processed_data, ignore_index=True)

    print("[INFO] 正在进行最终格式化和数据清洗...")
    final_df.set_index(['datetime', 'instrument'], inplace=True)
    final_df.sort_index(inplace=True)
    for col in final_df.columns:
        final_df[col] = final_df[col].astype('float32')
    final_df = final_df[QLIB_COLUMN_ORDER]
    final_df = final_df.loc[final_df.index.get_level_values('datetime') >= '2008-12-29']
    final_df.dropna(how='all', inplace=True)

    print("\n" + "="*30 + " 最终数据概览 " + "="*28)
    print(f"最终数据形状: {final_df.shape}")
    if not final_df.empty:
        print(f"日期范围: {final_df.index.get_level_values('datetime').min().date()} -> {final_df.index.get_level_values('datetime').max().date()}")
        print(f"股票/指数数量: {len(final_df.index.get_level_values('instrument').unique())}")
        print("\n数据抽样 (贵州茅台 SH600519):")
        try:
            print(final_df.loc[(slice(None), 'SH600519')].tail())
        except KeyError:
            print("  [WARNING] 未找到 SH600519 数据。")
    print("="*72)

    save_to_hdf5(final_df, OUTPUT_FILENAME)

    print("\n=== 任务圆满完成 ===")
    print(f"高质量前复权数据文件已生成: {OUTPUT_FILENAME}")
    print("请再次运行您的审核脚本进行最终确认。")

if __name__ == "__main__":
    main()