#!/usr/bin/env python3
"""
每日股票评分 + 持续追踪 - 下午3:15运行
获取最近10日涨停股票，评分后推送TOP8
- 今日评分：最近一次涨停的评分
- 首板日期：首次涨停的日期
- 追踪逻辑：只计算交易日（周一到周五）
"""
import akshare as ak
import pandas as pd
import json
from datetime import datetime, timedelta

# 设置代理
import os
os.environ['https_proxy'] = 'http://127.0.0.1:7890'
os.environ['http_proxy'] = 'http://127.0.0.1:7890'

DATA_DIR = "/root/.openclaw/workspace/sunda-longtou/data"
TOP8_FILE = f"{DATA_DIR}/daily_top8.json"
TRACKING_FILE = f"{DATA_DIR}/tracking_records.json"

def is_trade_day(date_str):
    """判断是否是交易日（周一到周五）"""
    dt = datetime.strptime(date_str, "%Y%m%d")
    return dt.weekday() < 5  # 0-4 是周一到周五

def get_trade_dates(n=10):
    """获取最近n个交易日"""
    dates = []
    today = datetime.now()
    
    # 向前查找n个交易日
    while len(dates) < n:
        if today.weekday() < 5:  # 周一到周五
            dates.append(today.strftime("%Y%m%d"))
        today -= timedelta(days=1)
    
    return dates

def count_trade_days_between(start_date, end_date):
    """计算两个日期之间的交易日数（不包括start_date）"""
    start = datetime.strptime(start_date, "%Y%m%d")
    end = datetime.strptime(end_date, "%Y%m%d")
    
    count = 0
    current = start + timedelta(days=1)
    while current <= end:
        if current.weekday() < 5:  # 周一到周五
            count += 1
        current += timedelta(days=1)
    
    return count

def score_stock(row):
    """评分函数"""
    score = 60  # 基础分
    
    # 1. 涨幅加分
    zf = row.get('涨跌幅', 0) or 0
    if zf >= 20: score += 20
    elif zf >= 10: score += 15
    elif zf >= 5: score += 5
    
    # 2. 连板加分
    lban = row.get('连板数', 0) or 0
    if lban >= 1:
        score += int(lban * 12)
        if lban >= 5: score += 10
    
    # 3. 换手率
    hs = row.get('换手率', 0) or 0
    if hs >= 50: score += 15
    elif hs >= 30: score += 10
    elif hs >= 15: score += 5
    
    # 4. 封板时间
    mf = row.get('首次封板', '')
    if mf:
        try:
            hm = int(mf[:2]) * 60 + int(mf[2:4])
            if hm < 930: score += 10
            elif hm < 1000: score += 5
        except:
            pass
    
    # 5. 炸板次数
    zdb = row.get('炸板次数', 0) or 0
    if zdb == 0: score += 10
    elif zdb <= 2: score += 5
    
    return score

def load_tracking():
    """加载追踪数据"""
    try:
        with open(TRACKING_FILE, 'r') as f:
            return json.load(f)
    except:
        return {"stocks": {}}

def save_tracking(data):
    """保存追踪数据"""
    with open(TRACKING_FILE, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def add_to_tracking(tracking, stock, score, date):
    """将股票加入追踪"""
    key = f"{stock['代码']}_{date}"
    if key not in tracking['stocks']:
        tracking['stocks'][key] = {
            'code': stock['代码'],
            'name': stock['名称'],
            'first_date': date,
            'score': score,
            'status': 'tracking',
            'day1_change': None,
            'day2_change': None,
            'day3_change': None,
            'result': None
        }
        return True
    return False

def main():
    print("=" * 60)
    print("股票评分系统 - 多日涨停股票评分（交易日版）")
    print("=" * 60)
    
    # 获取最近10个交易日
    trade_dates = get_trade_dates(10)
    today = trade_dates[0]
    
    print(f"\n📅 评分日期: {today}")
    
    # 获取所有日期的涨停股票和评分
    all_zt_data = {}  # code -> {name, scores: {date: score}, first_date}
    
    for date in trade_dates:
        try:
            df = ak.stock_zt_pool_em(date=date)
            print(f"  {date}: {len(df)}只涨停")
            
            for _, row in df.iterrows():
                code = row.get('代码')
                name = row.get('名称')
                score = score_stock(row)
                
                if code not in all_zt_data:
                    all_zt_data[code] = {
                        'name': name,
                        'scores': {},
                        'first_date': date
                    }
                
                all_zt_data[code]['scores'][date] = score
                if date < all_zt_data[code]['first_date']:
                    all_zt_data[code]['first_date'] = date
                    
        except Exception as e:
            print(f"  {date} 获取失败: {e}")
    
    # 计算每只股票的今日评分和首板日期
    stocks_with_scores = []
    for code, data in all_zt_data.items():
        sorted_dates = sorted(data['scores'].keys(), reverse=True)
        latest_date = sorted_dates[0]
        latest_score = data['scores'][latest_date]
        
        stocks_with_scores.append({
            'code': code,
            'name': data['name'],
            'today_score': latest_score,
            'latest_date': latest_date,
            'first_date': data['first_date'],
        })
    
    stocks_with_scores.sort(key=lambda x: x['today_score'], reverse=True)
    
    print(f"\n📊 共 {len(stocks_with_scores)} 只涨停股票")
    
    # 加载追踪数据并更新状态
    tracking = load_tracking()
    
    print("\n📈 更新追踪状态...")
    
    # 获取今日之前的交易日列表（用于计算交易日差）
    past_trade_dates = [d for d in trade_dates if d < today]
    
    for key, stock in list(tracking['stocks'].items()):
        if stock.get('status') != 'tracking':
            continue
        
        code = stock.get('code')
        first_date = stock.get('first_date')
        
        # 检查今天是否涨停
        is_up_today = code in all_zt_data
        
        # 计算距离首板的交易日数
        trade_day_count = count_trade_days_between(first_date, today)
        
        # 更新状态
        if trade_day_count == 1:
            stock['day1_change'] = '涨停' if is_up_today else '未涨停'
            print(f"  第1天: {stock['name']} - {stock['day1_change']}")
        elif trade_day_count == 2:
            stock['day2_change'] = '涨停' if is_up_today else '未涨停'
            print(f"  第2天: {stock['name']} - {stock['day2_change']}")
        elif trade_day_count == 3:
            stock['day3_change'] = '涨停' if is_up_today else '未涨停'
            if is_up_today:
                stock['result'] = '成功 ✅'
                stock['status'] = 'success'
                print(f"  第3天: {stock['name']} - 成功! ✅")
            else:
                stock['result'] = '失败 ❌'
                stock['status'] = 'dropped'
                print(f"  第3天: {stock['name']} - 失败 ❌")
        elif trade_day_count > 3:
            if not is_up_today:
                stock['result'] = '放弃'
                stock['status'] = 'dropped'
                print(f"  超过3天: {stock['name']} - 放弃")
        
        # 重新首板
        if is_up_today and stock.get('status') in ['dropped', 'success']:
            old_first = stock.get('first_date')
            stock['first_date'] = today
            stock['day1_change'] = None
            stock['day2_change'] = None
            stock['day3_change'] = None
            stock['result'] = None
            stock['status'] = 'tracking'
            stock['score'] = all_zt_data[code]['scores'].get(today, stock['score'])
            print(f"  🔄 重新首板: {stock['name']} (从{old_first}→{today})")
    
    # 添加新的追踪
    for s in stocks_with_scores:
        row = {'代码': s['code'], '名称': s['name']}
        add_to_tracking(tracking, row, s['today_score'], s['latest_date'])
    
    save_tracking(tracking)
    
    # 输出TOP8
    print("\n" + "=" * 60)
    print("🏆 TOP 8 评分股票")
    print("=" * 60)
    print(f"{'排名':<4} {'代码':<8} {'名称':<10} {'今日评分':<8} {'首板日期':<10} {'最近涨停'}")
    print("-" * 60)
    
    for i, s in enumerate(stocks_with_scores[:8], 1):
        print(f"{i:<4} {s['code']:<8} {s['name']:<10} {s['today_score']:<8} {s['first_date']:<10} {s['latest_date']}")
    
    # 保存TOP8
    top8_list = [{
        'code': s['code'],
        'name': s['name'],
        'score': s['today_score'],
        'first_date': s['first_date'],
        'latest_date': s['latest_date']
    } for s in stocks_with_scores[:8]]
    
    try:
        with open(TOP8_FILE, 'r') as f:
            top8_data = json.load(f)
    except:
        top8_data = {"dates": {}}
    
    top8_data['dates'][today] = top8_list
    
    with open(TOP8_FILE, 'w') as f:
        json.dump(top8_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 已保存到 {TOP8_FILE}")
    print("=" * 60)

if __name__ == "__main__":
    main()
