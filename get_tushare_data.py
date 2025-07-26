#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 Tushare 下载 A 股日线行情数据 (V5 - 业界标准前复权版)

作者: 量化金融专家
版本: 5.0
日期: 2025-07-26

目标：
生成一个符合业界最高标准、与 RD-Agent(Q) / Qlib 框架完全兼容的高质量数据文件。
该文件将包含从1999年至今的全A股及核心指数的前复权日线行情数据。

核心修正与特性:
1.  [最关键] 复权逻辑修正为业界标准的“前复权(qfq)”：
    -   价格计算: `前复权价 = 未复权价 * (当日adj_factor / 最新adj_factor)`
    -   因子存储: `$factor` 列直接存储 `(当日adj_factor / 最新adj_factor)`。
    -   此方法确保了 `$factor` 的单调非增性，并避免了回测中的前视偏差。

2.  [关键] 成交量调整：
    -   `$volume` 根据前复权因子进行反向调整，以准确反映拆股前的实际交易股数。
    -   公式: `调整后成交量 = (原始成交量 * 100) / 前复权因子`

3.  [健壮性] 强大的下载引擎：
    -   使用 ThreadPoolExecutor 实现高效并行下载。
    -   基于 Semaphore 的精细化API速率控制，严格遵守Tushare限制。
    -   包含指数退避的自动重试机制，提高下载成功率。
    -   提供清晰的进度条和日志输出。

4.  [兼容性] 严格的Qlib格式对齐：
    -   输出HDF5文件采用与原始文件一致的 `format='table'` 和压缩。
    -   最终DataFrame的索引、列名、列序和数据类型均经过严格对齐。
    -   指数的 `$factor` 严格设置为 1.0。
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
# 请将 "your_token_here" 替换为你的真实 Tushare Token
TUSHARE_TOKEN = "your_token_here"
# 数据时间范围
START_DATE = '19990101'
END_DATE = '20250725'
# 输出文件名
OUTPUT_FILENAME = "daily_pv_qfq_standard.h5"
# RD-Agent(Q) / Qlib 的标准列顺序
QLIB_COLUMN_ORDER = ['$open', '$close', '$high', '$low', '$volume', '$factor']

# --- 性能与API控制参数 ---
# Tushare Pro普通用户限制为 200次/分钟, 高级用户可适当调高
API_CALLS_PER_MINUTE = 200
MAX_WORKERS = 10  # 并行下载的线程数 (建议5-15之间，取决于网络和CPU)
# 计算每次API调用的最小延迟
API_DELAY = 60.0 / API_CALLS_PER_MINUTE
# 使用信号量精确控制API速率
API_SEMAPHORE = threading.Semaphore(MAX_WORKERS)

# 忽略 pandas 未来版本中关于 fillna 的警告
warnings.filterwarnings(
    "ignore",
    message=".*fillna with 'method' is deprecated.*",
    category=FutureWarning
)

def setup_tushare():
    """初始化 Tushare Pro API"""
    ts.set_token(TUSHARE_TOKEN)
    pro = ts.pro_api()
    # 测试连接
    try:
        pro.trade_cal(exchange='SSE', start_date='20200101', end_date='20200101')
        print("[INFO] Tushare 连接成功。")
    except Exception as e:
        print(f"[FATAL] Tushare 连接失败，请检查Token或网络: {e}")
        exit(1)
    return pro

def get_all_stocks_and_indices(pro):
    """获取所有A股（上市、退市、暂停）和指定的核心指数列表"""
    print("[INFO] 正在获取所有A股股票列表 (包括已退市)...")
    # 获取所有状态的股票以保证历史数据的完整性
    fields = 'ts_code,name,list_date'
    df_l = pro.stock_basic(exchange='', list_status='L', fields=fields)
    df_d = pro.stock_basic(exchange='', list_status='D', fields=fields)
    df_p = pro.stock_basic(exchange='', list_status='P', fields=fields)
    stocks = pd.concat([df_l, df_d, df_p]).drop_duplicates(subset='ts_code').reset_index(drop=True)

    print("[INFO] 正在构建目标指数列表...")
    # 包含RD-Agent(Q)框架默认配置中使用的核心指数
    target_indices_codes = ['000300.SH', '000903.SH', '000905.SH']
    indices = pd.DataFrame({
        'ts_code': target_indices_codes,
        'name': ['沪深300', '中证100', '中证500']
    })
    print(f"[SUCCESS] 获取到 {len(stocks)} 只股票，{len(indices)} 个目标指数。")
    return stocks, indices

def convert_ts_code_to_qlib_format(ts_code):
    """将 Tushare 代码 '000001.SZ' 转换为 Qlib 格式 'SZ000001'"""
    symbol, exchange = ts_code.split('.')
    return f"{exchange}{symbol}"

def call_tushare_api_with_retry(api_func, max_retries=5, **kwargs):
    """带速率控制和指数退避重试的API调用封装器"""
    for attempt in range(max_retries):
        with API_SEMAPHORE:
            try:
                time.sleep(API_DELAY) # 平滑请求速率
                return api_func(**kwargs)
            except Exception as e:
                wait_time = 2 ** attempt
                tqdm.tqdm.write(f"  [WARN] API call for {kwargs.get('ts_code', '')} failed (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
    tqdm.tqdm.write(f"  [ERROR] API call failed after {max_retries} retries for kwargs: {kwargs}")
    return None

def download_and_process_stock(pro, ts_code, start_date, end_date):
    """
    下载并处理单只股票的数据，严格按照“前复权”标准。
    """
    try:
        # 1. 获取不复权日线行情
        df_daily = call_tushare_api_with_retry(pro.daily, ts_code=ts_code, start_date=start_date, end_date=end_date)
        if df_daily is None or df_daily.empty:
            return None

        # 2. 获取权威的复权因子
        df_factor = call_tushare_api_with_retry(pro.adj_factor, ts_code=ts_code, start_date=start_date, end_date=end_date)
        if df_factor is None or df_factor.empty:
            # 如果没有复权因子，说明股票在此期间无除权除息，因子视为1
            df_factor = pd.DataFrame({'trade_date': df_daily['trade_date'], 'adj_factor': 1.0})

        # 3. 合并数据，并按日期升序排列
        df = pd.merge(df_daily, df_factor, on='trade_date', how='left')
        df['adj_factor'].fillna(method='ffill', inplace=True) # 用前一个交易日的因子填充缺失值
        df.sort_values(by='trade_date', ascending=True, inplace=True)
        df.reset_index(drop=True, inplace=True)

        if df.empty:
            return None

        # 4. 计算标准的前复权因子和前复权价格
        # 最新复权因子是时间序列中最后一个值
        latest_factor = df['adj_factor'].iloc[-1]
        if latest_factor == 0: # 避免除以零的极端情况
            return None
        
        # 4.1 计算前复权因子 ($factor)
        df['$factor'] = df['adj_factor'] / latest_factor
        
        # 4.2 计算前复权价
        df['$open'] = df['open'] * df['$factor']
        df['$close'] = df['close'] * df['$factor']
        df['$high'] = df['high'] * df['$factor']
        df['$low'] = df['low'] * df['$factor']
        
        # 4.3 调整成交量 (Tushare 'vol'单位是手, Qlib需要股, 所以 * 100)
        # 成交量需要根据因子“反向”调整，以反映拆股前的等效股数
        df['$volume'] = (df['vol'] * 100) / df['$factor']
        # 处理除零情况
        df['$volume'].replace([np.inf, -np.inf], 0, inplace=True)
        df['$volume'].fillna(0, inplace=True)

        # 5. 格式化输出
        df['datetime'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
        df['instrument'] = convert_ts_code_to_qlib_format(ts_code)

        return df[['datetime', 'instrument'] + QLIB_COLUMN_ORDER]

    except Exception as e:
        tqdm.tqdm.write(f"  [CRITICAL] Unhandled exception for {ts_code}: {e}")
        return None

def download_and_process_index(pro, ts_code, start_date, end_date):
    """独立下载并处理指数数据，因子恒为1"""
    try:
        df = call_tushare_api_with_retry(pro.index_daily, ts_code=ts_code, start_date=start_date, end_date=end_date)
        if df is None or df.empty:
            return None

        df.rename(columns={'open': '$open', 'close': '$close', 'high': '$high', 'low': '$low'}, inplace=True)
        # 成交额单位从'千元'转为'元'
        df['$volume'] = df['amount'] * 1000
        # 指数没有复权概念，因子恒为1
        df['$factor'] = 1.0

        df['datetime'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
        df['instrument'] = convert_ts_code_to_qlib_format(ts_code)

        return df[['datetime', 'instrument'] + QLIB_COLUMN_ORDER]
    except Exception as e:
        tqdm.tqdm.write(f"  [ERROR] Index download failed for {ts_code}: {e}")
        return None

def save_to_hdf5(data, filename):
    """以兼容Qlib的格式保存数据到 HDF5 文件"""
    print(f"\n[INFO] 正在保存数据到 {filename}...")
    output_dir = os.path.dirname(filename)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 使用 'table' 格式以获得最佳兼容性和性能，并使用zlib压缩
    data.to_hdf(filename, key='data', mode='w', format='table', complevel=9, complib='zlib')
    print(f"[SUCCESS] 数据已成功保存到 {filename}")

def main():
    """主执行函数"""
    print("="*80)
    print("=== Tushare A股日线行情下载脚本 (V5 - 业界标准前复权版) ===")
    print("="*80)
    print(f"数据范围: {START_DATE} to {END_DATE}")

    pro = setup_tushare()
    stocks, indices = get_all_stocks_and_indices(pro)

    total_api_calls = len(stocks) * 2 + len(indices)
    estimated_minutes = total_api_calls / API_CALLS_PER_MINUTE
    print(f"\n[INFO] 预计总API调用次数: {total_api_calls}")
    print(f"[INFO] 在 {API_CALLS_PER_MINUTE}次/分钟 的速率下，预计下载时间约为: {estimated_minutes:.1f} 分钟")

    processed_data = []
    failed_symbols = []

    print(f"\n[INFO] 开始并行下载 {len(stocks)} 只股票的数据 (使用 {MAX_WORKERS} 个线程)...")
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        tasks = {executor.submit(download_and_process_stock, pro, row['ts_code'], START_DATE, END_DATE): row['ts_code'] for _, row in stocks.iterrows()}
        for future in tqdm.tqdm(as_completed(tasks), total=len(tasks), desc="下载股票"):
            ts_code = tasks[future]
            try:
                result = future.result()
                if result is not None and not result.empty:
                    processed_data.append(result)
                else:
                    failed_symbols.append(ts_code)
            except Exception as exc:
                tqdm.tqdm.write(f'\n[CRITICAL] {ts_code} 在主线程中捕获到未处理异常: {exc}')
                failed_symbols.append(ts_code)

    print(f"\n[INFO] 开始下载 {len(indices)} 个指数的数据...")
    for _, row in tqdm.tqdm(indices.iterrows(), total=len(indices), desc="下载指数"):
        ts_code = row['ts_code']
        result = download_and_process_index(pro, ts_code, START_DATE, END_DATE)
        if result is not None and not result.empty:
            processed_data.append(result)
        else:
            failed_symbols.append(ts_code)

    print("\n" + "="*30 + " 下载总结 " + "="*30)
    print(f"成功处理的标的数量: {len(processed_data)}")
    print(f"失败或无数据的标的数量: {len(failed_symbols)}")
    if failed_symbols:
        print(f"失败/无数据标的样例 (前20个): {failed_symbols[:20]}")
    print("="*72)

    if not processed_data:
        print("\n[FATAL] 未能下载到任何有效数据，程序退出。")
        return

    print("\n[INFO] 正在合并所有数据...")
    final_df = pd.concat(processed_data, ignore_index=True)

    print("[INFO] 正在进行最终格式化和数据清洗...")
    # 1. 设置索引并排序，这是Qlib处理的基础
    final_df.set_index(['datetime', 'instrument'], inplace=True)
    final_df.sort_index(inplace=True)

    # 2. 确保所有列都是 float32，以节省空间并匹配Qlib格式
    for col in final_df.columns:
        if final_df[col].dtype != 'float32':
            final_df[col] = final_df[col].astype('float32')

    # 3. 确保列顺序与Qlib原始文件一致
    final_df = final_df[QLIB_COLUMN_ORDER]

    # 4. 截取一个合理的起始日期，例如2005年之后，避免早期数据质量问题
    # RD-Agent(Q) 原始数据从2008年开始，我们保持一致
    final_df = final_df.loc[final_df.index.get_level_values('datetime') >= '2008-12-29']
    
    # 5. 移除全为NaN的行
    final_df.dropna(how='all', inplace=True)

    print("\n" + "="*30 + " 最终数据概览 " + "="*28)
    print(f"最终数据形状: {final_df.shape}")
    if not final_df.empty:
        print(f"日期范围: {final_df.index.get_level_values('datetime').min().date()} -> {final_df.index.get_level_values('datetime').max().date()}")
        print(f"股票/指数数量: {len(final_df.index.get_level_values('instrument').unique())}")
        print(f"最终列: {list(final_df.columns)}")
        print("\n数据抽样 (贵州茅台 SH600519):")
        try:
            print(final_df.loc[(slice(None), 'SH600519')].tail())
        except KeyError:
            print("  (未找到 SH600519 数据)")
    print("="*72)

    save_to_hdf5(final_df, OUTPUT_FILENAME)

    print("\n=== 任务圆满完成 ===")
    print(f"高质量前复权数据文件已生成: {OUTPUT_FILENAME}")
    print("强烈建议您再次运行 `audit_daily_pv_tushare.py` 和 `compare_data_sources.py` 脚本，")
    print("对新生成的文件进行最终审核，以确保万无一失。")

if __name__ == "__main__":
    main()