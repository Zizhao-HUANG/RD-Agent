#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将Qlib数据转换为RD Agent的HDF5格式
"""

import numpy as np
import pandas as pd
from pathlib import Path
import h5py
from tqdm import tqdm
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class QlibToRdAgentConverter:
    def __init__(self, qlib_dir, output_file):
        self.qlib_dir = Path(qlib_dir)
        self.output_file = Path(output_file)
        self.calendar = None
        self.instruments = None
        
    def load_calendar(self):
        """加载交易日历"""
        logger.info("加载交易日历...")
        calendar_file = self.qlib_dir / "calendars" / "day.txt"
        with open(calendar_file, 'r') as f:
            self.calendar = [line.strip() for line in f.readlines() if line.strip()]
        logger.info(f"交易日历加载完成，共 {len(self.calendar)} 个交易日")
        
    def load_instruments(self):
        """加载股票列表"""
        logger.info("加载股票列表...")
        instruments_file = self.qlib_dir / "instruments" / "all.txt"
        df = pd.read_csv(instruments_file, header=None)
        self.instruments = df[0].tolist()
        logger.info(f"股票列表加载完成，共 {len(self.instruments)} 只股票")
        
    def load_stock_data(self, symbol):
        """加载单个股票的数据"""
        try:
            stock_dir = self.qlib_dir / "features" / symbol
            
            # 检查股票目录是否存在
            if not stock_dir.exists():
                logger.warning(f"股票目录不存在: {stock_dir}")
                return None
            
            # 读取各个字段的数据
            data_dict = {}
            fields = ['open', 'close', 'high', 'low', 'volume', 'adjclose']
            
            for field in fields:
                bin_file = stock_dir / f"{field}.day.bin"
                if bin_file.exists():
                    data = np.fromfile(bin_file, dtype=np.float32)
                    data_dict[field] = data
                else:
                    logger.warning(f"字段文件不存在: {bin_file}")
                    return None
            
            # 检查数据长度是否一致
            lengths = [len(data) for data in data_dict.values()]
            if len(set(lengths)) != 1:
                logger.warning(f"股票 {symbol} 数据长度不一致: {lengths}")
                return None
                
            return data_dict
            
        except Exception as e:
            logger.error(f"加载股票 {symbol} 数据时出错: {e}")
            return None
    
    def create_multiindex_dataframe(self):
        """创建MultiIndex DataFrame"""
        logger.info("开始创建MultiIndex DataFrame...")
        
        # 创建日期索引
        dates = pd.to_datetime(self.calendar)
        
        # 创建空的DataFrame列表
        df_list = []
        
        # 处理每个股票
        for symbol in tqdm(self.instruments, desc="处理股票数据"):
            stock_data = self.load_stock_data(symbol)
            
            if stock_data is None:
                continue
                
            # 创建股票数据DataFrame
            stock_df = pd.DataFrame({
                '$open': stock_data['open'],
                '$close': stock_data['close'],
                '$high': stock_data['high'],
                '$low': stock_data['low'],
                '$volume': stock_data['volume'],
                '$factor': np.ones(len(stock_data['close']))  # 默认因子值为1
            }, index=dates[:len(stock_data['close'])])
            
            # 添加股票代码索引
            stock_df['instrument'] = symbol
            stock_df.set_index('instrument', append=True, inplace=True)
            
            df_list.append(stock_df)
        
        # 合并所有股票数据
        logger.info("合并所有股票数据...")
        combined_df = pd.concat(df_list, axis=0)
        
        # 检查索引名称并重新排列
        logger.info(f"索引名称: {combined_df.index.names}")
        if combined_df.index.names[0] is None:
            # 如果索引没有名称，先设置名称
            combined_df.index.names = ['datetime', 'instrument']
        
        # 重新排列索引
        combined_df = combined_df.reorder_levels(['datetime', 'instrument'])
        combined_df.sort_index(inplace=True)
        
        logger.info(f"MultiIndex DataFrame创建完成，形状: {combined_df.shape}")
        return combined_df
    
    def convert(self):
        """执行转换"""
        logger.info("开始Qlib到RD Agent格式转换...")
        
        # 1. 加载日历和股票列表
        self.load_calendar()
        self.load_instruments()
        
        # 2. 创建MultiIndex DataFrame
        df = self.create_multiindex_dataframe()
        
        # 3. 保存为HDF5格式
        logger.info(f"保存到HDF5文件: {self.output_file}")
        df.to_hdf(self.output_file, key='data', mode='w', format='table', 
                 complevel=9, complib='blosc')
        
        logger.info("转换完成！")
        
        # 4. 输出统计信息
        print(f"\n=== 转换结果统计 ===")
        print(f"输出文件: {self.output_file}")
        print(f"数据形状: {df.shape}")
        print(f"时间范围: {df.index.get_level_values(0).min()} 到 {df.index.get_level_values(0).max()}")
        print(f"股票数量: {df.index.get_level_values(1).nunique()}")
        print(f"总数据点: {len(df)}")
        print(f"数据字段: {list(df.columns)}")
        
        return df

def main():
    """主函数"""
    # 配置路径
    qlib_dir = "/home/shenzi/.qlib/qlib_data/cn_data"
    output_file = "/home/shenzi/RD-Agent/qlib_converted_daily_pv.h5"
    
    # 创建转换器
    converter = QlibToRdAgentConverter(qlib_dir, output_file)
    
    # 执行转换
    df = converter.convert()
    
    print(f"\n✅ 转换成功！文件保存在: {output_file}")

if __name__ == "__main__":
    main() 