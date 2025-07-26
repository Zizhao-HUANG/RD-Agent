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

def audit_data(filepath):
    """
    对单个 HDF5 数据文件进行全面、健壮的审核。
    新版审核脚本，不再依赖HDF5底层格式。
    """
    print_section(f"开始审核文件: {filepath}")

    # 1. 文件加载
    print("\n=== 1. 数据加载与基本信息 ===")
    try:
        df = pd.read_hdf(filepath, key='data')
        print("[SUCCESS] 文件加载成功。")
    except Exception as e:
        print(f"[FATAL] 加载文件失败: {e}")
        print("请检查文件路径、文件是否损坏或key是否为'data'。")
        return

    print(f"DataFrame 形状: {df.shape}")
    print(f"索引类型: {type(df.index)}")
    if isinstance(df.index, pd.MultiIndex):
        print(f"索引名称: {df.index.names}")
    print(f"列名: {list(df.columns)}")
    print(f"列数据类型:\n{df.dtypes.to_string()}")

    # 2. MultiIndex 结构与范围
    print("\n=== 2. 索引结构与范围 ===")
    if not isinstance(df.index, pd.MultiIndex) or df.index.names != ['datetime', 'instrument']:
        print("[ERROR] 索引不是名为 ['datetime', 'instrument'] 的 MultiIndex！")
        return

    dates = df.index.get_level_values('datetime')
    instruments = df.index.get_level_values('instrument')
    print(f"Level 0 (datetime): {dates.min()} ~ {dates.max()} (共{len(dates.unique())}个)")
    print(f"Level 1 (instrument): 共{len(instruments.unique())}个标的")
    print(f"索引样例:\n{df.index[:5].to_list()}")

    # 3. 股票与指数代码检查
    print("\n=== 3. 标的代码检查 ===")
    all_instruments = instruments.unique()
    stock_codes = [i for i in all_instruments if i.startswith(('SH6', 'SZ0', 'SZ3', 'BJ'))]
    index_codes = [i for i in all_instruments if not i.startswith(('SH6', 'SZ0', 'SZ3', 'BJ'))]
    print(f"股票数量: {len(stock_codes)}")
    print(f"指数数量: {len(index_codes)}")
    print(f"股票样例: {stock_codes[:10]}")
    print(f"指数样例: {index_codes[:10]}")

    # 4. 复权因子 ($factor) 检查
    print("\n=== 4. 复权因子 ($factor) 检查 ===")
    # 4.1 股票因子单调性
    non_monotonic_stocks = []
    # 随机抽查500只股票以提高效率
    sample_stocks = np.random.choice(stock_codes, min(500, len(stock_codes)), replace=False)
    print(f"[INFO] 抽查 {len(sample_stocks)} 只股票的 $factor 单调性...")
    for inst in tqdm(sample_stocks, desc="检查股票因子单调性"):
        factor_series = df.loc[(slice(None), inst), '$factor'].dropna()
        # 前复权因子应为单调非增
        if not factor_series.is_monotonic_decreasing:
            non_monotonic_stocks.append(inst)
    
    if non_monotonic_stocks:
        print(f"[WARNING] 发现 {len(non_monotonic_stocks)}/{len(sample_stocks)} 个抽样股票的 $factor 非单调非增！")
        print(f"  - 样例: {non_monotonic_stocks[:10]}")
    else:
        print("[SUCCESS] 抽样股票的 $factor 均符合单调非增特性。")

    # 4.2 指数因子是否为1
    if index_codes:
        df_indices_factor = df.loc[(slice(None), index_codes), '$factor'].dropna()
        non_one_factors = df_indices_factor[df_indices_factor != 1.0]
        if not non_one_factors.empty:
            print(f"[WARNING] 发现指数的 $factor 不全为 1.0！")
            print(f"  - 涉及的指数数量: {len(non_one_factors.index.get_level_values('instrument').unique())}")
            print(f"  - 异常因子值统计:\n{non_one_factors.describe()}")
        else:
            print("[SUCCESS] 所有指数的 $factor 均为 1.0。")
    else:
        print("[INFO] 未找到指数数据进行检查。")

    # 5. 关键字段分布与极值检查
    print("\n=== 5. 关键字段分布检查 ===")
    for col in ['$open', '$close', '$high', '$low', '$volume', '$factor']:
        if col in df.columns:
            print(f"\n--- {col} ---")
            print(df[col].describe(percentiles=[.01, .25, .5, .75, .99]).to_string())

    # 6. 缺失值检查
    print("\n=== 6. 缺失值检查 ===")
    print(df.isnull().sum().to_string())

    # 7. 数据抽样
    print("\n=== 7. 数据抽样 ===")
    print("--- 数据头 (前5行) ---")
    print(df.head())
    print("\n--- 数据尾 (后5行) ---")
    print(df.tail())
    print("\n--- 贵州茅台 (SH600519) 最新数据 ---")
    try:
        print(df.loc[(slice(None), '600519.SH')].tail())
    except KeyError:
        print("[WARNING] 未在数据中找到 'SH600519' (贵州茅台)。")

    print_section("审核完成")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="对 RD-Agent(Q) / Qlib 的 HDF5 数据文件进行全面审核。")
    parser.add_argument("filepath", type=str, help="要审核的数据文件路径 (e.g., daily_pv_qfq_standard.h5)")
    args = parser.parse_args()
    audit_data(args.filepath)