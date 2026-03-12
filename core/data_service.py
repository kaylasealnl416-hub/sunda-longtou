#!/usr/bin/env python3
"""
数据服务 - 统一数据获取接口
Data Service - Unified Data Access Layer

功能：
1. 统一数据获取接口
2. 解耦数据源和业务逻辑
3. 支持数据缓存
4. 异常处理和降级

作者：开发者欧达
日期：2026-03-12
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path


class DataService:
    """数据服务 - 统一数据访问层"""
    
    def __init__(self, data_dir: str = None):
        """
        初始化数据服务
        
        Args:
            data_dir: 数据目录路径
        """
        if data_dir is None:
            data_dir = os.path.join(
                os.path.dirname(__file__), 
                '../data'
            )
        
        self.data_dir = data_dir
        self.cache = {}
        
        # 延迟导入，避免循环依赖
        self._popularity_fetcher = None
        self._tracking_system = None
    
    @property
    def popularity_fetcher(self):
        """延迟加载人气榜获取器"""
        if self._popularity_fetcher is None:
            from popularity_fetcher import PopularityFetcher
            self._popularity_fetcher = PopularityFetcher()
        return self._popularity_fetcher
    
    @property
    def tracking_system(self):
        """延迟加载跟踪系统"""
        if self._tracking_system is None:
            from tracking_system import TrackingSystem
            self._tracking_system = TrackingSystem()
        return self._tracking_system
    
    def get_zt_stocks(self, date: str = None) -> List[Dict]:
        """
        获取涨停股数据
        
        Args:
            date: 日期 (YYYYMMDD)，默认今天
        
        Returns:
            涨停股列表
        """
        if date is None:
            date = datetime.now().strftime('%Y%m%d')
        
        # 检查缓存
        cache_key = f'zt_stocks_{date}'
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # 从文件读取
        file_path = os.path.join(self.data_dir, 'daily', f'zt_{date}.csv')
        
        if not os.path.exists(file_path):
            print(f"⚠️  数据文件不存在: {file_path}")
            return []
        
        try:
            import pandas as pd
            df = pd.read_csv(file_path)
            stocks = df.to_dict('records')
            
            # 缓存
            self.cache[cache_key] = stocks
            
            return stocks
        
        except Exception as e:
            print(f"❌ 读取涨停股数据失败: {e}")
            return []
    
    def get_popularity_rank(self, limit: int = 50, use_cache: bool = True) -> List[Dict]:
        """
        获取人气榜数据
        
        Args:
            limit: 返回数量
            use_cache: 是否使用缓存
        
        Returns:
            人气榜列表 [{'rank': 1, 'code': '600905', 'name': '三峡能源', ...}, ...]
        """
        cache_key = f'popularity_rank_{limit}'
        
        # 检查缓存
        if use_cache and cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            # 获取人气榜（直接返回列表）
            rank_data = self.popularity_fetcher.fetch_eastmoney_rank(limit=limit)
            
            if rank_data and isinstance(rank_data, list):
                # 缓存
                self.cache[cache_key] = rank_data
                return rank_data
            
            return []
        
        except Exception as e:
            print(f"⚠️  获取人气榜失败: {e}")
            return []
    
    def get_tracking_stocks(self, status: str = 'tracking') -> List[Dict]:
        """
        获取跟踪中的股票
        
        Args:
            status: 状态 ('waiting', 'tracking', 'completed')
        
        Returns:
            股票列表
        """
        try:
            if status == 'waiting':
                return self.tracking_system.get_waiting_stocks()
            elif status == 'tracking':
                return self.tracking_system.get_tracking_stocks()
            elif status == 'completed':
                return self.tracking_system.get_completed_stocks()
            else:
                return []
        
        except Exception as e:
            print(f"⚠️  获取跟踪股票失败: {e}")
            return []
    
    def add_to_tracking(self, stocks: List[Dict]) -> bool:
        """
        添加股票到跟踪列表
        
        Args:
            stocks: 股票列表 [{'code': '600905', 'name': '三峡能源', ...}, ...]
        
        Returns:
            是否成功
        """
        try:
            self.tracking_system.add_first_board_stocks(stocks)
            return True
        
        except Exception as e:
            print(f"❌ 添加到跟踪列表失败: {e}")
            return False
    
    def get_stock_by_code(self, code: str, date: str = None) -> Optional[Dict]:
        """
        根据代码获取股票数据
        
        Args:
            code: 股票代码
            date: 日期 (YYYYMMDD)
        
        Returns:
            股票数据字典，如果不存在返回None
        """
        stocks = self.get_zt_stocks(date)
        
        for stock in stocks:
            if stock.get('code') == code or stock.get('代码') == code:
                return stock
        
        return None
    
    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()
        print("✅ 缓存已清空")
    
    def get_cache_info(self) -> Dict:
        """
        获取缓存信息
        
        Returns:
            缓存统计信息
        """
        return {
            'cache_size': len(self.cache),
            'cache_keys': list(self.cache.keys())
        }


# 测试代码
if __name__ == '__main__':
    print("=" * 70)
    print("🔧 数据服务测试")
    print("=" * 70)
    
    service = DataService()
    
    # 测试1：获取涨停股
    print("\n📊 测试1：获取涨停股数据")
    stocks = service.get_zt_stocks('20260312')
    print(f"  涨停股数量: {len(stocks)}")
    if stocks:
        print(f"  示例: {stocks[0].get('name', stocks[0].get('名称'))} ({stocks[0].get('code', stocks[0].get('代码'))})")
    
    # 测试2：获取人气榜
    print("\n🔥 测试2：获取人气榜")
    popularity = service.get_popularity_rank(limit=10)
    print(f"  人气榜数量: {len(popularity)}")
    if popularity:
        for i, item in enumerate(popularity[:5], 1):
            print(f"  {i}. {item['name']} ({item['code']}) - 排名{item['rank']}")
    
    # 测试3：获取跟踪股票
    print("\n📍 测试3：获取跟踪股票")
    tracking = service.get_tracking_stocks('waiting')
    print(f"  等待跟踪: {len(tracking)}")
    
    tracking = service.get_tracking_stocks('tracking')
    print(f"  跟踪中: {len(tracking)}")
    
    # 测试4：缓存信息
    print("\n💾 测试4：缓存信息")
    cache_info = service.get_cache_info()
    print(f"  缓存项数: {cache_info['cache_size']}")
    print(f"  缓存键: {cache_info['cache_keys']}")
    
    print("\n✅ 测试完成")
