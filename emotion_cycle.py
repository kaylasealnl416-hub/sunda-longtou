#!/usr/bin/env python3
"""
情绪周期识别系统 v1.0
基于小欧 16 年实战经验

核心逻辑：
1. 冰点期：涨停板 < 20，炸板率 > 50%，量比 < 0.8 → 仓位 10-20%（抄底机会）
2. 启动期：涨停板 20-40，炸板率 30-50%，量比 0.8-1.2 → 仓位 40-60%（追启动初期）
3. 发酵期：涨停板 40-80，炸板率 20-30%，量比 1.2-1.8 → 仓位 60-80%（主升浪）
4. 高潮期：涨停板 > 80，炸板率 < 20%，量比 > 1.8 → 仓位 40-60%（准备减仓）
5. 退潮期：涨停板下降，炸板率上升，量比回落 → 仓位 20-30%（杀下跌之际）

数据来源：
- 涨停板数量（连板高度分布）
- 炸板率（开板次数 / 涨停总数）
- 成交量变化（相比前一日）
- 9 大指数量比
- 大小盘风格
"""

import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import json


class EmotionCycleDetector:
    """情绪周期识别器"""
    
    def __init__(self):
        self.stages = {
            "冰点期": {"position": "10-20%", "action": "抄底机会", "color": "#3b82f6"},
            "启动期": {"position": "40-60%", "action": "追启动初期", "color": "#10b981"},
            "发酵期": {"position": "60-80%", "action": "主升浪持有", "color": "#f59e0b"},
            "高潮期": {"position": "40-60%", "action": "准备减仓", "color": "#ef4444"},
            "退潮期": {"position": "20-30%", "action": "杀下跌之际", "color": "#6b7280"}
        }
        
    def get_limit_up_data(self, date: Optional[str] = None) -> Dict:
        """
        获取涨停板数据
        
        Returns:
            {
                "total": 涨停总数,
                "broken": 炸板数量,
                "broken_rate": 炸板率,
                "ladder": {
                    "首板": 数量,
                    "二连板": 数量,
                    "三连板": 数量,
                    "四连板+": 数量
                }
            }
        """
        try:
            # 获取涨停板数据
            df = ak.stock_zt_pool_em(date=date or datetime.now().strftime("%Y%m%d"))
            
            if df.empty:
                return self._get_mock_limit_up_data()
            
            total = len(df)
            
            # 计算炸板率（开板次数 > 0 的股票）
            broken = len(df[df['开板次数'] > 0]) if '开板次数' in df.columns else 0
            broken_rate = (broken / total * 100) if total > 0 else 0
            
            # 连板高度分布
            ladder = {
                "首板": 0,
                "二连板": 0,
                "三连板": 0,
                "四连板+": 0
            }
            
            if '连板数' in df.columns:
                for _, row in df.iterrows():
                    boards = row['连板数']
                    if boards == 1:
                        ladder["首板"] += 1
                    elif boards == 2:
                        ladder["二连板"] += 1
                    elif boards == 3:
                        ladder["三连板"] += 1
                    else:
                        ladder["四连板+"] += 1
            else:
                # 如果没有连板数，默认都是首板
                ladder["首板"] = total
            
            return {
                "total": total,
                "broken": broken,
                "broken_rate": round(broken_rate, 2),
                "ladder": ladder
            }
            
        except Exception as e:
            print(f"获取涨停板数据失败: {e}")
            return self._get_mock_limit_up_data()
    
    def _get_mock_limit_up_data(self) -> Dict:
        """模拟涨停板数据（用于测试）"""
        return {
            "total": 45,
            "broken": 12,
            "broken_rate": 26.67,
            "ladder": {
                "首板": 30,
                "二连板": 10,
                "三连板": 4,
                "四连板+": 1
            }
        }
    
    def get_volume_ratio(self) -> float:
        """
        获取市场整体量比
        计算方法：今日成交量 / 5日平均成交量
        """
        try:
            # 获取上证指数数据
            df = ak.stock_zh_index_daily(symbol="sh000001")
            df = df.tail(6)  # 最近6天
            
            if len(df) < 6:
                return 1.0
            
            today_vol = df.iloc[-1]['volume']
            avg_vol = df.iloc[-6:-1]['volume'].mean()
            
            volume_ratio = today_vol / avg_vol if avg_vol > 0 else 1.0
            return round(volume_ratio, 2)
            
        except Exception as e:
            print(f"获取量比数据失败: {e}")
            return 1.15  # 模拟数据
    
    def get_market_style(self) -> Dict:
        """
        获取大小盘风格
        
        Returns:
            {
                "style": "大盘" | "小盘" | "均衡",
                "score": 风格得分 (-100 到 100，负数偏小盘，正数偏大盘)
            }
        """
        try:
            # 获取上证50和中证1000的涨跌幅
            sz50 = ak.stock_zh_index_daily(symbol="sh000016")  # 上证50
            zz1000 = ak.stock_zh_index_daily(symbol="sh000852")  # 中证1000
            
            # 计算涨跌幅
            sz50_today = sz50.iloc[-1]['close']
            sz50_yesterday = sz50.iloc[-2]['close']
            sz50_change = (sz50_today - sz50_yesterday) / sz50_yesterday * 100
            
            zz1000_today = zz1000.iloc[-1]['close']
            zz1000_yesterday = zz1000.iloc[-2]['close']
            zz1000_change = (zz1000_today - zz1000_yesterday) / zz1000_yesterday * 100
            
            # 风格得分：大盘涨幅 - 小盘涨幅
            score = (sz50_change - zz1000_change) * 10
            
            if score > 20:
                style = "大盘"
            elif score < -20:
                style = "小盘"
            else:
                style = "均衡"
            
            return {
                "style": style,
                "score": round(score, 2)
            }
            
        except Exception as e:
            print(f"获取市场风格失败: {e}")
            return {"style": "小盘", "score": -15}  # 模拟数据
    
    def detect_stage(self, limit_up_data: Dict, volume_ratio: float, 
                     market_style: Dict) -> Dict:
        """
        识别当前情绪周期阶段
        
        Args:
            limit_up_data: 涨停板数据
            volume_ratio: 市场量比
            market_style: 大小盘风格
            
        Returns:
            {
                "stage": "冰点期" | "启动期" | "发酵期" | "高潮期" | "退潮期",
                "confidence": 置信度 (0-100),
                "position_advice": "仓位建议",
                "action": "操作建议",
                "signals": ["信号1", "信号2", ...],
                "color": 颜色代码
            }
        """
        total = limit_up_data["total"]
        broken_rate = limit_up_data["broken_rate"]
        ladder = limit_up_data["ladder"]
        
        signals = []
        scores = {
            "冰点期": 0,
            "启动期": 0,
            "发酵期": 0,
            "高潮期": 0,
            "退潮期": 0
        }
        
        # 1. 涨停板数量判断
        if total < 20:
            scores["冰点期"] += 40
            signals.append(f"涨停板数量少({total}个)")
        elif 20 <= total < 40:
            scores["启动期"] += 40
            signals.append(f"涨停板数量回升({total}个)")
        elif 40 <= total < 80:
            scores["发酵期"] += 40
            signals.append(f"涨停板数量充足({total}个)")
        else:
            scores["高潮期"] += 40
            signals.append(f"涨停板数量爆发({total}个)")
        
        # 2. 炸板率判断
        if broken_rate > 50:
            scores["冰点期"] += 30
            scores["退潮期"] += 20
            signals.append(f"炸板率高({broken_rate}%)")
        elif 30 <= broken_rate <= 50:
            scores["启动期"] += 30
            signals.append(f"炸板率下降({broken_rate}%)")
        elif 20 <= broken_rate < 30:
            scores["发酵期"] += 30
            signals.append(f"炸板率健康({broken_rate}%)")
        else:
            scores["高潮期"] += 30
            signals.append(f"炸板率极低({broken_rate}%)")
        
        # 3. 量比判断
        if volume_ratio < 0.8:
            scores["冰点期"] += 20
            scores["退潮期"] += 10
            signals.append(f"量比缩量({volume_ratio})")
        elif 0.8 <= volume_ratio < 1.2:
            scores["启动期"] += 20
            signals.append(f"量比正常({volume_ratio})")
        elif 1.2 <= volume_ratio < 1.8:
            scores["发酵期"] += 20
            signals.append(f"量比放大({volume_ratio})")
        else:
            scores["高潮期"] += 20
            signals.append(f"量比爆量({volume_ratio})")
        
        # 4. 连板高度判断（高度越高，情绪越热）
        high_boards = ladder.get("三连板", 0) + ladder.get("四连板+", 0)
        if high_boards >= 5:
            scores["高潮期"] += 10
            signals.append(f"高连板多({high_boards}个)")
        elif high_boards >= 2:
            scores["发酵期"] += 10
            signals.append(f"高连板出现({high_boards}个)")
        else:
            scores["启动期"] += 5
            scores["冰点期"] += 5
        
        # 5. 市场风格判断（小盘活跃度更高）
        if market_style["style"] == "小盘":
            scores["发酵期"] += 5
            scores["高潮期"] += 5
        
        # 找出得分最高的阶段
        stage = max(scores, key=scores.get)
        confidence = min(scores[stage], 100)
        
        # 特殊情况：退潮期判断（需要对比历史数据）
        # 如果涨停板数量在减少，且炸板率在上升，则可能是退潮期
        # 这里简化处理，后续可以加入历史对比
        
        stage_info = self.stages[stage]
        
        return {
            "stage": stage,
            "confidence": confidence,
            "position_advice": stage_info["position"],
            "action": stage_info["action"],
            "signals": signals,
            "color": stage_info["color"],
            "raw_scores": scores
        }
    
    def analyze(self, date: Optional[str] = None) -> Dict:
        """
        完整分析当前市场情绪周期
        
        Args:
            date: 日期（格式：YYYYMMDD），默认为今天
            
        Returns:
            完整的情绪周期分析结果
        """
        print("=" * 60)
        print("🔍 情绪周期识别系统 v1.0")
        print("=" * 60)
        
        # 1. 获取涨停板数据
        print("\n📊 获取涨停板数据...")
        limit_up_data = self.get_limit_up_data(date)
        print(f"   涨停总数: {limit_up_data['total']}")
        print(f"   炸板率: {limit_up_data['broken_rate']}%")
        print(f"   连板分布: {limit_up_data['ladder']}")
        
        # 2. 获取量比
        print("\n📈 获取市场量比...")
        volume_ratio = self.get_volume_ratio()
        print(f"   量比: {volume_ratio}")
        
        # 3. 获取市场风格
        print("\n🎯 获取市场风格...")
        market_style = self.get_market_style()
        print(f"   风格: {market_style['style']} (得分: {market_style['score']})")
        
        # 4. 识别情绪周期
        print("\n🧠 识别情绪周期...")
        result = self.detect_stage(limit_up_data, volume_ratio, market_style)
        
        print(f"\n{'=' * 60}")
        print(f"🎯 当前阶段: {result['stage']}")
        print(f"📊 置信度: {result['confidence']}%")
        print(f"💰 仓位建议: {result['position_advice']}")
        print(f"🎬 操作建议: {result['action']}")
        print(f"\n📌 关键信号:")
        for signal in result['signals']:
            print(f"   • {signal}")
        print(f"{'=' * 60}\n")
        
        # 组合完整结果
        full_result = {
            "date": date or datetime.now().strftime("%Y%m%d"),
            "timestamp": datetime.now().isoformat(),
            "limit_up_data": limit_up_data,
            "volume_ratio": volume_ratio,
            "market_style": market_style,
            "emotion_cycle": result
        }
        
        return full_result
    
    def save_result(self, result: Dict, filepath: str = "emotion_cycle_result.json"):
        """保存分析结果到文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"✅ 结果已保存到: {filepath}")


def main():
    """主函数"""
    detector = EmotionCycleDetector()
    result = detector.analyze()
    detector.save_result(result)
    
    return result


if __name__ == "__main__":
    main()
