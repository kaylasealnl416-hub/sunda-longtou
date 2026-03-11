#!/usr/bin/env python3
"""
新闻聚合 v7 - 简化版（无需代理）
- 使用国内可访问的新闻源
- 飞书推送
"""
import requests
import json
from datetime import datetime

def get_wallstreetcn_news():
    """获取华尔街见闻热门新闻"""
    try:
        # 使用公开API（无需登录）
        url = "https://api-one-wscn.awtmt.com/apiv1/content/lives/latest"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        resp = requests.get(url, headers=headers, timeout=10)
        data = resp.json()
        
        news = []
        if 'data' in data and 'items' in data['data']:
            for item in data['data']['items'][:8]:
                title = item.get('title', '')
                content = item.get('content_text', '')
                if title:
                    news.append({
                        'title': title,
                        'content': content[:100],
                        'source': '华尔街见闻'
                    })
        return news
    except Exception as e:
        print(f"  ⚠️ 华尔街见闻获取失败: {e}")
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
                        'content': item.get('description', '')[:100],
                        'source': '36氪'
                    })
        return news
    except Exception as e:
        print(f"  ⚠️ 36氪获取失败: {e}")
        return []

def send_to_feishu(content):
    """推送到飞书"""
    webhook_url = "https://open.feishu.cn/open-apis/bot/v2/hook/7f7a42b7-ed24-4be3-9253-9d4ea4cb0bee"
    
    try:
        msg = {"msg_type": "text", "content": {"text": content}}
        resp = requests.post(webhook_url, json=msg, timeout=10)
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
    print("📰 新闻聚合 v7 (简化版)")
    print("=" * 60)
    
    all_news = []
    
    # 获取华尔街见闻
    print("\n📈 获取华尔街见闻...")
    news = get_wallstreetcn_news()
    all_news.extend(news)
    print(f"  ✅ 获取 {len(news)} 条")
    
    # 获取36氪
    print("\n🚀 获取36氪快讯...")
    news = get_36kr_news()
    all_news.extend(news)
    print(f"  ✅ 获取 {len(news)} 条")
    
    # 保存
    today = datetime.now().strftime("%Y%m%d")
    filename = f'/root/.openclaw/workspace/sunda-longtou/data/news_{today}.json'
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(all_news, f, ensure_ascii=False, indent=2)
    
    # 输出
    print("\n" + "=" * 60)
    print("📊 今日新闻")
    print("=" * 60)
    for i, n in enumerate(all_news[:10], 1):
        print(f"\n{i}. [{n['source']}] {n['title']}")
        if n.get('content'):
            print(f"   {n['content'][:60]}...")
    
    # 飞书推送
    print("\n📨 飞书推送...")
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    msg_text = f"📰 每日新闻简报 ({now})\n\n"
    
    for i, n in enumerate(all_news[:10], 1):
        source = n.get('source', '未知')
        title = n['title'][:50]
        msg_text += f"{i}. [{source}] {title}\n"
        if n.get('content') and len(n['content']) > 5:
            msg_text += f"   {n['content'][:60]}...\n"
        msg_text += "\n"
    
    send_to_feishu(msg_text)
    
    print("\n" + "=" * 60)
    print(f"✅ 完成! 共 {len(all_news)} 条新闻")
    print("=" * 60)

if __name__ == "__main__":
    main()
