#!/usr/bin/env python3
"""
量比评分系统 v2.0
基于小欧核心经验：量比是核心指标（权重 30%）

核心逻辑：
1. 量比 < 0.5 + 创新高 = 主力高度控盘（15分）
2. 量比 > 1.5 + 上涨 = 放量进攻（12分）
3. 量比 0.8-1.2 = 正常（8分）
4. 量比异常（过高或过低）= 风险（低分）

评分标准（满分 30 分）：
- 基础分（0-15分）：根据量比区间
- 加分项（0-15分）：结合价格走势和创新高
"""

import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json


class VolumeRatioScorer:
    """量比评分器"""
    
    def __init__(self):
        self.max_score = 30  # 量比最高 30 分
        
    def get_stock_data(self, stock_code: str, days: int = 60) -> Optional[pd.DataFrame]:
        """
        获取股票历史数据
        
        Args:
            stock_code: 股票代码（如 "000001"）
            days: 获取天数
            
        Returns:
            DataFrame with columns: date, open, high, low, close, volume
        """
        try:
            # 转换股票代码格式
            if stock_code.startswith('6'):
                symbol = f"sh{stock_code}"
            else:
                symbol = f"sz{stock_code}"
            
            # 获取历史数据
            df = ak.stock_zh_a_hist(symbol=stock_code, period="daily", adjust="qfq")
            
            if df.empty:
                return None
            
            # 重命名列
            df = df.rename(columns={
                '日期': 'date',
                '开盘': 'open',
                '最高': 'high',
                '最低': 'low',
                '收盘': 'close',
                '成交量': 'volume',
                '成交额': 'amount',
                '涨跌幅': 'change_pct'
            })
            
            return df.tail(days)
            
        except Exception as e:
            print(f"获取股票数据失败 {stock_code}: {e}")
            return None
    
    def calculate_volume_ratio(self, df: pd.DataFrame) -> float:
        """
        计算量比
        量比 = 今日成交量 / 5日平均成交量
        """
        if len(df) < 6:
            return 1.0
        
        today_vol = df.iloc[-1]['volume']
        avg_vol = df.iloc[-6:-1]['volume'].mean()
        
        volume_ratio = today_vol / avg_vol if avg_vol > 0 else 1.0
        return round(volume_ratio, 2)
    
    def is_new_high(self, df: pd.DataFrame, days: int = 20) -> bool:
        """
        判断是否创新高
        
        Args:
            days: 多少天内的新高（默认 20 天）
        """
        if len(df) < days:
            return False
        
        recent_df = df.tail(days)
        today_close = df.iloc[-1]['close']
        max_close = recent_df['close'].max()
        
        # 今日收盘价是否等于或接近最高价（允许 0.5% 误差）
        return today_close >= max_close * 0.995
    
    def get_price_change(self, df: pd.DataFrame) -> float:
        """获取今日涨跌幅"""
        if 'change_pct' in df.columns:
            return df.iloc[-1]['change_pct']
        
        # 手动计算
        today_close = df.iloc[-1]['close']
        yesterday_close = df.iloc[-2]['close']
        change_pct = (today_close - yesterday_close) / yesterday_close * 100
        return round(change_pct, 2)
    
    def score_volume_ratio(self, volume_ratio: float, price_change: float, 
                          is_new_high: bool) -> Dict:
        """
        量比评分核心算法
        
        Args:
            volume_ratio: 量比
            price_change: 涨跌幅（%）
            is_new_high: 是否创新高
            
        Returns:
            {
                "score": 总分,
                "base_score": 基础分,
                "bonus_score": 加分,
                "reason": 评分理由,
                "signal": 信号类型
            }
        """
        base_score = 0
        bonus_score = 0
        reason = []
        signal = "中性"
        
        # === 基础分（0-15分）===
        
        # 1. 缩量创新高 = 主力高度控盘（最高分）
        if volume_ratio < 0.5 and is_new_high:
            base_score = 15
            reason.append(f"缩量创新高(量比{volume_ratio})，主力高度控盘")
            signal = "强烈看多"
        
        # 2. 缩量 + 上涨（但未创新高）
        elif volume_ratio < 0.8 and price_change > 0:
            base_score = 12
            reason.append(f"缩量上涨(量比{volume_ratio})，筹码稳定")
            signal = "看多"
        
        # 3. 缩量 + 下跌 = 可能是洗盘
        elif volume_ratio < 0.8 and price_change < 0:
            base_score = 8
            reason.append(f"缩量下跌(量比{volume_ratio})，可能洗盘")
            signal = "观望"
        
        # 4. 放量突破 = 主力进攻
        elif volume_ratio > 1.5 and price_change > 3:
            base_score = 14
            reason.append(f"放量突破(量比{volume_ratio})，主力进攻")
            signal = "强烈看多"
        
        # 5. 放量上涨（涨幅 0-3%）
        elif volume_ratio > 1.5 and 0 < price_change <= 3:
            base_score = 11
            reason.append(f"放量上涨(量比{volume_ratio})，资金活跃")
            signal = "看多"
        
        # 6. 放量下跌 = 可能出货
        elif volume_ratio > 1.5 and price_change < -3:
            base_score = 3
            reason.append(f"放量下跌(量比{volume_ratio})，可能出货")
            signal = "看空"
        
        # 7. 量比正常（0.8-1.2）
        elif 0.8 <= volume_ratio <= 1.2:
            if price_change > 0:
                base_score = 9
                reason.append(f"量比正常(量比{volume_ratio})，温和上涨")
                signal = "中性偏多"
            else:
                base_score = 6
                reason.append(f"量比正常(量比{volume_ratio})，温和下跌")
                signal = "中性"
        
        # 8. 量比异常（过高 > 3）
        elif volume_ratio > 3:
            base_score = 5
            reason.append(f"量比过高(量比{volume_ratio})，警惕风险")
            signal = "警惕"
        
        # 9. 其他情况
        else:
            base_score = 7
            reason.append(f"量比{volume_ratio}，观察中")
            signal = "中性"
        
        # === 加分项（0-15分）===
        
        # 1. 创新高加分
        if is_new_high:
            bonus_score += 5
            reason.append("创20日新高")
        
        # 2. 涨停或接近涨停
        if price_change >= 9.5:
            bonus_score += 5
            reason.append(f"涨停({price_change}%)")
        elif price_change >= 7:
            bonus_score += 3
            reason.append(f"大涨({price_change}%)")
        
        # 3. 量比与涨幅配合度
        if volume_ratio > 1.5 and price_change > 5:
            bonus_score += 3
            reason.append("量价配合良好")
        elif volume_ratio < 0.8 and price_change > 3:
            bonus_score += 4
            reason.append("缩量上涨，控盘强")
        
        # 4. 连续上涨加分（需要历史数据，这里简化）
        # TODO: 后续可以加入连续上涨天数判断
        
        # 总分
        total_score = min(base_score + bonus_score, self.max_score)
        
        return {
            "score": total_score,
            "base_score": base_score,
            "bonus_score": bonus_score,
            "reason": " | ".join(reason),
            "signal": signal,
            "volume_ratio": volume_ratio
        }
    
    def analyze_stock(self, stock_code: str, stock_name: str = "") -> Dict:
        """
        分析单只股票的量比评分
        
        Args:
            stock_code: 股票代码
            stock_name: 股票名称（可选）
            
        Returns:
            完整的量比分析结果
        """
        print(f"\n{'='*60}")
        print(f"📊 量比评分分析: {stock_name}({stock_code})")
        print(f"{'='*60}")
        
        # 1. 获取股票数据
        df = self.get_stock_data(stock_code)
        if df is None or len(df) < 6:
            return {
                "stock_code": stock_code,
                "stock_name": stock_name,
                "error": "数据不足",
                "score": 0
            }
        
        # 2. 计算量比
        volume_ratio = self.calculate_volume_ratio(df)
        print(f"量比: {volume_ratio}")
        
        # 3. 判断是否创新高
        is_new_high = self.is_new_high(df, days=20)
        print(f"20日新高: {'是' if is_new_high else '否'}")
        
        # 4. 获取涨跌幅
        price_change = self.get_price_change(df)
        print(f"今日涨跌幅: {price_change}%")
        
        # 5. 评分
        score_result = self.score_volume_ratio(volume_ratio, price_change, is_new_high)
        
        print(f"\n📈 评分结果:")
        print(f"   总分: {score_result['score']}/{self.max_score}")
        print(f"   基础分: {score_result['base_score']}")
        print(f"   加分: {score_result['bonus_score']}")
        print(f"   信号: {score_result['signal']}")
        print(f"   理由: {score_result['reason']}")
        print(f"{'='*60}\n")
        
        # 组合完整结果
        result = {
            "stock_code": stock_code,
            "stock_name": stock_name,
            "date": str(df.iloc[-1]['date']),
            "close": float(df.iloc[-1]['close']),
            "volume": int(df.iloc[-1]['volume']),
            "volume_ratio": float(volume_ratio),
            "price_change": float(price_change),
            "is_new_high": bool(is_new_high),
            "score": int(score_result['score']),
            "base_score": int(score_result['base_score']),
            "bonus_score": int(score_result['bonus_score']),
            "reason": score_result['reason'],
            "signal": score_result['signal']
        }
        
        return result
    
    def batch_analyze(self, stock_list: List[Tuple[str, str]]) -> List[Dict]:
        """
        批量分析股票
        
        Args:
            stock_list: [(股票代码, 股票名称), ...]
            
        Returns:
            分析结果列表，按得分排序
        """
        results = []
        
        for stock_code, stock_name in stock_list:
            result = self.analyze_stock(stock_code, stock_name)
            if "error" not in result:
                results.append(result)
        
        # 按得分排序
        results.sort(key=lambda x: x['score'], reverse=True)
        
        return results


def main():
    """主函数 - 测试量比评分系统"""
    scorer = VolumeRatioScorer()
    
    # 测试股票列表（从今天的涨停板中选几个）
    test_stocks = [
        ("002261", "拓维信息"),
        ("601868", "中国能建"),
        ("002506", "协鑫集成"),
        ("000533", "顺钠股份"),
        ("600821", "金开新能"),
    ]
    
    print("🚀 量比评分系统 v2.0 - 测试运行")
    print("基于小欧核心经验：量比是核心指标（权重 30%）\n")
    
    # 批量分析
    results = scorer.batch_analyze(test_stocks)
    
    # 输出排名
    print("\n" + "="*60)
    print("📊 量比评分排名（TOP 5）")
    print("="*60)
    print(f"{'排名':<6}{'股票':<20}{'量比':<10}{'涨跌幅':<10}{'得分':<10}{'信号':<15}")
    print("-"*60)
    
    for i, result in enumerate(results[:5], 1):
        print(f"{i:<6}{result['stock_name']}({result['stock_code']})<20"
              f"{result['volume_ratio']:<10}{result['price_change']}%<10"
              f"{result['score']}/{scorer.max_score}<10{result['signal']:<15}")
    
    print("="*60)
    
    # 保存结果
    output_file = "volume_ratio_scores.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 结果已保存到: {output_file}")
    
    return results


if __name__ == "__main__":
    main()
