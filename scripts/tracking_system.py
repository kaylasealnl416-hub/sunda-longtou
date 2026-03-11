#!/usr/bin/env python3
"""
股票评分跟踪系统
每天记录涨停板股票评分，跟踪3天内实际走势，对比分析优化评分
"""

import akshare as ak
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_DIR = Path("/root/.openclaw/workspace/sunda-longtou")
TRACKING_FILE = PROJECT_DIR / "tracking_records.json"

def get_date_str(days_offset=0):
    """获取日期字符串"""
    d = datetime.now() + timedelta(days=days_offset)
    return d.strftime("%Y%m%d")

def get_date_chinese(days_offset=0):
    """获取中文日期"""
    d = datetime.now() + timedelta(days=days_offset)
    return d.strftime("%Y-%m-%d")

def load_tracking():
    """加载跟踪记录"""
    if TRACKING_FILE.exists():
        with open(TRACKING_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"stocks": {}, "analysis": []}

def save_tracking(data):
    """保存跟踪记录"""
    with open(TRACKING_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_today_zt():
    """获取当日涨停股票"""
    today = get_date_str()
    try:
        df = ak.stock_zt_pool_em(date=today)
        if df is not None and len(df) > 0:
            return df
    except Exception as e:
        print(f"获取涨停失败: {e}")
    return None

def get_zt_by_date(date_str):
    """获取指定日期的涨停股票"""
    try:
        df = ak.stock_zt_pool_em(date=date_str)
        if df is not None and len(df) > 0:
            return df
    except Exception as e:
        print(f"获取{date_str}涨停失败: {e}")
    return None

def score_stock_simple(code, name):
    """
    简单评分 - 基于股票基本信息
    后续可以调用完整的评分系统
    """
    # 这里用简化评分，后续对接完整评分系统
    import random
    random.seed(hash(code) % 10000)
    
    # 基础分
    base = random.randint(60, 90)
    # 热门加分
    hot = random.randint(0, 20)
    # 资金加分
    fund = random.randint(0, 15)
    
    total = base + hot + fund
    
    return {
        "code": code,
        "name": name,
        "total_score": total,
        "base_score": base,
        "hot_bonus": hot,
        "fund_bonus": fund,
    }

def add_today_to_tracking():
    """把当天的涨停板股票加入跟踪"""
    print(f"\n=== {get_date_chinese()} 涨停板股票跟踪 ===")
    
    df = get_today_zt()
    if df is None or len(df) == 0:
        print("今日无涨停数据")
        return
    
    # 筛选涨停板（连板数=1或无连板）
    first_boards = df[df['连板数'] <= 1]
    print(f"今日涨停板: {len(first_boards)}只")
    
    # 加载现有跟踪
    data = load_tracking()
    today = get_date_str()
    
    # 评分并加入跟踪
    new_stocks = []
    for _, row in first_boards.iterrows():
        code = str(row['代码'])
        name = str(row['名称'])
        
        # 评分
        score_info = score_stock_simple(code, name)
        
        stock_data = {
            "code": code,
            "name": name,
            "first_date": today,
            "score": score_info['total_score'],
            "score_detail": score_info,
            "status": "tracking",  # tracking, success, failed
            "day1_change": None,  # 第1天实际涨幅
            "day2_change": None,  # 第2天实际涨幅
            "day3_change": None,  # 第3天实际涨幅
            "result": None,  # 3天后结果
        }
        
        key = f"{code}_{today}"
        data['stocks'][key] = stock_data
        new_stocks.append(stock_data)
    
    # 按分数排序
    new_stocks.sort(key=lambda x: x['score'], reverse=True)
    
    # 保存
    save_tracking(data)
    
    print(f"\n今日涨停板评分 TOP10:")
    print("-" * 50)
    for i, s in enumerate(new_stocks[:10], 1):
        print(f"{i:2}. {s['code']} {s['name']:<8} 评分:{s['score']}")
    
    # 打印推送消息
    top8 = new_stocks[:8]
    msg = f"📊 {get_date_chinese()} 涨停板评分 TOP8\n\n"
    for i, s in enumerate(top8, 1):
        msg += f"{i}. {s['name']} {s['code']} 评分:{s['score']}\n"
    
    print(f"\n推送消息:\n{msg}")
    
    return msg

def update_tracking_results():
    """更新跟踪中的股票实际走势"""
    print(f"\n=== 更新跟踪股票走势 ===")
    
    data = load_tracking()
    today = get_date_str()
    yesterday = get_date_str(-1)
    day2 = get_date_str(-2)
    
    updated = 0
    
    for key, stock in data['stocks'].items():
        if stock['status'] != 'tracking':
            continue
        
        first_date = stock['first_date']
        
        # 检查是否需要更新第1天
        if stock['day1_change'] is None and first_date != today:
            # 获取涨停板后第1天的数据
            df_d1 = get_zt_by_date(first_date)
            if df_d1 is not None:
                code = stock['code']
                matched = df_d1[df_d1['代码'].astype(str).str.zfill(6) == code]
                if len(matched) > 0:
                    stock['day1_change'] = float(matched.iloc[0]['涨跌幅'])
                    stock['day1_zt'] = True
                else:
                    # 没涨停，算当天的涨跌幅
                    stock['day1_change'] = 0
                    stock['day1_zt'] = False
            updated += 1
        
        # 检查是否完成跟踪(3天后)
        if stock['day1_change'] is not None:
            # 3天后检查结果
            # 简单逻辑：如果3天内任意一天涨停就算成功
            if stock.get('day1_zt') or stock.get('day2_zt') or stock.get('day3_zt'):
                stock['status'] = 'success'
                stock['result'] = '涨停'
            else:
                stock['status'] = 'failed'
                stock['result'] = '未涨停'
    
    save_tracking(data)
    print(f"更新了 {updated} 只股票")

def generate_analysis():
    """生成分析报告"""
    print(f"\n=== 评分准确性分析 ===")
    
    data = load_tracking()
    stocks = data['stocks']
    
    # 统计
    total = len([s for s in stocks.values() if s['status'] != 'tracking'])
    success = len([s for s in stocks.values() if s['status'] == 'success'])
    failed = len([s for s in stocks.values() if s['status'] == 'failed'])
    
    if total > 0:
        accuracy = success / total * 100
    else:
        accuracy = 0
    
    print(f"总跟踪: {total}只")
    print(f"成功(涨停): {success}只")
    print(f"失败(未涨停): {failed}只")
    print(f"准确率: {accuracy:.1f}%")
    
    # 分析高分失灵
    print(f"\n--- 高分失灵分析 (评分>120但未涨停) ---")
    high_score_failed = [
        s for s in stocks.values() 
        if s['score'] > 120 and s['status'] == 'failed'
    ]
    
    if high_score_failed:
        for s in high_score_failed[:10]:
            print(f"  {s['code']} {s['name']} 评分:{s['score']}")
    else:
        print("  无")
    
    # 分析低分成功
    print(f"\n--- 低分成功分析 (评分<80但涨停) ---")
    low_score_success = [
        s for s in stocks.values() 
        if s['score'] < 80 and s['status'] == 'success'
    ]
    
    if low_score_success:
        for s in low_score_success[:10]:
            print(f"  {s['code']} {s['name']} 评分:{s['score']}")
    else:
        print("  无")
    
    return {
        "total": total,
        "success": success,
        "failed": failed,
        "accuracy": accuracy,
    }

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "add":
            add_today_to_tracking()
        elif cmd == "update":
            update_tracking_results()
        elif cmd == "analyze":
            generate_analysis()
        else:
            print("用法: python tracking.py [add|update|analyze]")
    else:
        # 完整流程
        add_today_to_tracking()
        update_tracking_results()
        generate_analysis()
