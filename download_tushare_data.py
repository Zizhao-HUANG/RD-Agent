#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 Tushare 下载 A 股日线行情数据
目标：生成一个与 Qlib 原始 daily_pv.h5 文件在数据结构和数值逻辑上
      都高度兼容，同时扩展了股票池和时间范围的高质量数据文件。

二次审核修正：
1. [MAJOR] 修正了指数下载失败的记录逻辑，使其更直接和健壮。
2. [MINOR] 优化了 process_stock_data 函数的内存使用，在计算后立即删除临时列。
3. [COSMETIC] 统一了日志输出，在tqdm循环期间一致使用tqdm.write。
4. 保持了关键的 Semaphore API 速率控制器和并行下载逻辑。
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

# --- 配置区 ---
TUSHARE_TOKEN = "4e231cd75686342a6b80f13b2d8c5ca8c682cdeb9b668830dc97fc0d"
START_DATE = '19990101'
END_DATE = datetime.now().strftime('%Y%m%d')
OUTPUT_FILENAME = "daily_pv_tushare_final_approved.h5"
API_DELAY = 0.1
MAX_WORKERS = 8
API_SEMAPHORE = threading.Semaphore(3)

def setup_tushare():
    """初始化 Tushare"""
    ts.set_token(TUSHARE_TOKEN)
    return ts.pro_api()

def get_all_stocks_and_indices(pro):
    """获取所有 A 股股票和【指定】的指数列表"""
    print("正在获取所有A股股票列表...")
    stocks = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,list_date')
    print("正在构建目标指数列表...")
    target_indices_codes = ['000300.SH', '000903.SH', '000905.SH']
    indices = pd.DataFrame({'ts_code': target_indices_codes, 'name': ['CSI 300', 'CSI 100', 'CSI 500']})
    print(f"获取到 {len(stocks)} 只股票，{len(indices)} 个目标指数")
    return stocks, indices

def convert_ts_code_to_qlib_format(ts_code):
    """将 Tushare 股票代码 '000001.SZ' 转换为 Qlib 格式 'SZ000001'"""
    symbol, exchange = ts_code.split('.')
    return f"{exchange}{symbol}"

def call_tushare_api(api_func, **kwargs):
    """带速率控制的API调用封装器"""
    with API_SEMAPHORE:
        time.sleep(API_DELAY)
        return api_func(**kwargs)

def download_stock_data(pro, ts_code, start_date, end_date):
    """下载单只股票的后复权和不复权数据"""
    try:
        df_hfq = call_tushare_api(ts.pro_bar, ts_code=ts_code, adj='hfq', start_date=start_date, end_date=end_date, asset='E', freq='D')
        if df_hfq.empty: return None
        
        df_unadj = call_tushare_api(ts.pro_bar, ts_code=ts_code, adj=None, start_date=start_date, end_date=end_date, asset='E', freq='D')
        if df_unadj.empty: return None

        return pd.merge(df_hfq, df_unadj, on=['ts_code', 'trade_date'], suffixes=('_hfq', '_unadj'), how='inner')
    except Exception as e:
        tqdm.tqdm.write(f"  [ERROR] {ts_code}: 下载失败 - {e}")
        return None

def download_index_data(pro, ts_code, start_date, end_date):
    """独立下载并处理指数数据"""
    try:
        df = call_tushare_api(ts.pro_bar, ts_code=ts_code, asset='I', start_date=start_date, end_date=end_date, freq='D')
        if df.empty:
            tqdm.tqdm.write(f"  [WARN] {ts_code}: 无指数数据")
            return None
        
        df = df.rename(columns={'open': '$open', 'close': '$close', 'high': '$high', 'low': '$low'})
        df['$volume'] = df['amount'] * 1000
        df['$factor'] = np.nan if ts_code == '000905.SH' else 1.0
        df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
        df['instrument'] = df['ts_code'].apply(convert_ts_code_to_qlib_format)
        df = df.rename(columns={'trade_date': 'datetime'})
        
        columns_needed = ['datetime', 'instrument', '$open', '$close', '$high', '$low', '$volume', '$factor']
        tqdm.tqdm.write(f"  [INFO] {ts_code}: 下载了 {len(df)} 条指数记录")
        return df[columns_needed]
    except Exception as e:
        tqdm.tqdm.write(f"  [ERROR] {ts_code}: 指数下载失败 - {e}")
        return None

def process_stock_data(raw_stock_list):
    """处理合并后的股票数据，精确计算 $factor 和 $volume"""
    print("\n正在处理股票数据...")
    if not raw_stock_list:
        print("没有需要处理的股票数据。")
        return pd.DataFrame()
    
    all_data = pd.concat(raw_stock_list, ignore_index=True)
    print(f"合并后总股票记录数: {len(all_data)}")
    
    # 计算新列
    all_data['$factor'] = np.where(all_data['close_unadj'] != 0, all_data['close_hfq'] / all_data['close_unadj'], np.nan)
    all_data['$volume'] = np.where((all_data['$factor'].notna()) & (all_data['$factor'] != 0), (all_data['vol_unadj'] * 100) / all_data['$factor'], 0)
    all_data['$open'] = all_data['open_hfq']
    all_data['$close'] = all_data['close_hfq']
    all_data['$high'] = all_data['high_hfq']
    all_data['$low'] = all_data['low_hfq']
    
    # [FIX 2] 立即删除不再需要的原始列以释放内存
    all_data.drop(columns=[
        'open_hfq', 'high_hfq', 'low_hfq', 'close_hfq', 'pre_close_hfq', 'change_hfq', 'pct_chg_hfq', 'vol_hfq', 'amount_hfq',
        'open_unadj', 'high_unadj', 'low_unadj', 'close_unadj', 'pre_close_unadj', 'change_unadj', 'pct_chg_unadj', 'vol_unadj', 'amount_unadj'
    ], inplace=True)
    
    all_data['trade_date'] = pd.to_datetime(all_data['trade_date'], format='%Y%m%d')
    all_data['instrument'] = all_data['ts_code'].apply(convert_ts_code_to_qlib_format)
    
    final_data = all_data.rename(columns={'trade_date': 'datetime'})
    print("股票数据处理完成。")
    return final_data

def save_to_hdf5(data, filename):
    """保存数据到 HDF5 文件"""
    print(f"\n正在保存到 {filename}...")
    os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else '.', exist_ok=True)
    data.to_hdf(filename, key='data', mode='w', complevel=9, complib='zlib')
    print(f"数据已保存到 {filename}")
    # ... (验证部分无需修改) ...

def main():
    """主函数 - 专家二次审核版"""
    print("=== Tushare A股数据下载脚本 (专家二次审核版) ===")
    print(f"数据范围: {START_DATE} to {END_DATE}")
    
    pro = setup_tushare()
    stocks, indices = get_all_stocks_and_indices(pro)
    
    raw_stock_list = []
    failed_stocks = []
    
    print(f"\n开始并行下载 {len(stocks)} 只股票的数据 (使用 {MAX_WORKERS} 个线程, API并发度: {API_SEMAPHORE._value})...")
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        tasks = {executor.submit(download_stock_data, pro, row['ts_code'], START_DATE, END_DATE): row['ts_code'] for _, row in stocks.iterrows()}
        
        for future in tqdm.tqdm(as_completed(tasks), total=len(tasks), desc="下载股票"):
            ts_code = tasks[future]
            try:
                result = future.result()
                if result is not None:
                    raw_stock_list.append(result)
                else:
                    failed_stocks.append(ts_code)
            except Exception as exc:
                tqdm.tqdm.write(f'\n[CRITICAL] {ts_code} 在主线程中捕获到未处理异常: {exc}')
                failed_stocks.append(ts_code)

    # --- 下载指数数据 (串行) ---
    print(f"\n开始下载 {len(indices)} 个指数的数据...")
    raw_index_list = []
    failed_indices = []
    for _, row in indices.iterrows():
        ts_code = row['ts_code']
        # [FIX 4] 使用 print 因为这不在 tqdm 循环内
        print(f"  [INFO] 正在下载指数: {ts_code}")
        result = download_index_data(pro, ts_code, START_DATE, END_DATE)
        if result is not None:
            raw_index_list.append(result)
        else:
            # [FIX 1] 直接、清晰地记录失败
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
    for col in final_df.columns:
        if final_df[col].dtype != 'float32':
            final_df[col] = final_df[col].astype('float32')
    final_df = final_df.loc[final_df.index.get_level_values('datetime') >= '2008-12-29'].sort_index()
    
    print(f"最终数据形状: {final_df.shape}")
    if not final_df.empty:
        print(f"日期范围: {final_df.index.levels[0].min()} 到 {final_df.index.levels[0].max()}")
        print(f"股票/指数数量: {len(final_df.index.levels[1])}")

    save_to_hdf5(final_df, OUTPUT_FILENAME)
    
    print(f"\n=== 任务完成 ===")
    print(f"输出文件: {OUTPUT_FILENAME}")

if __name__ == "__main__":
    main()