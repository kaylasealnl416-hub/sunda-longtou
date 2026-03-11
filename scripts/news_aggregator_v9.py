#!/usr/bin/env python3
"""
新闻聚合 v9 - 优化版
- 36氪快讯
- 虎嗅快讯
- IT之家快讯
- 飞书推送
"""
import requests
import json
from datetime import datetime
import time

FEISHU_WEBHOOK = "https://open.feishu.cn/open-apis/bot/v2/hook/7f7a42b7-ed24-4be3-9253-9d4ea4cb0bee"

def get_36kr_news():
    """获取36氪快讯"""
    try:
        url = "https://www.36kr.com/api/newsflash"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        resp = requests.get(url, headers=headers, timeout=10)
        data = resp.json()
        
        news = []
        if 'data' in data and 'items' in data['data']:
            for item in data['data']['items'][:6]:
                title = item.get('title', '')
                if title:
                    news.append({
                        'title': title,
                        'content': item.get('description', '')[:80],
                        'source': '36氪'
                    })
        return news
    except Exception as e:
        print(f"  ⚠️ 36氪获取失败: {e}")
        return []

def get_huxiu_news():
    """获取虎嗅快讯"""
    try:
        url = "https://www.huxiu.com/v2_action/article_list"
        params = {
            'platform': 'www',
            'type': '24h',
            'page': 1,
            'pagesize': 10
        }
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        data = resp.json()
        
        news = []
        if 'data' in data and 'dataList' in data['data']:
            for item in data['data']['dataList'][:6]:
                title = item.get('title', '')
                if title:
                    news.append({
                        'title': title,
                        'content': item.get('description', '')[:80],
                        'source': '虎嗅'
                    })
        return news
    except Exception as e:
        print(f"  ⚠️ 虎嗅获取失败: {e}")
        return []

def get_ithome_news():
    """获取IT之家快讯"""
    try:
        url = "https://api.ithome.com/json/newslist/news"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        resp = requests.get(url, headers=headers, timeout=10)
        data = resp.json()
        
        news = []
        if isinstance(data, list):
            for item in data[:6]:
                title = item.get('title', '')
                if title:
                    news.append({
                        'title': title,
                        'content': item.get('description', '')[:80],
                        'source': 'IT之家'
                    })
        return news
    except Exception as e:
        print(f"  ⚠️ IT之家获取失败: {e}")
        return []

def get_caijing_news():
    """获取财经网快讯"""
    try:
        url = "http://api.caijing.com.cn/news/list"
        params = {
            'channel': 'finance',
            'page': 1,
            'pagesize': 10
        }
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        data = resp.json()
        
        news = []
        if 'data' in data and 'list' in data['data']:
            for item in data['data']['list'][:6]:
                title = item.get('title', '')
                if title:
                    news.append({
                        'title': title,
                        'content': item.get('summary', '')[:80],
                        'source': '财经网'
                    })
        return news
    except Exception as e:
        print(f"  ⚠️ 财经网获取失败: {e}")
        return []

def send_to_feishu(content):
    """推送到飞书"""
    try:
        msg = {"msg_type": "text", "content": {"text": content}}
        resp = requests.post(FEISHU_WEBHOOK, json=msg, timeout=10)
        if resp.status_code == 200:
            print("  ✅ 飞书推送成功")
            return True
        else:
            print(f"  ⚠️ 飞书推送失败: {resp.text}")
    except Exception as e:
        print(f"  ⚠️ 飞书推送异常: {e}")
    return False

def main():
    print("=" * 60)
    print("📰 新闻聚合 v9")
    print("=" * 60)
    
    all_news = []
    
    # 获取各个源
    sources = [
        ("36氪快讯", get_36kr_news),
        ("虎嗅24h", get_huxiu_news),
        ("IT之家", get_ithome_news),
        ("财经网", get_caijing_news)
    ]
    
    for name, func in sources:
        print(f"\n📈 获取{name}...")
        news = func()
        all_news.extend(news)
        print(f"  ✅ 获取 {len(news)} 条")
        time.sleep(0.5)
    
    # 保存
    today = datetime.now().strftime("%Y%m%d")
    filename = f'/root/.openclaw/workspace/sunda-longtou/data/news_{today}.json'
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(all_news, f, ensure_ascii=False, indent=2)
    
    # 输出
    print("\n" + "=" * 60)
    print("📊 今日新闻汇总")
    print("=" * 60)
    for i, n in enumerate(all_news[:15], 1):
        print(f"\n{i}. [{n['source']}] {n['title'][:50]}")
    
    # 飞书推送
    print("\n📨 飞书推送...")
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    msg_text = f"📰 科技财经简报 ({now})\n\n"
    
    # 按来源分组
    by_source = {}
    for n in all_news:
        source = n['source']
        if source not in by_source:
            by_source[source] = []
        by_source[source].append(n)
    
    for source, items in by_source.items():
        msg_text += f"【{source}】\n"
        for i, n in enumerate(items[:5], 1):
            title = n['title'][:45]
            msg_text += f"{i}. {title}\n"
        msg_text += "\n"
    
    send_to_feishu(msg_text)
    
    print("\n" + "=" * 60)
    print(f"✅ 完成! 共 {len(all_news)} 条新闻")
    print("=" * 60)

if __name__ == "__main__":
    main()
