#!/usr/bin/env python3
"""
龙头股动态评分系统 V4.0
基于情绪周期的动态评分策略

核心改进：
1. 五种评分策略（冰点/启动/发酵/高潮/退潮）
2. 根据情绪周期动态调整权重
3. 同一现象，不同周期，不同分数
4. 顺势而为，不猜顶底

评分公式（满分 100 分）：
- 情绪面 30 分 = 情绪周期(15分) + 量比(15分)
- 资金面 25 分 = 资金净流入(15分) + 大单占比(10分)
- 技术面 30 分 = 连板高度(12分) + 封板质量(10分) + 趋势(8分)
- 题材面 10 分 = 主线题材(6分) + 人气热度(4分)
- 基本面 5 分 = 业绩连续性(3分) + 业绩增长(2分)
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from emotion_cycle import EmotionCycleDetectorV2
import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json


class DynamicScoringStrategy:
    """动态评分策略基类"""
    
    def __init__(self, stage_name: str):
        self.stage_name = stage_name
    
    def adjust_board_score(self, boards: int, base_score: float) -> float:
        """调整连板高度得分"""
        return base_score
    
    def adjust_volume_score(self, volume_ratio: float, base_score: float) -> float:
        """调整量比得分"""
        return base_score
    
    def adjust_turnover_score(self, turnover: float, base_score: float) -> float:
        """调整换手率得分"""
        return base_score


class IcePeriodStrategy(DynamicScoringStrategy):
    """冰点期评分策略"""
    
    def __init__(self):
        super().__init__("冰点期")
    
    def adjust_board_score(self, boards: int, base_score: float) -> float:
        """冰点期：首板加分，高连板减分"""
        if boards == 1:
            return base_score + 2  # 首板加分（启动信号）
        elif boards >= 4:
            return base_score - 2  # 高连板减分（风险）
        return base_score
    
    def adjust_volume_score(self, volume_ratio: float, base_score: float) -> float:
        """冰点期：缩量加分（惜售是好事）"""
        if volume_ratio < 0.5:
            return base_score + 3  # 缩量创新高 = 主力控盘
        return base_score
    
    def adjust_turnover_score(self, turnover: float, base_score: float) -> float:
        """冰点期：低换手加分（惜售）"""
        if turnover < 3:
            return base_score + 3
        return base_score


class StartPeriodStrategy(DynamicScoringStrategy):
    """启动期评分策略"""
    
    def __init__(self):
        super().__init__("启动期")
    
    def adjust_board_score(self, boards: int, base_score: float) -> float:
        """启动期：2-3连板加分（确定性高）"""
        if boards in [2, 3]:
            return base_score + 2  # 2-3连板加分
        elif boards >= 5:
            return base_score - 1  # 高连板略减分
        return base_score
    
    def adjust_volume_score(self, volume_ratio: float, base_score: float) -> float:
        """启动期：放量突破加分"""
        if volume_ratio > 1.5:
            return base_score + 2  # 放量突破 = 主力进攻
        return base_score


class FermentPeriodStrategy(DynamicScoringStrategy):
    """发酵期评分策略"""
    
    def __init__(self):
        super().__init__("发酵期")
    
    def adjust_board_score(self, boards: int, base_score: float) -> float:
        """发酵期：3-4连板加分（主升浪）"""
        if boards in [3, 4]:
            return base_score + 2  # 3-4连板加分
        return base_score
    
    def adjust_turnover_score(self, turnover: float, base_score: float) -> float:
        """发酵期：充分换手加分（5-15%）"""
        if 5 <= turnover <= 15:
            return base_score + 3  # 充分换手 = 承接强
        return base_score


class ClimaxPeriodStrategy(DynamicScoringStrategy):
    """高潮期评分策略"""
    
    def __init__(self):
        super().__init__("高潮期")
    
    def adjust_board_score(self, boards: int, base_score: float) -> float:
        """高潮期：高连板减分（风险）"""
        if boards >= 4:
            return base_score - 2  # 高连板减分
        return base_score
    
    def adjust_volume_score(self, volume_ratio: float, base_score: float) -> float:
        """高潮期：放量减分（可能出货）"""
        if volume_ratio > 2.0:
            return base_score - 2  # 巨量减分
        return base_score
    
    def adjust_turnover_score(self, turnover: float, base_score: float) -> float:
        """高潮期：高换手减分（出货风险）"""
        if turnover > 20:
            return base_score - 2  # 高换手减分
        return base_score


class RetreatPeriodStrategy(DynamicScoringStrategy):
    """退潮期评分策略"""
    
    def __init__(self):
        super().__init__("退潮期")
    
    def adjust_board_score(self, boards: int, base_score: float) -> float:
        """退潮期：所有连板减分"""
        if boards >= 2:
            return base_score - 3  # 连板减分
        return base_score
    
    def adjust_volume_score(self, volume_ratio: float, base_score: float) -> float:
        """退潮期：放量减分"""
        if volume_ratio > 1.5:
            return base_score - 2
        return base_score


class DragonStockScorerV4:
    """龙头股动态评分系统 V4.0"""
    
    def __init__(self):
        # 初始化情绪周期检测器
        self.emotion_detector = EmotionCycleDetectorV2()
        
        # 初始化五种评分策略
        self.strategies = {
            "冰点期": IcePeriodStrategy(),
            "启动期": StartPeriodStrategy(),
            "发酵期": FermentPeriodStrategy(),
            "高潮期": ClimaxPeriodStrategy(),
            "退潮期": RetreatPeriodStrategy()
        }
        
        # 当前市场情绪
        self.market_emotion = None
        self.current_strategy = None
    
    def init_market_data(self):
        """初始化市场数据"""
        print("🔄 初始化市场数据...")
        
        # 获取情绪周期
        emotion_result = self.emotion_detector.analyze()
        self.market_emotion = emotion_result['emotion_cycle']
        
        # 选择对应的评分策略
        stage = self.market_emotion['stage']
        self.current_strategy = self.strategies[stage]
        
        print(f"✅ 当前情绪周期: {stage}")
        print(f"✅ 使用策略: {self.current_strategy.stage_name}评分策略\n")
    
    def score_emotion(self, stock_data: Dict) -> Dict:
        """
        情绪面评分（30分）
        = 情绪周期得分(15分) + 量比得分(15分)
        """
        # 1. 情绪周期得分（15分）
        emotion_stage = self.market_emotion['stage']
        emotion_scores = {
            "冰点期": 15,    # 冰点期最高分（逆向思维）
            "启动期": 12,    # 启动期次高（确定性高）
            "发酵期": 10,    # 发酵期中等（主升浪）
            "高潮期": 6,     # 高潮期较低（风险高）
            "退潮期": 3      # 退潮期最低（及时止损）
        }
        emotion_score = emotion_scores.get(emotion_stage, 8)
        
        # 2. 量比得分（15分）
        volume_ratio = stock_data.get('volume_ratio', 1.0)
        涨幅 = stock_data.get('change_pct', 0)
        
        # 基础量比评分
        if volume_ratio < 0.5 and 涨幅 > 0:
            volume_score = 15  # 缩量创新高 = 主力控盘
        elif volume_ratio > 1.5 and 涨幅 > 5:
            volume_score = 13  # 放量突破
        elif volume_ratio > 1.5 and 涨幅 > 0:
            volume_score = 11  # 放量上涨
        elif 0.8 <= volume_ratio <= 1.2 and 涨幅 > 0:
            volume_score = 9   # 量比正常 + 上涨
        elif 0.8 <= volume_ratio <= 1.2 and 涨幅 < 0:
            volume_score = 6   # 量比正常 + 下跌
        elif volume_ratio < 0.8 and 涨幅 < 0:
            volume_score = 7   # 缩量下跌（可能洗盘）
        elif volume_ratio > 1.5 and 涨幅 < -3:
            volume_score = 3   # 放量下跌（出货）
        else:
            volume_score = 5   # 其他情况
        
        # 动态调整
        volume_score = self.current_strategy.adjust_volume_score(volume_ratio, volume_score)
        volume_score = max(0, min(15, volume_score))  # 限制在0-15分
        
        total = emotion_score + volume_score
        
        return {
            "total": round(total, 2),
            "emotion_score": emotion_score,
            "emotion_stage": emotion_stage,
            "volume_score": round(volume_score, 2),
            "volume_ratio": volume_ratio
        }
    
    def score_technical(self, stock_data: Dict) -> Dict:
        """
        技术面评分（30分）
        = 连板高度(12分) + 封板质量(10分) + 趋势(8分)
        """
        # 1. 连板高度（12分）
        boards = stock_data.get('consecutive_boards', 0)
        
        if boards >= 4:
            board_score = 12
        elif boards == 3:
            board_score = 10
        elif boards == 2:
            board_score = 8
        elif boards == 1:
            board_score = 6
        else:
            # 未涨停，按涨幅给分
            涨幅 = stock_data.get('change_pct', 0)
            if 涨幅 > 7:
                board_score = 5
            elif 涨幅 > 5:
                board_score = 4
            elif 涨幅 > 3:
                board_score = 3
            elif 涨幅 > 0:
                board_score = 2
            else:
                board_score = 0
        
        # 动态调整
        board_score = self.current_strategy.adjust_board_score(boards, board_score)
        board_score = max(0, min(12, board_score))
        
        # 2. 封板质量（10分）
        开板次数 = stock_data.get('open_times', 0)
        封成比 = stock_data.get('seal_ratio', 0)
        
        if boards > 0:
            # 涨停股才有封板质量
            if 开板次数 == 0:
                seal_score = 10  # 无开板
            elif 开板次数 == 1:
                seal_score = 8   # 开板1次
            elif 开板次数 == 2:
                seal_score = 6   # 开板2次
            else:
                seal_score = 4   # 开板≥3次
            
            # 封成比加分
            if 封成比 > 3:
                seal_score = min(10, seal_score + 2)
            elif 封成比 > 1:
                seal_score = min(10, seal_score + 1)
        else:
            seal_score = 0
        
        # 3. 趋势（8分）
        均线数 = stock_data.get('ma_above_count', 0)  # 站上几条均线
        
        if 均线数 >= 4:
            trend_score = 8  # 站上4条均线
        elif 均线数 == 3:
            trend_score = 6  # 站上3条均线
        elif 均线数 == 2:
            trend_score = 4  # 站上2条均线
        else:
            trend_score = 2  # 站上≤1条均线
        
        total = board_score + seal_score + trend_score
        
        return {
            "total": round(total, 2),
            "board_score": round(board_score, 2),
            "seal_score": round(seal_score, 2),
            "trend_score": round(trend_score, 2),
            "boards": boards
        }
    
    def score_capital(self, stock_data: Dict) -> Dict:
        """
        资金面评分（25分）
        = 资金净流入(15分) + 大单占比(10分)
        """
        # 1. 资金净流入（15分）
        net_inflow = stock_data.get('net_inflow', 0)  # 单位：万元
        
        if net_inflow > 5000:
            inflow_score = 15  # 超大单净流入
        elif net_inflow > 1000:
            inflow_score = 12  # 大单净流入
        elif net_inflow > 0:
            inflow_score = 9   # 中单净流入
        elif net_inflow > -1000:
            inflow_score = 6   # 小幅流出
        else:
            inflow_score = 3   # 大幅流出
        
        # 2. 大单占比（10分）
        big_order_ratio = stock_data.get('big_order_ratio', 0)
        
        if big_order_ratio > 0.6:
            big_order_score = 10  # 大单占比>60%
        elif big_order_ratio > 0.4:
            big_order_score = 8   # 大单占比40-60%
        elif big_order_ratio > 0.3:
            big_order_score = 6   # 大单占比30-40%
        else:
            big_order_score = 4   # 大单占比<30%
        
        total = inflow_score + big_order_score
        
        return {
            "total": round(total, 2),
            "inflow_score": round(inflow_score, 2),
            "big_order_score": round(big_order_score, 2)
        }
    
    def score_theme(self, stock_data: Dict) -> Dict:
        """
        题材面评分（10分）
        = 主线题材(6分) + 人气热度(4分)
        """
        # 1. 主线题材（6分）
        theme_level = stock_data.get('theme_level', '无')
        
        theme_scores = {
            "国家级": 6,
            "部委级": 5,
            "行业级": 4,
            "个股级": 2,
            "无": 0
        }
        theme_score = theme_scores.get(theme_level, 0)
        
        # 2. 人气热度（4分）
        popularity = stock_data.get('popularity', '跟风股')
        
        popularity_scores = {
            "市场总龙头": 4,
            "板块龙头": 3,
            "人气股": 2,
            "跟风股": 1
        }
        popularity_score = popularity_scores.get(popularity, 1)
        
        total = theme_score + popularity_score
        
        return {
            "total": round(total, 2),
            "theme_score": round(theme_score, 2),
            "popularity_score": round(popularity_score, 2)
        }
    
    def score_fundamental(self, stock_data: Dict) -> Dict:
        """
        基本面评分（5分）
        = 业绩连续性(3分) + 业绩增长(2分)
        """
        # 1. 业绩连续性（3分）
        盈利季度 = stock_data.get('profit_quarters', 4)
        
        if 盈利季度 >= 4:
            continuity_score = 3  # 连续盈利
        elif 盈利季度 >= 2:
            continuity_score = 2  # 偶尔亏损
        elif 盈利季度 >= 1:
            continuity_score = 1  # 连续亏损
        else:
            continuity_score = -2  # ST风险
        
        # 2. 业绩增长（2分）
        增长率 = stock_data.get('profit_growth', 0)
        
        if 增长率 > 50:
            growth_score = 2
        elif 增长率 > 20:
            growth_score = 1.5
        elif 增长率 > 0:
            growth_score = 1
        else:
            growth_score = 0
        
        total = continuity_score + growth_score
        
        return {
            "total": round(total, 2),
            "continuity_score": round(continuity_score, 2),
            "growth_score": round(growth_score, 2)
        }
    
    def score_stock(self, stock_data: Dict) -> Dict:
        """
        对单只股票进行完整评分
        
        Args:
            stock_data: 股票数据字典
            
        Returns:
            完整的评分结果
        """
        # 确保市场数据已初始化
        if self.market_emotion is None:
            self.init_market_data()
        
        # 各维度评分
        emotion_result = self.score_emotion(stock_data)
        technical_result = self.score_technical(stock_data)
        capital_result = self.score_capital(stock_data)
        theme_result = self.score_theme(stock_data)
        fundamental_result = self.score_fundamental(stock_data)
        
        # 计算总分
        total_score = (
            emotion_result['total'] +
            technical_result['total'] +
            capital_result['total'] +
            theme_result['total'] +
            fundamental_result['total']
        )
        
        # 评级
        if total_score >= 90:
            rating = "SSS"
            level = "市场总龙头"
        elif total_score >= 80:
            rating = "SS"
            level = "板块龙头"
        elif total_score >= 70:
            rating = "S"
            level = "强势股"
        elif total_score >= 60:
            rating = "A"
            level = "合格标的"
        elif total_score >= 50:
            rating = "B"
            level = "一般标的"
        else:
            rating = "C"
            level = "弱势股"
        
        return {
            "stock_code": stock_data.get('code', ''),
            "stock_name": stock_data.get('name', ''),
            "total_score": round(total_score, 2),
            "rating": rating,
            "level": level,
            "emotion_cycle": self.market_emotion['stage'],
            "strategy": self.current_strategy.stage_name,
            "scores": {
                "emotion": emotion_result,
                "technical": technical_result,
                "capital": capital_result,
                "theme": theme_result,
                "fundamental": fundamental_result
            }
        }
    
    def save_result(self, result: Dict, filepath: str = "dragon_scores_v4.json"):
        """保存评分结果"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"✅ 结果已保存到: {filepath}")


def main():
    """测试函数"""
    scorer = DragonStockScorerV4()
    scorer.init_market_data()
    
    # 测试数据
    test_stock = {
        "code": "600905",
        "name": "三峡能源",
        "consecutive_boards": 3,
        "open_times": 0,
        "seal_ratio": 5.2,
        "volume_ratio": 1.8,
        "change_pct": 10.0,
        "ma_above_count": 4,
        "net_inflow": 8000,
        "big_order_ratio": 0.65,
        "theme_level": "国家级",
        "popularity": "板块龙头",
        "profit_quarters": 4,
        "profit_growth": 35
    }
    
    print("=" * 70)
    print("📊 龙头股动态评分系统 V4.0 - 测试")
    print("=" * 70)
    
    result = scorer.score_stock(test_stock)
    
    print(f"\n股票: {result['stock_name']} ({result['stock_code']})")
    print(f"总分: {result['total_score']} 分")
    print(f"评级: {result['rating']} - {result['level']}")
    print(f"情绪周期: {result['emotion_cycle']}")
    print(f"评分策略: {result['strategy']}")
    
    print(f"\n各维度得分:")
    print(f"  情绪面: {result['scores']['emotion']['total']}/30")
    print(f"  技术面: {result['scores']['technical']['total']}/30")
    print(f"  资金面: {result['scores']['capital']['total']}/25")
    print(f"  题材面: {result['scores']['theme']['total']}/10")
    print(f"  基本面: {result['scores']['fundamental']['total']}/5")
    
    scorer.save_result(result)
    
    return result


if __name__ == "__main__":
    main()
