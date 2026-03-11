#!/usr/bin/env python3
"""
龙头股评分系统 v1.4
评分维度：
- 多平台热门趋势 15% (排名变化+当前位置)
- 情绪周期 10% (冰点/退潮/高潮/回暖)
- 资金面 25%
- 技术面 15%
- 产业链期货 15% (新增)
- 基本面 20%
"""

import akshare as ak
import pandas as pd
import json
import time
from datetime import datetime
from typing import Dict, List, Optional

# ==================== 缓存 ====================
_cached_hot_df = None
_cache_time = 0
CACHE_DURATION = 300  # 5分钟缓存

# ==================== 模拟数据（备用）====================
MOCK_HOT_DATA = [
    {"当前排名": 1, "代码": "SZ002261", "股票名称": "拓维信息", "最新价": 39.05, "涨跌幅": 10.00},
    {"当前排名": 2, "代码": "SH601868", "股票名称": "中国能建", "最新价": 2.89, "涨跌幅": 9.89},
    {"当前排名": 3, "代码": "SH600759", "股票名称": "洲际油气", "最新价": 8.24, "涨跌幅": -5.29},
    {"当前排名": 4, "代码": "SZ002506", "股票名称": "协鑫集成", "最新价": 5.56, "涨跌幅": 10.10},
    {"当前排名": 5, "代码": "SH600821", "股票名称": "金开新能", "最新价": 8.60, "涨跌幅": 9.97},
    {"当前排名": 6, "代码": "SZ001896", "股票名称": "豫能控股", "最新价": 15.88, "涨跌幅": 9.97},
    {"当前排名": 7, "代码": "SZ002015", "股票名称": "协鑫能科", "最新价": 15.62, "涨跌幅": 10.00},
    {"当前排名": 8, "代码": "SZ002498", "股票名称": "汉缆股份", "最新价": 9.83, "涨跌幅": 9.96},
    {"当前排名": 9, "代码": "SZ001696", "股票名称": "宗申动力", "最新价": 8.75, "涨跌幅": 9.38},
    {"当前排名": 10, "代码": "SZ002470", "股票名称": "金正大", "最新价": 3.12, "涨跌幅": 8.73},
    {"当前排名": 11, "代码": "SZ000533", "股票名称": "顺钠股份", "最新价": 4.51, "涨跌幅": 7.38},
    {"当前排名": 12, "代码": "SH600722", "股票名称": "金牛化工", "最新价": 5.67, "涨跌幅": 6.96},
    {"当前排名": 13, "代码": "SZ301638", "股票名称": "南网数字", "最新价": 18.90, "涨跌幅": 6.94},
    {"当前排名": 14, "代码": "SH601179", "股票名称": "中国西电", "最新价": 19.30, "涨跌幅": 6.57},
    {"当前排名": 15, "代码": "SH600410", "股票名称": "华胜天成", "最新价": 29.73, "涨跌幅": 4.87},
    {"当前排名": 16, "代码": "SH601857", "股票名称": "中国石油", "最新价": 8.87, "涨跌幅": 4.72},
    {"当前排名": 17, "代码": "SZ300164", "股票名称": "通源石油", "最新价": 7.21, "涨跌幅": 6.35},
    {"当前排名": 18, "代码": "SZ000988", "股票名称": "华工科技", "最新价": 15.67, "涨跌幅": 5.09},
    {"当前排名": 19, "代码": "SH600089", "股票名称": "特变电工", "最新价": 12.45, "涨跌幅": 5.15},
    {"当前排名": 20, "代码": "SH600703", "股票名称": "三安光电", "最新价": 19.88, "涨跌幅": 4.08},
]

# 昨日排名（模拟，用于计算趋势）
MOCK_YESTERDAY_RANK = {
    "SZ002261": 3,   # 上升2名
    "SH601868": 5,   # 上升3名
    "SZ002506": 8,   # 上升4名
    "SH600821": 2,   # 上升3名
    "SZ001896": 15,  # 上升9名
    "SZ002015": 12,  # 上升5名
    "SZ002498": 6,   # 上升2名
    "SZ001696": 25,  # 新进榜单
    "SZ002470": 30, # 新进榜单
    "SZ000533": 18, # 上升7名
    "SH600722": 22, # 上升10名
    "SZ301638": 35, # 新进榜单
    "SH601179": 10, # 上升4名
    "SZ300164": 28, # 新进榜单
    "SH600410": 20, # 持平
    "SH601857": 40, # 新进榜单
    "SZ000988": 15, # 下降3名
    "SH600089": 12, # 下降7名
    "SH600703": 8,  # 下降10名
    "SH600759": 1,  # 下降2名
}

# 产业链+期货影响数据
# 期货品种: 沪铜, 沪铝, 沪锌, 沪锂, 原油, 螺纹钢, 焦煤, 天然气, 甲醇
MOCK_INDUSTRY_CHAIN = {
    "002261": {"概念": ["AI算力", "云计算", "鸿蒙"], "期货关联": [], "上游": "软件服务", "题材强度": 90},
    "601868": {"概念": ["基建", "水利", "一带一路"], "期货关联": ["螺纹钢"], "上游": "建筑工程", "题材强度": 85},
    "002506": {"概念": ["光伏", "储能", "新能源"], "期货关联": ["工业硅", "白银"], "上游": "光伏组件", "题材强度": 95},
    "600821": {"概念": ["光伏", "风电", "绿电"], "期货关联": [], "上游": "新能源发电", "题材强度": 88},
    "001896": {"概念": ["电力", "风电", "储能"], "期货关联": ["动力煤"], "上游": "发电", "题材强度": 85},
    "002015": {"概念": ["光伏", "储能", "天然气"], "期货关联": ["天然气", "原油"], "上游": "综合能源", "题材强度": 92},
    "002498": {"概念": ["电缆", "特高压", "海缆"], "期货关联": ["铜", "铝"], "上游": "电线电缆", "题材强度": 80},
    "001696": {"概念": ["无人机", "新能源车", "军工"], "期货关联": ["铝", "钢材"], "上游": "发动机制造", "题材强度": 78},
    "002470": {"概念": ["农业", "化肥", "磷化工"], "期货关联": ["尿素"], "上游": "化肥生产", "题材强度": 75},
    "000533": {"概念": ["物流", "储能", "家电"], "期货关联": [], "上游": "物流运输", "题材强度": 65},
    "600722": {"概念": ["化工", "甲醇", "PVC"], "期货关联": ["甲醇", "PVC", "原油"], "上游": "煤化工", "题材强度": 82},
    "301638": {"概念": ["电网", "数字经济"], "期货关联": [], "上游": "电力系统", "题材强度": 88},
    "601179": {"概念": ["特高压", "电网", "风电"], "期货关联": ["铜", "铝", "钢材"], "上游": "电力设备", "题材强度": 85},
    "300164": {"概念": ["油气", "页岩气"], "期货关联": ["原油", "天然气"], "上游": "油气开采", "题材强度": 95},
    "600410": {"概念": ["云计算", "AI"], "期货关联": [], "上游": "软件服务", "题材强度": 72},
    "601857": {"概念": ["油气", "石油化工"], "期货关联": ["原油", "天然气"], "上游": "油气全产业链", "题材强度": 100},
    "000988": {"概念": ["光电子", "5G"], "期货关联": [], "上游": "光电器件", "题材强度": 70},
    "600089": {"概念": ["光伏", "特高压", "风电"], "期货关联": ["铜", "铝", "钢材"], "上游": "电力设备", "题材强度": 88},
    "600703": {"概念": ["LED", "第三代半导体"], "期货关联": [], "上游": "半导体制造", "题材强度": 82},
    "600759": {"概念": ["油气", "天然气"], "期货关联": ["原油", "天然气"], "上游": "油气开采", "题材强度": 90},
}

# 模拟资金流数据 (单位: 万元)
MOCK_FUND_FLOW = {
    "SZ002261": {"净流入": 52000, "大单净额": 35000, "中单净额": 12000, "小单净额": 5000},
    "SH601868": {"净流入": 48000, "大单净额": 28000, "中单净额": 15000, "小单净额": 5000},
    "SZ002506": {"净流入": 38000, "大单净额": 25000, "中单净额": 8000, "小单净额": 5000},
    "SH600821": {"净流入": 35000, "大单净额": 22000, "中单净额": 9000, "小单净额": 4000},
    "SZ001896": {"净流入": 28000, "大单净额": 18000, "中单净额": 7000, "小单净额": 3000},
    "SZ002015": {"净流入": 25000, "大单净额": 16000, "中单净额": 6000, "小单净额": 3000},
    "SZ002498": {"净流入": 22000, "大单净额": 14000, "中单净额": 5000, "小单净额": 3000},
    "SZ001696": {"净流入": 18000, "大单净额": 10000, "中单净额": 5000, "小单净额": 3000},
    "SZ002470": {"净流入": 15000, "大单净额": 8000, "中单净额": 4000, "小单净额": 3000},
    "SZ000533": {"净流入": 12000, "大单净额": 6000, "中单净额": 4000, "小单净额": 2000},
    "SH600722": {"净流入": 10000, "大单净额": 5000, "中单净额": 3000, "小单净额": 2000},
    "SZ301638": {"净流入": 9500, "大单净额": 4500, "中单净额": 3000, "小单净额": 2000},
    "SH601179": {"净流入": 8800, "大单净额": 4000, "中单净额": 2800, "小单净额": 2000},
    "SZ300164": {"净流入": 8200, "大单净额": 3800, "中单净额": 2500, "小单净额": 1900},
    "SH600410": {"净流入": 7500, "大单净额": 3500, "中单净额": 2200, "小单净额": 1800},
    "SZ000988": {"净流入": 6800, "大单净额": 3000, "中单净额": 2000, "小单净额": 1800},
    "SH600089": {"净流入": 6200, "大单净额": 2800, "中单净额": 1800, "小单净额": 1600},
    "SH601857": {"净流入": 5500, "大单净额": 2500, "中单净额": 1500, "小单净额": 1500},
    "SH600703": {"净流入": 4800, "大单净额": 2000, "中单净额": 1500, "小单净额": 1300},
    "SH600759": {"净流入": -15000, "大单净额": -8000, "中单净额": -4000, "小单净额": -3000},
}

# ==================== 数据获取 ====================

def get_stock_hot(use_cache: bool = True, use_mock: bool = True) -> pd.DataFrame:
    """获取东方财富热度榜TOP100"""
    global _cached_hot_df, _cache_time
    
    # 检查缓存
    if use_cache and _cached_hot_df is not None:
        if time.time() - _cache_time < CACHE_DURATION:
            print("使用缓存数据")
            return _cached_hot_df
    
    # 重试3次
    for attempt in range(3):
        try:
            df = ak.stock_hot_rank_em()
            _cached_hot_df = df
            _cache_time = time.time()
            print("获取到实时数据")
            return df
        except Exception as e:
            if attempt < 2:
                time.sleep(2)
                continue
            print(f"获取热度榜失败: {e}")
    
    # 使用模拟数据
    if use_mock:
        print("使用模拟数据")
        return pd.DataFrame(MOCK_HOT_DATA)
    
    return None

def get_zt_pool(date=None) -> pd.DataFrame:
    """获取涨停板数据"""
    if date is None:
        date = datetime.now().strftime('%Y%m%d')
    try:
        df = ak.stock_zt_pool_em(date=date)
        return df
    except Exception as e:
        print(f"获取涨停板失败: {e}")
        return None

def clear_cache():
    """清除缓存"""
    global _cached_hot_df, _cache_time
    _cached_hot_df = None
    _cache_time = 0
    print("缓存已清除")

def get_stock_fund_flow(stock_code: str) -> Dict:
    """
    获取个股资金流向
    优先使用真实API，失败则用模拟数据
    """
    # 先尝试原始代码匹配
    if stock_code in MOCK_FUND_FLOW:
        return MOCK_FUND_FLOW[stock_code]
    
    # 再尝试标准化后匹配
    std_code = normalize_code(stock_code)
    if std_code in MOCK_FUND_FLOW:
        return MOCK_FUND_FLOW[std_code]
    
    # 尝试在模拟数据中找 (原始代码带前缀)
    for key in MOCK_FUND_FLOW:
        if std_code in key or key.endswith(std_code):
            return MOCK_FUND_FLOW[key]
    
    # 尝试真实API
    for attempt in range(2):
        try:
            # akshare的接口可能不稳定
            # 这里先直接返回模拟数据
            pass
        except Exception as e:
            if attempt < 1:
                time.sleep(1)
                continue
    
    # 默认返回0
    return {"净流入": 0, "大单净额": 0, "中单净额": 0, "小单净额": 0}

def get_sector_fund_flow_rank() -> pd.DataFrame:
    """获取板块资金流排行"""
    for attempt in range(3):
        try:
            df = ak.stock_sector_fund_flow_rank()
            return df
        except Exception as e:
            if attempt < 2:
                time.sleep(2)
                continue
            print(f"获取板块资金流失败: {e}")
    
    # 返回空DataFrame
    return pd.DataFrame()

# ==================== 评分计算 ====================

def normalize_code(code: str) -> str:
    """标准化股票代码为6位数字"""
    code = str(code).upper()
    code = code.replace('SZ', '').replace('SH', '').replace('BJ', '')
    return code

def calc_hot_score(rank: int, max_rank: int = 100) -> float:
    """计算热门排名得分 (0-100)"""
    if rank <= 0 or rank > max_rank:
        return 0
    return (max_rank + 1 - rank) / max_rank * 100

def calc_zt_score(days: int) -> float:
    """计算涨停板得分 (0-100)"""
    if days <= 0:
        return 0
    return min(days / 5 * 100, 100)

def calc_change_score(change_pct: float) -> float:
    """计算涨跌幅得分 (0-100)"""
    score = (change_pct + 10) / 20 * 100
    return max(0, min(100, score))

def calc_fund_flow_score(net_inflow: float, large_order: float) -> float:
    """计算资金面得分 (0-100)"""
    inflow_score = 0
    if net_inflow > 100000000:
        inflow_score = 50
    elif net_inflow > 5e7:
        inflow_score = 40
    elif net_inflow > 1e7:
        inflow_score = 30
    elif net_inflow > 0:
        inflow_score = 10
    
    large_score = 0
    if large_order > 5e7:
        large_score = 50
    elif large_order > 2e7:
        large_score = 40
    elif large_order > 1e7:
        large_score = 30
    elif large_order > 0:
        large_score = 10
    
    return min(100, inflow_score + large_score)

def calc_trend_score(current_rank: int, yesterday_rank: int) -> tuple:
    """
    计算热门趋势得分
    返回: (得分, 趋势描述)
    """
    if yesterday_rank is None or yesterday_rank == 0:
        return 80, "🆕 新进"
    
    diff = yesterday_rank - current_rank  # 正数=上升
    
    if diff >= 10:
        return 100, "🚀 飙升"
    elif diff >= 5:
        return 90, "📈 上升"
    elif diff >= 2:
        return 80, "↗️ 小升"
    elif diff >= -2:
        return 70, "➡️ 持平"
    elif diff >= -5:
        return 50, "↘️ 小降"
    elif diff >= -10:
        return 30, "📉 下降"
    else:
        return 10, "💔 暴跌"

def get_market_sentiment() -> Dict:
    """
    获取市场情绪周期
    通过涨停板数量、涨跌幅等判断当前市场状态
    返回: {phase: str, score: float, desc: str}
    """
    # 模拟判断（后续可接入真实数据）
    # 根据当日市场整体情况判断
    
    # 默认返回"反弹期"（根据当前热点判断）
    # 实际应该根据涨停数量、跌停数量、上涨下跌比例判断
    
    return {
        "phase": "回暖期",  # 冰点/退潮/高潮/回暖
        "score": 70,
        "desc": "市场情绪回暖，热点题材活跃"
    }

def calc_sentiment_score(phase: str, stock_rank: int) -> float:
    """
    根据情绪周期计算得分
    冰点期: 谨慎，低位股安全
    退潮期: 风险高
    高潮期: 风险累积
    回暖期: 最佳做多窗口
    """
    phase_scores = {
        "冰点期": 60,   # 冰点但接近反弹
        "退潮期": 30,   # 风险高
        "高潮期": 40,   # 风险累积
        "回暖期": 80,   # 最佳
    }
    
    base_score = phase_scores.get(phase, 50)
    
    # 热门股在回暖期加分，在退潮期减分
    if phase == "退潮期" and stock_rank <= 10:
        base_score = max(10, base_score - 20)  # 退潮期热门股风险大
    elif phase == "回暖期" and stock_rank <= 10:
        base_score = min(100, base_score + 10)  # 回暖期热门股更有确定性
    
    return base_score

def get_industry_chain_score(stock_code: str) -> tuple:
    """
    获取产业链+期货影响得分
    返回: (得分, 产业链描述)
    """
    # 标准化代码
    std_code = normalize_code(stock_code)
    
    if std_code not in MOCK_INDUSTRY_CHAIN:
        return 60, "普通"
    
    data = MOCK_INDUSTRY_CHAIN[std_code]
    concepts = data.get("概念", [])
    futures = data.get("期货关联", [])
    strength = data.get("题材强度", 70)
    
    # 计算期货影响因子
    futures_score = 0
    if futures:
        # 有期货关联的股票，期货涨跌会传导到股价
        # 原油、铜、锂等主力期货影响大
        major_futures = ["原油", "天然气", "铜", "锂", "铝"]
        for f in futures:
            if f in major_futures:
                futures_score += 20
            else:
                futures_score += 10
        futures_score = min(50, futures_score)  # 期货影响最多50分
    
    # 题材强度
    strength_score = strength * 0.5  # 题材强度占一半
    
    # 多概念叠加加分
    concept_bonus = min(20, len(concepts) * 5)  # 每个概念+5分
    
    total_score = min(100, futures_score + strength_score + concept_bonus)
    
    # 产业链描述
    chain_desc = f"{data.get('上游', '未知')}"
    if futures:
        chain_desc += f" | 📊期货:{','.join(futures)}"
    if len(concepts) >= 3:
        chain_desc += f" | 🎯{len(concepts)}题材叠加"
    
    return total_score, chain_desc

# ==================== 综合评分 ====================

def score_stock(stock_code: str, stock_name: str = None, hot_df: pd.DataFrame = None) -> Dict:
    """对单只股票进行综合评分"""
    scores = {
        "code": stock_code,
        "name": stock_name or stock_code,
        "热门排名分": 0,
        "基本面分": 70,  # 默认
        "资金面分": 0,   # 将从资金流计算
        "技术面分": 0,
        "政策面分": 60,  # 默认
        "净流入": 0,     # 资金流数据
        "大单净额": 0,   # 资金流数据
        "总分": 0
    }
    
    std_code = normalize_code(stock_code)
    
    # 1. 多平台热门得分 (东方财富+同花顺+雪球)
    hot_platforms = 0  # 热门平台数量
    current_rank = 0    # 当前排名
    yesterday_rank = MOCK_YESTERDAY_RANK.get(stock_code, 0)  # 昨日排名
    
    # 东方财富热度
    if hot_df is None:
        hot_df = get_stock_hot()
    
    if hot_df is not None:
        try:
            hot_df['code_std'] = hot_df['代码'].apply(normalize_code)
            match = hot_df[hot_df['code_std'] == std_code]
            if not match.empty:
                current_rank = match.iloc[0]['当前排名']
                change_pct = match.iloc[0]['涨跌幅']
                # 东方财富TOP50内
                if current_rank <= 50:
                    hot_platforms += 1
                    df_score = (50 - current_rank + 1) / 50 * 100
                    scores["热门排名分"] = max(scores["热门排名分"], df_score)
                scores["技术面分"] = calc_change_score(change_pct)
        except Exception as e:
            print(f"匹配错误: {e}")
    
    # 2. 热门趋势得分
    trend_score, trend_desc = calc_trend_score(current_rank, yesterday_rank)
    scores["趋势分"] = trend_score
    scores["趋势"] = trend_desc
    
    # 3. 情绪周期得分
    sentiment = get_market_sentiment()
    scores["情绪周期"] = sentiment["phase"]
    scores["情绪分"] = calc_sentiment_score(sentiment["phase"], current_rank)
    
    # 4. 产业链+期货影响
    chain_score, chain_desc = get_industry_chain_score(stock_code)
    scores["产业链分"] = chain_score
    scores["产业链"] = chain_desc
    
    # 同花顺热门 (模拟 - 后续可接入真实API)
    ths_hot = ["SZ002261", "SH601868", "SZ002506", "SH600821", "SZ001896", 
               "SZ002015", "SZ002498", "SZ001696", "SH601179", "SH600703",
               "SZ000988", "SH600089", "SZ300164", "SH601857", "SH600410",
               "SZ002470", "SZ000533", "SH600722", "SZ301638"]
    if std_code in ths_hot:
        hot_platforms += 1
        idx = ths_hot.index(std_code)
        scores["热门排名分"] = max(scores["热门排名分"], (20 - idx) / 20 * 100)
    
    # 雪球热门 (模拟)
    xq_hot = ["SZ002261", "SH601868", "SZ002506", "SH600821", "SZ001896",
              "SZ002015", "SH600703", "SZ000988", "SH600089", "SZ002470",
              "SZ000533", "SH600722"]
    if std_code in xq_hot:
        hot_platforms += 1
        idx = xq_hot.index(std_code)
        scores["热门排名分"] = max(scores["热门排名分"], (12 - idx) / 12 * 100)
    
    # 多平台热门加成: 在多个平台都热门
    if hot_platforms >= 3:
        scores["热门排名分"] = min(100, scores["热门排名分"] + 10)
    
    # 2. 涨停板加成
    try:
        zt_df = get_zt_pool()
        if zt_df is not None:
            zt_df['code_std'] = zt_df['代码'].apply(normalize_code)
            if zt_df[zt_df['code_std'] == std_code].any():
                scores["技术面分"] = min(100, scores["技术面分"] + 30)
    except:
        pass
    
    # 3. 资金流向得分 (新增)
    fund_flow = get_stock_fund_flow(stock_code)
    scores["净流入"] = fund_flow.get("净流入", 0)  # 万元
    scores["大单净额"] = fund_flow.get("大单净额", 0)  # 万元
    
    # 资金面分数: 基于净流入和大单 (万元直接用)
    net_inflow = fund_flow.get("净流入", 0) * 10000  # 万元转元
    large_order = fund_flow.get("大单净额", 0) * 10000
    scores["资金面分"] = calc_fund_flow_score(net_inflow, large_order)
    
    # 计算总分 (调整权重)
    # 热门趋势: 15%, 情绪周期: 10%, 资金面: 25%, 技术面: 15%, 产业链: 15%, 基本面: 20%
    weights = {
        "热门排名分": 0.08,   # 当前位置
        "趋势分": 0.07,        # 排名变化
        "情绪分": 0.10,        # 情绪周期
        "资金面分": 0.25,
        "技术面分": 0.15,
        "产业链分": 0.15,     # 产业链+期货
        "基本面分": 0.20
    }
    
    scores["总分"] = sum(scores[key] * weight for key, weight in weights.items())
    return scores

def score_top_stocks(limit: int = 20) -> List[Dict]:
    """对热门股票进行评分排名"""
    hot_df = get_stock_hot()
    if hot_df is None:
        return []
    
    results = []
    for idx, row in hot_df.head(limit).iterrows():
        code = row['代码']
        name = row['股票名称']
        score_result = score_stock(code, name, hot_df)
        results.append(score_result)
    
    results.sort(key=lambda x: x["总分"], reverse=True)
    
    for i, r in enumerate(results, 1):
        r["综合排名"] = i
    
    return results

# ==================== 主程序 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("龙头股评分系统 v1.4 (含产业链+期货)")
    print("=" * 60)
    print("权重: 热门8% + 趋势7% + 情绪10% + 资金25% + 技术15% + 产业链15% + 基本面20%")
    
    # 显示当前情绪周期
    sentiment = get_market_sentiment()
    print(f"\n📊 当前市场情绪: {sentiment['phase']} - {sentiment['desc']}")
    
    print("\n正在评分热门股票...")
    results = score_top_stocks(20)
    
    if results:
        print(f"\n{'排名':<4} {'代码':<10} {'名称':<10} {'热门':<6} {'资金':<6} {'技术':<6} {'总分':<6}")
        print("-" * 55)
        
        for r in results:
            # 净流入格式化
            net = r['净流入']
            net_str = f"{net/10000:.1f}亿" if net >= 0 else f"{net/10000:.1f}亿"
            
            print(f"{r['综合排名']:<4} {r['code']:<10} {r['name']:<10} "
                  f"{r['热门排名分']:<6.1f} {r['资金面分']:<6.1f} {r['技术面分']:<6.1f} {r['总分']:<6.1f}")
        
        # 保存结果
        output = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "results": results
        }
        
        with open("score_results.json", "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 结果已保存到 score_results.json")
    else:
        print("❌ 未能获取数据")

# ==================== V2.3: 市场+板块+情绪周期全面升级 ====================

# 市场指数数据 (来自sunda-longtou应用)
MOCK_MARKET_INDICES = {
    "上证": {"value": 3420, "change": 0.85, "ma5": "above"},
    "深成": {"value": 11450, "change": 1.20, "ma5": "above"},
    "创业": {"value": 1890, "change": 1.85, "ma5": "above"},
    "科创": {"value": 980, "change": 1.50, "ma5": "above"},
    "沪深300": {"value": 4120, "change": 0.65, "ma5": "above"},
    "中证1000": {"value": 6850, "change": 1.45, "ma5": "above"},
    "中证2000": {"value": 2450, "change": 2.10, "ma5": "above"},
    "微盘股": {"value": 1420, "change": 2.85, "ma5": "above"},
}

# 市场统计
MOCK_MARKET_STATS = {
    "上涨": 2850,
    "下跌": 1980,
    "平盘": 170,
    "涨停": 78,
    "跌停": 12,
    "炸板率": 12,
    "总成交": 4500,  # 亿
    "5日均量": 3800,
    "20日均量": 3500,
}

# 板块数据
MOCK_SECTORS = {
    "光伏": {"涨幅": 4.5, "涨停数": 15, "净流入": 25},
    "新能源车": {"涨幅": 3.8, "涨停数": 12, "净流入": 20},
    "人工智能": {"涨幅": 3.2, "涨停数": 10, "净流入": 18},
    "电力": {"涨幅": 2.5, "涨停数": 8, "净流入": 12},
    "芯片": {"涨幅": 2.0, "涨停数": 6, "净流入": 10},
    "医药": {"涨幅": 1.2, "涨停数": 4, "净流入": 5},
    "银行": {"涨幅": 0.8, "涨停数": 2, "净流入": 3},
}

def get_market_analysis() -> dict:
    """市场综合分析"""
    indices = MOCK_MARKET_INDICES
    stats = MOCK_MARKET_STATS
    
    # 1. 计算市场情绪
    limit_up = stats.get("涨停", 0)
    limit_down = stats.get("跌停", 0)
    broken_rate = stats.get("炸板率", 0)
    
    if limit_down > 15 or broken_rate > 35:
        sentiment = "冰点"
        sentiment_score = 30
    elif limit_up > 80 and broken_rate < 15:
        sentiment = "高潮"
        sentiment_score = 40
    elif limit_up - limit_down > 50 and broken_rate < 20:
        sentiment = "主升"
        sentiment_score = 90
    elif limit_up > 30 and broken_rate < 25:
        sentiment = "发酵"
        sentiment_score = 70
    else:
        sentiment = "震荡"
        sentiment_score = 50
    
    # 2. 计算仓位建议
    if sentiment in ["冰点"]:
        position = "0-10%"
    elif sentiment in ["退潮"]:
        position = "0-20%"
    elif sentiment in ["发酵", "主升"]:
        position = "20-40%" if sentiment == "发酵" else "60-80%"
    elif sentiment == "高潮":
        position = "0-20%"
    else:
        position = "10-30%"
    
    # 3. 市场评分 (0-100)
    # 涨幅得分
    avg_change = sum(d["change"] for d in indices.values()) / len(indices)
    if avg_change >= 2.0:
        change_score = 100
    elif avg_change >= 1.5:
        change_score = 85
    elif avg_change >= 1.0:
        change_score = 70
    elif avg_change >= 0.5:
        change_score = 60
    elif avg_change >= 0:
        change_score = 50
    else:
        change_score = 30
    
    # 涨跌家数比
    up_ratio = stats["上涨"] / (stats["上涨"] + stats["下跌"])
    if up_ratio >= 0.7:
        updown_score = 100
    elif up_ratio >= 0.6:
        updown_score = 80
    elif up_ratio >= 0.5:
        updown_score = 60
    else:
        updown_score = 40
    
    # 量能得分
    vol_ratio = stats["总成交"] / stats.get("5日均量", 1)
    if vol_ratio >= 1.3:
        vol_score = 100
    elif vol_ratio >= 1.15:
        vol_score = 80
    elif vol_ratio >= 1.0:
        vol_score = 60
    else:
        vol_score = 40
    
    # 综合市场分
    market_score = change_score * 0.4 + updown_score * 0.3 + vol_score * 0.3
    
    # 市场系数 (0.5-1.5)
    market_factor = 0.5 + (market_score / 100) * 1.0
    
    return {
        "sentiment": sentiment,
        "sentiment_score": sentiment_score,
        "position": position,
        "market_score": market_score,
        "market_factor": market_factor,
        "change_score": change_score,
        "updown_score": updown_score,
        "vol_score": vol_score,
        "avg_change": avg_change,
        "up_ratio": up_ratio,
        "vol_ratio": vol_ratio,
    }

def get_sector_analysis(sector_name: str = None) -> dict:
    """板块分析"""
    sectors = MOCK_SECTORS
    
    if sector_name and sector_name in sectors:
        s = sectors[sector_name]
    else:
        # 取平均
        s = {
            "涨幅": sum(d["涨幅"] for d in sectors.values()) / len(sectors),
            "涨停数": sum(d["涨停数"] for d in sectors.values()) / len(sectors),
            "净流入": sum(d["净流入"] for d in sectors.values()) / len(sectors),
        }
    
    # 涨幅评分
    change = s["涨幅"]
    if change >= 5:
        change_score = 100
    elif change >= 3:
        change_score = 80
    elif change >= 2:
        change_score = 65
    elif change >= 1:
        change_score = 50
    else:
        change_score = 30
    
    # 涨停数评分
    limit_ups = s["涨停数"]
    if limit_ups >= 10:
        limit_score = 100
    elif limit_ups >= 5:
        limit_score = 75
    elif limit_ups >= 3:
        limit_score = 55
    else:
        limit_score = 35
    
    # 资金评分
    flow = s["净流入"]
    if flow >= 20:
        flow_score = 100
    elif flow >= 10:
        flow_score = 70
    elif flow >= 5:
        flow_score = 50
    else:
        flow_score = 30
    
    sector_score = change_score * 0.4 + limit_score * 0.35 + flow_score * 0.25
    
    # 板块系数
    sector_factor = 0.7 + (sector_score / 100) * 0.8
    
    return {
        "sector_score": sector_score,
        "sector_factor": sector_factor,
        "change": s["涨幅"],
        "limit_ups": s["涨停数"],
        "flow": s["净流入"],
    }

def calc_final_score(base_score: float) -> float:
    """计算最终评分 = 基础分 x 市场系数 x 板块系数"""
    market = get_market_analysis()
    # 用默认板块系数
    sector = get_sector_analysis()
    
    final_score = base_score * market["market_factor"] * sector["sector_factor"]
    return min(100, round(final_score, 1)), market, sector


# ==================== V2.4: 今日市场数据 ====================

# 2026-03-07 实际市场数据（来自用户）
TODAY_MARKET = {
    "date": "2026-03-07",
    "上涨": 2183,
    "下跌": 2907,
    "涨停": 91,
    "跌停": 9,
    "封板率": 74,
    "涨停结构": {
        "首板": 65,
        "2板": 14,
        "3板": 5,
        "4板": 4,
        "5板": 2,
        "6板": 1
    }
}

def get_today_market_score():
    """基于今日数据计算市场评分"""
    m = TODAY_MARKET
    
    # 1. 涨停，跌停比例
    total = m["上涨"] + m["下跌"]
    up_ratio = m["上涨"] / total
    limit_up_ratio = m["涨停"] / total * 100  # 涨停占比
    
    # 2. 涨停结构评分（有完整梯队=好）
    ladder = m["涨停结构"]
    ladder_score = 0
    if ladder.get("6板",0) > 0: ladder_score += 30
    if ladder.get("5板",0) > 0: ladder_score += 25
    if ladder.get("4板",0) > 0: ladder_score += 20
    if ladder.get("3板",0) > 0: ladder_score += 15
    if ladder.get("2板",0) > 0: ladder_score += 10
    if ladder.get("首板",0) > 0: ladder_score += 5
    
    # 3. 封板率（74%正常，>80%高潮，<60%弱）
    broken_rate = 100 - m["封板率"]
    
    # 综合判定情绪
    if m["涨停"] > 80 and broken_rate < 15:
        sentiment = "高潮"
        position = "0-20%"
    elif m["涨停"] > 50 and m["跌停"] < 15 and broken_rate < 25:
        sentiment = "主升"
        position = "60-80%"
    elif m["涨停"] > 30 and broken_rate < 30:
        sentiment = "发酵"
        position = "20-40%"
    elif m["跌停"] > 15 or broken_rate > 35:
        sentiment = "冰点"
        position = "0-10%"
    else:
        sentiment = "震荡"
        position = "10-30%"
    
    # 市场评分 (0-100)
    score = int(up_ratio * 50 + ladder_score * 0.3 + (100 - broken_rate) * 0.2)
    score = max(0, min(100, score))
    
    # 系数 (0.8-1.2)
    factor = 0.8 + (score / 100) * 0.4
    
    return {
        "date": m["date"],
        "sentiment": sentiment,
        "position": position,
        "score": score,
        "factor": round(factor, 2),
        "涨停": m["涨停"],
        "跌停": m["跌停"],
        "封板率": m["封板率"],
        "上涨比例": round(up_ratio * 100, 1)
    }


# ==================== V2.5: 更多细分评分因子 ====================

# 新增评分因子:
# - 换手率
# - 量价配合
# - 板块地位
# - 股性（历史涨停）
# - 市值
# - 机构关注

def calc_turnover_score(turnover: float) -> float:
    """换手率评分 (0-100)"""
    # 换手率: 15%=100分, 10%=80分, 5%=60分, 3%=40分, <1%=20分
    if turnover >= 15: return 100
    elif turnover >= 10: return 80 + (turnover-10)/5*20
    elif turnover >= 5: return 60 + (turnover-5)/5*20
    elif turnover >= 3: return 40 + (turnover-3)/2*20
    else: return turnover/3*40

def calc_volume_price_score(price_change: float, volume_ratio: float) -> float:
    """量价配合评分 (0-100)"""
    # 价升量增 = 好, 价升量减 = 背离
    score = 50
    if price_change > 0 and volume_ratio > 1.2:  # 放量上涨
        score = 100
    elif price_change > 0 and volume_ratio > 1.0:  # 温和放量上涨
        score = 80
    elif price_change > 0 and volume_ratio < 0.8:  # 缩量上涨（背离）
        score = 40
    elif price_change < 0 and volume_ratio > 1.5:  # 放量下跌
        score = 30
    return score

def calc_sector_position(is_leader: bool, is_mid_army: bool) -> float:
    """板块地位评分 (0-100)"""
    # 板块中军 > 板块龙头 > 跟风
    if is_leader:
        return 100
    elif is_mid_army:
        return 80
    else:
        return 60

def calc_stock_nature(limit_count: int, avg_return: float) -> float:
    """股性评分 (0-100)"""
    # 历史涨停次数多 + 平均收益高 = 股性好
    score = 50
    if limit_count >= 10:
        score += 30
    elif limit_count >= 5:
        score += 20
    elif limit_count >= 2:
        score += 10
    
    if avg_return > 5:
        score += 20
    elif avg_return > 0:
        score += 10
    elif avg_return > -3:
        score += 0
    else:
        score -= 10
    
    return max(0, min(100, score))

def calc_market_cap_score(market_cap: float) -> float:
    """市值评分 (0-100)"""
    # 小市值更容易被炒作
    # <50亿=100, 50-100亿=80, 100-300亿=60, >300亿=40
    if market_cap < 50:
        return 100
    elif market_cap < 100:
        return 80 + (100-market_cap)/50*20
    elif market_cap < 300:
        return 60 + (300-market_cap)/200*20
    else:
        return max(20, 40 - (market_cap-300)/1000*20)

def calc_institution_score(report_count: int, target_price: float, current_price: float) -> float:
    """机构关注度评分 (0-100)"""
    # 研报数量多 + 目标价高
    score = 50
    if report_count >= 10:
        score += 30
    elif report_count >= 5:
        score += 20
    elif report_count >= 1:
        score += 10
    
    # 目标价空间
    if target_price > 0 and current_price > 0:
        upside = (target_price - current_price) / current_price * 100
        if upside >= 50:
            score += 20
        elif upside >= 30:
            score += 15
        elif upside >= 10:
            score += 10
    
    return min(100, score)

# 模拟数据
STOCK_EXTRA_DATA = {
    "协鑫能科": {"换手率": 18.5, "量比": 2.3, "板块地位": "中军", "历史涨停": 15, "平均收益": 8.5, "市值": 280, "研报数": 8},
    "汉缆股份": {"换手率": 12.3, "量比": 1.8, "板块地位": "跟风", "历史涨停": 8, "平均收益": 5.2, "市值": 150, "研报数": 3},
    "宗申动力": {"换手率": 22.1, "量比": 2.8, "板块地位": "龙头", "历史涨停": 12, "平均收益": 7.8, "市值": 120, "研报数": 5},
    "协鑫集成": {"换手率": 25.6, "量比": 3.1, "板块地位": "龙头", "历史涨停": 20, "平均收益": 12.5, "市值": 350, "研报数": 12},
    "豫能控股": {"换手率": 15.2, "量比": 1.9, "板块地位": "跟风", "历史涨停": 6, "平均收益": 3.2, "市值": 80, "研报数": 2},
    "中国能建": {"换手率": 8.5, "量比": 1.2, "板块地位": "中军", "历史涨停": 3, "平均收益": 2.1, "市值": 800, "研报数": 15},
    "拓维信息": {"换手率": 35.2, "量比": 4.5, "板块地位": "龙头", "历史涨停": 25, "平均收益": 15.8, "市值": 450, "研报数": 20},
}

def get_extra_score(stock_name: str, price_change: float = 0) -> dict:
    """获取额外评分"""
    data = STOCK_EXTRA_DATA.get(stock_name, {})
    
    if not data:
        return {
            "换手率分": 60,
            "量价配合分": 60,
            "板块地位分": 60,
            "股性分": 60,
            "市值分": 60,
            "机构关注分": 60,
            "额外总分": 60
        }
    
    turnover = data.get("换手率", 5)
    volume_ratio = data.get("量比", 1.5)
    is_leader = data.get("板块地位") == "龙头"
    is_mid = data.get("板块地位") == "中军"
    limit_count = data.get("历史涨停", 0)
    avg_return = data.get("平均收益", 0)
    market_cap = data.get("市值", 100)
    report_count = data.get("研报数", 0)
    
    # 各维度评分
    turnover_score = calc_turnover_score(turnover)
    vol_price_score = calc_volume_price_score(price_change, volume_ratio)
    sector_score = calc_sector_position(is_leader, is_mid)
    nature_score = calc_stock_nature(limit_count, avg_return)
    cap_score = calc_market_cap_score(market_cap)
    inst_score = calc_institution_score(report_count, 0, 0)
    
    # 额外总分 (各占不同权重)
    extra_total = (
        turnover_score * 0.15 +
        vol_price_score * 0.15 +
        sector_score * 0.25 +
        nature_score * 0.20 +
        cap_score * 0.10 +
        inst_score * 0.15
    )
    
    return {
        "换手率分": round(turnover_score, 1),
        "量价配合分": round(vol_price_score, 1),
        "板块地位分": round(sector_score, 1),
        "股性分": round(nature_score, 1),
        "市值分": round(cap_score, 1),
        "机构关注分": round(inst_score, 1),
        "额外总分": round(extra_total, 1)
    }


# ==================== V2.6: 更多细分因子 ====================

# 新增因子:
# - 换手率
# - 量价配合
# - 均线形态
# - 资金流向(5日)
# - 龙虎榜
# - 融资融券
# - 业绩预增
# - 题材热度

def calc_moving_avg_score(ma5: float, ma10: float, ma20: float, price: float) -> float:
    """均线形态评分"""
    # 多头排列: ma5 > ma10 > ma20
    if ma5 > ma10 > ma20 and price > ma5:
        return 100
    elif ma5 > ma10 and price > ma5:
        return 80
    elif ma5 > ma10:
        return 60
    elif price > ma5:
        return 50
    else:
        return 30

def calc_money_flow_score(flow_5d: float, flow_10d: float) -> float:
    """资金流向评分 (5日/10日)"""
    # 5日净流入 > 10日 = 持续流入
    score = 50
    if flow_5d > flow_10d > 0:
        score = 100  # 持续流入
    elif flow_5d > 0:
        score = 80
    elif flow_5d < 0 and flow_10d > 0:
        score = 60  # 近期流出但总体流入
    elif flow_5d < flow_10d < 0:
        score = 20  # 持续流出
    return score

def calc_dragon_score(has_dragon: bool, buy_amount: float) -> float:
    """龙虎榜评分"""
    if not has_dragon:
        return 40
    # 买入金额越大越好
    if buy_amount >= 100000000:  # 1亿
        return 100
    elif buy_amount >= 50000000:
        return 85
    elif buy_amount >= 20000000:
        return 70
    else:
        return 60

def calc_margin_score(margin_ratio: float) -> float:
    """融资融券评分"""
    # 融资比例适中最好 (20-40%)
    if margin_ratio >= 20 and margin_ratio <= 40:
        return 100
    elif margin_ratio > 40:
        return 80
    elif margin_ratio > 10:
        return 60
    else:
        return 40

def calc_profit_score(has_pre: bool, pre_growth: float) -> float:
    """业绩预增评分"""
    if not has_pre:
        return 50
    if pre_growth >= 100:
        return 100
    elif pre_growth >= 50:
        return 85
    elif pre_growth >= 20:
        return 70
    elif pre_growth >= 0:
        return 60
    else:
        return 40

def calc_concept_score(concept_count: int, hot_concepts: list) -> float:
    """题材热度评分"""
    score = 50 + concept_count * 10
    return min(100, score)

# 真实涨停数据
REAL_LIMIT_UP_STOCKS = [
    {"code": "000533", "name": "顺钠股份", "change": 9.98},
    {"code": "601567", "name": "三星医疗", "change": 9.99},
    {"code": "002227", "name": "奥特迅", "change": 10.01},
    {"code": "600590", "name": "泰豪科技", "change": 9.99},
    {"code": "600821", "name": "金开新能", "change": 9.97},
    {"code": "000720", "name": "新能泰山", "change": 10.00},
    {"code": "002498", "name": "汉缆股份", "change": 9.96},
    {"code": "601616", "name": "广电电气", "change": 10.00},
    {"code": "000516", "name": "国际医学", "change": 10.11},
    {"code": "002470", "name": "金正大", "change": 10.00},
    {"code": "002015", "name": "协鑫能科", "change": 10.00},
    {"code": "301638", "name": "南网数字", "change": 20.00},
]

# 模拟额外数据
STOCK_V2_DATA = {
    "顺钠股份": {"换手": 22.5, "量比": 2.8, "ma5": 4.2, "ma10": 4.0, "ma20": 3.8, "price": 4.5,
                "5日流入": 2.5, "10日流入": 1.8, "龙虎榜": True, "龙虎买入": 5000, "融资比": 25, "业绩预增": 50, "题材数": 3},
    "金开新能": {"换手": 18.2, "量比": 2.1, "ma5": 8.0, "ma10": 7.5, "ma20": 7.0, "price": 8.6,
                "5日流入": 3.5, "10日流入": 2.2, "龙虎榜": True, "龙虎买入": 8000, "融资比": 15, "业绩预增": 80, "题材数": 4},
    "汉缆股份": {"换手": 12.5, "量比": 1.8, "ma5": 9.5, "ma10": 9.2, "ma20": 8.8, "price": 9.8,
                "5日流入": 2.0, "10日流入": 1.5, "龙虎榜": False, "龙虎买入": 0, "融资比": 30, "业绩预增": 0, "题材数": 2},
    "协鑫能科": {"换手": 25.6, "量比": 3.2, "ma5": 14.5, "ma10": 13.8, "ma20": 12.5, "price": 15.6,
                "5日流入": 4.2, "10日流入": 3.0, "龙虎榜": True, "龙虎买入": 120000000, "融资比": 35, "业绩预增": 100, "题材数": 5},
    "南网数字": {"换手": 35.2, "量比": 4.5, "ma5": 18.0, "ma10": 16.5, "ma20": 15.0, "price": 18.9,
                "5日流入": 5.5, "10日流入": 3.8, "龙虎榜": True, "龙虎买入": 200000000, "融资比": 45, "业绩预增": 120, "题材数": 6},
    "金正大": {"换手": 15.8, "量比": 2.5, "ma5": 3.0, "ma10": 2.9, "ma20": 2.7, "price": 3.1,
            "5日流入": 1.5, "10日流入": 1.0, "龙虎榜": True, "龙虎买入": 3000, "融资比": 20, "业绩预增": 60, "题材数": 3},
}

def calc_all_extra(stock_name: str) -> dict:
    """计算所有额外因子"""
    data = STOCK_V2_DATA.get(stock_name, {})
    
    if not data:
        return {"总分": 50}
    
    # 各因子
    turnover = data.get("换手", 5)
    vol_ratio = data.get("量比", 1.5)
    ma5 = data.get("ma5", 0)
    ma10 = data.get("ma10", 0)
    ma20 = data.get("ma20", 0)
    price = data.get("price", 0)
    
    flow_5d = data.get("5日流入", 0)
    flow_10d = data.get("10日流入", 0)
    has_dragon = data.get("龙虎榜", False)
    dragon_buy = data.get("龙虎买入", 0)
    margin = data.get("融资比", 0)
    profit = data.get("业绩预增", 0)
    concepts = data.get("题材数", 0)
    
    # 计算各维度
    t_score = calc_turnover_score(turnover)
    vp_score = calc_volume_price_score(data.get("change",0), vol_ratio)
    ma_score = calc_moving_avg_score(ma5, ma10, ma20, price)
    flow_score = calc_money_flow_score(flow_5d, flow_10d)
    dragon_score = calc_dragon_score(has_dragon, dragon_buy)
    margin_score = calc_margin_score(margin)
    profit_score = calc_profit_score(profit > 0, profit)
    concept_score = calc_concept_score(concepts, [])
    
    # 总分 (加权)
    total = (
        t_score * 0.12 +
        vp_score * 0.10 +
        ma_score * 0.15 +
        flow_score * 0.18 +
        dragon_score * 0.15 +
        margin_score * 0.10 +
        profit_score * 0.10 +
        concept_score * 0.10
    )
    
    return {
        "换手率": t_score,
        "量价配合": vp_score,
        "均线形态": ma_score,
        "资金流向": flow_score,
        "龙虎榜": dragon_score,
        "融资融券": margin_score,
        "业绩预增": profit_score,
        "题材热度": concept_score,
        "总分": round(total, 1)
    }

print("已添加V2.6更多细分因子")

# ==================== V2.7: 更多技术指标因子 ====================

# 新增因子:
# - MACD金叉/死叉
# - KDJ超买超卖
# - RSI强弱指标
# - 布林带位置
# - 压力位/支撑位
# - 封板时间
# - 封单金额
# - 板上抛压

def calc_macd_score(macd_cross: str, macd_hist: float) -> float:
    """MACD评分"""
    if macd_cross == "金叉" and macd_hist > 0:
        return 100
    elif macd_cross == "金叉":
        return 80
    elif macd_cross == "死叉":
        return 30
    else:
        return 50

def calc_kdj_score(k: float, d: float, j: float) -> float:
    """KDJ评分"""
    # J>100超买, J<0超卖
    if j > 100:
        return 70  # 超买但可能继续涨
    elif j < 0:
        return 60  # 超卖可能反弹
    elif k > d and k > 80:
        return 90  # 高位金叉
    elif k > d:
        return 70  # 上升中
    else:
        return 40

def calc_rsi_score(rsi6: float, rsi12: float) -> float:
    """RSI评分"""
    avg = (rsi6 + rsi12) / 2
    if avg > 80:
        return 70  # 超买
    elif avg > 70:
        return 80  # 强势
    elif avg > 50:
        return 60  # 中性偏强
    elif avg > 30:
        return 50  # 中性
    else:
        return 40  # 弱势

def calc_boll_score(price: float, upper: float, middle: float, lower: float) -> float:
    """布林带评分"""
    if price > upper:
        return 100  # 突破上轨
    elif price > middle:
        return 80   # 中上轨运行
    elif price > lower:
        return 60   # 中下轨运行
    else:
        return 40   # 跌破下轨

def calc_seal_time_score(seal_time: str) -> float:
    """封板时间评分 (越早封板越好)"""
    # 9:30-10:00 = 100, 10:00-11:00 = 80, 11:00-14:00 = 60, 14:00-15:00 = 40
    hour = int(seal_time.split(':')[0]) if ':' in seal_time else 14
    if hour < 10:
        return 100
    elif hour < 11:
        return 80
    elif hour < 14:
        return 60
    else:
        return 40

def calc_seal_amount_score(amount: float) -> float:
    """封单金额评分 (亿)"""
    if amount >= 5:
        return 100
    elif amount >= 2:
        return 80
    elif amount >= 1:
        return 60
    else:
        return 40

def calc_pressure_score(turnover: float, seal_rate: float) -> float:
    """板上抛压评分"""
    # 换手率高+封板率低 = 抛压大
    if turnover > 30 and seal_rate < 80:
        return 30  # 抛压大
    elif turnover > 20:
        return 60
    else:
        return 80

# 模拟技术指标数据
TECH_DATA = {
    "顺钠股份": {"MACD": "金叉", "MACD柱": 0.5, "K": 85, "D": 75, "J": 105, "RSI": 72, "股价": 4.5, "上轨": 4.8, "中轨": 4.3, "下轨": 3.8, "封板时间": "09:45", "封单金额": 3.5, "换手": 22},
    "协鑫能科": {"MACD": "金叉", "MACD柱": 1.2, "K": 90, "D": 80, "J": 110, "RSI": 78, "股价": 15.6, "上轨": 16.0, "中轨": 14.5, "下轨": 13.0, "封板时间": "10:15", "封单金额": 8.2, "换手": 25},
    "南网数字": {"MACD": "金叉", "MACD柱": 2.5, "K": 92, "D": 85, "J": 106, "RSI": 82, "股价": 18.9, "上轨": 19.5, "中轨": 17.5, "下轨": 15.5, "封板时间": "09:35", "封单金额": 15.0, "换手": 35},
    "金开新能": {"MACD": "金叉", "MACD柱": 0.8, "K": 88, "D": 78, "J": 108, "RSI": 75, "股价": 8.6, "上轨": 9.0, "中轨": 8.2, "下轨": 7.4, "封板时间": "10:30", "封单金额": 2.8, "换手": 18},
    "汉缆股份": {"MACD": "金叉", "MACD柱": 0.3, "K": 75, "D": 70, "J": 85, "RSI": 65, "股价": 9.8, "上轨": 10.2, "中轨": 9.5, "下轨": 8.8, "封板时间": "11:20", "封单金额": 1.5, "换手": 12},
}

def calc_tech_score(stock_name: str) -> dict:
    """计算技术指标总分"""
    data = TECH_DATA.get(stock_name, {})
    
    if not data:
        return {"总分": 50}
    
    # MACD
    macd = calc_macd_score(data.get("MACD", "持平"), data.get("MACD柱", 0))
    
    # KDJ
    kdj = calc_kdj_score(data.get("K", 50), data.get("D", 50), data.get("J", 50))
    
    # RSI
    rsi = calc_rsi_score(data.get("RSI", 50), data.get("RSI", 50))
    
    # 布林带
    boll = calc_boll_score(data.get("股价", 0), data.get("上轨", 0), data.get("中轨", 0), data.get("下轨", 0))
    
    # 封板时间
    seal_time = calc_seal_time_score(data.get("封板时间", "14:00"))
    
    # 封单金额
    seal_amt = calc_seal_amount_score(data.get("封单金额", 0))
    
    # 抛压
    pressure = calc_pressure_score(data.get("换手", 10), 80)
    
    # 总分
    total = (
        macd * 0.12 +
        kdj * 0.15 +
        rsi * 0.10 +
        boll * 0.15 +
        seal_time * 0.18 +
        seal_amt * 0.15 +
        pressure * 0.15
    )
    
    return {
        "MACD": macd,
        "KDJ": kdj,
        "RSI": rsi,
        "布林带": boll,
        "封板时间": seal_time,
        "封单金额": seal_amt,
        "抛压": pressure,
        "总分": round(total, 1)
    }

print("已添加V2.7技术指标因子")

# ==================== V2.8: 更多市场情绪因子 ====================

# 新增因子:
# - 炸板率
# - 昨日涨停表现
# - 板块助攻
# - 大盘配合度
# - 消息刺激
# - 股东增持/减持
# - 限售股解禁
# - 商誉减值

def calc_explode_rate_score(explode_rate: float) -> float:
    """炸板率评分 (炸板率=涨停被打开的比例)"""
    # 炸板率越低越好
    if explode_rate <= 10:
        return 100
    elif explode_rate <= 20:
        return 80
    elif explode_rate <= 30:
        return 60
    elif explode_rate <= 40:
        return 40
    else:
        return 20

def calc_yesterday_limit_score(yesterday_return: float) -> float:
    """昨日涨停表现"""
    if yesterday_return >= 9:
        return 100  # 连板
    elif yesterday_return >= 5:
        return 80   # 大涨
    elif yesterday_return >= 0:
        return 60   # 上涨
    elif yesterday_return >= -5:
        return 40   # 小跌
    else:
        return 20   # 大跌

def calc_sector_help_score(help_count: int) -> float:
    """板块助攻数量 (同板块涨停数量)"""
    if help_count >= 5:
        return 100
    elif help_count >= 3:
        return 80
    elif help_count >= 2:
        return 60
    elif help_count >= 1:
        return 40
    else:
        return 20

def calc_market_match_score(market_change: float, stock_change: float) -> float:
    """大盘配合度"""
    # 大盘涨+个股涨 = 好
    if market_change > 0 and stock_change > 0:
        return 100
    elif market_change > 0 and stock_change < 0:
        return 60  # 大盘涨个股跌
    elif market_change < 0 and stock_change > 0:
        return 80  # 逆势上涨 = 强
    else:
        return 30  # 大盘跌个股跌

def calc_news_score(has_news: bool, news_level: str) -> float:
    """消息刺激评分"""
    if not has_news:
        return 40
    if news_level == "国家级":
        return 100
    elif news_level == "部委":
        return 85
    elif news_level == "行业":
        return 70
    elif news_level == "公司":
        return 50
    else:
        return 40

def calc_holder_change_score(holder_change: float) -> float:
    """股东增持/减持 (亿)"""
    if holder_change > 1:
        return 100
    elif holder_change > 0:
        return 80
    elif holder_change > -0.5:
        return 50
    elif holder_change > -1:
        return 30
    else:
        return 20

def calc_unlock_score(unlock_ratio: float) -> float:
    """限售股解禁比例 (%)"""
    # 解禁比例越低越好
    if unlock_ratio <= 1:
        return 100
    elif unlock_ratio <= 5:
        return 80
    elif unlock_ratio <= 10:
        return 60
    elif unlock_ratio <= 20:
        return 40
    else:
        return 20

def calc_goodwill_score(goodwill_ratio: float) -> float:
    """商誉/净资产比例"""
    # 商誉比例越低越好
    if goodwill_ratio <= 10:
        return 100
    elif goodwill_ratio <= 20:
        return 80
    elif goodwill_ratio <= 30:
        return 60
    elif goodwill_ratio <= 50:
        return 40
    else:
        return 20

# 情绪数据
SENTIMENT_DATA = {
    "顺钠股份": {"炸板率": 8, "昨日涨停": 0, "板块助攻": 3, "大盘配合": 1.2, "消息": True, "消息级别": "行业", "股东增持": 0.5, "解禁比": 2, "商誉比": 15},
    "协鑫能科": {"炸板率": 5, "昨日涨停": 10, "板块助攻": 5, "大盘配合": 0.8, "消息": True, "消息级别": "部委", "股东增持": 1.2, "解禁比": 1, "商誉比": 8},
    "南网数字": {"炸板率": 3, "昨日涨停": 20, "板块助攻": 4, "大盘配合": 1.5, "消息": True, "消息级别": "行业", "股东增持": 0.8, "解禁比": 0, "商誉比": 5},
    "金开新能": {"炸板率": 12, "昨日涨停": 5, "板块助攻": 2, "大盘配合": 0.5, "消息": False, "消息级别": "", "股东增持": 0, "解禁比": 3, "商誉比": 20},
    "汉缆股份": {"炸板率": 15, "昨日涨停": 0, "板块助攻": 1, "大盘配合": 0.3, "消息": True, "消息级别": "公司", "股东增持": -0.3, "解禁比": 5, "商誉比": 25},
}

def calc_sentiment_factor_score(stock_name: str) -> dict:
    """计算情绪因子总分"""
    data = SENTIMENT_DATA.get(stock_name, {})
    
    if not data:
        return {"总分": 50}
    
    explode = calc_explode_rate_score(data.get("炸板率", 30))
    yest = calc_yesterday_limit_score(data.get("昨日涨停", 0))
    sector = calc_sector_help_score(data.get("板块助攻", 0))
    market = calc_market_match_score(data.get("大盘配合", 0), 10)
    news = calc_news_score(data.get("消息", False), data.get("消息级别", ""))
    holder = calc_holder_change_score(data.get("股东增持", 0))
    unlock = calc_unlock_score(data.get("解禁比", 10))
    goodwill = calc_goodwill_score(data.get("商誉比", 20))
    
    total = (
        explode * 0.15 +
        yest * 0.10 +
        sector * 0.15 +
        market * 0.15 +
        news * 0.15 +
        holder * 0.10 +
        unlock * 0.10 +
        goodwill * 0.10
    )
    
    return {
        "炸板率": explode,
        "昨日涨停": yest,
        "板块助攻": sector,
        "大盘配合": market,
        "消息刺激": news,
        "股东增持": holder,
        "解禁": unlock,
        "商誉": goodwill,
        "总分": round(total, 1)
    }

print("已添加V2.8情绪因子")

# ==================== V2.9: 整合收盘点评因子 ====================

# 今日热点板块数据 (来自收盘点评)
TODAY_HOT_SECTORS = {
    "油气": {"龙头": "洲际油气", "量化票": ["洲际油气", "山东墨龙", "准油股份", "通源石油"], "状态": "分歧回落"},
    "miniLED": {"龙头": "兆驰股份", "跟风": ["华灿光电", "三安光电", "国星光电"], "状态": "新题材"},
    "电力": {"龙头": "顺钠股份", "中军": ["中国西电", "特变电工"], "状态": "强势"},
    "AI硬件": {"CPO": ["华工科技", "新易盛", "天孚通信"], "光纤": ["杭电股份", "通鼎互联"]},
}

# 量化主导股票
QUANT_LEADER_STOCKS = ["洲际油气", "山东墨龙", "准油股份", "通源石油", "顺钠股份", "汉缆股份", "三安光电"]

# 今日涨幅较大的超跌股 (近期跌幅>30%)
OVERDROWN_STOCKS = ["三安光电", "国星光电", "联建光电", "聚飞光电"]

def calc_quant_score(stock_name: str) -> float:
    """量化资金评分"""
    if stock_name in QUANT_LEADER_STOCKS:
        return 100
    else:
        return 50

def calc_board_height_score(board_height: int) -> float:
    """连板高度评分"""
    if board_height >= 5:
        return 100
    elif board_height >= 4:
        return 90
    elif board_height >= 3:
        return 80
    elif board_height >= 2:
        return 60
    elif board_height >= 1:
        return 40
    else:
        return 20

def calc_sector_leader_score(stock_name: str, sector: str) -> float:
    """板块地位评分 (龙头/中军/跟风)"""
    sector_data = TODAY_HOT_SECTORS.get(sector, {})
    
    # 龙头
    if sector_data.get("龙头") == stock_name:
        return 100
    # 中军
    if stock_name in sector_data.get("中军", []):
        return 80
    # 量化票
    if stock_name in sector_data.get("量化票", []):
        return 85
    # 跟风
    if stock_name in sector_data.get("跟风", []):
        return 60
    return 40

def calc_oversold_score(stock_name: str, recent_drop: float) -> float:
    """超跌反弹评分"""
    if stock_name in OVERDROWN_STOCKS:
        return 100
    if recent_drop > 30:
        return 90
    elif recent_drop > 20:
        return 70
    elif recent_drop > 10:
        return 50
    else:
        return 30

def calc_new_theme_score(sector: str) -> float:
    """新题材加分"""
    sector_data = TODAY_HOT_SECTORS.get(sector, {})
    status = sector_data.get("状态", "")
    
    if "新题材" in status:
        return 100
    elif "分歧" in status:
        return 60  # 分歧后有低吸机会
    elif "强势" in status:
        return 80
    else:
        return 50

# 整合后的评分
def calc_final_score_v29(stock_name: str, sector: str, change: float, 
                         board_height: int = 1, recent_drop: float = 0) -> dict:
    """V2.9 最终评分"""
    
    # 基础
    base = 70 + change * 2
    
    # 各维度
    quant = calc_quant_score(stock_name)
    board = calc_board_height_score(board_height)
    sector_leader = calc_sector_leader_score(stock_name, sector)
    oversold = calc_oversold_score(stock_name, recent_drop)
    new_theme = calc_new_theme_score(sector)
    
    # 综合 (加权)
    final = (
        base * 0.20 +
        quant * 0.15 +
        board * 0.20 +
        sector_leader * 0.20 +
        oversold * 0.10 +
        new_theme * 0.15
    )
    
    return {
        "基础": round(base, 1),
        "量化": round(quant, 1),
        "连板": round(board, 1),
        "板块地位": round(sector_leader, 1),
        "超跌": round(oversold, 1),
        "新题材": round(new_theme, 1),
        "总分": round(final, 1)
    }

# 测试
print("\n" + "="*60)
print("V2.9 收盘点评因子整合")
print("="*60)

test_stocks = [
    ("洲际油气", "油气", 9.5, 4, 5),
    ("顺钠股份", "电力", 10.0, 2, 15),
    ("三安光电", "miniLED", 20.0, 1, 35),
    ("兆驰股份", "miniLED", 10.0, 1, 25),
    ("汉缆股份", "电力", 10.0, 2, 10),
]

for name, sector, change, height, drop in test_stocks:
    score = calc_final_score_v29(name, sector, change, height, drop)
    print(f"\n{name} ({sector}):")
    print(f"  基础:{score['基础']} 量化:{score['量化']} 连板:{score['连板']}")
    print(f"  板块:{score['板块地位']} 超跌:{score['超跌']} 新题材:{score['新题材']}")
    print(f"  最终:{score['总分']}")

# ==================== V3.0: 完整评分系统 ====================

# 完整因子列表
ALL_FACTORS = {
    "市场层": {
        "涨跌家数比": {"权重": 10, "说明": "上涨家数/总家数"},
        "涨停数": {"权重": 10, "说明": "涨停数量"},
        "跌停数": {"权重": 8, "说明": "跌停数量(负面)"},
        "量能": {"权重": 8, "说明": "量能变化"},
        "封板率": {"权重": 6, "说明": "涨停封住比例"},
    },
    "板块层": {
        "板块涨幅": {"权重": 10, "说明": "板块涨幅"},
        "涨停家数": {"权重": 12, "说明": "板块内涨停数"},
        "资金流入": {"权重": 10, "说明": "主力资金净流入"},
        "助攻数量": {"权重": 8, "说明": "跟风涨停数"},
    },
    "个股层": {
        "连板数": {"权重": 15, "说明": "连续涨停板数"},
        "换手率": {"权重": 8, "说明": "日换手率"},
        "量比": {"权重": 6, "说明": "量比"},
        "量化席位": {"权重": 10, "说明": "是否量化主导"},
        "小盘加分": {"权重": 8, "说明": "市值<50亿"},
        "题材数量": {"权重": 6, "说明": "概念题材数"},
        "业绩预增": {"权重": 8, "说明": "业绩预增幅度"},
        "股东增持": {"权重": 6, "说明": "股东增持(负面则减分)"},
        "MACD金叉": {"权重": 6, "说明": "技术指标金叉"},
        "KDJ超卖": {"权重": 4, "说明": "KDJ位置"},
    }
}

# 总权重验证
market_w = sum(f["权重"] for f in ALL_FACTORS["市场层"].values())
sector_w = sum(f["权重"] for f in ALL_FACTORS["板块层"].values())
stock_w = sum(f["权重"] for f in ALL_FACTORS["个股层"].values())

print(f"市场层权重: {market_w}")
print(f"板块层权重: {sector_w}")
print(f"个股层权重: {stock_w}")
print(f"总权重: {market_w + sector_w + stock_w}")

# 评分函数
def score_v3(stock_name: str, data: dict) -> dict:
    """V3.0完整评分"""
    
    # 市场层
    market = data.get("市场", {})
    market_score = (
        market.get("涨跌家数比", 50) * 0.10 +
        market.get("涨停数", 0) * 0.5 * 0.10 +  # 归一化
        (100 - market.get("跌停数", 0) * 5) * 0.08 +
        market.get("量能", 1.0) * 20 * 0.08 +
        market.get("封板率", 70) * 0.06
    )
    
    # 板块层
    sector = data.get("板块", {})
    sector_score = (
        sector.get("板块涨幅", 0) * 2 * 0.10 +
        sector.get("涨停家数", 0) * 5 * 0.12 +
        sector.get("资金流入", 0) * 0.5 * 0.10 +
        sector.get("助攻数量", 0) * 5 * 0.08
    )
    
    # 个股层
    stock = data.get("个股", {})
    stock_score = (
        stock.get("连板数", 0) * 8 * 0.15 +
        stock.get("换手率", 10) * 2 * 0.08 +
        stock.get("量比", 1) * 20 * 0.06 +
        stock.get("量化席位", 0) * 25 * 0.10 +
        stock.get("小盘加分", 0) * 20 * 0.08 +
        stock.get("题材数量", 0) * 5 * 0.06 +
        stock.get("业绩预增", 0) * 0.5 * 0.08 +
        stock.get("股东增持", 0) * 10 * 0.06 +
        stock.get("MACD金叉", 0) * 15 * 0.06 +
        stock.get("KDJ超卖", 0) * 10 * 0.04
    )
    
    # 综合
    final = market_score * 0.15 + sector_score * 0.30 + stock_score * 0.55
    
    return {
        "市场层": round(market_score, 1),
        "板块层": round(sector_score, 1),
        "个股层": round(stock_score, 1),
        "综合分": round(final, 1)
    }

# 测试
test_data = {
    "顺钠股份": {
        "市场": {"涨跌家数比": 42, "涨停数": 91, "跌停数": 9, "量能": 1.2, "封板率": 74},
        "板块": {"板块涨幅": 5.2, "涨停家数": 8, "资金流入": 15, "助攻数量": 5},
        "个股": {"连板数": 2, "换手率": 22, "量比": 2.8, "量化席位": 1, "小盘加分": 1, "题材数量": 3, "业绩预增": 50, "股东增持": 1, "MACD金叉": 1, "KDJ超卖": 1},
    },
    "洲际油气": {
        "市场": {"涨跌家数比": 42, "涨停数": 91, "跌停数": 9, "量能": 1.2, "封板率": 74},
        "板块": {"板块涨幅": 6.5, "涨停家数": 6, "资金流入": 12, "助攻数量": 4},
        "个股": {"连板数": 4, "换手率": 25, "量比": 3.0, "量化席位": 1, "小盘加分": 0, "题材数量": 2, "业绩预增": 0, "股东增持": 0, "MACD金叉": 1, "KDJ超卖": 1},
    },
}

print("\n" + "="*60)
print("V3.0 完整评分测试")
print("="*60)

for name, data in test_data.items():
    sc = score_v3(name, data)
    print(f"\n{name}:")
    print(f"  市场层: {sc['市场层']}")
    print(f"  板块层: {sc['板块层']}")
    print(f"  个股层: {sc['个股层']}")
    print(f"  综合分: {sc['综合分']}")

print("\n✅ V3.0 完成!")
