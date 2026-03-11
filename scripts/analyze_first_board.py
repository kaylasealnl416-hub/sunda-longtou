#!/usr/bin/env python3
"""
首板分析脚本 - 分析今日涨停板并评分
"""
import json
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

def load_today_zt():
    """加载今日涨停数据"""
    data_file = Path(__file__).parent.parent / "data" / "all_zt_today.json"
    if not data_file.exists():
        return []
    
    with open(data_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_score_results():
    """加载评分结果"""
    score_file = Path(__file__).parent.parent / "score_results.json"
    if not score_file.exists():
        return []
    
    with open(score_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data.get('results', [])

def analyze_first_boards():
    """分析首板股票"""
    zt_stocks = load_today_zt()
    score_results = load_score_results()
    
    # 创建评分字典（按代码索引）
    score_dict = {}
    for stock in score_results:
        code = stock['code'].replace('SZ', '').replace('SH', '')
        score_dict[code] = stock
    
    # 筛选首板（lianban=1）
    first_boards = [s for s in zt_stocks if s.get('lianban') == 1]
    
    print(f"\n{'='*60}")
    print(f"📊 今日首板分析 ({len(first_boards)}只)")
    print(f"{'='*60}\n")
    
    # 分析每只首板
    analyzed = []
    for stock in first_boards:
        code = stock['code']
        name = stock['name']
        
        # 查找评分
        score_info = score_dict.get(code)
        
        if score_info:
            total_score = score_info.get('总分', 0)
            industry = score_info.get('产业链', '未知')
            trend = score_info.get('趋势', '未知')
            
            analyzed.append({
                'code': code,
                'name': name,
                'score': total_score,
                'industry': industry,
                'trend': trend,
                'amount': stock.get('amount', 0),
                'first_time': stock.get('first_time', ''),
                'last_time': stock.get('last_time', '')
            })
    
    # 按评分排序
    analyzed.sort(key=lambda x: x['score'], reverse=True)
    
    # 输出TOP10
    print("🏆 TOP10 首板评分:\n")
    for i, stock in enumerate(analyzed[:10], 1):
        score = stock['score']
        emoji = "🔥" if score >= 80 else "📈" if score >= 70 else "⚠️"
        
        print(f"{i:2d}. {emoji} {stock['name']:8s} ({stock['code']})")
        print(f"    评分: {score:.1f} | 趋势: {stock['trend']}")
        print(f"    板块: {stock['industry']}")
        print(f"    封板: {stock['first_time'][:4]}→{stock['last_time'][:4]}")
        print(f"    成交: {stock['amount']/1e8:.2f}亿\n")
    
    # 统计
    high_score = [s for s in analyzed if s['score'] >= 80]
    mid_score = [s for s in analyzed if 70 <= s['score'] < 80]
    
    print(f"\n{'='*60}")
    print(f"📈 评分分布:")
    print(f"  🔥 高分(≥80): {len(high_score)}只")
    print(f"  📈 中分(70-80): {len(mid_score)}只")
    print(f"  ⚠️  低分(<70): {len(analyzed) - len(high_score) - len(mid_score)}只")
    print(f"{'='*60}\n")
    
    return analyzed

if __name__ == '__main__':
    analyze_first_boards()
