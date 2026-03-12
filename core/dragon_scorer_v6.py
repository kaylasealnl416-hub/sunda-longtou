#!/usr/bin/env python3
"""
龙头股评分系统 V6.0 - 威科夫理论深度整合版
Wyckoff-Based Dragon Stock Scoring System

核心升级：
1. 资金面整合威科夫量价分析（30分）
2. 技术面增加K线形态分析（25分）
3. 情绪面优化量比评分逻辑（30分）
4. 所有维度基于《量价分析》理论重构

评分公式（满分 100 分）：
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 情绪面 30分 = 情绪周期(15) + 量比分析(15)
💰 资金面 30分 = 威科夫量价(12) + 资金流(10) + 大单(8)  ⭐ 升级
📈 技术面 25分 = 连板(10) + K线形态(8) + 趋势(7)      ⭐ 升级
🎯 题材面 10分 = 主线题材(6) + 人气热度(4)
📋 基本面 5分  = 业绩连续(3) + 业绩增长(2)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

理论基础：
- 第2章：成交量的相对性
- 第3章：影线揭示情绪
- 第4章：投入产出定律
- 第5章：吸筹派筹周期
- 第6章：放量止跌/止涨
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from emotion_cycle import EmotionCycleDetectorV2
from wyckoff_analyzer import WyckoffAnalyzer
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import json


class DragonStockScorerV6:
    """龙头股评分系统 V6.0 - 威科夫理论深度整合"""
    
    def __init__(self):
        self.emotion_detector = EmotionCycleDetectorV2()
        self.wyckoff_analyzer = WyckoffAnalyzer()
        self.market_emotion = None
    
    def init_market_data(self):
        """初始化市场数据"""
        print("🔄 初始化市场数据...")
        emotion_result = self.emotion_detector.analyze()
        self.market_emotion = emotion_result['emotion_cycle']
        print(f"✅ 当前情绪周期: {self.market_emotion['stage']}")
        print(f"✅ 置信度: {self.market_emotion['confidence']}%\n")
    
    def score_emotion(self, stock_data: Dict) -> Dict:
        """
        情绪面评分（30分）⭐ 优化
        = 情绪周期(15分) + 量比分析(15分)
        
        优化点：
        1. 量比评分结合威科夫理论
        2. 区分缩量创新高 vs 放量突破
        3. 识别量价背离
        """
        # 1. 情绪周期得分（15分）
        emotion_stage = self.market_emotion['stage']
        emotion_scores = {
            "冰点期": 15,  # 最佳买入时机
            "启动期": 12,  # 确定性高
            "发酵期": 10,  # 主升浪
            "高潮期": 6,   # 风险增加
            "退潮期": 3    # 及时止损
        }
        emotion_score = emotion_scores.get(emotion_stage, 8)
        
        # 2. 量比分析（15分）⭐ 基于威科夫理论优化
        volume_ratio = stock_data.get('volume_ratio', 1.0)
        change_pct = stock_data.get('change_pct', 0)
        is_new_high = stock_data.get('is_new_high', False)
        
        # 威科夫量价关系评分
        volume_score = self._score_volume_price_relation(
            volume_ratio, change_pct, is_new_high, emotion_stage
        )
        
        total = emotion_score + volume_score
        
        return {
            "total": round(total, 2),
            "emotion_score": emotion_score,
            "emotion_stage": emotion_stage,
            "volume_score": round(volume_score, 2),
            "volume_ratio": volume_ratio,
            "analysis": self._get_volume_analysis(volume_ratio, change_pct)
        }
    
    def _score_volume_price_relation(
        self, 
        volume_ratio: float, 
        change_pct: float,
        is_new_high: bool,
        emotion_stage: str
    ) -> float:
        """
        量价关系评分（基于威科夫投入产出定律）
        
        核心逻辑：
        1. 缩量创新高（主力控盘）= 15分
        2. 放量突破（真突破）= 13分
        3. 价涨量增（确认）= 11分
        4. 价涨量缩（背离）= 6分
        5. 放量下跌（出货）= 3分
        """
        score = 5  # 基础分
        
        # 1. 缩量创新高（主力高度控盘）⭐⭐⭐
        if is_new_high and volume_ratio < 0.6 and change_pct > 0:
            score = 15
            reason = "缩量创新高（主力控盘）"
        
        # 2. 放量突破（真突破）⭐⭐
        elif volume_ratio > 1.8 and change_pct > 7:
            score = 13
            reason = "放量突破（真突破）"
        
        # 3. 价涨量增（健康上涨）✅
        elif volume_ratio > 1.2 and change_pct > 3:
            score = 11
            reason = "价涨量增（健康上涨）"
        
        # 4. 适度放量上涨
        elif 0.8 <= volume_ratio <= 1.5 and change_pct > 0:
            score = 9
            reason = "适度放量上涨"
        
        # 5. 价涨量缩（上涨乏力）⚠️
        elif volume_ratio < 0.8 and change_pct > 3:
            score = 6
            reason = "价涨量缩（上涨乏力）"
        
        # 6. 缩量下跌（可能洗盘）
        elif volume_ratio < 0.8 and change_pct < 0:
            score = 7
            reason = "缩量下跌（可能洗盘）"
        
        # 7. 放量下跌（主力出货）❌
        elif volume_ratio > 1.5 and change_pct < -3:
            score = 3
            reason = "放量下跌（主力出货）"
        
        # 8. 巨量异常（警惕）
        elif volume_ratio > 3:
            score = 4
            reason = "巨量异常（警惕）"
        
        else:
            score = 5
            reason = "正常"
        
        # 根据情绪周期动态调整
        if emotion_stage == "冰点期":
            if volume_ratio < 0.6:
                score = min(15, score + 2)  # 冰点期缩量加分
        elif emotion_stage == "高潮期":
            if volume_ratio > 2.0:
                score = max(3, score - 2)   # 高潮期放量减分
        
        return max(0, min(15, score))
    
    def _get_volume_analysis(self, volume_ratio: float, change_pct: float) -> str:
        """获取量价分析描述"""
        if volume_ratio < 0.6 and change_pct > 0:
            return "缩量创新高，主力高度控盘"
        elif volume_ratio > 1.8 and change_pct > 7:
            return "放量突破，真突破信号"
        elif volume_ratio > 1.2 and change_pct > 3:
            return "价涨量增，健康上涨"
        elif volume_ratio < 0.8 and change_pct > 3:
            return "价涨量缩，上涨乏力，警惕顶部"
        elif volume_ratio > 1.5 and change_pct < -3:
            return "放量下跌，主力出货"
        else:
            return "量价关系正常"
    
    def score_capital(self, stock_data: Dict, df: pd.DataFrame = None) -> Dict:
        """
        资金面评分（30分）⭐ 深度优化
        = 威科夫量价(12分) + 资金流(10分) + 大单(8分)
        
        优化点：
        1. 威科夫分析权重提升到12分
        2. 识别买入高峰/抛售高峰
        3. 识别市场周期（吸筹/派筹）
        """
        # 1. 威科夫量价分析（12分）⭐ 核心
        wyckoff_score = 6  # 默认分数
        wyckoff_signals = []
        wyckoff_phase = "unknown"
        
        if df is not None and len(df) >= 60:
            wyckoff_result = self.wyckoff_analyzer.analyze(df)
            # 威科夫得分归一化到0-12分
            wyckoff_score = (wyckoff_result['score'] / 30) * 12
            wyckoff_signals = wyckoff_result['signals']
            wyckoff_phase = wyckoff_result['phase']
        
        # 2. 资金净流入（10分）
        net_inflow = stock_data.get('net_inflow', 0)
        
        if net_inflow > 5000:
            inflow_score = 10
        elif net_inflow > 2000:
            inflow_score = 8
        elif net_inflow > 500:
            inflow_score = 6
        elif net_inflow > 0:
            inflow_score = 4
        elif net_inflow > -500:
            inflow_score = 3
        else:
            inflow_score = 1
        
        # 3. 大单占比（8分）
        big_order_ratio = stock_data.get('big_order_ratio', 0)
        
        if big_order_ratio > 0.7:
            big_order_score = 8
        elif big_order_ratio > 0.5:
            big_order_score = 6
        elif big_order_ratio > 0.3:
            big_order_score = 4
        else:
            big_order_score = 2
        
        total = wyckoff_score + inflow_score + big_order_score
        
        return {
            "total": round(total, 2),
            "wyckoff_score": round(wyckoff_score, 2),
            "wyckoff_phase": wyckoff_phase,
            "wyckoff_signals": wyckoff_signals,
            "inflow_score": round(inflow_score, 2),
            "big_order_score": round(big_order_score, 2)
        }
    
    def score_technical(self, stock_data: Dict, df: pd.DataFrame = None) -> Dict:
        """
        技术面评分（25分）⭐ 优化
        = 连板高度(10分) + K线形态(8分) + 趋势(7分)
        
        优化点：
        1. 新增K线形态分析（影线、实体）
        2. 识别锤头线、上吊线、十字星
        3. 结合威科夫理论评分
        """
        # 1. 连板高度（10分）
        boards = stock_data.get('consecutive_boards', 0)
        emotion_stage = self.market_emotion['stage']
        
        board_score = self._score_boards(boards, emotion_stage)
        
        # 2. K线形态（8分）⭐ 新增
        candle_score = 4  # 默认分数
        candle_type = "normal"
        
        if df is not None and len(df) >= 2:
            candle_result = self._analyze_candle_pattern(df)
            candle_score = candle_result['score']
            candle_type = candle_result['type']
        
        # 3. 趋势（7分）
        ma_above_count = stock_data.get('ma_above_count', 0)
        
        if ma_above_count >= 4:
            trend_score = 7
        elif ma_above_count == 3:
            trend_score = 5
        elif ma_above_count == 2:
            trend_score = 3
        else:
            trend_score = 1
        
        total = board_score + candle_score + trend_score
        
        return {
            "total": round(total, 2),
            "board_score": round(board_score, 2),
            "candle_score": round(candle_score, 2),
            "candle_type": candle_type,
            "trend_score": round(trend_score, 2),
            "boards": boards
        }
    
    def _score_boards(self, boards: int, emotion_stage: str) -> float:
        """
        连板高度评分（基于情绪周期动态调整）
        
        核心逻辑：
        - 冰点期：首板加分
        - 启动期：2-3连板加分
        - 发酵期：3-4连板加分
        - 高潮期：高连板减分
        """
        # 基础分数
        if boards >= 5:
            base_score = 10
        elif boards == 4:
            base_score = 9
        elif boards == 3:
            base_score = 8
        elif boards == 2:
            base_score = 7
        elif boards == 1:
            base_score = 6
        else:
            base_score = 3
        
        # 根据情绪周期调整
        if emotion_stage == "冰点期":
            if boards == 1:
                base_score = min(10, base_score + 2)
            elif boards >= 4:
                base_score = max(0, base_score - 2)
        
        elif emotion_stage == "启动期":
            if boards in [2, 3]:
                base_score = min(10, base_score + 1)
        
        elif emotion_stage == "发酵期":
            if boards in [3, 4]:
                base_score = min(10, base_score + 1)
        
        elif emotion_stage == "高潮期":
            if boards >= 4:
                base_score = max(0, base_score - 2)
        
        return max(0, min(10, base_score))
    
    def _analyze_candle_pattern(self, df: pd.DataFrame) -> Dict:
        """
        K线形态分析（基于第3章和第6章理论）
        
        识别：
        1. 锤头线（长下影线）= 看涨信号
        2. 上吊线（长上影线）= 看跌信号
        3. 十字星（小实体）= 犹豫不决
        4. 高实体 = 情绪强烈
        """
        latest = df.iloc[-1]
        
        # 计算K线要素
        body_size = abs(latest['close'] - latest['open'])
        total_range = latest['high'] - latest['low']
        
        if total_range == 0:
            return {"score": 4, "type": "normal"}
        
        upper_shadow = latest['high'] - max(latest['open'], latest['close'])
        lower_shadow = min(latest['open'], latest['close']) - latest['low']
        
        lower_shadow_ratio = lower_shadow / total_range
        upper_shadow_ratio = upper_shadow / total_range
        body_ratio = body_size / total_range
        
        # 判断形态
        score = 4
        candle_type = "normal"
        
        # 1. 锤头线（长下影线 > 60%）⭐ 看涨
        if lower_shadow_ratio > 0.6 and body_ratio < 0.3:
            score = 8
            candle_type = "hammer"
        
        # 2. 上吊线（长上影线 > 60%）⚠️ 看跌
        elif upper_shadow_ratio > 0.6 and body_ratio < 0.3:
            score = 2
            candle_type = "hanging_man"
        
        # 3. 十字星（实体很小）
        elif body_ratio < 0.1:
            score = 4
            candle_type = "doji"
        
        # 4. 高实体阳线（实体 > 70%）
        elif body_ratio > 0.7 and latest['close'] > latest['open']:
            score = 7
            candle_type = "strong_bullish"
        
        # 5. 高实体阴线（实体 > 70%）
        elif body_ratio > 0.7 and latest['close'] < latest['open']:
            score = 3
            candle_type = "strong_bearish"
        
        # 6. 正常K线
        else:
            score = 5
            candle_type = "normal"
        
        return {
            "score": max(0, min(8, score)),
            "type": candle_type,
            "lower_shadow_ratio": round(lower_shadow_ratio, 2),
            "upper_shadow_ratio": round(upper_shadow_ratio, 2),
            "body_ratio": round(body_ratio, 2)
        }
    
    def score_theme(self, stock_data: Dict) -> Dict:
        """题材面评分（10分）"""
        theme_level = stock_data.get('theme_level', '无')
        theme_scores = {
            "国家级": 6,
            "部委级": 5,
            "行业级": 4,
            "个股级": 2,
            "无": 0
        }
        theme_score = theme_scores.get(theme_level, 0)
        
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
        """基本面评分（5分）"""
        profit_quarters = stock_data.get('profit_quarters', 4)
        
        if profit_quarters >= 4:
            continuity_score = 3
        elif profit_quarters >= 2:
            continuity_score = 2
        elif profit_quarters >= 1:
            continuity_score = 1
        else:
            continuity_score = -2
        
        profit_growth = stock_data.get('profit_growth', 0)
        
        if profit_growth > 50:
            growth_score = 2
        elif profit_growth > 20:
            growth_score = 1.5
        elif profit_growth > 0:
            growth_score = 1
        else:
            growth_score = 0
        
        total = continuity_score + growth_score
        
        return {
            "total": round(total, 2),
            "continuity_score": round(continuity_score, 2),
            "growth_score": round(growth_score, 2)
        }
    
    def score_stock(self, stock_data: Dict, df: pd.DataFrame = None) -> Dict:
        """
        对单只股票进行完整评分
        
        Args:
            stock_data: 股票数据字典
            df: 历史K线数据（用于威科夫分析和K线形态分析）
        """
        if self.market_emotion is None:
            self.init_market_data()
        
        # 各维度评分
        emotion_result = self.score_emotion(stock_data)
        capital_result = self.score_capital(stock_data, df)
        technical_result = self.score_technical(stock_data, df)
        theme_result = self.score_theme(stock_data)
        fundamental_result = self.score_fundamental(stock_data)
        
        # 计算总分
        total_score = (
            emotion_result['total'] +
            capital_result['total'] +
            technical_result['total'] +
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
            "scores": {
                "emotion": emotion_result,
                "capital": capital_result,
                "technical": technical_result,
                "theme": theme_result,
                "fundamental": fundamental_result
            }
        }


def main():
    """测试函数"""
    scorer = DragonStockScorerV6()
    scorer.init_market_data()
    
    # 测试数据
    test_stock = {
        "code": "600905",
        "name": "三峡能源",
        "consecutive_boards": 3,
        "volume_ratio": 1.8,
        "change_pct": 10.0,
        "is_new_high": False,
        "ma_above_count": 4,
        "net_inflow": 8000,
        "big_order_ratio": 0.65,
        "theme_level": "国家级",
        "popularity": "板块龙头",
        "profit_quarters": 4,
        "profit_growth": 35
    }
    
    # 模拟K线数据
    dates = pd.date_range(start='2024-01-01', periods=60, freq='D')
    df = pd.DataFrame({
        'open': [10 + i*0.1 for i in range(60)],
        'high': [10.5 + i*0.1 for i in range(60)],
        'low': [9.5 + i*0.1 for i in range(60)],
        'close': [10 + i*0.1 for i in range(60)],
        'volume': [1000000 + i*10000 for i in range(60)]
    }, index=dates)
    
    print("=" * 70)
    print("📊 龙头股评分系统 V6.0 - 威科夫理论深度整合")
    print("=" * 70)
    
    result = scorer.score_stock(test_stock, df)
    
    print(f"\n股票: {result['stock_name']} ({result['stock_code']})")
    print(f"总分: {result['total_score']} 分")
    print(f"评级: {result['rating']} - {result['level']}")
    print(f"情绪周期: {result['emotion_cycle']}")
    
    print(f"\n各维度得分:")
    print(f"  📊 情绪面: {result['scores']['emotion']['total']}/30")
    print(f"     - 情绪周期: {result['scores']['emotion']['emotion_score']}/15")
    print(f"     - 量比分析: {result['scores']['emotion']['volume_score']}/15")
    print(f"     - 分析: {result['scores']['emotion']['analysis']}")
    
    print(f"\n  💰 资金面: {result['scores']['capital']['total']}/30")
    print(f"     - 威科夫量价: {result['scores']['capital']['wyckoff_score']}/12 ⭐")
    print(f"     - 资金净流入: {result['scores']['capital']['inflow_score']}/10")
    print(f"     - 大单占比: {result['scores']['capital']['big_order_score']}/8")
    if result['scores']['capital']['wyckoff_signals']:
        print(f"     - 威科夫信号:")
        for signal in result['scores']['capital']['wyckoff_signals']:
            print(f"       {signal}")
    
    print(f"\n  📈 技术面: {result['scores']['technical']['total']}/25")
    print(f"     - 连板高度: {result['scores']['technical']['board_score']}/10")
    print(f"     - K线形态: {result['scores']['technical']['candle_score']}/8 ⭐")
    print(f"     - 形态类型: {result['scores']['technical']['candle_type']}")
    print(f"     - 趋势: {result['scores']['technical']['trend_score']}/7")
    
    print(f"\n  🎯 题材面: {result['scores']['theme']['total']}/10")
    print(f"  📋 基本面: {result['scores']['fundamental']['total']}/5")
    
    return result


if __name__ == "__main__":
    main()
