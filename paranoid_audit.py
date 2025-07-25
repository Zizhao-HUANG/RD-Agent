#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
paranoid_audit.py: 对新生成的 daily_pv.h5 文件进行偏执狂级别的审计。

本脚本将同时加载原始文件和新生成的文件，进行地狱级、逐项、并排的对比，
以确保新文件在结构、元数据、数据类型和核心数值逻辑上与原始文件完全兼容，
并验证其扩展部分（新日期、新股票）的合理性。
"""

import pandas as pd
import h5py
import numpy as np
import sys
from tqdm import tqdm

# --- 配置区 ---
# 请将路径替换为你的实际文件路径
OLD_FILE_PATH = "/home/shenzi/RD-Agent/git_ignore_folder/factor_implementation_source_data/daily_pv.h5"
NEW_FILE_PATH = "/home/shenzi/RD-Agent/daily_pv_tushare_rebuilt.h5" # 假设新文件在当前目录

# --- 辅助函数与常量 ---
class Color:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'

# 检查计数器
CHECKS_PASSED = 0
CHECKS_FAILED = 0

def print_check(title, condition, pass_msg="一致", fail_msg="不一致", details=""):
    """打印检查结果，并更新全局计数器。"""
    global CHECKS_PASSED, CHECKS_FAILED
    print(f"\n--- {title} ---")
    if condition:
        print(f"{Color.GREEN}[PASS]{Color.END} {pass_msg}")
        CHECKS_PASSED += 1
    else:
        print(f"{Color.RED}[FAIL]{Color.END} {fail_msg}")
        if details:
            print(details)
        CHECKS_FAILED += 1
    return condition

def compare_and_report(title, old_val, new_val, details_formatter=None):
    """比较两个值并报告结果。"""
    condition = (old_val == new_val)
    details = ""
    if not condition:
        if details_formatter:
            details = details_formatter(old_val, new_val)
        else:
            details = f"  - 原始值: {old_val}\n  -   新值: {new_val}"
    pass_msg = f"一致: {old_val}"
    fail_msg = "不一致!"
    return print_check(title, condition, pass_msg, fail_msg, details)

# --- 主审计流程 ---
def main():
    print("="*80)
    print("                P A R A N O I D   A U D I T   S T A R T S")
    print("="*80)
    print(f"原始文件: {OLD_FILE_PATH}")
    print(f"新文件:   {NEW_FILE_PATH}")

    # === 1. 文件存在性与基础加载 ===
    print("\n\n" + "="*25 + " 1. 基础加载检查 " + "="*25)
    try:
        df_old = pd.read_hdf(OLD_FILE_PATH, key="data")
        print(f"{Color.GREEN}[OK]{Color.END} 成功加载原始文件。")
    except Exception as e:
        print(f"{Color.RED}[FATAL]{Color.END} 无法加载原始文件: {e}")
        sys.exit(1)

    try:
        df_new = pd.read_hdf(NEW_FILE_PATH, key="data")
        print(f"{Color.GREEN}[OK]{Color.END} 成功加载新文件。")
    except Exception as e:
        print(f"{Color.RED}[FATAL]{Color.END} 无法加载新文件: {e}")
        sys.exit(1)

    # === 2. HDF5 底层结构检查 (偏执狂模式) ===
    print("\n\n" + "="*25 + " 2. HDF5 底层结构检查 " + "="*25)
    with h5py.File(OLD_FILE_PATH, 'r') as f_old, h5py.File(NEW_FILE_PATH, 'r') as f_new:
        old_keys = set(f_old['data'].keys())
        new_keys = set(f_new['data'].keys())
        compare_and_report("HDF5 'data' 组内部 Keys", old_keys, new_keys)

        # 检查每个内部数组的形状和类型
        if old_keys == new_keys:
            for k in sorted(list(old_keys)):
                d_old = f_old[f'data/{k}']
                d_new = f_new[f'data/{k}']
                # 只比较元数据数组，忽略巨大的 block_values
                if 'values' not in k and 'label' not in k:
                    compare_and_report(f"  - 内部 Key '{k}' Shape", d_old.shape, d_new.shape)
                    compare_and_report(f"  - 内部 Key '{k}' Dtype", d_old.dtype, d_new.dtype)

    # === 3. DataFrame 顶层结构检查 ===
    print("\n\n" + "="*25 + " 3. DataFrame 顶层结构检查 " + "="*25)
    compare_and_report("列名顺序和内容", list(df_old.columns), list(df_new.columns))
    compare_and_report("列数据类型", df_old.dtypes.to_dict(), df_new.dtypes.to_dict())
    compare_and_report("索引类型", type(df_old.index), type(df_new.index))
    compare_and_report("索引名称", df_old.index.names, df_new.index.names)

    # === 4. MultiIndex 'datetime' 级别检查 ===
    print("\n\n" + "="*25 + " 4. 'datetime' 索引检查 " + "="*25)
    dt_old = df_old.index.levels[0]
    dt_new = df_new.index.levels[0]
    compare_and_report("DatetimeIndex Dtype", dt_old.dtype, dt_new.dtype)
    print_check(
        "新数据日期范围是否完全覆盖旧数据",
        dt_new.min() <= dt_old.min() and dt_new.max() >= dt_old.max(),
        f"是: 新({dt_new.min().date()}~{dt_new.max().date()}) vs 旧({dt_old.min().date()}~{dt_old.max().date()})",
        "否!",
        f"  - 新范围: {dt_new.min().date()} ~ {dt_new.max().date()}\n  - 旧范围: {dt_old.min().date()} ~ {dt_old.max().date()}"
    )
    
    # 检查在旧日期范围内，新数据是否引入了交易日空缺
    old_range_dates_in_new = dt_new[(dt_new >= dt_old.min()) & (dt_new <= dt_old.max())]
    missing_dates = dt_old.difference(old_range_dates_in_new)
    print_check(
        "旧日期范围内无交易日丢失",
        len(missing_dates) == 0,
        "旧范围内的所有交易日都存在于新数据中。",
        f"新数据在旧日期范围内丢失了 {len(missing_dates)} 个交易日!",
        f"  - 丢失日期样例: {missing_dates[:5].strftime('%Y-%m-%d').to_list()}"
    )

    # === 5. MultiIndex 'instrument' 级别检查 ===
    print("\n\n" + "="*25 + " 5. 'instrument' 索引检查 " + "="*25)
    inst_old = df_old.index.levels[1]
    inst_new = df_new.index.levels[1]
    compare_and_report("InstrumentIndex Dtype", inst_old.dtype, inst_new.dtype)
    
    missing_instruments = inst_old.difference(inst_new)
    print_check(
        "新数据股票池是否为旧数据的超集",
        len(missing_instruments) == 0,
        f"是: 新({len(inst_new)}) vs 旧({len(inst_old)})",
        f"否! 新数据丢失了 {len(missing_instruments)} 个旧股票/指数!",
        f"  - 丢失代码样例: {list(missing_instruments[:5])}"
    )

    # === 6. 核心数据逻辑与健全性检查 ===
    print("\n\n" + "="*25 + " 6. 核心数据逻辑检查 " + "="*25)
    
    # 6.1 $factor 检查
    print("\n--- 6.1 $factor (复权因子) 逻辑检查 ---")
    # 检查指数的 $factor 是否符合预期
    old_indices = [i for i in inst_old if i.startswith(('SH000', 'SZ000'))]
    common_indices = [i for i in old_indices if i in inst_new]
    
    # 特例：中证500 (SH000905) 在旧数据中为 NaN
    factor_sh000905_old_is_nan = df_old.loc[(slice(None), 'SH000905'), '$factor'].isnull().all()
    factor_sh000905_new_is_nan = df_new.loc[(slice(None), 'SH000905'), '$factor'].isnull().all()
    print_check("  - 指数 SH000905 的 $factor 是否为 NaN", 
                factor_sh000905_old_is_nan == factor_sh000905_new_is_nan,
                f"是, 均为 {factor_sh000905_new_is_nan}",
                f"否! 旧: {factor_sh000905_old_is_nan}, 新: {factor_sh000905_new_is_nan}")

    # 其他公共指数的 $factor 是否为 1.0
    other_common_indices = [i for i in common_indices if i != 'SH000905']
    if other_common_indices:
        old_factor_sum = df_old.loc[(slice(None), other_common_indices), '$factor'].sum()
        old_factor_count = df_old.loc[(slice(None), other_common_indices), '$factor'].count()
        new_factor_sum = df_new.loc[(slice(None), other_common_indices), '$factor'].sum()
        new_factor_count = df_new.loc[(slice(None), other_common_indices), '$factor'].count()
        
        is_one_old = np.allclose(old_factor_sum, old_factor_count)
        is_one_new = np.allclose(new_factor_sum, new_factor_count)
        
        print_check("  - 其他公共指数的 $factor 是否为 1.0",
                    is_one_new,
                    "是, 新数据中的指数 $factor 均为 1.0",
                    "否! 新数据中的指数 $factor 不全为 1.0",
                    f"  - 旧数据是否为1.0: {is_one_old}")

    # 检查股票的 $factor 是否单调递增 (这是后复权因子的核心属性)
    print("  - 检查股票 $factor 的单调性 (随机抽样200只)...")
    new_stocks = [i for i in inst_new if not i.startswith(('SH000', 'SZ000'))]
    sample_stocks = np.random.choice(new_stocks, min(200, len(new_stocks)), replace=False)
    non_monotonic_count = 0
    for stock in tqdm(sample_stocks, desc="检查Factor单调性", ncols=80):
        factors = df_new.loc[(slice(None), stock), '$factor'].dropna()
        if not factors.is_monotonic_increasing:
            non_monotonic_count += 1
    print_check(
        "  - 股票 $factor 是否为单调递增",
        non_monotonic_count == 0,
        "是, 抽样检查的所有股票 $factor 均为单调递增。",
        f"否! 在抽样的 {len(sample_stocks)} 只股票中, 发现 {non_monotonic_count} 只股票的 $factor 非单调!"
    )

    # 6.2 价格健全性检查
    print("\n--- 6.2 价格健全性检查 (low <= open/close <= high) ---")
    violations_new = df_new[(df_new['$open'] < df_new['$low']) | (df_new['$open'] > df_new['$high']) | \
                            (df_new['$close'] < df_new['$low']) | (df_new['$close'] > df_new['$high'])]
    violation_rate = len(violations_new) / len(df_new.dropna()) if len(df_new.dropna()) > 0 else 0
    print_check(
        "价格关系是否健全",
        violation_rate < 0.0001, # 允许万分之一以下的误差
        f"是, 价格关系不健全的数据点占比极低 ({violation_rate:.6%})",
        f"否! 价格关系不健全的数据点占比过高 ({violation_rate:.6%})",
        f"  - 共发现 {len(violations_new)} 条违规记录。"
    )

    # 6.3 成交量/额健全性检查
    print("\n--- 6.3 成交量健全性检查 ---")
    negative_volume = df_new[df_new['$volume'] < 0]
    print_check(
        "$volume 是否全部非负",
        len(negative_volume) == 0,
        "是, 所有成交量数据均 >= 0",
        f"否! 发现 {len(negative_volume)} 条负成交量记录!"
    )

    # === 7. 数据重叠区数值差异分析 (终极偏执) ===
    print("\n\n" + "="*25 + " 7. 重叠数据数值差异分析 " + "="*25)
    common_index = df_old.index.intersection(df_new.index)
    print(f"找到 {len(common_index)} 条重叠记录 (相同日期和代码) 用于数值比较。")

    if len(common_index) > 0:
        df_old_common = df_old.loc[common_index].dropna()
        df_new_common = df_new.loc[common_index].dropna()
        
        # 重新对齐，因为 dropna 可能导致索引不一致
        common_after_dropna = df_old_common.index.intersection(df_new_common.index)
        df_old_common = df_old_common.loc[common_after_dropna]
        df_new_common = df_new_common.loc[common_after_dropna]

        print("计算重叠区域各列的平均绝对百分比误差 (MAPE)...")
        for col in ['$open', '$close', '$high', '$low', '$volume', '$factor']:
            # 避免除以零
            abs_error = np.abs(df_new_common[col] - df_old_common[col])
            mape = np.mean(abs_error / np.abs(df_old_common[col]).replace(0, 1)) * 100
            
            print_check(
                f"  - 列 '{col}' 的数值相似度",
                mape < 2.0, # 允许 2% 的平均差异，因为数据源不同
                f"高度相似, MAPE = {mape:.4f}%",
                f"差异过大, MAPE = {mape:.4f}%",
            )
    else:
        print(f"{Color.YELLOW}[SKIP]{Color.END} 未找到重叠数据，无法进行数值差异分析。")


    # === 8. 最终审计报告 ===
    print("\n\n" + "="*30 + " 最终审计报告 " + "="*30)
    print(f"总计检查项: {CHECKS_PASSED + CHECKS_FAILED}")
    print(f"  - {Color.GREEN}通过: {CHECKS_PASSED}{Color.END}")
    print(f"  - {Color.RED}失败: {CHECKS_FAILED}{Color.END}")

    if CHECKS_FAILED == 0:
        print(f"\n{Color.GREEN}结论: [高度兼容] 新文件通过了所有偏执审计。文件结构、元数据和核心逻辑与原始文件高度一致，且数据扩展部分合理。可以安全替换。{Color.END}")
    else:
        print(f"\n{Color.RED}结论: [存在风险] 新文件未能通过所有审计。请仔细检查上述 [FAIL] 项目。在解决这些问题之前，不建议替换原始文件。{Color.END}")
    print("="*80)


if __name__ == "__main__":
    main()