#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自定义qlib数据转换脚本
处理时区问题并转换为qlib格式
"""

import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path
from tqdm import tqdm
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CustomDumpBin:
    def __init__(self, csv_path, qlib_dir, freq="day", max_workers=1):
        self.csv_path = Path(csv_path)
        self.qlib_dir = Path(qlib_dir)
        self.freq = freq
        self.max_workers = max_workers
        
        # 创建目录
        self.qlib_dir.mkdir(parents=True, exist_ok=True)
        (self.qlib_dir / "features").mkdir(exist_ok=True)
        (self.qlib_dir / "calendars").mkdir(exist_ok=True)
        (self.qlib_dir / "instruments").mkdir(exist_ok=True)
        
        # 字段映射
        self.field_mapping = {
            "open": "open",
            "close": "close", 
            "high": "high",
            "low": "low",
            "volume": "volume",
            "adjclose": "adjclose"
        }
        
        self.all_dates = set()
        self.symbols = []
        
    def process_csv_file(self, csv_file):
        """处理单个CSV文件"""
        try:
            # 读取CSV文件
            df = pd.read_csv(csv_file)
            
            # 处理日期列 - 避免时区问题
            df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d', errors='coerce')
            df = df.dropna(subset=['date'])
            
            if df.empty:
                return None, set()
            
            # 获取股票代码
            symbol = df['symbol'].iloc[0]
            
            # 获取日期范围
            dates = set(df['date'].dt.strftime('%Y-%m-%d'))
            
            # 选择需要的字段
            fields = ['open', 'close', 'high', 'low', 'volume', 'adjclose']
            df_selected = df[fields].copy()
            
            # 转换为numpy数组
            data_dict = {}
            for field in fields:
                data_dict[field] = df_selected[field].values.astype(np.float32)
            
            return symbol, dates, data_dict
            
        except Exception as e:
            logger.warning(f"处理文件 {csv_file} 时出错: {e}")
            return None, set()
    
    def get_all_dates_and_symbols(self):
        """获取所有日期和股票代码"""
        logger.info("开始扫描所有CSV文件...")
        
        csv_files = list(self.csv_path.glob("*.csv"))
        logger.info(f"找到 {len(csv_files)} 个CSV文件")
        
        all_dates = set()
        symbols = []
        
        for csv_file in tqdm(csv_files, desc="扫描文件"):
            try:
                df = pd.read_csv(csv_file)
                df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d', errors='coerce')
                df = df.dropna(subset=['date'])
                
                if not df.empty:
                    symbol = df['symbol'].iloc[0]
                    symbols.append(symbol)
                    dates = set(df['date'].dt.strftime('%Y-%m-%d'))
                    all_dates.update(dates)
                    
            except Exception as e:
                logger.warning(f"扫描文件 {csv_file} 时出错: {e}")
        
        self.all_dates = sorted(list(all_dates))
        self.symbols = sorted(list(set(symbols)))
        
        logger.info(f"总共找到 {len(self.symbols)} 个股票，{len(self.all_dates)} 个交易日")
        
    def create_calendar_file(self):
        """创建交易日历文件"""
        logger.info("创建交易日历文件...")
        
        calendar_file = self.qlib_dir / "calendars" / f"{self.freq}.txt"
        with open(calendar_file, 'w') as f:
            for date in self.all_dates:
                f.write(f"{date}\n")
        
        logger.info(f"交易日历文件已创建: {calendar_file}")
    
    def create_instruments_file(self):
        """创建股票列表文件"""
        logger.info("创建股票列表文件...")
        
        instruments_file = self.qlib_dir / "instruments" / "all.txt"
        with open(instruments_file, 'w') as f:
            for symbol in self.symbols:
                f.write(f"{symbol}\n")
        
        logger.info(f"股票列表文件已创建: {instruments_file}")
    
    def process_symbol_data(self, csv_file):
        """处理单个股票的数据"""
        try:
            result = self.process_csv_file(csv_file)
            if result[0] is None:
                return None
            
            symbol, dates, data_dict = result
            
            # 创建股票目录
            symbol_dir = self.qlib_dir / "features" / symbol
            symbol_dir.mkdir(exist_ok=True)
            
            # 保存数据文件
            for field, data in data_dict.items():
                bin_file = symbol_dir / f"{field}.{self.freq}.bin"
                data.tofile(bin_file)
            
            return symbol
            
        except Exception as e:
            logger.warning(f"处理股票数据时出错: {e}")
            return None
    
    def dump_all(self):
        """转换所有数据"""
        logger.info("开始转换数据...")
        
        # 1. 获取所有日期和股票代码
        self.get_all_dates_and_symbols()
        
        # 2. 创建日历文件
        self.create_calendar_file()
        
        # 3. 创建股票列表文件
        self.create_instruments_file()
        
        # 4. 处理所有股票数据
        csv_files = list(self.csv_path.glob("*.csv"))
        logger.info(f"开始处理 {len(csv_files)} 个股票的数据...")
        
        processed_count = 0
        
        if self.max_workers == 1:
            # 单线程处理
            for csv_file in tqdm(csv_files, desc="处理股票数据"):
                symbol = self.process_symbol_data(csv_file)
                if symbol:
                    processed_count += 1
        else:
            # 多线程处理
            with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {executor.submit(self.process_symbol_data, csv_file): csv_file for csv_file in csv_files}
                
                for future in tqdm(as_completed(futures), total=len(futures), desc="处理股票数据"):
                    symbol = future.result()
                    if symbol:
                        processed_count += 1
        
        logger.info(f"数据转换完成！成功处理 {processed_count} 个股票")
        logger.info(f"数据保存在: {self.qlib_dir}")

def main():
    parser = argparse.ArgumentParser(description="自定义qlib数据转换工具")
    parser.add_argument("--csv_path", required=True, help="CSV数据目录路径")
    parser.add_argument("--qlib_dir", required=True, help="qlib数据输出目录")
    parser.add_argument("--freq", default="day", help="数据频率 (day/1min)")
    parser.add_argument("--max_workers", type=int, default=1, help="最大工作线程数")
    
    args = parser.parse_args()
    
    # 创建转换器并执行转换
    converter = CustomDumpBin(
        csv_path=args.csv_path,
        qlib_dir=args.qlib_dir,
        freq=args.freq,
        max_workers=args.max_workers
    )
    
    converter.dump_all()

if __name__ == "__main__":
    main() 