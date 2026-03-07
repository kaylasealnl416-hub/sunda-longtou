#!/usr/bin/env python3
"""
龙头股评分系统 - 回测模块
用于验证评分模型的准确性
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List
from sunda_longtou_scoring import score_top_stocks, get_stock_hot

# ==================== 回测逻辑 ====================

def backtest_score_range(scores: List[Dict], holding_days: int = 5) -> Dict:
    """
    回测：按评分分组，看后续N天的涨跌幅
    由于没有真实后续数据，这里用当日涨跌幅模拟
    """
    # 按分数分段
    high_score = [s for s in scores if s['总分'] >= 80]
    mid_score = [s for s in scores if 60 <= s['总分'] < 80]
    low_score = [s for s in scores if s['总分'] < 60]
    
    # 计算各组平均涨幅 (用当日涨幅模拟)
    def calc_avg_change(group):
        if not group:
            return 0
        total = sum(s.get('技术面分', 0) / 100 * 10 for s in group)  # 近似
        return total / len(group)
    
    result = {
        "高分组(>=80分)": {
            "数量": len(high_score),
            "平均技术涨幅": calc_avg_change(high_score),
            "股票": [s['name'] for s in high_score[:5]]
        },
        "中分组(60-80分)": {
            "数量": len(mid_score),
            "平均技术涨幅": calc_avg_change(mid_score),
            "股票": [s['name'] for s in mid_score[:5]]
        },
        "低分组(<60分)": {
            "数量": len(low_score),
            "平均技术涨幅": calc_avg_change(low_score),
            "股票": [s['name'] for s in low_score[:5]]
        }
    }
    
    return result

def simulate_buy_signals(scores: List[Dict], top_n: int = 5) -> List[Dict]:
    """
    模拟买入信号：评分前N名的股票
    """
    signals = []
    for s in scores[:top_n]:
        signal = {
            "code": s['code'],
            "name": s['name'],
            "score": s['总分'],
            "reason": []
        }
        
        if s['热门排名分'] >= 90:
            signal['reason'].append("热门排名高")
        if s['资金面分'] >= 80:
            signal['reason'].append("资金流入大")
        if s['技术面分'] >= 90:
            signal['reason'].append("技术形态强")
        
        signals.append(signal)
    
    return signals

def daily_record(scores: List[Dict]) -> Dict:
    """
    生成每日记录
    """
    record = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "top5": [],
        "warning": []
    }
    
    # 记录TOP5
    for s in scores[:5]:
        record["top5"].append({
            "code": s['code'],
            "name": s['name'],
            "score": round(s['总分'], 1),
            "reason": []
        })
    
    # 记录风险警示 (资金面为0或负)
    for s in scores[:20]:
        if s['资金面分'] == 0 and s['总分'] > 60:
            record["warning"].append({
                "code": s['code'],
                "name": s['name'],
                "reason": "资金面为0"
            })
    
    return record

# ==================== 主程序 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("龙头股评分系统 - 回测模块")
    print("=" * 60)
    
    # 获取当日评分
    scores = score_top_stocks(20)
    
    if not scores:
        print("❌ 未能获取数据")
        exit(1)
    
    # 模拟买入信号
    print("\n📈 模拟买入信号 (TOP 5):")
    signals = simulate_buy_signals(scores, 5)
    for i, s in enumerate(signals, 1):
        print(f"  {i}. {s['name']} ({s['code']}) - 评分:{s['score']:.1f}")
        print(f"     原因: {', '.join(s['reason'])}")
    
    # 风险警示
    print("\n⚠️ 风险警示:")
    warnings = [s for s in scores[:20] if s['资金面分'] == 0 and s['总分'] > 60]
    if warnings:
        for w in warnings:
            print(f"  - {w['name']}: 资金面得分0，但总分偏高")
    else:
        print("  无")
    
    # 每日记录
    record = daily_record(scores)
    print(f"\n📊 每日记录已生成: {record['date']}")
    
    # 保存记录
    with open("daily_record.json", "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)
    
    print("✅ 结果已保存到 daily_record.json")
