import pandas as pd
import numpy as np
import h5py
import argparse
from tqdm import tqdm

# 设置Pandas显示选项以便观察
pd.set_option('display.width', 200)
pd.set_option('display.max_rows', 100)
pd.set_option('display.max_columns', 10)

def print_section(title):
    """打印格式化的节标题"""
    print("\n" + "="*80)
    print(f"=== {title.center(74)} ===")
    print("="*80)

def load_data(filepath):
    """
    从HDF5文件加载数据到Pandas DataFrame。
    该结构是RD-Agent(Q) / Qlib的典型格式。
    """
    print(f"\n[INFO] 正在加载数据: {filepath} ...")
    try:
        with h5py.File(filepath, 'r') as f:
            if 'data' in f:
                group = f['data']
                # 这种结构是pandas to_hdf的标准'table'格式
                df = pd.read_hdf(filepath, key='data')
                print(f"[SUCCESS] 文件加载成功。")
                return df
            else:
                print(f"[ERROR] HDF5文件中未找到 'data' 组。")
                return None
    except Exception as e:
        print(f"[ERROR] 加载文件时出错: {e}")
        return None

def compare_metadata(df_old, df_new, name_old, name_new):
    """比较两个DataFrame的元数据"""
    print_section("1. 元数据对比")
    
    print(f"--- {name_old} (原始) ---")
    print(f"  - 数据形状: {df_old.shape}")
    print(f"  - 日期范围: {df_old.index.get_level_values('datetime').min()} -> {df_old.index.get_level_values('datetime').max()}")
    instruments_old = df_old.index.get_level_values('instrument').unique()
    print(f"  - 标的数量: {len(instruments_old)}")

    print(f"\n--- {name_new} (新建) ---")
    print(f"  - 数据形状: {df_new.shape}")
    print(f"  - 日期范围: {df_new.index.get_level_values('datetime').min()} -> {df_new.index.get_level_values('datetime').max()}")
    instruments_new = df_new.index.get_level_values('instrument').unique()
    print(f"  - 标的数量: {len(instruments_new)}")

    print("\n--- 标的集合差异 ---")
    lost_instruments = instruments_old.difference(instruments_new)
    added_instruments = instruments_new.difference(instruments_old)
    print(f"  - 原始数据中有，但新数据中没有的标的 (丢失): {len(lost_instruments)} 个")
    if len(lost_instruments) > 0:
        print(f"    - 样例: {list(lost_instruments[:10])}")
    
    print(f"  - 新数据中有，但原始数据中没有的标的 (新增): {len(added_instruments)} 个")
    if len(added_instruments) > 0:
        print(f"    - 样例: {list(added_instruments[:10])}")

def check_factor_monotonicity(df, name):
    """检查复权因子的单调性"""
    print_section(f"4. 复权因子 ($factor) 单调性检查 - {name}")
    
    instruments = df.index.get_level_values('instrument').unique()
    non_monotonic_stocks = []
    
    # 随机抽样以提高效率，或设置为 instruments 进行全量检查
    sample_instruments = np.random.choice(instruments, min(500, len(instruments)), replace=False)
    
    print(f"[INFO] 抽查 {len(sample_instruments)} 个标的...")
    for inst in tqdm(sample_instruments, desc=f"检查 {name} 单调性"):
        factor_series = df.loc[(slice(None), inst), '$factor'].dropna()
        # 前复权因子应为单调非增
        if not factor_series.is_monotonic_decreasing:
            non_monotonic_stocks.append(inst)
            
    if non_monotonic_stocks:
        print(f"[WARNING] 在 {name} 数据中发现 {len(non_monotonic_stocks)}/{len(sample_instruments)} 个抽样标的 $factor 非单调非增！")
        print(f"  - 样例: {non_monotonic_stocks[:10]}")
    else:
        print(f"[SUCCESS] 在 {name} 数据的抽样标的中，$factor 均符合单调非增特性。")

def check_index_factor(df, name):
    """检查指数的复权因子是否为1"""
    print_section(f"5. 指数因子检查 - {name}")
    
    # 指数代码通常不包含数字688(科创板), 60(沪A), 00(深A), 30(创A)
    # 这是一个粗略的判断，但对常见指数有效
    index_codes = [i for i in df.index.get_level_values('instrument').unique() if not (i.startswith('SH6') or i.startswith('SZ0') or i.startswith('SZ3') or i.startswith('BJ'))]
    
    if not index_codes:
        print("[INFO] 未找到明确的指数代码。")
        return

    df_indices = df.loc[(slice(None), index_codes), '$factor'].dropna()
    
    non_one_factors = df_indices[df_indices != 1.0]
    
    if not non_one_factors.empty:
        print(f"[WARNING] 在 {name} 数据中发现指数的 $factor 不为 1.0！")
        print(f"  - 涉及的指数数量: {len(non_one_factors.index.get_level_values('instrument').unique())}")
        print(f"  - 异常因子值统计:\n{non_one_factors.describe()}")
        print(f"  - 异常样例:\n{non_one_factors.head()}")
    else:
        print(f"[SUCCESS] 在 {name} 数据中，所有指数的 $factor 均为 1.0。")


def main(old_path, new_path):
    df_old = load_data(old_path)
    df_new = load_data(new_path)

    if df_old is None or df_new is None:
        print("\n[FATAL] 数据加载失败，无法进行比较。")
        return

    # 1. 元数据对比
    compare_metadata(df_old, df_new, old_path.split('/')[-1], new_path.split('/')[-1])

    # 2. 创建公共数据集用于直接比较
    print_section("2. 创建公共数据集")
    common_dates = df_old.index.get_level_values('datetime').intersection(df_new.index.get_level_values('datetime'))
    common_instruments = df_old.index.get_level_values('instrument').intersection(df_new.index.get_level_values('instrument'))
    
    print(f"[INFO] 共有 {len(common_dates)} 个共同交易日。")
    print(f"[INFO] 共有 {len(common_instruments)} 个共同标的。")

    common_idx = pd.MultiIndex.from_product([common_dates, common_instruments], names=['datetime', 'instrument'])
    
    # 使用 reindex 保证对齐，缺失处为 NaN
    old_common = df_old.reindex(common_idx)
    new_common = df_new.reindex(common_idx)
    
    # 移除在新旧数据中都完全是NaN的行，这些是共同的非交易日/未上市日
    old_common.dropna(how='all', inplace=True)
    new_common = new_common.reindex(old_common.index)

    print(f"[INFO] 创建的公共数据集形状: {old_common.shape}")

    # 3. 核心验证：价格格式与复权关系
    print_section("3. 核心验证：价格格式与复权关系")
    print("[HYPOTHESIS] 假设: 新数据为未复权价, 旧数据为前复权价。")
    print("[VERIFICATION] 验证: new_price * new_factor ≈ old_price")

    # 创建一个DataFrame用于对比
    compare_df = pd.DataFrame({
        'old_close': old_common['$close'],
        'new_raw_close': new_common['$close'],
        'new_factor': new_common['$factor']
    })
    
    # 计算新数据复权后的价格
    compare_df['new_adj_close'] = compare_df['new_raw_close'] * compare_df['new_factor']
    
    # 计算差异
    compare_df['abs_diff'] = (compare_df['new_adj_close'] - compare_df['old_close']).abs()
    # 相对差异，避免除以0
    compare_df['rel_diff'] = (compare_df['abs_diff'] / compare_df['old_close'].abs()).replace([np.inf, -np.inf], np.nan)

    print("\n--- 复现价格与原始价格的差异统计 ---")
    print(compare_df[['abs_diff', 'rel_diff']].describe(percentiles=[.5, .9, .95, .99]))

    print("\n--- 抽样对比 (SH600000) ---")
    try:
        sh600000_sample = compare_df.loc[(slice(None), 'SH600000'), :].dropna().tail(10)
        print(sh600000_sample)
    except KeyError:
        print("[INFO] SH600000 不在公共数据集中或无重叠数据。")

    print("\n--- 抽样对比 (SZ000002) ---")
    try:
        sz000002_sample = compare_df.loc[(slice(None), 'SZ000002'), :].dropna().tail(10)
        print(sz000002_sample)
    except KeyError:
        print("[INFO] SZ000002 不在公共数据集中或无重叠数据。")

    # 4 & 5. 因子单调性和指数因子检查
    check_factor_monotonicity(df_old, "原始数据")
    check_factor_monotonicity(df_new, "新数据")
    
    check_index_factor(df_old, "原始数据")
    check_index_factor(df_new, "新数据")

    # 6. 缺失值模式对比
    print_section("6. 公共数据集上的缺失值对比")
    old_nan_mask = old_common.isnull()
    new_nan_mask = new_common.isnull()

    print("\n--- 原始数据有值，但新数据缺失 (可能丢失了数据) ---")
    diff_nan_1 = ( (~old_nan_mask) & new_nan_mask ).sum()
    print(diff_nan_1[diff_nan_1 > 0])

    print("\n--- 原始数据缺失，但新数据有值 (数据被补全) ---")
    diff_nan_2 = ( old_nan_mask & (~new_nan_mask) ).sum()
    print(diff_nan_2[diff_nan_2 > 0])
    
    print_section("审核完成")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="对比两个RD-Agent(Q)框架的HDF5数据文件。")
    parser.add_argument("old_file", type=str, help="原始数据文件的路径 (e.g., daily_pv_tushare.h5)")
    parser.add_argument("new_file", type=str, help="新构建的数据文件的路径 (e.g., daily_pv_tushare_rebuilt_v4.h5)")
    
    args = parser.parse_args()
    
    main(args.old_file, args.new_file)