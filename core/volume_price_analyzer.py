#!/usr/bin/env python3
"""
量价分析模块 - 基于威科夫理论
参考：《量价分析：量价分析创始人威科夫的盘口解读方法》

核心理论：
1. 价格可以被操纵，成交量不能
2. 成交量揭示局内人的真实意图
3. 量价关系决定趋势的真实性

六大核心信号：
1. 放量止跌 = 底部吸筹信号（最强买入）
2. 放量止涨 = 顶部派发信号（最强卖出）
3. 价涨量增 = 趋势健康，继续持有
4. 价涨量缩 = 上涨乏力，警惕顶部
5. 价跌量增 = 趋势健康，空仓观望
6. 价跌量缩 = 下跌乏力，关注底部
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta


class VolumePriceAnalyzer:
    """量价分析器 - 威科夫理论实现"""
    
    def __init__(self):
        self.signals = []
    
    def analyze(self, df: pd.DataFrame) -> Dict:
        """
        完整的量价分析
        
        Args:
            df: 包含 OHLCV 数据的 DataFrame
                必须包含: open, high, low, close, volume
        
        Returns:
            量价分析结果字典
        """
        if len(df) < 20:
            return self._default_result()
        
        # 计算成交量均线
        df = self._calculate_volume_ma(df)
        
        # 1. 识别放量止跌（最强买入信号）
        stopping_volume_down = self._detect_stopping_volume_down(df)
        
        # 2. 识别放量止涨（最强卖出信号）
        stopping_volume_up = self._detect_stopping_volume_up(df)
        
        # 3. 识别量价关系
        volume_price_relation = self._analyze_volume_price_relation(df)
        
        # 4. 识别缩量创新高（主力控盘）
        low_volume_new_high = self._detect_low_volume_new_high(df)
        
        # 5. 识别突破信号
        breakout_signal = self._detect_breakout(df)
        
        # 6. 综合评分
        score = self._calculate_volume_price_score(
            stopping_volume_down,
            stopping_volume_up,
            volume_price_relation,
            low_volume_new_high,
            breakout_signal
        )
        
        return {
            "score": score,
            "stopping_volume_down": stopping_volume_down,
            "stopping_volume_up": stopping_volume_up,
            "volume_price_relation": volume_price_relation,
            "low_volume_new_high": low_volume_new_high,
            "breakout_signal": breakout_signal,
            "signals": self.signals
        }
    
    def _calculate_volume_ma(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算成交量均线"""
        df = df.copy()
        df['volume_ma5'] = df['volume'].rolling(window=5).mean()
        df['volume_ma10'] = df['volume'].rolling(window=10).mean()
        df['volume_ma20'] = df['volume'].rolling(window=20).mean()
        return df
    
    def _detect_stopping_volume_down(self, df: pd.DataFrame) -> Dict:
        """
        检测放量止跌（Stopping Volume - Downside）
        
        特征：
        1. 价格大幅下跌（跌幅>3%）
        2. 成交量明显放大（>2倍均量）
        3. 收盘价接近最高价（下影线长）
        4. 下一根K线向上
        
        含义：局内人在底部大量吸筹，吸收所有抛盘
        """
        if len(df) < 2:
            return {"detected": False, "strength": 0}
        
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        # 1. 价格行为：大幅下跌但收盘价接近最高价
        跌幅 = (latest['close'] - prev['close']) / prev['close'] * 100
        下影线比例 = (latest['close'] - latest['low']) / (latest['high'] - latest['low']) if latest['high'] != latest['low'] else 0
        
        # 2. 成交量：明显放大
        volume_ratio = latest['volume'] / latest['volume_ma5'] if latest['volume_ma5'] > 0 else 1
        
        # 3. 判断条件
        detected = False
        strength = 0
        
        if 跌幅 < -3 and volume_ratio > 2.0 and 下影线比例 > 0.6:
            detected = True
            strength = 10  # 最强信号
            self.signals.append("🔥 放量止跌（底部吸筹信号）")
        elif 跌幅 < -2 and volume_ratio > 1.5 and 下影线比例 > 0.5:
            detected = True
            strength = 8
            self.signals.append("⚠️ 疑似放量止跌")
        
        return {
            "detected": detected,
            "strength": strength,
            "跌幅": round(跌幅, 2),
            "volume_ratio": round(volume_ratio, 2),
            "下影线比例": round(下影线比例, 2)
        }
    
    def _detect_stopping_volume_up(self, df: pd.DataFrame) -> Dict:
        """
        检测放量止涨（Stopping Volume - Upside）
        
        特征：
        1. 价格大幅上涨（涨幅>5%）
        2. 成交量明显放大（>2倍均量）
        3. 收盘价接近最低价（上影线长）
        4. 下一根K线向下
        
        含义：局内人在顶部大量派发，散户接盘
        """
        if len(df) < 2:
            return {"detected": False, "strength": 0}
        
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        # 1. 价格行为：大幅上涨但收盘价接近最低价
        涨幅 = (latest['close'] - prev['close']) / prev['close'] * 100
        上影线比例 = (latest['high'] - latest['close']) / (latest['high'] - latest['low']) if latest['high'] != latest['low'] else 0
        
        # 2. 成交量：明显放大
        volume_ratio = latest['volume'] / latest['volume_ma5'] if latest['volume_ma5'] > 0 else 1
        
        # 3. 判断条件
        detected = False
        strength = 0
        
        if 涨幅 > 5 and volume_ratio > 2.0 and 上影线比例 > 0.6:
            detected = True
            strength = -10  # 负分表示卖出信号
            self.signals.append("🚨 放量止涨（顶部派发信号）")
        elif 涨幅 > 3 and volume_ratio > 1.5 and 上影线比例 > 0.5:
            detected = True
            strength = -8
            self.signals.append("⚠️ 疑似放量止涨")
        
        return {
            "detected": detected,
            "strength": strength,
            "涨幅": round(涨幅, 2),
            "volume_ratio": round(volume_ratio, 2),
            "上影线比例": round(上影线比例, 2)
        }
    
    def _analyze_volume_price_relation(self, df: pd.DataFrame) -> Dict:
        """
        分析量价关系
        
        四种基本关系：
        1. 价涨量增 = 健康上涨（正常）
        2. 价涨量缩 = 上涨乏力（背离）
        3. 价跌量增 = 健康下跌（正常）
        4. 价跌量缩 = 下跌乏力（背离）
        """
        if len(df) < 2:
            return {"relation": "未知", "score": 0}
        
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        # 价格变化
        price_change = (latest['close'] - prev['close']) / prev['close'] * 100
        
        # 成交量变化
        volume_change = (latest['volume'] - prev['volume']) / prev['volume'] * 100 if prev['volume'] > 0 else 0
        
        # 判断关系
        if price_change > 0 and volume_change > 0:
            relation = "价涨量增"
            score = 8  # 健康上涨
            self.signals.append("✅ 价涨量增（趋势健康）")
        elif price_change > 0 and volume_change < 0:
            relation = "价涨量缩"
            score = 3  # 上涨乏力
            self.signals.append("⚠️ 价涨量缩（上涨乏力）")
        elif price_change < 0 and volume_change > 0:
            relation = "价跌量增"
            score = 0  # 健康下跌
            self.signals.append("❌ 价跌量增（下跌趋势）")
        elif price_change < 0 and volume_change < 0:
            relation = "价跌量缩"
            score = 5  # 下跌乏力
            self.signals.append("⚠️ 价跌量缩（可能见底）")
        else:
            relation = "横盘"
            score = 4
        
        return {
            "relation": relation,
            "score": score,
            "price_change": round(price_change, 2),
            "volume_change": round(volume_change, 2)
        }
    
    def _detect_low_volume_new_high(self, df: pd.DataFrame) -> Dict:
        """
        检测缩量创新高
        
        特征：
        1. 价格创近期新高（20日内）
        2. 成交量明显缩小（<0.5倍均量）
        
        含义：主力高度控盘，惜售
        """
        if len(df) < 20:
            return {"detected": False, "strength": 0}
        
        latest = df.iloc[-1]
        recent_20 = df.iloc[-20:]
        
        # 1. 是否创新高
        is_new_high = latest['close'] >= recent_20['close'].max()
        
        # 2. 成交量是否缩小
        volume_ratio = latest['volume'] / latest['volume_ma5'] if latest['volume_ma5'] > 0 else 1
        
        detected = False
        strength = 0
        
        if is_new_high and volume_ratio < 0.5:
            detected = True
            strength = 9  # 强烈的控盘信号
            self.signals.append("🔥 缩量创新高（主力控盘）")
        elif is_new_high and volume_ratio < 0.8:
            detected = True
            strength = 6
            self.signals.append("✅ 缩量新高（惜售）")
        
        return {
            "detected": detected,
            "strength": strength,
            "is_new_high": is_new_high,
            "volume_ratio": round(volume_ratio, 2)
        }
    
    def _detect_breakout(self, df: pd.DataFrame) -> Dict:
        """
        检测突破信号
        
        真突破的特征：
        1. 突破关键阻力位（20日高点）
        2. 成交量明显放大（>1.5倍均量）
        3. 收盘价远离突破位（>3%）
        
        假突破的特征：
        1. 成交量很小（<均量）
        2. 收盘价接近突破位
        """
        if len(df) < 20:
            return {"detected": False, "is_real": False, "strength": 0}
        
        latest = df.iloc[-1]
        recent_20 = df.iloc[-20:-1]  # 排除最新一根
        
        # 1. 是否突破20日高点
        resistance = recent_20['high'].max()
        is_breakout = latest['close'] > resistance
        
        if not is_breakout:
            return {"detected": False, "is_real": False, "strength": 0}
        
        # 2. 成交量是否放大
        volume_ratio = latest['volume'] / latest['volume_ma5'] if latest['volume_ma5'] > 0 else 1
        
        # 3. 突破幅度
        breakout_pct = (latest['close'] - resistance) / resistance * 100
        
        # 判断真假突破
        detected = True
        is_real = False
        strength = 0
        
        if volume_ratio > 1.5 and breakout_pct > 3:
            is_real = True
            strength = 8  # 真突破
            self.signals.append("🚀 放量突破（真突破）")
        elif volume_ratio > 1.2 and breakout_pct > 1:
            is_real = True
            strength = 6
            self.signals.append("✅ 突破确认")
        else:
            is_real = False
            strength = 2  # 假突破
            self.signals.append("⚠️ 疑似假突破")
        
        return {
            "detected": detected,
            "is_real": is_real,
            "strength": strength,
            "volume_ratio": round(volume_ratio, 2),
            "breakout_pct": round(breakout_pct, 2)
        }
    
    def _calculate_volume_price_score(
        self,
        stopping_volume_down: Dict,
        stopping_volume_up: Dict,
        volume_price_relation: Dict,
        low_volume_new_high: Dict,
        breakout_signal: Dict
    ) -> float:
        """
        计算量价分析综合得分（满分10分）
        
        评分逻辑：
        1. 放量止跌 = +10分（最强买入信号）
        2. 缩量创新高 = +9分（主力控盘）
        3. 放量突破 = +8分（趋势确认）
        4. 价涨量增 = +8分（健康上涨）
        5. 价涨量缩 = +3分（上涨乏力）
        6. 价跌量缩 = +5分（下跌乏力）
        7. 放量止涨 = -10分（顶部派发）
        8. 价跌量增 = 0分（健康下跌）
        """
        score = 0
        
        # 1. 放量止跌（最高优先级）
        if stopping_volume_down['detected']:
            score = stopping_volume_down['strength']
            return min(10, score)  # 直接返回，不叠加其他信号
        
        # 2. 放量止涨（最高优先级，负分）
        if stopping_volume_up['detected']:
            score = stopping_volume_up['strength']
            return max(0, score)  # 负分转为0分
        
        # 3. 缩量创新高
        if low_volume_new_high['detected']:
            score += low_volume_new_high['strength']
        
        # 4. 突破信号
        if breakout_signal['detected'] and breakout_signal['is_real']:
            score += breakout_signal['strength']
        
        # 5. 量价关系
        score += volume_price_relation['score']
        
        # 限制在0-10分
        return min(10, max(0, score))
    
    def _default_result(self) -> Dict:
        """默认结果"""
        return {
            "score": 5,
            "stopping_volume_down": {"detected": False, "strength": 0},
            "stopping_volume_up": {"detected": False, "strength": 0},
            "volume_price_relation": {"relation": "未知", "score": 5},
            "low_volume_new_high": {"detected": False, "strength": 0},
            "breakout_signal": {"detected": False, "is_real": False, "strength": 0},
            "signals": ["数据不足"]
        }


def test_analyzer():
    """测试函数"""
    # 模拟数据
    dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
    
    # 模拟一个放量止跌的案例
    data = {
        'open': [10 + i*0.1 for i in range(30)],
        'high': [10.5 + i*0.1 for i in range(30)],
        'low': [9.5 + i*0.1 for i in range(30)],
        'close': [10 + i*0.1 for i in range(30)],
        'volume': [1000000 + i*10000 for i in range(30)]
    }
    
    # 最后一天：大跌但收盘价接近最高价，成交量放大
    data['close'][-1] = data['close'][-2] * 0.95  # 跌5%
    data['low'][-1] = data['close'][-1] * 0.97    # 下影线长
    data['high'][-1] = data['close'][-1] * 1.01
    data['volume'][-1] = data['volume'][-2] * 2.5  # 放量2.5倍
    
    df = pd.DataFrame(data, index=dates)
    
    analyzer = VolumePriceAnalyzer()
    result = analyzer.analyze(df)
    
    print("=" * 70)
    print("📊 量价分析测试")
    print("=" * 70)
    print(f"\n综合得分: {result['score']}/10")
    print(f"\n检测到的信号:")
    for signal in result['signals']:
        print(f"  {signal}")
    
    print(f"\n详细结果:")
    print(f"  放量止跌: {result['stopping_volume_down']}")
    print(f"  放量止涨: {result['stopping_volume_up']}")
    print(f"  量价关系: {result['volume_price_relation']}")
    print(f"  缩量创新高: {result['low_volume_new_high']}")
    print(f"  突破信号: {result['breakout_signal']}")


if __name__ == "__main__":
    test_analyzer()
