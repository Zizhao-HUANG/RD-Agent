#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
正确的数据生成脚本
使用qlib的表达式引擎生成数据
"""

import qlib
from qlib.constant import REG_CN
import pandas as pd

def generate_correct_data():
    """使用正确的方式生成数据"""
    print("=== 使用qlib表达式引擎生成数据 ===\n")
    
    # 初始化qlib
    qlib.init(provider_uri="~/.qlib/qlib_data/cn_data", region=REG_CN)
    from qlib.data import D
    
    print("1. 获取股票列表...")
    instruments = D.instruments()
    print(f"   股票数量: {len(instruments)}")
    
    print("\n2. 定义字段...")
    fields = ["$open", "$close", "$high", "$low", "$volume", "$factor"]
    print(f"   字段: {fields}")
    
    print("\n3. 生成数据...")
    try:
        # 使用qlib的表达式引擎生成数据
        data = D.features(instruments, fields, freq="day")
        print(f"   原始数据形状: {data.shape}")
        
        # 交换索引级别并排序
        data = data.swaplevel().sort_index()
        print(f"   交换索引后形状: {data.shape}")
        
        # 截取2008年12月29日之后的数据
        data = data.loc["2008-12-29":].sort_index()
        print(f"   截取时间范围后形状: {data.shape}")
        
        print("\n4. 保存数据...")
        output_file = "/home/shenzi/RD-Agent/rdagent/scenarios/qlib/experiment/factor_data_template/daily_pv_all_correct.h5"
        data.to_hdf(output_file, key="data")
        print(f"   数据已保存到: {output_file}")
        
        print("\n5. 数据统计:")
        print(f"   数据形状: {data.shape}")
        print(f"   时间范围: {data.index.get_level_values(0).min()} 到 {data.index.get_level_values(0).max()}")
        print(f"   股票数量: {data.index.get_level_values(1).nunique()}")
        print(f"   总数据点: {len(data)}")
        print(f"   数据字段: {list(data.columns)}")
        
        # 检查$factor字段
        print(f"\n6. $factor字段统计:")
        print(f"   最小值: {data['$factor'].min():.6f}")
        print(f"   最大值: {data['$factor'].max():.6f}")
        print(f"   平均值: {data['$factor'].mean():.6f}")
        print(f"   中位数: {data['$factor'].median():.6f}")
        print(f"   标准差: {data['$factor'].std():.6f}")
        
        return data, output_file
        
    except Exception as e:
        print(f"❌ 生成数据时出错: {e}")
        return None, None

def copy_to_target_directory():
    """复制到目标目录"""
    print("\n=== 复制到目标目录 ===")
    
    source_file = "/home/shenzi/RD-Agent/rdagent/scenarios/qlib/experiment/factor_data_template/daily_pv_all_correct.h5"
    target_file = "/home/shenzi/RD-Agent/git_ignore_folder/factor_implementation_source_data/daily_pv.h5"
    
    try:
        import shutil
        import os
        
        # 确保目标目录存在
        os.makedirs(os.path.dirname(target_file), exist_ok=True)
        
        # 复制文件
        shutil.copy2(source_file, target_file)
        print(f"✅ 文件已复制到: {target_file}")
        
        # 验证文件
        df = pd.read_hdf(target_file, key="data")
        print(f"✅ 验证成功，数据形状: {df.shape}")
        
        return True
        
    except Exception as e:
        print(f"❌ 复制文件时出错: {e}")
        return False

if __name__ == "__main__":
    # 生成数据
    data, output_file = generate_correct_data()
    
    if data is not None:
        # 复制到目标目录
        success = copy_to_target_directory()
        
        if success:
            print("\n🎉 数据生成和部署完成！")
            print("✅ 现在可以使用更新后的数据了")
        else:
            print("\n❌ 数据部署失败")
    else:
        print("\n❌ 数据生成失败") 