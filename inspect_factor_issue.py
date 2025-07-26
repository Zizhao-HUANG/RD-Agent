#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据问题深度检查脚本

功能:
从一个给定的HDF5数据文件中，提取指定股票的完整历史数据，
并保存为CSV格式，以便进行手动分析和问题诊断。
这对于理解复权因子为何非单调至关重要。
"""

import pandas as pd
import numpy as np
import argparse
import os

def print_section(title):
    """打印格式化的节标题"""
    print("\n" + "="*80)
    print(f"=== {title.center(74)} ===")
    print("="*80)

def inspect_data(filepath, output_csv_path):
    """
    执行数据检查并生成报告。
    """
    print_section(f"开始检查文件: {filepath}")

    # 1. 加载数据
    print(f"[INFO] 正在加载数据文件: {filepath}...")
    try:
        df = pd.read_hdf(filepath, key='data')
        print(f"[SUCCESS] 文件加载成功，总行数: {len(df)}")
    except Exception as e:
        print(f"[FATAL] 加载文件失败: {e}")
        return

    # 2. 选取要深入调查的股票代码
    # 这些代码是从您的审核报告中发现'非单调'的股票里挑选出来的典型代表
    stocks_to_inspect = [
        'SH601101', # 昊华能源
        'SH600230', # 沧州大化
        'SH688551', # 科思科技
        'SH688005', # 容百科技
        'SZ000153'  # 丰原药业
    ]
    print(f"[INFO] 将提取以下股票的完整历史进行分析: {stocks_to_inspect}")

    # 3. 提取并整合数据
    inspection_dfs = []
    for stock_code in stocks_to_inspect:
        print(f"  -> 正在提取 {stock_code} 的数据...")
        try:
            # 提取该股票的所有数据
            stock_df = df.loc[(slice(None), stock_code)].copy()
            
            # 增加一个分隔符，以便在CSV中清晰地区分不同股票
            separator = pd.DataFrame([f"--- Data for {stock_code} ---"], columns=['$open'])
            inspection_dfs.append(separator)
            
            # 将索引转为列，方便在CSV中查看
            inspection_dfs.append(stock_df.reset_index())

        except KeyError:
            print(f"  [WARNING] 在数据文件中未找到 {stock_code}。")
            separator = pd.DataFrame([f"--- Data for {stock_code} (NOT FOUND) ---"], columns=['$open'])
            inspection_dfs.append(separator)

    if not inspection_dfs:
        print("[ERROR] 未能提取到任何待分析的数据。")
        return

    # 4. 合并并保存到CSV
    print(f"\n[INFO] 正在将提取的数据合并并保存到: {output_csv_path}")
    final_report_df = pd.concat(inspection_dfs, ignore_index=True)
    
    # 设置浮点数显示格式，避免科学计数法
    pd.options.display.float_format = '{:.6f}'.format
    final_report_df.to_csv(output_csv_path, index=False, float_format='%.6f')

    print(f"[SUCCESS] 检查报告已生成！请用Excel或文本编辑器打开 '{output_csv_path}' 进行分析。")
    print_section("检查完成")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="深度检查HDF5数据文件中的复权因子问题。")
    parser.add_argument("filepath", type=str, help="要检查的HDF5数据文件路径。")
    parser.add_argument(
        "--output", 
        type=str, 
        default="inspection_report.csv", 
        help="输出的CSV报告文件名 (默认为: inspection_report.csv)"
    )
    args = parser.parse_args()
    
    inspect_data(args.filepath, args.output)