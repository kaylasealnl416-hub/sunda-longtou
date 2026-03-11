#!/usr/bin/env python3
"""
热点新闻扫描 - 整合国内+国外新闻
"""
import json
from datetime import datetime

PROJECT_DIR = "/root/.openclaw/workspace/sunda-longtou"
NEWS_FILE = f"{PROJECT_DIR}/daily_news.json"

# API Keys
TIAN_API_KEY = "1c0f3329c582a3258098ab63c6a214dd"
NEWSDATA_API_KEY = "pub_d6a787d62a834e2896a8f730c88ad040"

# 关键词 -> 板块映射
KEYWORD_BOARD = {
    "石油": "石油板块", "原油": "石油板块", "黄金": "黄金板块",
    "AI": "AI板块", "人工智能": "AI板块",
    "芯片": "半导体板块", "半导体": "半导体板块",
    "新能源": "新能源板块", "光伏": "光伏板块",
    "电动车": "新能源汽车板块", "锂电": "锂电池板块",
    "军工": "军工板块", "医药": "医药板块",
    "银行": "银行板块", "房地产": "房地产板块",
    "券商": "券商板块", "保险": "保险板块",
    "伊朗": "石油板块", "中东": "石油板块",
    "苹果": "科技板块", "华为": "科技板块",
    "伊朗": "地缘政治", "战争": "地缘政治",
}

def fetch_tian(api_name):
    url = f"https://apis.tianapi.com/{api_name}/index?key={TIAN_API_KEY}"
    import urllib.request
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read())
    except: return {}

def fetch_newsdata():
    url = f"https://newsdata.io/api/1/latest?apikey={NEWSDATA_API_KEY}&q=stock&language=en"
    import urllib.request
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read())
    except: return {}

def analyze_news():
    today = datetime.now().strftime("%Y%m%d")
    
    news_data = {
        "date": today,
        "weibo_hot": [],
        "baidu_hot": [],
        "global_hot": [],
        "related_boards": []
    }
    
    # 微博热搜
    wb_data = fetch_tian("weibohot")
    if wb_data.get("code") == 200:
        for item in wb_data.get("newslist", [])[:10]:
            word = item.get("hotword", "")
            news_data["weibo_hot"].append(word)
    
    # 百度热搜
    bd_data = fetch_tian("nethot")
    if bd_data.get("code") == 200:
        for item in bd_data.get("result", {}).get("list", [])[:10]:
            word = item.get("keyword", "")
            news_data["baidu_hot"].append(word)
    
    # 全球新闻
    global_data = fetch_newsdata()
    if global_data.get("status") == "success":
        for item in global_data.get("results", [])[:10]:
            title = item.get("title", "")
            news_data["global_hot"].append(title)
            for kw, board in KEYWORD_BOARD.items():
                if kw.lower() in title.lower() and board not in news_data["related_boards"]:
                    news_data["related_boards"].append(board)
    
    # 分析板块
    all_topics = news_data["weibo_hot"] + news_data["baidu_hot"]
    for topic in all_topics:
        for kw, board in KEYWORD_BOARD.items():
            if kw in topic and board not in news_data["related_boards"]:
                news_data["related_boards"].append(board)
    
    with open(NEWS_FILE, 'w', encoding='utf-8') as f:
        json.dump(news_data, f, ensure_ascii=False, indent=2)
    
    print(f"日期: {today}")
    print(f"微博热点: {news_data['weibo_hot'][:3]}")
    print(f"百度热点: {news_data['baidu_hot'][:3]}")
    print(f"全球热点: {news_data['global_hot'][:3]}")
    print(f"相关板块: {news_data['related_boards']}")
    return news_data

if __name__ == "__main__":
    analyze_news()
