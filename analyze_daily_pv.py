#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日价格和成交量数据统计分析脚本
对daily_pv.h5文件进行详尽的统计学描述
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def load_data(file_path):
    """加载HDF5数据文件"""
    try:
        df = pd.read_hdf(file_path, key="data")
        print(f"✅ 成功加载数据文件: {file_path}")
        print(f"📊 数据形状: {df.shape}")
        return df
    except Exception as e:
        print(f"❌ 加载数据失败: {e}")
        return None

def basic_info(df):
    """基本数据信息"""
    print("\n" + "="*60)
    print("📋 基本数据信息")
    print("="*60)
    
    print(f"数据维度: {df.shape[0]} 行 × {df.shape[1]} 列")
    print(f"数据时间范围: {df.index.min()} 到 {df.index.max()}")
    print(f"数据总天数: {len(df)}")
    
    print("\n列名信息:")
    for i, col in enumerate(df.columns, 1):
        print(f"  {i}. {col}")
    
    print("\n数据类型:")
    print(df.dtypes)
    
    print("\n缺失值统计:")
    missing_data = df.isnull().sum()
    if missing_data.sum() == 0:
        print("  ✅ 无缺失值")
    else:
        print(missing_data[missing_data > 0])

def descriptive_statistics(df):
    """描述性统计"""
    print("\n" + "="*60)
    print("📈 描述性统计")
    print("="*60)
    
    # 数值型列的描述性统计
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    print("\n数值型变量描述性统计:")
    desc_stats = df[numeric_cols].describe()
    print(desc_stats.round(4))
    
    # 计算额外的统计指标
    print("\n额外统计指标:")
    for col in numeric_cols:
        print(f"\n{col}:")
        print(f"  偏度 (Skewness): {df[col].skew():.4f}")
        print(f"  峰度 (Kurtosis): {df[col].kurtosis():.4f}")
        print(f"  变异系数 (CV): {(df[col].std() / df[col].mean() * 100):.2f}%")
        print(f"  四分位距 (IQR): {df[col].quantile(0.75) - df[col].quantile(0.25):.4f}")

def correlation_analysis(df):
    """相关性分析"""
    print("\n" + "="*60)
    print("🔗 相关性分析")
    print("="*60)
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) > 1:
        corr_matrix = df[numeric_cols].corr()
        print("\n皮尔逊相关系数矩阵:")
        print(corr_matrix.round(4))
        
        # 创建相关性热力图
        plt.figure(figsize=(10, 8))
        sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0, 
                   square=True, fmt='.3f')
        plt.title('变量相关性热力图')
        plt.tight_layout()
        plt.savefig('correlation_heatmap.png', dpi=300, bbox_inches='tight')
        plt.show()
        print("✅ 相关性热力图已保存为 'correlation_heatmap.png'")

def distribution_analysis(df):
    """分布分析"""
    print("\n" + "="*60)
    print("📊 分布分析")
    print("="*60)
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    # 创建分布图
    n_cols = len(numeric_cols)
    fig, axes = plt.subplots(2, n_cols, figsize=(4*n_cols, 8))
    
    for i, col in enumerate(numeric_cols):
        # 直方图
        axes[0, i].hist(df[col].dropna(), bins=50, alpha=0.7, color='skyblue', edgecolor='black')
        axes[0, i].set_title(f'{col} 分布直方图')
        axes[0, i].set_xlabel(col)
        axes[0, i].set_ylabel('频数')
        
        # Q-Q图
        stats.probplot(df[col].dropna(), dist="norm", plot=axes[1, i])
        axes[1, i].set_title(f'{col} Q-Q图')
    
    plt.tight_layout()
    plt.savefig('distribution_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()
    print("✅ 分布分析图已保存为 'distribution_analysis.png'")

def time_series_analysis(df):
    """时间序列分析"""
    print("\n" + "="*60)
    print("⏰ 时间序列分析")
    print("="*60)
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    # 检查索引是否为时间类型
    if not isinstance(df.index, pd.DatetimeIndex):
        print("⚠️  索引不是时间类型，尝试转换...")
        try:
            df.index = pd.to_datetime(df.index)
        except:
            print("❌ 无法转换为时间索引")
            return
    
    print(f"时间范围: {df.index.min()} 到 {df.index.max()}")
    print(f"总交易日数: {len(df)}")
    
    # 按年份统计
    yearly_stats = df.groupby(df.index.year).agg(['mean', 'std', 'count'])
    print("\n年度统计:")
    print(yearly_stats.round(4))
    
    # 时间序列图
    fig, axes = plt.subplots(len(numeric_cols), 1, figsize=(12, 4*len(numeric_cols)))
    if len(numeric_cols) == 1:
        axes = [axes]
    
    for i, col in enumerate(numeric_cols):
        axes[i].plot(df.index, df[col], linewidth=0.5, alpha=0.7)
        axes[i].set_title(f'{col} 时间序列')
        axes[i].set_xlabel('时间')
        axes[i].set_ylabel(col)
        axes[i].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('time_series.png', dpi=300, bbox_inches='tight')
    plt.show()
    print("✅ 时间序列图已保存为 'time_series.png'")

def outlier_analysis(df):
    """异常值分析"""
    print("\n" + "="*60)
    print("🔍 异常值分析")
    print("="*60)
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    for col in numeric_cols:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)]
        
        print(f"\n{col}:")
        print(f"  下界: {lower_bound:.4f}")
        print(f"  上界: {upper_bound:.4f}")
        print(f"  异常值数量: {len(outliers)} ({len(outliers)/len(df)*100:.2f}%)")
        
        if len(outliers) > 0:
            print(f"  异常值范围: {outliers[col].min():.4f} 到 {outliers[col].max():.4f}")

def summary_report(df):
    """生成总结报告"""
    print("\n" + "="*60)
    print("📋 数据质量总结报告")
    print("="*60)
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    print(f"✅ 数据完整性: {len(df)} 条记录")
    print(f"✅ 变量数量: {len(numeric_cols)} 个数值型变量")
    
    # 数据质量评分
    missing_rate = df.isnull().sum().sum() / (len(df) * len(df.columns)) * 100
    print(f"✅ 缺失值比例: {missing_rate:.2f}%")
    
    # 异常值比例
    total_outliers = 0
    for col in numeric_cols:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        outliers = df[(df[col] < Q1 - 1.5 * IQR) | (df[col] > Q3 + 1.5 * IQR)]
        total_outliers += len(outliers)
    
    outlier_rate = total_outliers / (len(df) * len(numeric_cols)) * 100
    print(f"✅ 异常值比例: {outlier_rate:.2f}%")
    
    print("\n🎯 建议:")
    if missing_rate > 5:
        print("  - 数据存在较多缺失值，建议进行缺失值处理")
    if outlier_rate > 10:
        print("  - 数据存在较多异常值，建议进行异常值检测和处理")
    if len(df) < 100:
        print("  - 数据量较少，统计结果可能不够稳定")
    
    print("  - 建议根据业务需求选择合适的统计方法")

def main():
    """主函数"""
    file_path = "/home/shenzi/RD-Agent/git_ignore_folder/factor_implementation_source_data/daily_pv.h5"
    
    print("🚀 开始分析每日价格和成交量数据...")
    print(f"📁 数据文件路径: {file_path}")
    
    # 加载数据
    df = load_data(file_path)
    if df is None:
        return
    
    # 执行各项分析
    basic_info(df)
    descriptive_statistics(df)
    correlation_analysis(df)
    distribution_analysis(df)
    time_series_analysis(df)
    outlier_analysis(df)
    summary_report(df)
    
    print("\n" + "="*60)
    print("🎉 分析完成！")
    print("="*60)
    print("📊 生成的文件:")
    print("  - correlation_heatmap.png (相关性热力图)")
    print("  - distribution_analysis.png (分布分析图)")
    print("  - time_series.png (时间序列图)")

if __name__ == "__main__":
    main()