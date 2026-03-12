#!/usr/bin/env python3
"""
数据获取脚本 - 每天15:55运行
Data Fetcher - Run at 15:55 daily

功能：
1. 获取当日涨停板数据
2. 获取人气榜单
3. 保存原始数据
4. 为评分系统准备数据
"""

import sys
import os
from datetime import datetime, timedelta
import pandas as pd

print("=" * 70)
print("📥 数据获取系统")
print("=" * 70)
print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)
print()

# 数据目录
data_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'daily')
os.makedirs(data_dir, exist_ok=True)

today = datetime.now().strftime('%Y%m%d')
today_str = datetime.now().strftime('%Y-%m-%d')

# ==================== 1. 获取涨停板数据 ====================
print("1️⃣ 获取当日涨停板数据...")
try:
    import akshare as ak
    
    zt_df = ak.stock_zt_pool_em(date=today)
    
    if zt_df.empty:
        print("❌ 今天没有涨停板数据")
        sys.exit(1)
    
    print(f"✅ 获取到 {len(zt_df)} 只涨停股")
    
    # 保存数据
    zt_path = os.path.join(data_dir, f'zt_{today}.csv')
    zt_df.to_csv(zt_path, index=False, encoding='utf-8-sig')
    print(f"💾 已保存: {zt_path}")
    
except Exception as e:
    print(f"❌ 获取涨停板数据失败: {e}")
    sys.exit(1)

print()

# ==================== 2. 获取昨日涨停板数据（用于计算赚钱效应） ====================
print("2️⃣ 获取昨日涨停板数据...")
try:
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
    yesterday_path = os.path.join(data_dir, f'zt_{yesterday}.csv')
    
    # 检查是否已有昨日数据
    if os.path.exists(yesterday_path):
        print(f"✅ 昨日数据已存在: {yesterday_path}")
    else:
        # 获取昨日数据
        df_yesterday = ak.stock_zt_pool_em(date=yesterday)
        df_yesterday.to_csv(yesterday_path, index=False, encoding='utf-8-sig')
        print(f"✅ 已获取并保存昨日数据: {yesterday_path}")
    
except Exception as e:
    print(f"⚠️  获取昨日数据失败: {e}")

print()

# ==================== 3. 获取人气榜单 ====================
print("3️⃣ 获取人气榜单...")
try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))
    from popularity_fetcher import PopularityFetcher
    
    fetcher = PopularityFetcher()
    rank_data = fetcher.fetch_all_sources(limit=50)
    fetcher.save_daily_rank(rank_data, date=today_str)
    
    print("✅ 人气榜单已获取并保存")
    
except Exception as e:
    print(f"⚠️  获取人气榜单失败: {e}")

print()

# ==================== 4. 数据统计 ====================
print("4️⃣ 数据统计...")
print(f"   涨停股数: {len(zt_df)}只")
print(f"   首板数: {len(zt_df[zt_df['连板数'] == 1])}只")
print(f"   连板数: {len(zt_df[zt_df['连板数'] > 1])}只")

board_stats = zt_df['连板数'].value_counts().sort_index()
for boards, count in board_stats.items():
    print(f"   {boards}板: {count}只")

print()

# ==================== 完成 ====================
print("=" * 70)
print("✅ 数据获取完成！")
print("=" * 70)
print()
print("📝 下一步: 等待评分系统运行（16:00）")
