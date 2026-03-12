#!/usr/bin/env python3
"""
人气榜单获取模块
Popularity Rank Fetcher

功能：
1. 获取东方财富人气榜TOP 100
2. 获取同花顺人气榜（待实现）
3. 获取开盘啦人气榜（待实现）
4. 数据持久化和历史记录
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd


class PopularityFetcher:
    """人气榜单获取器"""
    
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = os.path.join(
                os.path.dirname(__file__), 
                '../data/popularity'
            )
        
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
    
    def fetch_eastmoney_rank(self, limit: int = 50) -> List[Dict]:
        """
        获取东方财富人气榜
        
        Args:
            limit: 获取数量，默认50
        
        Returns:
            人气榜列表
        """
        try:
            import akshare as ak
            
            print(f"📊 获取东方财富人气榜 TOP {limit}...")
            
            # 获取人气榜数据
            df = ak.stock_hot_rank_em()
            
            if df.empty:
                print("❌ 未获取到数据")
                return []
            
            # 取前N条
            df = df.head(limit)
            
            # 转换为字典列表
            rank_list = []
            for idx, row in df.iterrows():
                rank_list.append({
                    'rank': int(row['当前排名']),
                    'code': str(row['代码']),
                    'name': row['股票名称'],
                    'price': float(row['最新价']),
                    'change': float(row['涨跌额']),
                    'change_pct': float(row['涨跌幅'])
                })
            
            print(f"✅ 成功获取 {len(rank_list)} 条数据")
            return rank_list
            
        except Exception as e:
            print(f"❌ 获取东方财富人气榜失败: {e}")
            return []
    
    def fetch_tonghuashun_rank(self, limit: int = 50) -> List[Dict]:
        """
        获取同花顺人气榜
        
        TODO: 需要抓包分析同花顺API
        """
        print("⚠️  同花顺人气榜接口待实现")
        return []
    
    def fetch_kaipanla_rank(self, limit: int = 50) -> List[Dict]:
        """
        获取开盘啦人气榜
        
        TODO: 需要抓包分析开盘啦API
        """
        print("⚠️  开盘啦人气榜接口待实现")
        return []
    
    def fetch_all_sources(self, limit: int = 50) -> Dict[str, List[Dict]]:
        """
        获取所有数据源的人气榜
        
        Returns:
            {
                'eastmoney': [...],
                'tonghuashun': [...],
                'kaipanla': [...]
            }
        """
        print("=" * 70)
        print("🔥 获取人气榜单 - 多数据源")
        print("=" * 70)
        print()
        
        results = {}
        
        # 东方财富
        results['eastmoney'] = self.fetch_eastmoney_rank(limit)
        print()
        
        # 同花顺
        results['tonghuashun'] = self.fetch_tonghuashun_rank(limit)
        print()
        
        # 开盘啦
        results['kaipanla'] = self.fetch_kaipanla_rank(limit)
        print()
        
        return results
    
    def save_daily_rank(self, rank_data: Dict[str, List[Dict]], date: str = None):
        """
        保存每日人气榜数据
        
        Args:
            rank_data: 人气榜数据
            date: 日期，默认今天
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        # 保存到文件
        output_path = os.path.join(self.data_dir, f'popularity_rank_{date}.json')
        
        data = {
            'date': date,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'sources': rank_data
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"💾 人气榜数据已保存: {output_path}")
    
    def load_daily_rank(self, date: str) -> Optional[Dict]:
        """
        加载指定日期的人气榜数据
        
        Args:
            date: 日期 (YYYY-MM-DD)
        
        Returns:
            人气榜数据
        """
        file_path = os.path.join(self.data_dir, f'popularity_rank_{date}.json')
        
        if not os.path.exists(file_path):
            return None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def merge_ranks(self, rank_data: Dict[str, List[Dict]]) -> List[Dict]:
        """
        合并多个数据源的人气榜
        
        计算综合排名：
        - 东方财富权重: 0.5
        - 同花顺权重: 0.3
        - 开盘啦权重: 0.2
        
        Returns:
            综合排名列表
        """
        # 收集所有股票
        stock_scores = {}
        
        # 东方财富 (权重0.5)
        for item in rank_data.get('eastmoney', []):
            code = item['code']
            # 排名越靠前，分数越高
            score = (100 - item['rank']) * 0.5
            stock_scores[code] = stock_scores.get(code, 0) + score
        
        # 同花顺 (权重0.3)
        for item in rank_data.get('tonghuashun', []):
            code = item['code']
            score = (100 - item['rank']) * 0.3
            stock_scores[code] = stock_scores.get(code, 0) + score
        
        # 开盘啦 (权重0.2)
        for item in rank_data.get('kaipanla', []):
            code = item['code']
            score = (100 - item['rank']) * 0.2
            stock_scores[code] = stock_scores.get(code, 0) + score
        
        # 按分数排序
        sorted_stocks = sorted(stock_scores.items(), key=lambda x: x[1], reverse=True)
        
        # 构建结果
        merged_rank = []
        for rank, (code, score) in enumerate(sorted_stocks, 1):
            # 从原始数据中找到股票信息
            stock_info = None
            for source_data in rank_data.values():
                for item in source_data:
                    if item['code'] == code:
                        stock_info = item
                        break
                if stock_info:
                    break
            
            if stock_info:
                merged_rank.append({
                    'rank': rank,
                    'code': code,
                    'name': stock_info['name'],
                    'score': round(score, 2),
                    'price': stock_info.get('price'),
                    'change_pct': stock_info.get('change_pct')
                })
        
        return merged_rank
    
    def print_rank(self, rank_list: List[Dict], title: str = "人气榜"):
        """打印人气榜"""
        print("=" * 70)
        print(f"🔥 {title}")
        print("=" * 70)
        print()
        
        if not rank_list:
            print("暂无数据")
            return
        
        print(f"{'排名':<6} {'代码':<10} {'名称':<12} {'最新价':<10} {'涨跌幅':<10}")
        print("-" * 70)
        
        for item in rank_list[:20]:  # 只显示前20
            rank = item.get('rank', 0)
            code = item.get('code', '')
            name = item.get('name', '')
            price = item.get('price', 0)
            change_pct = item.get('change_pct', 0)
            
            print(f"{rank:<6} {code:<10} {name:<12} {price:<10.2f} {change_pct:<10.2f}%")
        
        print()
        print("=" * 70)


def main():
    """测试函数"""
    fetcher = PopularityFetcher()
    
    # 获取所有数据源
    rank_data = fetcher.fetch_all_sources(limit=50)
    
    # 打印东方财富人气榜
    if rank_data['eastmoney']:
        fetcher.print_rank(rank_data['eastmoney'], "东方财富人气榜 TOP 20")
    
    # 保存数据
    fetcher.save_daily_rank(rank_data)
    
    # 合并排名
    if rank_data['eastmoney']:
        merged = fetcher.merge_ranks(rank_data)
        fetcher.print_rank(merged, "综合人气榜 TOP 20")


if __name__ == "__main__":
    main()
