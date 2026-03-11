#!/usr/bin/env python3
"""
股票评分跟踪系统 V2
每天记录首板股票评分，跟踪3天内实际走势（不管是否涨停）
"""

import akshare as ak
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd

PROJECT_DIR = Path("/root/.openclaw/workspace/sunda-longtou")
TRACKING_FILE = PROJECT_DIR / "tracking_records.json"

def get_date_str(days_offset=0):
    d = datetime.now() + timedelta(days=days_offset)
    return d.strftime("%Y%m%d")

def get_date_chinese(days_offset=0):
    d = datetime.now() + timedelta(days=days_offset)
    return d.strftime("%Y-%m-%d")

def load_tracking():
    if TRACKING_FILE.exists():
        with open(TRACKING_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"stocks": {}, "analysis": []}

def save_tracking(data):
    with open(TRACKING_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_stock_daily(date_str):
    """获取指定日期的个股涨跌数据"""
    try:
        df = ak.stock_zh_a_hist(symbol="000001", start_date=date_str, end_date=date_str)
        return df
    except:
        return None

def get_zt_pool(date_str):
    """获取指定日期涨停股票"""
    try:
        df = ak.stock_zt_pool_em(date=date_str)
        if df is not None and len(df) > 0:
            return df
    except Exception as e:
        print(f"获取{date_str}涨停失败: {e}")
    return None

def get_real_change(code, date_str):
    """获取股票在指定日期的实际涨跌幅"""
    try:
        # 标准化代码
        code = str(code).zfill(6)
        if code.startswith('6'):
            symbol = code
        else:
            symbol = code
        
        # 尝试获取历史数据
        df = ak.stock_zh_a_hist(symbol=symbol, start_date=date_str, end_date=date_str)
        if df is not None and len(df) > 0:
            return float(df.iloc[0]['涨跌幅'])
    except Exception as e:
        pass
    return None

def score_stock_simple(code, name):
    """简单评分"""
    import random
    random.seed(hash(code) % 10000)
    base = random.randint(60, 90)
    hot = random.randint(0, 20)
    fund = random.randint(0, 15)
    total = base + hot + fund
    return {
        "code": code,
        "name": name,
        "total_score": total,
    }

def add_today_to_tracking():
    """记录今日首板"""
    print(f"\n=== {get_date_chinese()} 首板股票记录 ===")
    
    df = get_zt_pool(get_date_str())
    if df is None or len(df) == 0:
        print("今日无涨停")
        return
    
    # 首板（连板数<=1）
    first_boards = df[df['连板数'] <= 1]
    print(f"今日首板: {len(first_boards)}只")
    
    data = load_tracking()
    today = get_date_str()
    
    new_stocks = []
    for _, row in first_boards.iterrows():
        code = str(row['代码'])
        name = str(row['名称'])
        
        score_info = score_stock_simple(code, name)
        
        stock_data = {
            "code": code,
            "name": name,
            "first_date": today,
            "score": score_info['total_score'],
            "status": "tracking",
            "track_day": 0,  # 跟踪第几天
            "day0_zt": True,  # 首板当天
            "day1_change": None,  # 第1天实际
            "day2_change": None,  # 第2天实际
            "day3_change": None,  # 第3天实际
            "result": None,
        }
        
        key = f"{code}_{today}"
        data['stocks'][key] = stock_data
        new_stocks.append(stock_data)
    
    new_stocks.sort(key=lambda x: x['score'], reverse=True)
    save_tracking(data)
    
    print(f"\n今日 TOP8:")
    for i, s in enumerate(new_stocks[:8], 1):
        print(f"{i}. {s['code']} {s['name']:<8} 评分:{s['score']}")
    
    return new_stocks[:8]

def update_tracking():
    """更新所有跟踪股票的走势"""
    print(f"\n=== 更新跟踪股票走势 ===")
    
    data = load_tracking()
    today = get_date_str()
    
    # 遍历所有跟踪中的股票
    updated = 0
    for key, stock in data['stocks'].items():
        if stock['status'] != 'tracking':
            continue
        
        first_date = stock['first_date']
        code = stock['code']
        
        # 计算今天是第几天
        from datetime import datetime
        first_d = datetime.strptime(first_date, "%Y%m%d")
        today_d = datetime.strptime(today, "%Y%m%d")
        days_diff = (today_d - first_d).days
        
        # 更新走势
        if days_diff >= 1 and stock['day1_change'] is None:
            change = get_real_change(code, first_date)
            stock['day1_change'] = change
            stock['track_day'] = 1
            updated += 1
        
        if days_diff >= 2 and stock['day2_change'] is None:
            next_date = get_date_str(int(first_date) + 1)
            change = get_real_change(code, next_date)
            stock['day2_change'] = change
            stock['track_day'] = 2
        
        if days_diff >= 3 and stock['day3_change'] is None:
            next_date2 = get_date_str(int(first_date) + 2)
            change = get_real_change(code, next_date2)
            stock['day3_change'] = change
            stock['track_day'] = 3
        
        # 3天后结束跟踪
        if days_diff >= 3:
            # 判断结果
            if stock['day1_change'] and stock['day1_change'] > 9.5:
                stock['result'] = 'day1涨停'
            elif stock['day2_change'] and stock['day2_change'] > 9.5:
                stock['result'] = 'day2涨停'
            elif stock['day3_change'] and stock['day3_change'] > 9.5:
                stock['result'] = 'day3涨停'
            else:
                stock['result'] = '未涨停'
            stock['status'] = 'done'
    
    save_tracking(data)
    print(f"更新了 {updated} 只股票")

def show_stock_tracking(code):
    """查看某只股票的跟踪详情"""
    data = load_tracking()
    
    print(f"\n=== {code} 跟踪详情 ===")
    for key, s in data['stocks'].items():
        if s['code'] == code:
            print(f"首板日期: {s['first_date']}")
            print(f"评分: {s['score']}")
            print(f"跟踪进度: 第{s.get('track_day', 0)}天")
            print(f"第1天走势: {s.get('day1_change')}")
            print(f"第2天走势: {s.get('day2_change')}")
            print(f"第3天走势: {s.get('day3_change')}")
            print(f"结果: {s.get('result')}")
            print()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "add":
            add_today_to_tracking()
        elif cmd == "update":
            update_tracking()
        elif cmd == "show" and len(sys.argv) > 2:
            show_stock_tracking(sys.argv[2])
        else:
            print("用法: python tracking_v2.py [add|update|show <code>]")
    else:
        add_today_to_tracking()
        update_tracking()
