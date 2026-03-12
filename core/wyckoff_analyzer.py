#!/usr/bin/env python3
"""
威科夫量价分析器 - 基于第2-5章核心理论
Wyckoff Volume Price Analysis

核心理论：
1. 成交量是唯一不能伪造的指标（第2章）
2. 价格只是故事的一部分，影线揭示情绪（第3章）
3. 只寻找两件事：确认 or 异常（第4章）
4. 识别市场周期：吸筹/派筹/测试/高峰（第5章）

评分逻辑：
- 买入高峰（长下影线+高成交量）= +20分 ⭐⭐⭐
- 供给测试成功（长下影线+低成交量）= +15分
- 价涨量增（确认）= +10分
- 缩量创新高（主力控盘）= +12分
- 抛售高峰（长上影线+高成交量）= -20分 ⚠️
- 需求测试成功（长上影线+低成交量）= -15分
- 价涨量缩（异常）= -8分
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime


class WyckoffAnalyzer:
    """威科夫量价分析器"""
    
    def __init__(self):
        self.signals = []
        self.phase = None
        self.confidence = 0
    
    def analyze(self, df: pd.DataFrame) -> Dict:
        """
        完整的威科夫量价分析
        
        Args:
            df: OHLCV数据，必须包含 open, high, low, close, volume
        
        Returns:
            分析结果字典
        """
        if len(df) < 60:  # 至少需要60根K线
            return self._default_result()
        
        self.signals = []
        
        # 计算成交量均线（相对性原则）
        df = self._calculate_volume_ma(df)
        
        # 第一步：微观分析（单根K线）
        single_result = self._analyze_single_candle(df)
        
        # 第二步：宏观分析（相邻K线，识别小趋势）
        trend_result = self._analyze_trend(df)
        
        # 第三步：全局分析（识别市场周期）
        phase_result = self._identify_market_phase(df)
        
        # 第四步：综合评分
        score = self._calculate_score(single_result, trend_result, phase_result)
        
        return {
            "score": score,
            "phase": self.phase,
            "confidence": self.confidence,
            "single_candle": single_result,
            "trend": trend_result,
            "phase_detail": phase_result,
            "signals": self.signals
        }
    
    def _calculate_volume_ma(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算成交量均线（相对性原则）"""
        df = df.copy()
        df['volume_ma5'] = df['volume'].rolling(window=5).mean()
        df['volume_ma20'] = df['volume'].rolling(window=20).mean()
        df['volume_ma60'] = df['volume'].rolling(window=60).mean()
        return df
    
    def _analyze_single_candle(self, df: pd.DataFrame) -> Dict:
        """
        微观分析：单根K线的量价关系
        
        核心：投入产出定律
        - 大产出（长实体）需要大投入（高成交量）
        - 小产出（短实体）只需小投入（低成交量）
        - 不匹配 = 异常
        """
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        # 计算K线要素
        body_size = abs(latest['close'] - latest['open'])
        total_range = latest['high'] - latest['low']
        upper_shadow = latest['high'] - max(latest['open'], latest['close'])
        lower_shadow = min(latest['open'], latest['close']) - latest['low']
        
        # 计算相对成交量
        volume_ratio_5 = latest['volume'] / latest['volume_ma5'] if latest['volume_ma5'] > 0 else 1
        volume_ratio_20 = latest['volume'] / latest['volume_ma20'] if latest['volume_ma20'] > 0 else 1
        
        # 计算涨跌幅
        change_pct = (latest['close'] - prev['close']) / prev['close'] * 100
        
        # 判断影线比例
        lower_shadow_ratio = lower_shadow / total_range if total_range > 0 else 0
        upper_shadow_ratio = upper_shadow / total_range if total_range > 0 else 0
        body_ratio = body_size / total_range if total_range > 0 else 0
        
        result = {
            "body_size": body_size,
            "body_ratio": round(body_ratio, 2),
            "lower_shadow_ratio": round(lower_shadow_ratio, 2),
            "upper_shadow_ratio": round(upper_shadow_ratio, 2),
            "volume_ratio_5": round(volume_ratio_5, 2),
            "volume_ratio_20": round(volume_ratio_20, 2),
            "change_pct": round(change_pct, 2),
            "type": "unknown"
        }
        
        # 1. 买入高峰（Buying Climax）⭐⭐⭐
        if (lower_shadow_ratio > 0.6 and 
            volume_ratio_20 > 1.5 and 
            change_pct < -2):
            result["type"] = "buying_climax"
            result["score"] = 20
            self.signals.append("🔥 买入高峰（抄底机会）")
        
        # 2. 抛售高峰（Selling Climax）⚠️
        elif (upper_shadow_ratio > 0.6 and 
              volume_ratio_20 > 1.5 and 
              change_pct > 3):
            result["type"] = "selling_climax"
            result["score"] = -20
            self.signals.append("🚨 抛售高峰（逃顶信号）")
        
        # 3. 供给测试（Supply Test）
        elif (lower_shadow_ratio > 0.5 and 
              volume_ratio_20 < 0.8 and 
              change_pct < 0):
            result["type"] = "supply_test"
            result["score"] = 15
            self.signals.append("✅ 供给测试成功（卖盘被吸收）")
        
        # 4. 需求测试（Demand Test）
        elif (upper_shadow_ratio > 0.5 and 
              volume_ratio_20 < 0.8 and 
              change_pct > 0):
            result["type"] = "demand_test"
            result["score"] = -15
            self.signals.append("⚠️ 需求测试成功（买盘被满足）")
        
        # 5. 确认：长阳线 + 高成交量
        elif (body_ratio > 0.7 and 
              change_pct > 3 and 
              volume_ratio_20 > 1.2):
            result["type"] = "confirmed_bullish"
            result["score"] = 10
            self.signals.append("✅ 价涨量增（确认上涨）")
        
        # 6. 异常：长阳线 + 低成交量（多头陷阱）
        elif (body_ratio > 0.7 and 
              change_pct > 3 and 
              volume_ratio_20 < 0.8):
            result["type"] = "anomaly_bull_trap"
            result["score"] = -10
            self.signals.append("⚠️ 长阳线+低成交量（多头陷阱）")
        
        # 7. 异常：短阳线 + 高成交量（市场走弱）
        elif (body_ratio < 0.3 and 
              change_pct > 0 and 
              volume_ratio_20 > 1.5):
            result["type"] = "anomaly_weakness"
            result["score"] = -8
            self.signals.append("⚠️ 短阳线+高成交量（市场走弱）")
        
        # 8. 缩量创新高（主力控盘）
        elif self._is_new_high(df) and volume_ratio_20 < 0.6:
            result["type"] = "low_volume_new_high"
            result["score"] = 12
            self.signals.append("🔥 缩量创新高（主力控盘）")
        
        # 9. 确认：短阳线 + 低成交量
        elif (body_ratio < 0.3 and 
              change_pct > 0 and 
              volume_ratio_20 < 0.8):
            result["type"] = "confirmed_weak"
            result["score"] = 5
            self.signals.append("✅ 短阳线+低成交量（确认）")
        
        else:
            result["type"] = "normal"
            result["score"] = 5
        
        return result
    
    def _analyze_trend(self, df: pd.DataFrame) -> Dict:
        """
        宏观分析：相邻K线的趋势
        
        核心：趋势中的量价关系
        - 上涨趋势：价格上涨 + 成交量放大 = 确认
        - 上涨趋势：价格上涨 + 成交量缩小 = 异常
        """
        recent = df.iloc[-4:]  # 最近4根K线
        
        if len(recent) < 4:
            return {"type": "unknown", "score": 0}
        
        # 判断趋势方向
        closes = recent['close'].values
        volumes = recent['volume'].values
        
        # 价格趋势
        price_trend = "up" if closes[-1] > closes[0] else "down" if closes[-1] < closes[0] else "flat"
        
        # 成交量趋势
        volume_trend = "increasing" if volumes[-1] > volumes[0] else "decreasing"
        
        result = {
            "price_trend": price_trend,
            "volume_trend": volume_trend,
            "type": "unknown",
            "score": 0
        }
        
        # 1. 上涨趋势 + 成交量递增 = 确认
        if price_trend == "up" and volume_trend == "increasing":
            result["type"] = "confirmed_uptrend"
            result["score"] = 10
            self.signals.append("✅ 上涨趋势确认（价涨量增）")
        
        # 2. 上涨趋势 + 成交量递减 = 异常
        elif price_trend == "up" and volume_trend == "decreasing":
            result["type"] = "anomaly_uptrend"
            result["score"] = -8
            self.signals.append("⚠️ 上涨趋势异常（价涨量缩）")
        
        # 3. 下跌趋势 + 成交量递增 = 确认
        elif price_trend == "down" and volume_trend == "increasing":
            result["type"] = "confirmed_downtrend"
            result["score"] = -10
            self.signals.append("❌ 下跌趋势确认（价跌量增）")
        
        # 4. 下跌趋势 + 成交量递减 = 异常（可能见底）
        elif price_trend == "down" and volume_trend == "decreasing":
            result["type"] = "anomaly_downtrend"
            result["score"] = 8
            self.signals.append("✅ 下跌趋势异常（价跌量缩，可能见底）")
        
        return result
    
    def _identify_market_phase(self, df: pd.DataFrame) -> Dict:
        """
        全局分析：识别市场周期
        
        威科夫市场周期：
        1. 吸筹（Accumulation）
        2. 买入高峰（Buying Climax）
        3. 供给测试（Supply Test）
        4. 上涨（Markup）
        5. 派筹（Distribution）
        6. 抛售高峰（Selling Climax）
        7. 需求测试（Demand Test）
        8. 下跌（Markdown）
        """
        recent_20 = df.iloc[-20:]
        recent_60 = df.iloc[-60:]
        
        # 判断是否在横盘整理
        price_range = recent_20['high'].max() - recent_20['low'].min()
        avg_price = recent_20['close'].mean()
        range_pct = (price_range / avg_price) * 100
        
        is_consolidation = range_pct < 10  # 波动幅度小于10%
        
        # 判断前期趋势
        long_term_change = (recent_60['close'].iloc[-1] - recent_60['close'].iloc[0]) / recent_60['close'].iloc[0] * 100
        
        result = {
            "phase": "unknown",
            "confidence": 0,
            "score": 0
        }
        
        # 1. 吸筹阶段（下跌后横盘）
        if is_consolidation and long_term_change < -10:
            result["phase"] = "accumulation"
            result["confidence"] = 70
            result["score"] = 15
            self.signals.append("📦 吸筹阶段（局内人买入）")
        
        # 2. 派筹阶段（上涨后横盘）
        elif is_consolidation and long_term_change > 10:
            result["phase"] = "distribution"
            result["confidence"] = 70
            result["score"] = -15
            self.signals.append("📤 派筹阶段（局内人卖出）")
        
        # 3. 上涨阶段
        elif long_term_change > 15:
            result["phase"] = "markup"
            result["confidence"] = 80
            result["score"] = 10
            self.signals.append("📈 上涨阶段")
        
        # 4. 下跌阶段
        elif long_term_change < -15:
            result["phase"] = "markdown"
            result["confidence"] = 80
            result["score"] = -10
            self.signals.append("📉 下跌阶段")
        
        self.phase = result["phase"]
        self.confidence = result["confidence"]
        
        return result
    
    def _is_new_high(self, df: pd.DataFrame, period: int = 20) -> bool:
        """判断是否创新高"""
        if len(df) < period:
            return False
        recent = df.iloc[-period:]
        return df.iloc[-1]['close'] >= recent['close'].max()
    
    def _calculate_score(self, single: Dict, trend: Dict, phase: Dict) -> float:
        """
        综合评分（满分30分）
        
        权重分配：
        - 单根K线：40%（12分）
        - 趋势分析：30%（9分）
        - 市场周期：30%（9分）
        """
        # 单根K线得分（-20 到 +20）
        single_score = single.get("score", 0)
        
        # 趋势得分（-10 到 +10）
        trend_score = trend.get("score", 0)
        
        # 市场周期得分（-15 到 +15）
        phase_score = phase.get("score", 0)
        
        # 归一化到0-30分
        # 最高分：20 + 10 + 15 = 45 → 30分
        # 最低分：-20 - 10 - 15 = -45 → 0分
        total = single_score + trend_score + phase_score
        
        # 线性映射：[-45, 45] → [0, 30]
        normalized = ((total + 45) / 90) * 30
        
        return round(max(0, min(30, normalized)), 2)
    
    def _default_result(self) -> Dict:
        """数据不足时的默认结果"""
        return {
            "score": 15,
            "phase": "unknown",
            "confidence": 0,
            "single_candle": {"type": "unknown", "score": 0},
            "trend": {"type": "unknown", "score": 0},
            "phase_detail": {"phase": "unknown", "score": 0},
            "signals": ["数据不足（需要至少60根K线）"]
        }


def test_analyzer():
    """测试函数"""
    # 模拟买入高峰的数据
    dates = pd.date_range(start='2024-01-01', periods=60, freq='D')
    
    # 前50天：下跌趋势
    data = {
        'open': [100 - i*0.5 for i in range(60)],
        'high': [101 - i*0.5 for i in range(60)],
        'low': [99 - i*0.5 for i in range(60)],
        'close': [100 - i*0.5 for i in range(60)],
        'volume': [1000000 + i*5000 for i in range(60)]
    }
    
    # 最后一天：买入高峰（长下影线 + 高成交量）
    data['open'][-1] = 70
    data['high'][-1] = 71
    data['low'][-1] = 65  # 长下影线
    data['close'][-1] = 70  # 收盘价接近开盘价
    data['volume'][-1] = 3000000  # 成交量放大3倍
    
    df = pd.DataFrame(data, index=dates)
    
    analyzer = WyckoffAnalyzer()
    result = analyzer.analyze(df)
    
    print("=" * 70)
    print("📊 威科夫量价分析测试")
    print("=" * 70)
    print(f"\n综合得分: {result['score']}/30")
    print(f"市场周期: {result['phase']} (置信度: {result['confidence']}%)")
    
    print(f"\n检测到的信号:")
    for signal in result['signals']:
        print(f"  {signal}")
    
    print(f"\n详细分析:")
    print(f"  单根K线: {result['single_candle']['type']} (得分: {result['single_candle'].get('score', 0)})")
    print(f"  趋势分析: {result['trend']['type']} (得分: {result['trend'].get('score', 0)})")
    print(f"  市场周期: {result['phase_detail']['phase']} (得分: {result['phase_detail'].get('score', 0)})")


if __name__ == "__main__":
    test_analyzer()
