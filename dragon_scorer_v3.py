#!/usr/bin/env python3
"""
龙头股评分系统 V3.0
基于小欧 16 年实战经验的完整评分系统

核心理念：
- 情绪优先：市场情绪 > 技术形态 > 基本面
- 量比核心：量比是核心指标（权重 30%）
- 主流为王：主流题材 + 主动上涨 + 主升浪

评分公式（总分 100）：
情绪面 (30分) = 情绪周期(15分) + 量比(15分)
资金面 (30分) = 资金净流入(15分) + 大单占比(15分)
技术面 (25分) = 连板高度(10分) + 封板质量(8分) + 趋势(7分)
题材面 (15分) = 主线题材(10分) + 人气辨识度(5分)

整合模块：
- emotion_cycle.py - 情绪周期识别
- volume_ratio_scorer.py - 量比评分
- theme_detector.py - 主流题材识别
"""

import sys
import json
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd

# 导入自定义模块
from emotion_cycle import EmotionCycleDetector
from volume_ratio_scorer import VolumeRatioScorer
from theme_detector import ThemeDetector


class DragonStockScorerV3:
    """龙头股评分系统 V3.0"""
    
    def __init__(self):
        # 初始化各个子系统
        self.emotion_detector = EmotionCycleDetector()
        self.volume_scorer = VolumeRatioScorer()
        self.theme_detector = ThemeDetector()
        
        # 当前市场状态（缓存）
        self.market_emotion = None
        self.main_theme = None
        
    def init_market_context(self):
        """初始化市场环境（情绪周期 + 主流题材）"""
        print("🔄 初始化市场环境...")
        
        # 1. 识别情绪周期
        print("\n1️⃣ 识别情绪周期...")
        self.market_emotion = self.emotion_detector.analyze()
        
        # 2. 识别主流题材
        print("\n2️⃣ 识别主流题材...")
        self.main_theme = self.theme_detector.detect_main_theme()
        
        print("\n✅ 市场环境初始化完成\n")
    
    def score_emotion(self, stock_code: str, stock_name: str) -> Dict:
        """
        情绪面评分（30分）
        = 情绪周期得分(15分) + 量比得分(15分)
        """
        # 1. 情绪周期得分（15分）
        emotion_cycle = self.market_emotion['emotion_cycle']
        stage = emotion_cycle['stage']
        
        # 根据情绪周期给分
        stage_scores = {
            "冰点期": 5,   # 冰点期：低分，等待启动
            "启动期": 15,  # 启动期：满分，追启动初期
            "发酵期": 12,  # 发酵期：高分，主升浪
            "高潮期": 8,   # 高潮期：中分，准备减仓
            "退潮期": 3    # 退潮期：低分，杀下跌之际
        }
        emotion_score = stage_scores.get(stage, 10)
        
        # 2. 量比得分（15分，从30分制转换）
        volume_result = self.volume_scorer.analyze_stock(stock_code, stock_name)
        if "error" in volume_result:
            volume_score = 7  # 默认分
        else:
            # 将30分制转换为15分制
            volume_score = round(volume_result['score'] * 15 / 30, 1)
        
        total_emotion_score = emotion_score + volume_score
        
        return {
            "total": round(total_emotion_score, 1),
            "emotion_cycle_score": emotion_score,
            "volume_score": round(volume_score, 1),
            "stage": stage,
            "volume_ratio": volume_result.get('volume_ratio', 0),
            "volume_signal": volume_result.get('signal', '未知')
        }
    
    def score_capital(self, stock_code: str) -> Dict:
        """
        资金面评分（30分）
        = 资金净流入(15分) + 大单占比(15分)
        
        注：这里暂时用模拟数据，后续可接入真实资金流数据
        """
        # TODO: 接入真实资金流数据
        # 暂时返回中性分数
        return {
            "total": 20,
            "net_inflow_score": 10,
            "big_order_score": 10,
            "net_inflow": 0,
            "big_order_ratio": 0
        }
    
    def score_technical(self, stock_code: str) -> Dict:
        """
        技术面评分（25分）
        = 连板高度(10分) + 封板质量(8分) + 趋势(7分)
        
        注：这里暂时用模拟数据，后续可接入涨停板数据
        """
        # TODO: 接入涨停板数据和趋势数据
        # 暂时返回中性分数
        return {
            "total": 15,
            "board_height_score": 5,
            "seal_quality_score": 5,
            "trend_score": 5,
            "board_height": 0,
            "seal_times": 0,
            "ma_count": 0
        }
    
    def score_theme(self, stock_code: str, stock_name: str) -> Dict:
        """
        题材面评分（15分）
        = 主线题材(10分) + 人气辨识度(5分)
        """
        # 1. 主线题材得分（10分）
        theme_score = 0
        is_main_theme = False
        
        if self.main_theme:
            main_theme_name = self.main_theme['main_theme']
            related_sectors = self.main_theme.get('related_sectors', [])
            
            # 检查股票是否属于主线题材
            # TODO: 需要获取股票所属板块信息
            # 这里暂时用简化逻辑
            theme_score = self.main_theme['score'] * 10 / 15  # 转换为10分制
            theme_score = round(theme_score, 1)
        
        # 2. 人气辨识度（5分）
        # TODO: 需要获取股票人气数据（龙虎榜、机构关注度等）
        popularity_score = 3  # 默认中等人气
        
        total_theme_score = theme_score + popularity_score
        
        return {
            "total": round(total_theme_score, 1),
            "theme_score": theme_score,
            "popularity_score": popularity_score,
            "main_theme": self.main_theme.get('main_theme', '未知') if self.main_theme else '未知',
            "theme_level": self.main_theme.get('level', '未知') if self.main_theme else '未知'
        }
    
    def score_stock(self, stock_code: str, stock_name: str = "") -> Dict:
        """
        对单只股票进行完整评分
        
        Returns:
            {
                "stock_code": 股票代码,
                "stock_name": 股票名称,
                "total_score": 总分,
                "grade": 评级,
                "emotion": 情绪面详情,
                "capital": 资金面详情,
                "technical": 技术面详情,
                "theme": 题材面详情,
                "recommendation": 操作建议
            }
        """
        print(f"\n{'='*70}")
        print(f"📊 评分分析: {stock_name}({stock_code})")
        print(f"{'='*70}")
        
        # 1. 情绪面评分（30分）
        print("\n1️⃣ 情绪面评分（30分）")
        emotion = self.score_emotion(stock_code, stock_name)
        print(f"   情绪周期: {emotion['stage']} → {emotion['emotion_cycle_score']}分")
        print(f"   量比评分: {emotion['volume_ratio']} → {emotion['volume_score']}分")
        print(f"   小计: {emotion['total']}/30")
        
        # 2. 资金面评分（30分）
        print("\n2️⃣ 资金面评分（30分）")
        capital = self.score_capital(stock_code)
        print(f"   资金净流入: {capital['net_inflow_score']}分")
        print(f"   大单占比: {capital['big_order_score']}分")
        print(f"   小计: {capital['total']}/30")
        
        # 3. 技术面评分（25分）
        print("\n3️⃣ 技术面评分（25分）")
        technical = self.score_technical(stock_code)
        print(f"   连板高度: {technical['board_height_score']}分")
        print(f"   封板质量: {technical['seal_quality_score']}分")
        print(f"   趋势得分: {technical['trend_score']}分")
        print(f"   小计: {technical['total']}/25")
        
        # 4. 题材面评分（15分）
        print("\n4️⃣ 题材面评分（15分）")
        theme = self.score_theme(stock_code, stock_name)
        print(f"   主线题材: {theme['main_theme']} ({theme['theme_level']}) → {theme['theme_score']}分")
        print(f"   人气辨识度: {theme['popularity_score']}分")
        print(f"   小计: {theme['total']}/15")
        
        # 5. 计算总分
        total_score = emotion['total'] + capital['total'] + technical['total'] + theme['total']
        
        # 6. 评级
        if total_score >= 85:
            grade = "SSS"
            recommendation = "强烈买入"
        elif total_score >= 75:
            grade = "SS"
            recommendation = "买入"
        elif total_score >= 65:
            grade = "S"
            recommendation = "关注"
        elif total_score >= 55:
            grade = "A"
            recommendation = "观望"
        elif total_score >= 45:
            grade = "B"
            recommendation = "谨慎"
        else:
            grade = "C"
            recommendation = "回避"
        
        print(f"\n{'='*70}")
        print(f"🎯 总分: {total_score}/100")
        print(f"⭐ 评级: {grade}")
        print(f"💡 建议: {recommendation}")
        print(f"{'='*70}\n")
        
        return {
            "stock_code": stock_code,
            "stock_name": stock_name,
            "total_score": round(total_score, 1),
            "grade": grade,
            "recommendation": recommendation,
            "emotion": emotion,
            "capital": capital,
            "technical": technical,
            "theme": theme,
            "timestamp": datetime.now().isoformat()
        }
    
    def batch_score(self, stock_list: List[tuple]) -> List[Dict]:
        """
        批量评分
        
        Args:
            stock_list: [(股票代码, 股票名称), ...]
        """
        results = []
        
        for stock_code, stock_name in stock_list:
            result = self.score_stock(stock_code, stock_name)
            results.append(result)
        
        # 按总分排序
        results.sort(key=lambda x: x['total_score'], reverse=True)
        
        return results
    
    def save_results(self, results: List[Dict], filepath: str = "dragon_scores_v3.json"):
        """保存评分结果"""
        output = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "timestamp": datetime.now().isoformat(),
            "market_emotion": self.market_emotion,
            "main_theme": self.main_theme,
            "stocks": results
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 结果已保存到: {filepath}")


def main():
    """主函数"""
    print("🚀 龙头股评分系统 V3.0")
    print("基于小欧 16 年实战经验\n")
    
    # 初始化评分系统
    scorer = DragonStockScorerV3()
    
    # 初始化市场环境
    scorer.init_market_context()
    
    # 测试股票列表
    test_stocks = [
        ("002261", "拓维信息"),
        ("601868", "中国能建"),
        ("002506", "协鑫集成"),
        ("000533", "顺钠股份"),
        ("600821", "金开新能"),
    ]
    
    # 批量评分
    results = scorer.batch_score(test_stocks)
    
    # 输出排名
    print("\n" + "="*70)
    print("📊 龙头股评分排名")
    print("="*70)
    print(f"{'排名':<6}{'股票':<20}{'总分':<10}{'评级':<8}{'建议':<12}")
    print("-"*70)
    
    for i, result in enumerate(results, 1):
        print(f"{i:<6}{result['stock_name']}({result['stock_code']})<20"
              f"{result['total_score']}/100<10{result['grade']:<8}{result['recommendation']:<12}")
    
    print("="*70)
    
    # 保存结果
    scorer.save_results(results)
    
    return results


if __name__ == "__main__":
    main()
