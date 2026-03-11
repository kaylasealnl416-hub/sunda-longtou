#!/usr/bin/env python3
"""
公众号文章监控 + 飞书推送
通过 wewe-rss 获取公众号更新
"""
import requests
import xml.etree.ElementTree as ET
import json
import re
from datetime import datetime

FEISHU_WEBHOOK = "https://open.feishu.cn/open-apis/bot/v2/hook/7f7a42b7-ed24-4be3-9253-9d4ea4cb0bee"
WEWE_RSS_URL = "http://localhost:4000"
AUTH_CODE = "wewe123"

def get_feed_list():
    """获取订阅的公众号列表"""
    url = f"{WEWE_RSS_URL}/feeds?auth_code={AUTH_CODE}"
    try:
        resp = requests.get(url, timeout=10)
        return resp.json()
    except Exception as e:
        print(f"  ⚠️ 获取订阅列表失败: {e}")
        return []

def get_feed_articles(feed_id, feed_name, limit=3):
    """获取指定公众号的最新文章"""
    url = f"{WEWE_RSS_URL}/feeds/{feed_id}?auth_code={AUTH_CODE}&limit={limit}"
    try:
        resp = requests.get(url, timeout=10)
        resp.encoding = 'utf-8'
        
        # 移除 xmlns 避免解析问题
        xml_text = re.sub(r' xmlns="[^"]*"', '', resp.text)
        
        root = ET.fromstring(xml_text)
        articles = []
        
        for entry in root.findall('.//entry'):
            title_elem = entry.find('title')
            link_elem = entry.find('link')
            updated_elem = entry.find('updated')
            
            if title_elem is not None and link_elem is not None:
                title = title_elem.text or ''
                link = link_elem.get('href', '')
                date = updated_elem.text if updated_elem is not None else ''
                
                articles.append({
                    'title': title,
                    'url': link,
                    'author': feed_name,
                    'date': date
                })
        
        return articles
    except Exception as e:
        print(f"  ⚠️ 获取 {feed_name} 文章失败: {e}")
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
    print("📱 公众号文章监控")
    print("=" * 60)
    
    # 获取订阅列表
    print("\n📥 获取订阅列表...")
    feeds = get_feed_list()
    print(f"  ✅ 共 {len(feeds)} 个订阅")
    
    if not feeds:
        print("  ⚠️ 没有订阅的公众号")
        return
    
    # 获取所有文章
    all_articles = []
    for feed in feeds:
        feed_id = feed.get('id')
        feed_name = feed.get('name', '未知')
        print(f"\n📰 获取 {feed_name}...")
        
        articles = get_feed_articles(feed_id, feed_name, limit=2)
        all_articles.extend(articles)
        print(f"  ✅ 获取 {len(articles)} 篇")
    
    if not all_articles:
        print("\n  ⚠️ 没有获取到文章")
        return
    
    # 按日期排序
    all_articles.sort(key=lambda x: x.get('date', ''), reverse=True)
    
    # 保存
    today = datetime.now().strftime("%Y%m%d")
    filename = f'/root/.openclaw/workspace/sunda-longtou/data/wechat_{today}.json'
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(all_articles, f, ensure_ascii=False, indent=2)
    
    # 输出
    print("\n" + "=" * 60)
    print("📊 最新文章")
    print("=" * 60)
    for i, art in enumerate(all_articles[:10], 1):
        print(f"\n{i}. [{art['author']}] {art['title']}")
        print(f"   {art['url']}")
    
    # 飞书推送
    print("\n📨 飞书推送...")
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    msg_text = f"📱 公众号更新提醒 ({now})\n\n"
    
    for i, art in enumerate(all_articles[:8], 1):
        author = art['author']
        title = art['title'][:50]
        msg_text += f"{i}. 【{author}】\n"
        msg_text += f"   {title}\n"
        msg_text += f"   {art['url']}\n\n"
    
    send_to_feishu(msg_text)
    
    print("\n" + "=" * 60)
    print(f"✅ 完成! 共 {len(all_articles)} 篇文章")
    print("=" * 60)

if __name__ == "__main__":
    main()
