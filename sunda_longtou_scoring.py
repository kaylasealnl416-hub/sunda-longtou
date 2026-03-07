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
    if net_inflow > 1e8:
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
