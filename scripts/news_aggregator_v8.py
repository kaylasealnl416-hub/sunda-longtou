#!/usr/bin/env python3
"""
新闻聚合 v8 - 完整版
- 雪球热帖
- 东方财富快讯
- 金十数据
- 36氪快讯
- 飞书推送
"""
import requests
import json
from datetime import datetime
import time

FEISHU_WEBHOOK = "https://open.feishu.cn/open-apis/bot/v2/hook/7f7a42b7-ed24-4be3-9253-9d4ea4cb0bee"

def get_xueqiu_hot():
    """获取雪球热帖"""
    try:
        url = "https://xueqiu.com/statuses/hot/listV2.json"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://xueqiu.com/'
        }
        resp = requests.get(url, headers=headers, timeout=10)
        data = resp.json()
        
        news = []
        if 'items' in data:
            for item in data['items'][:5]:
                title = item.get('title', '')
                text = item.get('text', '')
                if title:
                    news.append({
                        'title': title,
                        'content': text[:80] if text else '',
                        'source': '雪球'
                    })
        return news
    except Exception as e:
        print(f"  ⚠️ 雪球获取失败: {e}")
        return []

def get_eastmoney_news():
    """获取东方财富快讯"""
    try:
        url = "https://np-anotice-stock.eastmoney.com/api/content/ann"
        params = {
            'page_size': 10,
            'page_index': 1,
            'type': 'CAL',
            'client_source': 'web'
        }
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        data = resp.json()
        
        news = []
        if 'data' in data and 'list' in data['data']:
            for item in data['data']['list'][:5]:
                title = item.get('title', '')
                content = item.get('content', '')
                if title:
                    news.append({
                        'title': title,
                        'content': content[:80] if content else '',
                        'source': '东方财富'
                    })
        return news
    except Exception as e:
        print(f"  ⚠️ 东方财富获取失败: {e}")
        return []

def get_jin10_news():
    """获取金十数据快讯"""
    try:
        url = "https://flash-api.jin10.com/get_flash_list"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        resp = requests.get(url, headers=headers, timeout=10)
        data = resp.json()
        
        news = []
        if 'data' in data:
            for item in data['data'][:5]:
                title = item.get('data', {}).get('content', '')
                if title:
                    news.append({
                        'title': title[:100],
                        'content': '',
                        'source': '金十数据'
                    })
        return news
    except Exception as e:
        print(f"  ⚠️ 金十数据获取失败: {e}")
        return []

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
            for item in data['data']['items'][:5]:
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
    print("📰 新闻聚合 v8 (完整版)")
    print("=" * 60)
    
    all_news = []
    
    # 获取各个源
    sources = [
        ("雪球热帖", get_xueqiu_hot),
        ("东方财富", get_eastmoney_news),
        ("金十数据", get_jin10_news),
        ("36氪快讯", get_36kr_news)
    ]
    
    for name, func in sources:
        print(f"\n📈 获取{name}...")
        news = func()
        all_news.extend(news)
        print(f"  ✅ 获取 {len(news)} 条")
        time.sleep(0.5)  # 避免请求过快
    
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
        if n.get('content'):
            print(f"   {n['content'][:60]}...")
    
    # 飞书推送
    print("\n📨 飞书推送...")
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    msg_text = f"📰 财经新闻简报 ({now})\n\n"
    
    # 按来源分组
    by_source = {}
    for n in all_news:
        source = n['source']
        if source not in by_source:
            by_source[source] = []
        by_source[source].append(n)
    
    for source, items in by_source.items():
        msg_text += f"【{source}】\n"
        for i, n in enumerate(items[:4], 1):
            title = n['title'][:45]
            msg_text += f"{i}. {title}\n"
        msg_text += "\n"
    
    send_to_feishu(msg_text)
    
    print("\n" + "=" * 60)
    print(f"✅ 完成! 共 {len(all_news)} 条新闻")
    print("=" * 60)

if __name__ == "__main__":
    main()
