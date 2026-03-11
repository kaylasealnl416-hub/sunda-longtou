#!/usr/bin/env python3
"""
股票评分系统 V2.0 加强版 - 增加区分度
"""
import akshare as ak
import os
import json
from datetime import datetime, timedelta

os.environ['https_proxy'] = 'http://127.0.0.1:7890'
os.environ['http_proxy'] = 'http://127.0.0.1:7890'

DATA_DIR = "/root/.openclaw/workspace/sunda-longtou/data"

def get_trade_dates(n=5):
    dates = []
    today = datetime.now()
    while len(dates) < n:
        if today.weekday() < 5:
            dates.append(today.strftime("%Y%m%d"))
        today -= timedelta(days=1)
    return dates

def get_market_env():
    dates = get_trade_dates(5)
    df_today = ak.stock_zt_pool_em(date=dates[0])
    df_yesterday = ak.stock_zt_pool_em(date=dates[1])
    
    today_codes = set(df_today['代码'].tolist())
    yesterday_codes = set(df_yesterday['代码'].tolist())
    
    jinjin = today_codes & yesterday_codes
    jinjin_rate = len(jinjin) / len(yesterday_codes) * 100 if yesterday_codes else 0
    
    if jinjin_rate >= 60:
        stage, stage_score = "高潮", 0
    elif jinjin_rate >= 40:
        stage, stage_score = "一致", 5
    elif jinjin_rate >= 20:
        stage, stage_score = "分歧", 10
    else:
        stage, stage_score = "分歧转一致", 15
    
    return {
        'today_zt': len(df_today),
        'yesterday_zt': len(df_yesterday),
        'jinjin': len(jinjin),
        'jinjin_rate': jinjin_rate,
        'stage': stage,
        'stage_score': stage_score
    }

def score_stock_v3(row, market, sector_zt, sector_zt_pct):
    """加强版评分 - 拉开分差"""
    score = 50  # 基础分降低
    
    lban = row.get('连板数', 0) or 0
    zdb = row.get('炸板次数', 0) or 0
    amount = row.get('成交额', 0) or 0
    fb_money = row.get('封板资金', 0) or 0
    hs = row.get('换手率', 0) or 0
    
    # 1. 连板高度 - 大幅拉开差距
    if lban >= 5: score += 25   # 5板+
    elif lban == 4: score += 20
    elif lban == 3: score += 15
    elif lban == 2: score += 10
    elif lban == 1: score += 3   # 1板不加分
    
    # 2. 封板质量
    if zdb == 0: score += 8
    elif zdb == 1: score += 3
    # 封成比
    fb_ratio = fb_money / amount if amount > 0 else 0
    if fb_ratio > 0.5: score += 7
    elif fb_ratio > 0.2: score += 4
    elif fb_ratio > 0.05: score += 1
    
    # 3. 换手率 - 拉开差距
    if hs >= 30: score += 10
    elif hs >= 20: score += 7
    elif hs >= 10: score += 5
    elif hs >= 5: score += 3
    # 换手率过低扣分
    if hs < 2: score -= 3
    
    # 4. 成交金额 - 拉开差距
    amount_yi = amount / 100000000
    if amount_yi >= 50: score += 10
    elif amount_yi >= 20: score += 7
    elif amount_yi >= 10: score += 5
    elif amount_yi >= 5: score += 3
    
    # 5. 市场周期
    score += market['stage_score']
    
    # 6. 板块效应 - 拉开差距
    if sector_zt >= 10: score += 15
    elif sector_zt >= 6: score += 10
    elif sector_zt >= 3: score += 5
    
    # 板块占比
    if sector_zt_pct >= 0.1: score += 5  # 占市场10%以上
    
    # 7. 个股地位
    if lban >= 3: score += 10  # 龙头
    if amount_yi >= 30: score += 5  # 容量核心
    if lban == 1 and hs >= 20: score += 3  # 首板高换手
    
    return score

def main():
    print("=" * 60)
    print("股票评分系统 V2.0 加强版")
    print("=" * 60)
    
    market = get_market_env()
    print(f"\n市场: 今日{market['today_zt']}只 昨日{market['yesterday_zt']}只 晋级{market['jinjin']}只({market['jinjin_rate']:.0f}%) {market['stage']}")
    
    dates = get_trade_dates(1)
    today = dates[0]
    df = ak.stock_zt_pool_em(date=today)
    sector_counts = df['所属行业'].value_counts()
    total = len(df)
    
    results = []
    for _, row in df.iterrows():
        code = row.get('代码')
        name = row.get('名称')
        industry = row.get('所属行业', '')
        sector_zt = sector_counts.get(industry, 0)
        sector_zt_pct = sector_zt / total
        score = score_stock_v3(row, market, sector_zt, sector_zt_pct)
        lban = row.get('连板数', 0) or 0
        hs = row.get('换手率', 0) or 0
        amount_yi = row.get('成交额', 0) / 100000000
        results.append({'code': code, 'name': name, 'score': score, 'industry': industry, 
                       'lianban': lban, 'hs': hs, 'amount': amount_yi})
    
    results.sort(key=lambda x: x['score'], reverse=True)
    
    print(f"\n📅 {today} 涨停: {len(df)}只")
    print("\n" + "=" * 60)
    print("🏆 TOP 8")
    print("=" * 60)
    
    for i, r in enumerate(results[:8], 1):
        print(f"{i}. {r['name']} ({r['code']}) - {r['score']}分")
        print(f"   {r['lianban']}板 换手{r['hs']:.0f}% 成交{r['amount']:.0f}亿 {r['industry']}")
    
    # 保存
    top8_list = [{'code': r['code'], 'name': r['name'], 'score': r['score'], 'date': today} for r in results[:8]]
    with open(f"{DATA_DIR}/daily_top8.json", 'w') as f:
        json.dump({"version": "2.0", "dates": {today: top8_list}}, f, ensure_ascii=False, indent=2)
    
    print(f"\n分差: {results[0]['score']} - {results[7]['score']} = {results[0]['score'] - results[7]['score']}分")
    print("✅ 完成!")

if __name__ == "__main__":
    main()
