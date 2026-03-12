#!/usr/bin/env python3
"""
每日自动评分脚本
Daily Auto Scoring Script

功能：
1. 获取当日涨停板数据
2. 对所有涨停股评分
3. 生成TOP 8详细报告
4. 获取人气榜单
5. 更新历史跟踪
6. 计算赚钱效应
7. 发送报告到飞书
"""

import sys
import os
from datetime import datetime
import pandas as pd

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))

print("=" * 70)
print("🎯 龙头股评分系统 - 每日自动复盘")
print("=" * 70)
print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)
print()

# ==================== 1. 读取涨停板数据 ====================
print("1️⃣ 读取当日涨停板数据...")
try:
    today = datetime.now().strftime('%Y%m%d')
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'daily')
    zt_path = os.path.join(data_dir, f'zt_{today}.csv')
    
    if not os.path.exists(zt_path):
        print(f"❌ 数据文件不存在: {zt_path}")
        print("⚠️  请先运行 fetch_data.py 获取数据")
        sys.exit(1)
    
    zt_df = pd.read_csv(zt_path, encoding='utf-8-sig')
    
    if zt_df.empty:
        print("❌ 数据文件为空")
        sys.exit(1)
    
    print(f"✅ 读取到 {len(zt_df)} 只涨停股")
    
except Exception as e:
    print(f"❌ 读取涨停板数据失败: {e}")
    sys.exit(1)

print()

# ==================== 2. 评分系统 ====================
print("2️⃣ 对所有涨停股进行评分...")

def calculate_score(stock):
    """简化评分函数"""
    total_score = 0
    
    boards = int(stock['连板数'])
    turnover = float(stock['成交额'])
    turnover_rate = float(stock['换手率'])
    seal_amount = float(stock['封板资金'])
    bomb_count = int(stock['炸板次数'])
    
    # 情绪面 30分
    emotion_score = 0
    if boards >= 3:
        emotion_score += 10
    elif boards == 2:
        emotion_score += 12
    else:
        emotion_score += 15
    
    if turnover > 3e9 and 10 <= turnover_rate <= 15:
        emotion_score += 13
    elif turnover > 2e9:
        emotion_score += 11
    elif turnover > 1e9:
        emotion_score += 9
    else:
        emotion_score += 6
    
    total_score += emotion_score
    
    # 资金面 30分
    capital_score = 0
    if seal_amount > 3e8 and bomb_count == 0:
        capital_score += 12
    elif seal_amount > 2e8 and bomb_count <= 1:
        capital_score += 10
    elif seal_amount > 1e8:
        capital_score += 8
    else:
        capital_score += 6
    
    if turnover > 3e9:
        capital_score += 10
    elif turnover > 2e9:
        capital_score += 8
    elif turnover > 1e9:
        capital_score += 6
    else:
        capital_score += 4
    
    big_order_ratio = seal_amount / turnover * 100 if turnover > 0 else 0
    if big_order_ratio > 10:
        capital_score += 8
    elif big_order_ratio > 5:
        capital_score += 6
    elif big_order_ratio > 2:
        capital_score += 4
    else:
        capital_score += 2
    
    total_score += capital_score
    
    # 技术面 25分
    technical_score = 0
    if boards >= 5:
        technical_score += 10
    elif boards == 4:
        technical_score += 9
    elif boards == 3:
        technical_score += 8
    elif boards == 2:
        technical_score += 7
    else:
        technical_score += 6
    
    seal_time = str(int(stock['首次封板时间'])).zfill(6)
    if seal_time < '093000' and bomb_count == 0:
        technical_score += 8
    elif seal_time < '100000' and bomb_count == 0:
        technical_score += 7
    elif bomb_count == 0:
        technical_score += 6
    else:
        technical_score += 5
    
    if boards >= 3:
        technical_score += 7
    elif boards == 2:
        technical_score += 5
    else:
        technical_score += 3
    
    total_score += technical_score
    
    # 题材面 10分
    industry = stock['所属行业']
    theme_score = 0
    if '电力' in industry or '新能源' in industry or '光伏' in industry:
        theme_score += 6
    else:
        theme_score += 4
    
    if boards >= 3:
        theme_score += 4
    elif boards == 2:
        theme_score += 3
    else:
        theme_score += 2
    
    total_score += theme_score
    
    # 基本面 5分
    total_score += 3
    
    return total_score

# 评分
scores = []
for idx, row in zt_df.iterrows():
    score = calculate_score(row)
    scores.append({
        'code': row['代码'],
        'name': row['名称'],
        'score': score,
        'boards': int(row['连板数']),
        'turnover': float(row['成交额']),
        'change_pct': float(row['涨跌幅'])
    })

scores.sort(key=lambda x: x['score'], reverse=True)
print(f"✅ 评分完成，TOP 1: {scores[0]['name']} ({scores[0]['score']}分)")
print()

# ==================== 3. 生成报告 ====================
print("3️⃣ 生成TOP 8详细报告...")

report = f"""
🎯 龙头股评分系统 - 每日报告

📅 日期: {datetime.now().strftime('%Y-%m-%d')}
📊 涨停股数: {len(zt_df)}只
🏆 TOP 8 龙头股

"""

for i, stock in enumerate(scores[:8], 1):
    report += f"{i}. {stock['name']} ({stock['code']}) - {stock['score']}分\n"
    report += f"   {stock['boards']}板 | 成交{stock['turnover']/1e8:.2f}亿 | 涨幅{stock['change_pct']:.2f}%\n\n"

print("✅ 报告已生成")
print()

# ==================== 4. 读取人气榜 ====================
print("4️⃣ 读取人气榜单...")
try:
    import json
    
    today_str = datetime.now().strftime('%Y-%m-%d')
    popularity_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'popularity')
    popularity_path = os.path.join(popularity_dir, f'popularity_rank_{today_str}.json')
    
    if os.path.exists(popularity_path):
        with open(popularity_path, 'r', encoding='utf-8') as f:
            rank_data = json.load(f)
        
        if rank_data.get('sources', {}).get('eastmoney'):
            report += f"\n🔥 今日人气榜 TOP 5:\n"
            for item in rank_data['sources']['eastmoney'][:5]:
                report += f"{item['rank']}. {item['name']} ({item['code']}) 涨{item['change_pct']:.2f}%\n"
        
        print("✅ 人气榜已读取")
    else:
        print(f"⚠️  人气榜数据不存在: {popularity_path}")
        
except Exception as e:
    print(f"⚠️  人气榜读取失败: {e}")

print()

# ==================== 5. 更新历史跟踪 ====================
print("5️⃣ 更新历史跟踪...")
try:
    from tracking_system import TrackingSystem
    
    tracker = TrackingSystem()
    
    # 添加今日首板
    first_boards = [s for s in scores if s['boards'] == 1]
    if first_boards:
        tracker.add_first_board_stocks(first_boards)
    
    # 检查断板
    tracker.check_and_update(scores)
    
    print("✅ 历史跟踪已更新")
except Exception as e:
    print(f"⚠️  历史跟踪更新失败: {e}")

print()

# ==================== 6. 计算赚钱效应 ====================
print("6️⃣ 计算赚钱效应...")
try:
    from datetime import timedelta
    
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
    yesterday_path = os.path.join(data_dir, f'zt_{yesterday}.csv')
    
    if os.path.exists(yesterday_path):
        df_yesterday = pd.read_csv(yesterday_path, encoding='utf-8-sig')
        
        yesterday_first = df_yesterday[df_yesterday['连板数'] == 1]
        yesterday_codes = set(yesterday_first['代码'].astype(str))
        today_codes = set(zt_df['代码'].astype(str))
        
        success_codes = yesterday_codes & today_codes
        success_rate = len(success_codes) / len(yesterday_first) * 100 if len(yesterday_first) > 0 else 0
        
        report += f"\n📈 赚钱效应:\n"
        report += f"昨日首板: {len(yesterday_first)}只\n"
        report += f"今日晋级: {len(success_codes)}只\n"
        report += f"成功率: {success_rate:.2f}%\n"
        
        print(f"✅ 首板晋级成功率: {success_rate:.2f}%")
    else:
        print(f"⚠️  昨日数据不存在: {yesterday_path}")
        
except Exception as e:
    print(f"⚠️  赚钱效应计算失败: {e}")

print()

# ==================== 7. 发送到飞书 ====================
print("7️⃣ 发送报告到飞书...")
try:
    import requests
    
    FEISHU_WEBHOOK = "https://open.feishu.cn/open-apis/bot/v2/hook/7f7a42b7-ed24-4be3-9253-9d4ea4cb0bee"
    
    payload = {
        "msg_type": "text",
        "content": {"text": report}
    }
    
    resp = requests.post(FEISHU_WEBHOOK, json=payload, timeout=10)
    
    if resp.status_code == 200:
        print("✅ 报告已发送到飞书")
    else:
        print(f"⚠️  飞书推送失败: {resp.status_code}")
        
except Exception as e:
    print(f"⚠️  飞书推送失败: {e}")

print()

# ==================== 完成 ====================
print("=" * 70)
print("✅ 每日自动复盘完成！")
print("=" * 70)
