#!/usr/bin/env python3
"""
龙头股评分系统 V3.0
基于小欧 16 年实战经验的完整评分系统

核心理念：
- 情绪优先：市场情绪 > 技术形态 > 基本面
- 量比核心：量比是核心指标（权重 30%）
- 主流题材：主流、主动、主升

评分公式（满分 100 分）：
- 情绪面 30 分 = 情绪周期(15分) + 量比(15分)
- 资金面 30 分 = 资金净流入(15分) + 大单占比(15分)
- 技术面 25 分 = 连板高度(10分) + 封板质量(8分) + 趋势(7分)
- 题材面 15 分 = 主线题材(10分) + 人气辨识度(5分)

整合模块：
- emotion_cycle.py - 情绪周期识别
- volume_ratio_scorer.py - 量比评分
- theme_detector.py - 主流题材识别
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from emotion_cycle import EmotionCycleDetector
from volume_ratio_scorer import VolumeRatioScorer
from theme_detector import ThemeDetector

import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json


class DragonStockScorerV3:
    """龙头股评分系统 V3.0"""
    
    def __init__(self):
        # 初始化各个子系统
        self.emotion_detector = EmotionCycleDetector()
        self.volume_scorer = VolumeRatioScorer()
        self.theme_detector = ThemeDetector()
        
        # 评分权重
        self.weights = {
            "emotion": 0.30,  # 情绪面 30%
            "capital": 0.30,  # 资金面 30%
            "technical": 0.25,  # 技术面 25%
            "theme": 0.15     # 题材面 15%
        }
        
        # 缓存市场数据
        self.market_emotion = None
        self.main_theme = None
    
    def init_market_data(self):
        """初始化市场数据（情绪周期、主流题材）"""
        print("🔄 初始化市场数据...")
        
        # 1. 获取情绪周期
        print("   获取情绪周期...")
        emotion_result = self.emotion_detector.analyze()
        self.market_emotion = emotion_result['emotion_cycle']
        
        # 2. 获取主流题材
        print("   获取主流题材...")
        self.main_theme = self.theme_detector.detect_main_theme()
        
        print("✅ 市场数据初始化完成\n")
    
    def score_emotion(self, stock_code: str, stock_name: str) -> Dict:
        """
        情绪面评分（30分）
        = 情绪周期得分(15分) + 量比得分(15分)
        """
        # 1. 情绪周期得分（15分）
        # 根据当前市场情绪周期给分
        emotion_stage = self.market_emotion['stage']
        emotion_scores = {
            "冰点期": 15,    # 冰点期最高分（抄底机会）
            "启动期": 12,    # 启动期次高（追启动初期）
            "发酵期": 10,    # 发酵期中等（主升浪）
            "高潮期": 6,     # 高潮期较低（准备减仓）
            "退潮期": 3      # 退潮期最低（杀跌）
        }
        emotion_score = emotion_scores.get(emotion_stage, 8)
        
        # 2. 量比得分（15分）
        # 调用量比评分系统
        volume_result = self.volume_scorer.analyze_stock(stock_code, stock_name)
        
        if "error" in volume_result:
            volume_score = 0
        else:
            # 量比系统满分30分，这里需要15分，所以除以2
            volume_score = volume_result['score'] / 2
        
        total = emotion_score + volume_score
        
        return {
            "total": round(total, 2),
            "emotion_score": emotion_score,
            "emotion_stage": emotion_stage,
            "volume_score": round(volume_score, 2),
            "volume_ratio": volume_result.get('volume_ratio', 0),
            "volume_signal": volume_result.get('signal', '未知')
        }
    
    def score_capital(self, stock_code: str) -> Dict:
        """
        资金面评分（30分）
        = 资金净流入(15分) + 大单占比(15分)
        
        注：这里简化处理，实际需要接入资金流数据
        """
        # TODO: 接入真实资金流数据
        # 这里先用模拟数据
        
        # 模拟资金净流入（单位：万元）
        net_inflow = np.random.randint(-10000, 50000)
        
        # 资金净流入评分（15分）
        if net_inflow > 10000:
            inflow_score = 15
        elif net_inflow > 5000:
            inflow_score = 12
        elif net_inflow > 0:
            inflow_score = 9
        elif net_inflow > -5000:
            inflow_score = 6
        else:
            inflow_score = 3
        
        # 模拟大单占比
        big_order_ratio = np.random.uniform(0.2, 0.8)
        
        # 大单占比评分（15分）
        if big_order_ratio > 0.6:
            big_order_score = 15
        elif big_order_ratio > 0.4:
            big_order_score = 12
        elif big_order_ratio > 0.3:
            big_order_score = 9
        else:
            big_order_score = 6
        
        total = inflow_score + big_order_score
        
        return {
            "total": round(total, 2),
            "inflow_score": inflow_score,
            "net_inflow": net_inflow,
            "big_order_score": big_order_score,
            "big_order_ratio": round(big_order_ratio, 2)
        }
    
    def score_technical(self, stock_code: str) -> Dict:
        """
        技术面评分（25分）
        = 连板高度(10分) + 封板质量(8分) + 趋势(7分)
        
        注：这里简化处理，实际需要接入涨停板数据
        """
        # TODO: 接入真实涨停板数据
        # 这里先用模拟数据
        
        # 模拟连板高度
        board_height = np.random.choice([0, 1, 2, 3, 4], p=[0.7, 0.15, 0.08, 0.05, 0.02])
        
        # 连板高度评分（10分）
        board_scores = {0: 0, 1: 5, 2: 7, 3: 9, 4: 10}
        board_score = board_scores.get(board_height, 0)
        
        # 模拟封板质量（开板次数）
        open_times = np.random.choice([0, 1, 2, 3])
        
        # 封板质量评分（8分）
        seal_scores = {0: 8, 1: 6, 2: 4, 3: 2}
        seal_score = seal_scores.get(open_times, 0)
        
        # 模拟趋势（站上均线数量）
        ma_count = np.random.randint(0, 5)
        
        # 趋势评分（7分）
        trend_score = min(ma_count * 1.75, 7)
        
        total = board_score + seal_score + trend_score
        
        return {
            "total": round(total, 2),
            "board_score": board_score,
            "board_height": board_height,
            "seal_score": seal_score,
            "open_times": open_times,
            "trend_score": round(trend_score, 2),
            "ma_count": ma_count
        }
    
    def score_theme(self, stock_code: str, sector_name: str = "") -> Dict:
        """
        题材面评分（15分）
        = 主线题材(10分) + 人气辨识度(5分)
        """
        # 1. 主线题材评分（10分）
        # 判断股票是否属于主线题材
        if self.main_theme and sector_name:
            main_sector = self.main_theme.get('main_theme', '')
            related_sectors = self.main_theme.get('related_sectors', [])
            
            if sector_name == main_sector:
                # 主线题材龙头
                theme_score = 10
                theme_level = "主线龙头"
            elif sector_name in related_sectors:
                # 相关板块
                theme_score = 7
                theme_level = "相关板块"
            else:
                # 其他题材
                theme_score = 3
                theme_level = "其他题材"
        else:
            theme_score = 5
            theme_level = "未知"
        
        # 2. 人气辨识度评分（5分）
        # TODO: 接入真实人气数据（搜索指数、讨论热度等）
        # 这里先用模拟数据
        popularity = np.random.choice(["市场总龙头", "板块龙头", "人气股", "跟风"], 
                                     p=[0.05, 0.15, 0.30, 0.50])
        
        popularity_scores = {
            "市场总龙头": 5,
            "板块龙头": 4,
            "人气股": 3,
            "跟风": 1
        }
        popularity_score = popularity_scores.get(popularity, 2)
        
        total = theme_score + popularity_score
        
        return {
            "total": round(total, 2),
            "theme_score": theme_score,
            "theme_level": theme_level,
            "sector_name": sector_name,
            "popularity_score": popularity_score,
            "popularity": popularity
        }
    
    def score_stock(self, stock_code: str, stock_name: str = "", 
                   sector_name: str = "") -> Dict:
        """
        对单只股票进行完整评分
        
        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            sector_name: 所属板块
            
        Returns:
            完整的评分结果
        """
        print(f"\n{'='*70}")
        print(f"📊 龙头股评分系统 V3.0 - {stock_name}({stock_code})")
        print(f"{'='*70}")
        
        # 1. 情绪面评分
        print("\n🎭 情绪面评分（30分）...")
        emotion_result = self.score_emotion(stock_code, stock_name)
        print(f"   情绪周期: {emotion_result['emotion_stage']} ({emotion_result['emotion_score']}分)")
        print(f"   量比评分: {emotion_result['volume_score']}分 (量比{emotion_result['volume_ratio']})")
        print(f"   小计: {emotion_result['total']}/30")
        
        # 2. 资金面评分
        print("\n💰 资金面评分（30分）...")
        capital_result = self.score_capital(stock_code)
        print(f"   资金净流入: {capital_result['net_inflow']}万 ({capital_result['inflow_score']}分)")
        print(f"   大单占比: {capital_result['big_order_ratio']} ({capital_result['big_order_score']}分)")
        print(f"   小计: {capital_result['total']}/30")
        
        # 3. 技术面评分
        print("\n📈 技术面评分（25分）...")
        technical_result = self.score_technical(stock_code)
        print(f"   连板高度: {technical_result['board_height']}板 ({technical_result['board_score']}分)")
        print(f"   封板质量: 开板{technical_result['open_times']}次 ({technical_result['seal_score']}分)")
        print(f"   趋势: 站上{technical_result['ma_count']}条均线 ({technical_result['trend_score']}分)")
        print(f"   小计: {technical_result['total']}/25")
        
        # 4. 题材面评分
        print("\n🏷️  题材面评分（15分）...")
        theme_result = self.score_theme(stock_code, sector_name)
        print(f"   题材等级: {theme_result['theme_level']} ({theme_result['theme_score']}分)")
        print(f"   人气辨识: {theme_result['popularity']} ({theme_result['popularity_score']}分)")
        print(f"   小计: {theme_result['total']}/15")
        
        # 5. 计算总分
        total_score = (
            emotion_result['total'] +
            capital_result['total'] +
            technical_result['total'] +
            theme_result['total']
        )
        
        # 6. 评级
        if total_score >= 85:
            grade = "SSS"
            comment = "市场总龙头，极致确定性"
        elif total_score >= 75:
            grade = "SS"
            comment = "板块龙头，高确定性"
        elif total_score >= 65:
            grade = "S"
            comment = "强势股，值得关注"
        elif total_score >= 55:
            grade = "A"
            comment = "合格标的，可考虑"
        elif total_score >= 45:
            grade = "B"
            comment = "一般标的，观望"
        else:
            grade = "C"
            comment = "弱势股，回避"
        
        print(f"\n{'='*70}")
        print(f"🎯 总分: {total_score:.2f}/100")
        print(f"⭐ 评级: {grade}")
        print(f"💬 评价: {comment}")
        print(f"{'='*70}\n")
        
        # 组合完整结果
        result = {
            "stock_code": stock_code,
            "stock_name": stock_name,
            "sector_name": sector_name,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "timestamp": datetime.now().isoformat(),
            "total_score": round(total_score, 2),
            "grade": grade,
            "comment": comment,
            "emotion": emotion_result,
            "capital": capital_result,
            "technical": technical_result,
            "theme": theme_result,
            "market_context": {
                "emotion_stage": self.market_emotion['stage'],
                "position_advice": self.market_emotion['position_advice'],
                "main_theme": self.main_theme.get('main_theme', '未知') if self.main_theme else '未知'
            }
        }
        
        return result
    
    def batch_score(self, stock_list: List[Tuple[str, str, str]]) -> List[Dict]:
        """
        批量评分
        
        Args:
            stock_list: [(股票代码, 股票名称, 所属板块), ...]
            
        Returns:
            评分结果列表，按总分排序
        """
        results = []
        
        for stock_code, stock_name, sector_name in stock_list:
            result = self.score_stock(stock_code, stock_name, sector_name)
            results.append(result)
        
        # 按总分排序
        results.sort(key=lambda x: x['total_score'], reverse=True)
        
        return results
    
    def save_results(self, results: List[Dict], filepath: str = "dragon_scores_v3.json"):
        """保存评分结果"""
        # 转换所有 numpy 类型为 Python 原生类型
        def convert_types(obj):
            if isinstance(obj, dict):
                return {k: convert_types(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_types(item) for item in obj]
            elif isinstance(obj, (np.integer, np.int64)):
                return int(obj)
            elif isinstance(obj, (np.floating, np.float64)):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            else:
                return obj
        
        results_clean = convert_types(results)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results_clean, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 结果已保存到: {filepath}")


def main():
    """主函数 - 测试评分系统 V3.0"""
    print("🚀 龙头股评分系统 V3.0")
    print("基于小欧 16 年实战经验\n")
    
    # 初始化评分系统
    scorer = DragonStockScorerV3()
    scorer.init_market_data()
    
    # 测试股票列表
    test_stocks = [
        ("002261", "拓维信息", "软件服务"),
        ("601868", "中国能建", "电力"),
        ("002506", "协鑫集成", "光伏设备"),
        ("000533", "顺钠股份", "物流"),
        ("600821", "金开新能", "电力"),
    ]
    
    # 批量评分
    results = scorer.batch_score(test_stocks)
    
    # 输出排名
    print("\n" + "="*70)
    print("📊 龙头股评分排名")
    print("="*70)
    print(f"{'排名':<6}{'股票':<20}{'总分':<10}{'评级':<8}{'评价':<30}")
    print("-"*70)
    
    for i, result in enumerate(results, 1):
        print(f"{i:<6}{result['stock_name']}({result['stock_code']})<20"
              f"{result['total_score']:<10}{result['grade']:<8}{result['comment']:<30}")
    
    print("="*70)
    
    # 保存结果
    scorer.save_results(results)
    
    return results


if __name__ == "__main__":
    main()
