#!/usr/bin/env python3
"""
评分服务 - 统一评分接口
Score Service - Unified Scoring Interface

功能：
1. 统一评分接口
2. 整合人气榜数据
3. 批量评分优化
4. 评分结果缓存

作者：开发者欧达
日期：2026-03-12
"""

import os
import json
from typing import Dict, List, Optional
from datetime import datetime


class ScoreService:
    """评分服务 - 统一评分接口"""
    
    def __init__(self, config_path: str = None):
        """
        初始化评分服务
        
        Args:
            config_path: 配置文件路径（保留参数以兼容，但V6不使用）
        """
        self.config_path = config_path
        
        # 延迟导入
        self._scorer = None
        self._data_service = None
        
        # 缓存
        self.popularity_cache = None
        self.popularity_cache_time = None
    
    @property
    def scorer(self):
        """延迟加载评分器"""
        if self._scorer is None:
            from dragon_scorer_v6 import DragonStockScorerV6
            self._scorer = DragonStockScorerV6()  # V6不需要config_path
        return self._scorer
    
    @property
    def data_service(self):
        """延迟加载数据服务"""
        if self._data_service is None:
            from data_service import DataService
            self._data_service = DataService()
        return self._data_service
    
    def get_popularity_rank(self, force_refresh: bool = False) -> List[Dict]:
        """
        获取人气榜（带缓存）
        
        Args:
            force_refresh: 强制刷新
        
        Returns:
            人气榜列表
        """
        # 检查缓存（5分钟有效）
        if not force_refresh and self.popularity_cache is not None:
            if self.popularity_cache_time is not None:
                elapsed = (datetime.now() - self.popularity_cache_time).seconds
                if elapsed < 300:  # 5分钟
                    return self.popularity_cache
        
        # 获取新数据
        try:
            popularity = self.data_service.get_popularity_rank(limit=50)
            self.popularity_cache = popularity
            self.popularity_cache_time = datetime.now()
            return popularity
        
        except Exception as e:
            print(f"⚠️  获取人气榜失败: {e}")
            return []
    
    def score_stock(self, stock: Dict, use_popularity: bool = True) -> Dict:
        """
        评分单只股票（整合人气榜数据）
        
        Args:
            stock: 股票数据
            use_popularity: 是否使用人气榜数据
        
        Returns:
            评分结果 (V6格式)
        """
        # 数据格式转换（支持中英文字段名）
        normalized_stock = {
            'code': stock.get('code') or stock.get('代码'),
            'name': stock.get('name') or stock.get('名称'),
            '涨跌幅': stock.get('涨跌幅') or stock.get('change'),
            '最新价': stock.get('最新价') or stock.get('price'),
            '成交额': stock.get('成交额') or stock.get('amount'),
            '连板数': stock.get('连板数') or stock.get('boards', 0),
        }
        
        # 获取基础评分
        result = self.scorer.score_stock(normalized_stock)
        
        # 整合人气榜数据
        if use_popularity:
            popularity_rank = self.get_popularity_rank()
            
            if popularity_rank:
                stock_code = normalized_stock.get('code')
                
                # 标准化代码（去除SH/SZ前缀）
                def normalize_code(code):
                    if not code:
                        return ''
                    code_str = str(code)
                    # 去除SH/SZ前缀
                    if code_str.startswith('SH') or code_str.startswith('SZ'):
                        return code_str[2:]
                    return code_str
                
                normalized_stock_code = normalize_code(stock_code)
                
                # 查找股票在人气榜中的排名
                for item in popularity_rank:
                    item_code = normalize_code(item['code'])
                    
                    if item_code == normalized_stock_code:
                        rank = item['rank']
                        
                        # 根据排名加分
                        bonus = 0
                        if rank <= 10:
                            bonus = 2  # 前10名
                            print(f"  🔥 人气榜前10: +2分 (排名{rank})")
                        elif rank <= 30:
                            bonus = 1  # 前30名
                            print(f"  🔥 人气榜前30: +1分 (排名{rank})")
                        
                        # 加到题材面
                        if bonus > 0:
                            result['scores']['theme']['total'] = min(
                                result['scores']['theme']['total'] + bonus, 
                                10
                            )
                            result['scores']['theme']['popularity_score'] = min(
                                result['scores']['theme']['popularity_score'] + bonus,
                                4
                            )
                            
                            # 重新计算总分
                            result['total_score'] = sum([
                                result['scores']['emotion']['total'],
                                result['scores']['capital']['total'],
                                result['scores']['technical']['total'],
                                result['scores']['theme']['total'],
                                result['scores']['fundamental']['total']
                            ])
                            
                            # 重新评级
                            total = result['total_score']
                            if total >= 90:
                                result['rating'] = 'SS'
                                result['level'] = '超级龙头'
                            elif total >= 80:
                                result['rating'] = 'S'
                                result['level'] = '强势龙头'
                            elif total >= 70:
                                result['rating'] = 'A+'
                                result['level'] = '次级龙头'
                            elif total >= 60:
                                result['rating'] = 'A'
                                result['level'] = '跟风股'
                            elif total >= 50:
                                result['rating'] = 'B'
                                result['level'] = '普通股'
                            else:
                                result['rating'] = 'C'
                                result['level'] = '弱势股'
                        
                        break
        
        return result
    
    def score_batch(self, stocks: List[Dict], use_popularity: bool = True) -> List[Dict]:
        """
        批量评分
        
        Args:
            stocks: 股票列表
            use_popularity: 是否使用人气榜数据
        
        Returns:
            评分结果列表
        """
        results = []
        
        # 预加载人气榜（避免重复获取）
        if use_popularity:
            self.get_popularity_rank()
        
        for stock in stocks:
            try:
                result = self.score_stock(stock, use_popularity=use_popularity)
                results.append(result)
            
            except Exception as e:
                print(f"⚠️  评分失败 {stock.get('name', stock.get('名称'))}: {e}")
                continue
        
        # 按总分排序
        results.sort(key=lambda x: x['total_score'], reverse=True)
        
        return results
    
    def get_top_stocks(self, date: str = None, top_n: int = 8, use_popularity: bool = True) -> List[Dict]:
        """
        获取TOP N股票
        
        Args:
            date: 日期 (YYYYMMDD)
            top_n: 返回数量
            use_popularity: 是否使用人气榜数据
        
        Returns:
            TOP N股票列表
        """
        # 获取涨停股
        stocks = self.data_service.get_zt_stocks(date)
        
        if not stocks:
            print("⚠️  没有涨停股数据")
            return []
        
        # 批量评分
        results = self.score_batch(stocks, use_popularity=use_popularity)
        
        # 返回TOP N
        return results[:top_n]
    
    def compare_with_without_popularity(self, stock: Dict) -> Dict:
        """
        对比有无人气榜的评分差异
        
        Args:
            stock: 股票数据
        
        Returns:
            对比结果
        """
        # 不使用人气榜
        result_without = self.score_stock(stock, use_popularity=False)
        
        # 使用人气榜
        result_with = self.score_stock(stock, use_popularity=True)
        
        # 计算差异
        diff = result_with['total_score'] - result_without['total_score']
        
        return {
            'without': result_without,
            'with': result_with,
            'diff': diff
        }


# 测试代码
if __name__ == '__main__':
    print("=" * 70)
    print("🎯 评分服务测试")
    print("=" * 70)
    
    service = ScoreService()
    
    # 测试1：单只股票评分
    print("\n📊 测试1：单只股票评分（节能风电）")
    
    # 模拟股票数据
    stock = {
        'code': '601016',
        'name': '节能风电',
        '涨跌幅': 9.93,
        '最新价': 5.54,
        '成交额': 1234567890,
        '连板数': 1
    }
    
    print("\n不使用人气榜:")
    result_without = service.score_stock(stock, use_popularity=False)
    print(f"  总分: {result_without['total_score']}")
    print(f"  评级: {result_without['rating']} - {result_without['level']}")
    
    print("\n使用人气榜:")
    result_with = service.score_stock(stock, use_popularity=True)
    print(f"  总分: {result_with['total_score']}")
    print(f"  评级: {result_with['rating']} - {result_with['level']}")
    
    print(f"\n差异: {result_with['total_score'] - result_without['total_score']}分")
    
    # 测试2：批量评分
    print("\n" + "=" * 70)
    print("📊 测试2：批量评分TOP 5")
    
    stocks = service.data_service.get_zt_stocks('20260312')
    
    if stocks:
        top5 = service.get_top_stocks('20260312', top_n=5, use_popularity=True)
        
        print(f"\n找到 {len(stocks)} 只涨停股，TOP 5:")
        for i, result in enumerate(top5, 1):
            scores = result['scores']
            print(f"\n{i}. {result['stock_name']} ({result['stock_code']}) - {result['total_score']}分 [{result['rating']}]")
            print(f"   情绪:{scores['emotion']['total']} 资金:{scores['capital']['total']} 技术:{scores['technical']['total']} 题材:{scores['theme']['total']} 基本:{scores['fundamental']['total']}")
    
    print("\n✅ 测试完成")
