#!/usr/bin/env python3
"""
新闻聚合 v6 - 简洁版
- 英文RSS（BBC、CNN）
- 中文搜索（华尔街见闻热门）
- 智谱AI摘要
- 飞书推送
"""
import requests
import xml.etree.ElementTree as ET
import re
import json
from datetime import datetime
import os

# 代理配置（可选）
PROXY_ENABLED = False
if PROXY_ENABLED:
    os.environ['http_proxy'] = 'http://127.0.0.1:7890'
    os.environ['https_proxy'] = 'http://127.0.0.1:7890'

ZHIPU_API_KEY = "8312661b0c7c4ca3884a3a58010af6b3.KDkZ3kYpVxWEHmh5"

# 英文RSS源
RSS_SOURCES = {
    'bbc_world': 'https://feeds.bbci.co.uk/news/world/rss.xml',
    'cnn': 'http://rss.cnn.com/rss/edition.rss',
}

def fetch_rss(url, limit=6):
    try:
        r = requests.get(url, timeout=8)
        r.encoding = 'utf-8'
        root = ET.fromstring(r.text)
        items = root.findall('.//item')[:limit]
        news = []
        for item in items:
            title = item.find('title').text if item.find('title') is not None else ''
            link = item.find('link').text if item.find('link') is not None else ''
            if title and link:
                news.append({'title': title, 'link': link, 'source': 'RSS'})
        return news
    except Exception as e:
        print(f"  ⚠️ 获取失败: {e}")
        return []

def get_article_content(url):
    """用Jina提取正文"""
    try:
        jina_url = f"https://r.jina.ai/{url}"
        resp = requests.get(jina_url, timeout=15)
        if resp.status_code == 200:
            content = resp.text
            if 'Markdown Content:' in content:
                content = content.split('Markdown Content:')[1]
            content = re.sub(r'!\[.*?\]', '', content)
            content = re.sub(r'\[.*?\]', '', content)
            return content[:2000]
    except:
        return None

def generate_ai_summary(text, title):
    """智谱AI生成中文摘要"""
    if not text:
        return None
    
    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    headers = {
        "Authorization": f"Bearer {ZHIPU_API_KEY}",
        "Content-Type": "application/json"
    }
    
    prompt = f"""请阅读以下新闻，用中文提炼出3个关键要点。新闻标题: {title}

内容:
{text}

请用简洁的中文列出3个关键要点，每点不超过20字。"""

    data = {
        "model": "glm-4-flash",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 300
    }
    
    try:
        resp = requests.post(url, headers=headers, json=data, timeout=20)
        result = resp.json()
        if 'choices' in result and len(result['choices']) > 0:
            return result['choices'][0]['message']['content']
    except:
        pass
    return None

def send_to_feishu(content):
    """推送到飞书"""
    webhook_url = os.environ.get('FEISHU_WEBHOOK')
    if not webhook_url:
        cfg_path = '/root/.openclaw/workspace/sunda-longtou/api_keys/feishu.json'
        if os.path.exists(cfg_path):
            with open(cfg_path) as f:
                cfg = json.load(f)
                webhook_url = cfg.get('webhook')
    
    if not webhook_url:
        print("  ⚠️ 未配置飞书webhook，跳过推送")
        return False
    
    try:
        msg = {"msg_type": "text", "content": {"text": content}}
        resp = requests.post(webhook_url, json=msg, timeout=10)
        if resp.status_code == 200:
            print("  ✅ 飞书推送成功")
            return True
    except Exception as e:
        print(f"  ⚠️ 飞书推送异常: {e}")
    return False

def main():
    print("=" * 60)
    print("📰 新闻聚合 v6")
    print("=" * 60)
    
    all_news = []
    
    # 获取英文RSS
    print("\n🌍 获取英文RSS...")
    for name, url in RSS_SOURCES.items():
        print(f"  📰 {name}...")
        news = fetch_rss(url, 5)
        for n in news:
            n['source'] = name.upper()
            all_news.append(n)
    
    # 只取前8条做AI摘要（省API调用）
    print(f"\n📊 共 {len(all_news)} 条，取前8条做摘要")
    
    # AI摘要
    print("\n🤖 AI生成摘要...")
    for i, n in enumerate(all_news[:8]):
        print(f"  {i+1}: {n['title'][:35]}...")
        content = get_article_content(n['link'])
        if content:
            n['ai_summary'] = generate_ai_summary(content, n['title']) or n['title']
        else:
            n['ai_summary'] = n['title']
    
    # 保存
    today = datetime.now().strftime("%Y%m%d")
    filename = f'/root/.openclaw/workspace/sunda-longtou/data/news_{today}.json'
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(all_news, f, ensure_ascii=False, indent=2)
    
    # 输出
    print("\n" + "=" * 60)
    print("📊 今日新闻")
    print("=" * 60)
    for n in all_news[:6]:
        print(f"\n📰 {n['source']}: {n['title'][:45]}")
        print(f"   摘要: {n.get('ai_summary', '')[:80]}")
    
    # 飞书推送
    print("\n📨 飞书推送...")
    msg_text = "📰 每日新闻简报\n\n"
    for n in all_news[:6]:
        source = n.get('source', 'RSS')
        title = n['title'][:40]
        summary = n.get('ai_summary', '')[:50]
        msg_text += f"📰 [{source}] {title}\n"
        if summary and len(summary) > 5:
            msg_text += f"   → {summary}\n"
        msg_text += "\n"
    
    send_to_feishu(msg_text)
    
    print("\n" + "=" * 60)
    print(f"✅ 完成! 共{len(all_news)}条")
    print("=" * 60)

if __name__ == "__main__":
    main()
