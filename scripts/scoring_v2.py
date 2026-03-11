#!/usr/bin/env python3
"""
股票评分系统 V2
- 评分对象：当天所有涨停股票（首板、2板、3板...8板+）
- TOP8：所有参与评分的股票综合排名（含历史跟踪）
"""
import pandas as pd
import json
from datetime import datetime

DATA_DIR = "/root/.openclaw/workspace/sunda-longtou/data"
TRACKING_FILE = f"{DATA_DIR}/tracking_records.json"
TOP8_FILE = f"{DATA_DIR}/daily_top8.json"

def safe_num(val):
    if pd.isna(val): return 0
    if isinstance(val, (int, float)): return val
    try: return float(val)
    except: return 0

def score_stock(row):
    """评分函数"""
    score = 60  # 基础分
    
    # 1. 涨幅加分
    zf = safe_num(row.get('涨幅%', 0))
    if zf >= 20: score += 20    # 20cm+
    elif zf >= 10: score += 15  # 10cm+
    elif zf >= 5: score += 5
    
    # 2. 连板加分
    lban = safe_num(row.get('连板天', 0))
    if lban >= 1:
        score += lban * 12  # 每板+12分
        if lban >= 5: score += 10  # 5板以上额外+10
    
    # 3. 换手率加分
    hs = safe_num(row.get('换手Z', 0))
    if hs >= 50: score += 15
    elif hs >= 30: score += 10
    elif hs >= 15: score += 5
    
    # 4. 金额加分
    je = safe_num(row.get('总金额', 0))
    if je >= 500000: score += 15  # 5亿+
    elif je >= 200000: score += 10  # 2亿+
    elif je >= 100000: score += 5   # 1亿+
    
    # 5. 主力占比加分
    zl = safe_num(row.get('主力占比%', 0))
    if zl >= 20: score += 10
    elif zl >= 10: score += 5
    
    return score

def load_tracking():
    with open(TRACKING_FILE, 'r') as f:
        return json.load(f)

def save_tracking(data):
    with open(TRACKING_FILE, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def save_top8(all_stocks, date_str):
    """保存TOP8"""
    sorted_stocks = sorted(all_stocks.items(), key=lambda x: x[1].get('score', 0), reverse=True)
    
    top8 = []
    for k, v in sorted_stocks[:8]:
        top8.append({
            'code': v['code'],
            'name': v['name'],
            'score': v['score'],
            'boards': v.get('boards', []),
            'lianban': v.get('lianban', 1)
        })
    
    # 加载现有TOP8
    try:
        with open(TOP8_FILE, 'r') as f:
            top8_data = json.load(f)
    except:
        top8_data = {"dates": {}}
    
    top8_data['dates'][date_str] = top8
    
    with open(TOP8_FILE, 'w') as f:
        json.dump(top8_data, f, ensure_ascii=False, indent=2)
    
    return top8

def main():
    print("股票评分系统 V2")
    print("="*50)
    # 加载历史跟踪
    tracking = load_tracking()
    print(f"历史记录: {len(tracking.get('stocks', {}))}只")

if __name__ == "__main__":
    main()
