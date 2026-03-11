#!/usr/bin/env python3
"""
公众号文章聚合 - OpenClaw飞书推送
定时获取公众号文章，用AI摘要推送到飞书
"""
import requests
import xml.etree.ElementTree as ET
import json
import os
import re
import sys
from datetime import datetime

# 清除代理设置，避免干扰本地连接
for key in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY']:
    os.environ.pop(key, None)

ZHIPU_API_KEY = "8312661b0c7c4ca3884a3a58010af6b3.KDkZ3kYpVxWEHmh5"
WEWE_RSS_URL = "http://localhost:4000"
AUTH_CODE = "wewe123"

def get_feed_articles(limit=3):
    """获取所有公众号的最新文章"""
    url = f"{WEWE_RSS_URL}/feeds?auth_code={AUTH_CODE}"
    try:
        resp = requests.get(url, timeout=15)
        feeds = resp.json()
        
        all_articles = []
        for feed in feeds:
            feed_id = feed.get('id')
            feed_name = feed.get('name', '')
            
            articles_url = f"{WEWE_RSS_URL}/feeds/{feed_id}?auth_code={AUTH_CODE}&limit={limit}"
            try:
                art_resp = requests.get(articles_url, timeout=10)
                art_resp.encoding = 'utf-8'
                
                xml_text = art_resp.text
                xml_text = re.sub(r' xmlns="[^"]*"', '', xml_text)
                
                root = ET.fromstring(xml_text)
                for entry in root.findall('.//entry'):
                    title = entry.find('title')
                    link = entry.find('link')
                    updated = entry.find('updated')
                    
                    title_text = title.text if title is not None else ''
                    link_href = link.get('href') if link is not None else ''
                    date_text = updated.text if updated is not None else ''
                    
                    if title_text and link_href:
                        all_articles.append({
                            'title': title_text,
                            'url': link_href,
                            'author': feed_name,
                            'date': date_text
                        })
            except:
                pass
        
        all_articles.sort(key=lambda x: x.get('date', ''), reverse=True)
        return all_articles[:8]
    except:
        return []

def generate_summary(title, author):
    """智谱AI生成摘要"""
    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    headers = {
        "Authorization": f"Bearer {ZHIPU_API_KEY}",
        "Content-Type": "application/json"
    }
    
    prompt = f"""请用30字以内概括以下公众号文章的核心内容：
标题: {title}
公众号: {author}
只返回一句话概括。"""

    data = {
        "model": "glm-4-flash",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 100
    }
    
    try:
        resp = requests.post(url, headers=headers, json=data, timeout=15)
        result = resp.json()
        if 'choices' in result and len(result['choices']) > 0:
            return result['choices'][0]['message']['content'].strip()
    except:
        pass
    return None

def send_to_feishu(content):
    """通过OpenClaw发送飞书消息"""
    # 使用OpenClaw的message工具发送
    # 这里直接把内容输出，由cron的logger保存
    print(content)
    return True

def main():
    print("=" * 60)
    print("📱 公众号文章聚合")
    print("=" * 60)
    
    print("\n📥 获取最新文章...")
    articles = get_feed_articles(3)
    print(f"共获取 {len(articles)} 篇文章")
    
    if not articles:
        print("没有获取到文章")
        return
    
    # 构建消息
    msg_text = "📱 公众号今日要点\n\n"
    
    for i, art in enumerate(articles[:6]):
        title = art.get('title', '无标题')
        author = art.get('author', '未知')
        
        print(f"  {i+1}. 生成摘要: {title[:20]}...")
        summary = generate_summary(title, author)
        
        msg_text += f"📌 {author}\n"
        msg_text += f"   {title}\n"
        if summary:
            msg_text += f"   → {summary}\n"
        msg_text += "\n"
    
    # 输出消息（供cron捕获）
    print("\n" + "=" * 60)
    print(msg_text)
    print("=" * 60)

if __name__ == "__main__":
    main()
