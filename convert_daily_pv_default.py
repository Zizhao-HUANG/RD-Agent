#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
转换daily_pv_default.h5文件为纯文本格式
"""

import pandas as pd
import os
from datetime import datetime

def convert_h5_to_complete_text(h5_file_path, output_file_path, file_description):
    """
    将HDF5文件的全部内容转换为纯文本格式
    
    Args:
        h5_file_path: HDF5文件路径
        output_file_path: 输出文本文件路径
        file_description: 文件描述
    """
    print(f"正在处理文件: {h5_file_path}")
    
    try:
        # 使用pandas读取HDF5文件
        print("正在读取HDF5文件...")
        df = pd.read_hdf(h5_file_path)
        
        print(f"数据形状: {df.shape}")
        print(f"开始写入文件: {output_file_path}")
        
        with open(output_file_path, 'w', encoding='utf-8') as output_file:
            output_file.write(f"=== {file_description} ===\n")
            output_file.write(f"文件路径: {h5_file_path}\n")
            output_file.write(f"处理时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            output_file.write(f"数据形状: {df.shape}\n")
            output_file.write(f"数据列: {list(df.columns)}\n\n")
            
            # 输出全部数据
            if len(df) > 0:
                output_file.write("=== 数据样本 ===\n")
                output_file.write(df.to_string())
                output_file.write("\n\n")
                
                # 输出基本统计信息
                output_file.write("=== 数据统计 ===\n")
                output_file.write(f"数据行数: {len(df):,}\n")
                output_file.write(f"数据列数: {len(df.columns)}\n")
                output_file.write(f"时间范围: {df.index.get_level_values('datetime').min()} 到 {df.index.get_level_values('datetime').max()}\n")
                output_file.write(f"股票数量: {df.index.get_level_values('instrument').nunique():,}\n")
                output_file.write(f"缺失值数量: {df.isnull().sum().sum()}\n")
        
        print(f"文件 {h5_file_path} 处理完成，输出到 {output_file_path}")
        return True
        
    except Exception as e:
        print(f"处理文件 {h5_file_path} 时出错: {str(e)}")
        with open(output_file_path, 'w', encoding='utf-8') as output_file:
            output_file.write(f"=== {file_description} ===\n")
            output_file.write(f"文件路径: {h5_file_path}\n")
            output_file.write(f"处理时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            output_file.write(f"错误信息: {str(e)}\n")
        return False

def main():
    """主函数"""
    # 文件路径
    h5_file_path = "/home/shenzi/RD-Agent/daily_pv_default.h5"
    output_file_path = "daily_pv_default_complete.txt"
    
    print("开始转换daily_pv_default.h5文件为完整纯文本格式...")
    print("注意：这将生成一个包含所有数据行的大文件")
    
    # 处理文件
    print("\n" + "="*50)
    success = convert_h5_to_complete_text(h5_file_path, output_file_path, "daily_pv_default.h5 完整数据")
    
    if success:
        print(f"\n转换完成！")
        print(f"输出文件: {output_file_path}")
        
        # 显示文件大小
        if os.path.exists(output_file_path):
            size_mb = os.path.getsize(output_file_path) / (1024 * 1024)
            print(f"文件大小: {size_mb:.2f} MB")
    else:
        print(f"\n转换失败！")

if __name__ == "__main__":
    main() 