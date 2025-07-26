#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 Tushare 下载 A 股日线行情数据 (V4 - 复权逻辑修正版)

目标：生成一个与 Qlib 原始 daily_pv.h5 文件在数据结构和数值逻辑上
      都高度兼容，同时扩展了股票池和时间范围的高质量数据文件。

核心修正：
1. [CRITICAL] 复权逻辑修正：
   - 明确Tushare的`adj_factor`为前复权因子。
   - 新增逻辑：将获取的`adj_factor`转换为以首日为基准的后复权因子。
   - (df['$factor'] = df['adj_factor'] / df['adj_factor'].iloc[0])
   - 此修改旨在彻底解决 `$factor` 非单调和数值巨大偏差的问题。
2. [CRITICAL] HDF5 存储格式修正：
   - 将 `to_hdf` 的 `format` 参数从 'table' 改为 'fixed'。
   - 确保新文件的HDF5底层结构与原始Qlib文件完全一致。
3. [KEPT] 指数处理逻辑、列序修正等优化保持不变。
4. [NOTE] 暂未处理股票池不完整（退市股）的问题，此版本仍可能丢失部分历史股票。
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

# 忽略 pandas 未来版本中关于 fillna 的警告
warnings.filterwarnings(
    "ignore",
    message=".*fillna with 'method' is deprecated.*",
    category=FutureWarning
)

# --- 配置区 ---
# 请将 "your_token_here" 替换为你的真实 Tushare Token
TUSHARE_TOKEN = "xxx"
START_DATE = '19990101'
END_DATE = datetime.now().strftime('%Y%m%d')
OUTPUT_FILENAME = "daily_pv_tushare_rebuilt_v4.h5"
# 原始Qlib文件的标准列顺序
QLIB_COLUMN_ORDER = ['$open', '$close', '$high', '$low', '$volume', '$factor']

# --- 性能优化参数 ---
# Tushare Pro普通用户限制为 200次/分钟
API_CALLS_PER_MINUTE = 200
MAX_WORKERS = 14  # 并行下载的线程数
# 计算每次API调用的最小延迟
API_DELAY = 60.0 / API_CALLS_PER_MINUTE
# 使用信号量精确控制API速率
API_SEMAPHORE = threading.Semaphore(MAX_WORKERS)

def setup_tushare():
    """初始化 Tushare"""
    ts.set_token(TUSHARE_TOKEN)
    return ts.pro_api()

def get_all_stocks_and_indices(pro):
    """获取所有 A 股股票和【指定】的指数列表"""
    print("正在获取所有A股股票列表...")
    # 注意：此逻辑仅获取当前上市的股票，可能导致与包含退市股的旧数据不完全匹配
    stocks = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,list_date')
    print("正在构建目标指数列表...")
    # 仅包含 RD-Agent 框架默认配置中使用的核心指数
    target_indices_codes = ['000300.SH', '000903.SH', '000905.SH']
    indices = pd.DataFrame({'ts_code': target_indices_codes, 'name': ['CSI 300', 'CSI 100', 'CSI 500']})
    print(f"获取到 {len(stocks)} 只股票，{len(indices)} 个目标指数")
    return stocks, indices

def convert_ts_code_to_qlib_format(ts_code):
    """将 Tushare 股票代码 '000001.SZ' 转换为 Qlib 格式 'SZ000001'"""
    symbol, exchange = ts_code.split('.')
    return f"{exchange}{symbol}"

def call_tushare_api_with_retry(api_func, max_retries=3, **kwargs):
    """带速率控制和重试机制的API调用封装器"""
    for attempt in range(max_retries):
        with API_SEMAPHORE:
            try:
                # 每次调用前都稍作等待，以平滑请求速率
                time.sleep(API_DELAY)
                return api_func(**kwargs)
            except Exception as e:
                tqdm.tqdm.write(f"  [WARN] API call failed (attempt {attempt + 1}/{max_retries}): {e}. Retrying...")
                time.sleep(2 ** attempt) # 指数退避
    tqdm.tqdm.write(f"  [ERROR] API call failed after {max_retries} retries for kwargs: {kwargs}")
    return None

def download_and_process_stock(pro, ts_code, start_date, end_date):
    """
    下载并处理单只股票的数据，采用权威复权因子正向计算。
    """
    try:
        # 1. 获取不复权日线行情
        df_daily = call_tushare_api_with_retry(pro.daily, ts_code=ts_code, start_date=start_date, end_date=end_date)
        if df_daily is None or df_daily.empty:
            return None

        # 2. 获取权威的复权因子
        df_factor = call_tushare_api_with_retry(pro.adj_factor, ts_code=ts_code, start_date=start_date, end_date=end_date)
        if df_factor is None or df_factor.empty:
            return None

        # 3. 合并数据
        df = pd.merge(df_daily, df_factor, on='trade_date')
        if df.empty:
            return None
        
        # 数据是倒序的，需要先正序排列才能正确计算后复权因子
        df.sort_values(by='trade_date', ascending=True, inplace=True)
        df.reset_index(drop=True, inplace=True)

        # 4. 【关键修正】计算真正的后复权因子
        # Tushare的`adj_factor`是前复权因子，需要转换为后复权因子
        # 后复权因子 = 当日的前复权因子 / 历史第一天的前复权因子
        first_factor = df['adj_factor'].iloc[0]
        if first_factor == 0: # 避免除以零
            return None
        df['$factor'] = df['adj_factor'] / first_factor

        # 5. 正向计算Qlib所需的列
        df['$open'] = df['open'] * df['$factor']
        df['$close'] = df['close'] * df['$factor']
        df['$high'] = df['high'] * df['$factor']
        df['$low'] = df['low'] * df['$factor']
        # 成交量单位：Tushare 'vol'是手，Qlib需要股，所以 * 100
        df['$volume'] = np.where(df['$factor'] != 0, (df['vol'] * 100) / df['$factor'], 0)

        # 6. 格式化
        df['datetime'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
        df['instrument'] = convert_ts_code_to_qlib_format(ts_code)

        return df[['datetime', 'instrument'] + QLIB_COLUMN_ORDER]

    except Exception as e:
        tqdm.tqdm.write(f"  [ERROR] Unhandled exception for {ts_code}: {e}")
        return None

def download_and_process_index(pro, ts_code, start_date, end_date):
    """独立下载并处理指数数据"""
    try:
        df = call_tushare_api_with_retry(pro.index_daily, ts_code=ts_code, start_date=start_date, end_date=end_date)
        if df is None or df.empty:
            tqdm.tqdm.write(f"  [WARN] {ts_code}: 无指数数据")
            return None

        df.rename(columns={'open': '$open', 'close': '$close', 'high': '$high', 'low': '$low'}, inplace=True)
        # 成交额单位从'千元'转为'元'
        df['$volume'] = df['amount'] * 1000

        # 根据Qlib惯例，硬编码指数的复权因子
        if ts_code == '000905.SH': # 中证500在旧数据中为NaN
            df['$factor'] = np.nan
        else:
            df['$factor'] = 1.0

        df['datetime'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
        df['instrument'] = convert_ts_code_to_qlib_format(ts_code)

        tqdm.tqdm.write(f"  [INFO] {ts_code}: 下载了 {len(df)} 条指数记录")
        return df[['datetime', 'instrument'] + QLIB_COLUMN_ORDER]
    except Exception as e:
        tqdm.tqdm.write(f"  [ERROR] {ts_code}: 指数下载失败 - {e}")
        return None

def save_to_hdf5(data, filename):
    """保存数据到 HDF5 文件"""
    print(f"\n正在保存到 {filename}...")
    output_dir = os.path.dirname(filename)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 【关键修正】使用 'fixed' 格式以匹配原始文件的HDF5底层结构
    data.to_hdf(filename, key='data', mode='w', format='fixed', complevel=9, complib='zlib')
    print(f"数据已成功保存到 {filename}")

def main():
    """主函数"""
    print("=== Tushare A股数据下载脚本 (V4 - 复权逻辑修正版) ===")
    print(f"数据范围: {START_DATE} to {END_DATE}")

    pro = setup_tushare()
    stocks, indices = get_all_stocks_and_indices(pro)

    # 预估下载时间
    total_api_calls = len(stocks) * 2 + len(indices) # 每只股票2次API，每个指数1次
    estimated_minutes = total_api_calls / API_CALLS_PER_MINUTE
    print(f"\n预计总API调用次数: {total_api_calls}")
    print(f"在 {API_CALLS_PER_MINUTE}次/分钟 的速率下，预计下载时间约为: {estimated_minutes:.1f} 分钟")

    processed_stocks = []
    failed_stocks = []

    print(f"\n开始并行下载 {len(stocks)} 只股票的数据 (使用 {MAX_WORKERS} 个线程)...")
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        tasks = {executor.submit(download_and_process_stock, pro, row['ts_code'], START_DATE, END_DATE): row['ts_code'] for _, row in stocks.iterrows()}

        for future in tqdm.tqdm(as_completed(tasks), total=len(tasks), desc="下载股票"):
            ts_code = tasks[future]
            try:
                result = future.result()
                if result is not None and not result.empty:
                    processed_stocks.append(result)
                else:
                    failed_stocks.append(ts_code)
            except Exception as exc:
                tqdm.tqdm.write(f'\n[CRITICAL] {ts_code} 在主线程中捕获到未处理异常: {exc}')
                failed_stocks.append(ts_code)

    # --- 下载指数数据 (串行执行以避免速率问题) ---
    print(f"\n开始下载 {len(indices)} 个指数的数据...")
    processed_indices = []
    failed_indices = []
    for _, row in tqdm.tqdm(indices.iterrows(), total=len(indices), desc="下载指数"):
        ts_code = row['ts_code']
        result = download_and_process_index(pro, ts_code, START_DATE, END_DATE)
        if result is not None and not result.empty:
            processed_indices.append(result)
        else:
            failed_indices.append(ts_code)

    print("\n--- 下载总结 ---")
    print(f"股票成功: {len(processed_stocks)}, 失败: {len(failed_stocks)}")
    print(f"指数成功: {len(processed_indices)}, 失败: {len(failed_indices)}")
    if failed_stocks: print(f"失败的股票 (前10个): {failed_stocks[:10]}")
    if failed_indices: print(f"失败的指数: {failed_indices}")

    # --- 数据处理与合并 ---
    all_data_list = processed_stocks + processed_indices
    if not all_data_list:
        print("没有生成任何数据，程序退出。")
        return

    print("\n正在合并所有数据...")
    final_df = pd.concat(all_data_list, ignore_index=True)

    # --- 最终格式化 ---
    print("\n正在进行最终格式化...")
    # 1. 设置索引并排序
    final_df = final_df.set_index(['datetime', 'instrument']).sort_index()

    # 2. 确保所有列都是 float32
    for col in final_df.columns:
        if final_df[col].dtype != 'float32':
            final_df[col] = final_df[col].astype('float32')

    # 3. 确保列顺序与Qlib原始文件一致
    final_df = final_df[QLIB_COLUMN_ORDER]

    # 4. 截取与Qlib兼容的起始日期
    final_df = final_df.loc[final_df.index.get_level_values('datetime') >= '2008-12-29']

    print(f"最终数据形状: {final_df.shape}")
    if not final_df.empty:
        print(f"日期范围: {final_df.index.levels[0].min().date()} 到 {final_df.index.levels[0].max().date()}")
        print(f"股票/指数数量: {len(final_df.index.levels[1])}")
        print(f"最终列顺序: {list(final_df.columns)}")

    save_to_hdf5(final_df, OUTPUT_FILENAME)

    print(f"\n=== 任务完成 ===")
    print(f"输出文件: {OUTPUT_FILENAME}")
    print("建议再次运行 paranoid_audit.py 脚本进行最终审核。")

if __name__ == "__main__":
    main()