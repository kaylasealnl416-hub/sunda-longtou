"""
首板追踪系统 V2.0
核心逻辑：
- 首板出现 → 开始评分 → 追踪3天
- 3天内又涨停 → 继续追踪
- 3天不涨停 → 放弃
- 第二次首板 → 对比上次评分变化（+/-分）
"""

import json
from datetime import datetime, timedelta

# ==================== 数据存储 ====================

# 追踪记录
TRACK_FILE = "track_records.json"

def load_tracks():
    try:
        with open(TRACK_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_tracks(tracks):
    with open(TRACK_FILE, "w") as f:
        json.dump(tracks, f, ensure_ascii=False, indent=2)

# ==================== 首板追踪核心逻辑 ====================

def process_first_board(stock_name: str, stock_code: str, score: float, date: str):
    """
    处理首板
    1. 首次出现首板 → 开始追踪
    2. 再次出现首板 → 对比上次评分，记录变化
    """
    tracks = load_tracks()
    
    if stock_name not in tracks:
        # 首次首板
        tracks[stock_name] = {
            "code": stock_code,
            "first_board_date": date,
            "first_board_score": score,
            "boards": [{"date": date, "score": score, "type": "首板"}],
            "status": "追踪中",
            "track_days": 0,
            "total_change": 0
        }
        action = "✅ 首次首板，开始追踪"
    else:
        track = tracks[stock_name]
        
        # 检查是否已经在追踪
        if track["status"] == "追踪中":
            # 已经在追踪，可能是连板
            last_board = track["boards"][-1]
            if last_board["type"] == "首板":
                # 第二次首板
                change = score - track["first_board_score"]
                track["boards"].append({"date": date, "score": score, "type": "二次首板", "change": change})
                track["total_change"] += change
                action = f"🔄 二次首板，评分变化: {change:+.1f}"
            else:
                # 连板继续
                track["boards"].append({"date": date, "score": score, "type": "连板"})
                action = f"🔥 连续涨停，评分: {score}"
        else:
            # 重新出现首板（之前放弃了）
            old_score = track["first_board_score"]
            change = score - old_score
            track["first_board_date"] = date
            track["first_board_score"] = score
            track["status"] = "追踪中"
            track["track_days"] = 0
            track["boards"].append({"date": date, "score": score, "type": "新首板", "change": change})
            track["total_change"] = change
            action = f"🔙 重新首板，评分变化: {change:+.1f}"
    
    save_tracks(tracks)
    return action

def update_track_status(stock_name: str, has_limit: bool, change: float):
    """每日更新追踪状态"""
    tracks = load_tracks()
    
    if stock_name not in tracks:
        return "未追踪"
    
    track = tracks[stock_name]
    
    if track["status"] != "追踪中":
        return track["status"]
    
    track["track_days"] += 1
    
    if track["track_days"] > 3:
        # 追踪超过3天
        if has_limit:
            # 继续涨停，保持追踪
            track["boards"].append({"day": track["track_days"], "limit": True, "change": change})
            return "🔥 继续涨停"
        else:
            # 不涨停了，放弃
            track["status"] = "已放弃"
            track["boards"].append({"day": track["track_days"], "limit": False, "change": change})
            return "❌ 放弃追踪"
    
    # 3天内
    if has_limit:
        track["boards"].append({"day": track["track_days"], "limit": True, "change": change})
        return f"📈 Day{track['track_days']} 涨停"
    else:
        track["boards"].append({"day": track["track_days"], "limit": False, "change": change})
        return f"📉 Day{track['track_days']} 未涨停"
    
    save_tracks(tracks)

def get_tracking_stocks():
    """获取正在追踪的股票"""
    tracks = load_tracks()
    return {k: v for k, v in tracks.items() if v["status"] == "追踪中"}

def get_track_summary():
    """获取追踪汇总"""
    tracks = load_tracks()
    
    summary = {
        "total": len(tracks),
        "tracking": len([t for t in tracks.values() if t["status"] == "追踪中"]),
        "given_up": len([t for t in tracks.values() if t["status"] == "已放弃"]),
        "stocks": []
    }
    
    for name, data in tracks.items():
        summary["stocks"].append({
            "name": name,
            "status": data["status"],
            "first_score": data["first_board_score"],
            "change": data["total_change"],
            "days": data["track_days"]
        })
    
    return summary

# ==================== 测试 ====================

if __name__ == "__main__":
    print("="*60)
    print("首板追踪系统 V2.0 测试")
    print("="*60)
    
    # 模拟数据
    test_data = [
        ("顺钠股份", "000533", 85.0, "2026-03-05"),
        ("顺钠股份", "000533", 88.0, "2026-03-06"),  # 连板
        ("顺钠股份", "000533", 90.0, "2026-03-07"),  # 再板
        ("汉缆股份", "002498", 80.0, "2026-03-05"),
        # 第二天没涨停
    ]
    
    for name, code, score, date in test_data:
        action = process_first_board(name, code, score, date)
        print(f"{name}: {action}")
    
    print("\n" + "="*60)
    print("追踪汇总:")
    print("="*60)
    summary = get_track_summary()
    print(f"总计: {summary['total']}")
    print(f"追踪中: {summary['tracking']}")
    print(f"已放弃: {summary['given_up']}")
    
    for s in summary["stocks"]:
        emoji = "🔥" if s["status"] == "追踪中" else "❌"
        print(f"  {s['name']}: {s['first_score']}分 {s['change']:+.1f} {emoji}")

# ==================== 三层评分体系 ====================

def calc_market_score() -> dict:
    """市场环境评分 (0-100)"""
    # 从今日数据获取
    market_data = {
        "上涨": 2183,
        "下跌": 2907,
        "涨停": 91,
        "跌停": 9,
        "量能": 1.2  # 倍数
    }
    
    total = market_data["上涨"] + market_data["下跌"]
    up_ratio = market_data["上涨"] / total
    
    # 涨跌家数比
    up_score = up_ratio * 50
    
    # 涨停数
    limit_score = min(30, market_data["涨停"] / 3)
    
    # 量能
    vol_score = 20 if market_data["量能"] > 1 else 10
    
    total_score = up_score + limit_score + vol_score
    
    return {
        "score": round(total_score),
        "上涨比例": round(up_ratio * 100, 1),
        "涨停数": market_data["涨停"],
        "量能": market_data["量能"]
    }

def calc_sector_score(sector_name: str) -> dict:
    """板块热度评分 (0-100)"""
    # 板块数据
    sectors = {
        "电力": {"涨停": 8, "涨幅": 5.2, "资金流入": 15},
        "油气": {"涨停": 6, "涨幅": 4.8, "资金流入": 12},
        "miniLED": {"涨停": 5, "涨幅": 6.5, "资金流入": 8},
        "AI": {"涨停": 4, "涨幅": 3.2, "资金流入": 10},
    }
    
    data = sectors.get(sector_name, {"涨停": 1, "涨幅": 0.5, "资金流入": 0})
    
    # 涨停数 (40%)
    limit_score = min(40, data["涨停"] * 8)
    
    # 涨幅 (30%)
    change_score = min(30, data["涨幅"] * 5)
    
    # 资金流入 (30%)
    money_score = min(30, data["资金流入"] * 2)
    
    total = limit_score + change_score + money_score
    
    return {
        "score": round(total),
        "涨停": data["涨停"],
        "涨幅": data["涨幅"],
        "资金": data["资金流入"]
    }

def calc_stock_score_v3(stock_name: str, sector: str) -> dict:
    """个股评分 V3 (整合三层)"""
    # 个股因子
    stock_data = {
        "顺钠股份": {"换手": 22, "量比": 2.8, "量化": True, "小盘": True, "连板": 2},
        "汉缆股份": {"换手": 15, "量比": 1.8, "量化": True, "小盘": False, "连板": 1},
    }
    
    data = stock_data.get(stock_name, {"换手": 10, "量比": 1.5, "量化": False, "小盘": False, "连板": 1})
    
    # 换手率 (20%)
    turnover = 100 if data["换手"] > 20 else 60 if data["换手"] > 10 else 40
    
    # 量比 (10%)
    vol = 100 if data["量比"] > 2 else 60 if data["量比"] > 1.5 else 40
    
    # 量化加分 (15%)
    quant = 100 if data["量化"] else 50
    
    # 小盘加分 (15%)
    small = 100 if data["小盘"] else 60
    
    # 连板加分 (20%)
    board = min(40, data["连板"] * 20)
    
    # 题材 (20%)
    theme = 80
    
    total = turnover*0.2 + vol*0.1 + quant*0.15 + small*0.15 + board*0.2 + theme*0.2
    
    return {
        "score": round(total),
        "换手": turnover,
        "量比": vol,
        "量化": quant,
        "小盘": small,
        "连板": board
    }

def calc_final_score_v3(stock_name: str, sector: str) -> dict:
    """三层综合评分"""
    market = calc_market_score()
    sec = calc_sector_score(sector)
    stock = calc_stock_score_v3(stock_name, sector)
    
    # 综合 = 市场20% + 板块30% + 个股50%
    final = market["score"] * 0.2 + sec["score"] * 0.3 + stock["score"] * 0.5
    
    return {
        "市场": market["score"],
        "板块": sec["score"],
        "个股": stock["score"],
        "综合": round(final, 1),
        "建议": "🔥强烈推荐" if final >= 80 else "📈推荐" if final >= 70 else "➡️观察"
    }

# 测试
print("\n" + "="*60)
print("三层评分体系测试")
print("="*60)

for name, sector in [("顺钠股份", "电力"), ("汉缆股份", "电力")]:
    score = calc_final_score_v3(name, sector)
    print(f"\n{name} ({sector}):")
    print(f"  市场: {score['市场']} | 板块: {score['板块']} | 个股: {score['个股']}")
    print(f"  综合: {score['综合']} | 建议: {score['建议']}")
