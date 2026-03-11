#!/usr/bin/env python3
"""
实时监控系统 - 公众号文章、新闻、热搜第一时间推送
"""
import time
import json
import requests
from datetime import datetime
import os
import xml.etree.ElementTree as ET

# 配置
WEWE_RSS_URL = "http://localhost:4000"
AUTH_CODE = "wewe123"
CHECK_INTERVAL = 1800  # 30分钟检查一次
CHECK_START_HOUR = 7   # 早上7点开始
CHECK_END_HOUR = 21    # 晚上9点结束
STATE_FILE = "/root/.openclaw/workspace/sunda-longtou/data/monitor_state.json"
TIANAPI_KEY = "1c0f3329c582a3258098ab63c6a214dd"

# 热搜关键词 - 扩展为更广泛的话题
HOT_KEYWORDS = [
    # 直接财经
    "股市", "A股", "上证", "深证", "创业板", "科创板",
    "涨停", "跌停", "龙头股", "游资", "主力",
    "证监会", "央行", "降息", "降准", "IPO",
    
    # 科技产业
    "芯片", "半导体", "人工智能", "AI", "ChatGPT", "OpenClaw",
    "5G", "6G", "云计算", "大数据", "物联网",
    
    # 新能源
    "新能源", "电动车", "锂电池", "光伏", "风电", "储能",
    "特斯拉", "比亚迪", "宁德时代",
    
    # 消费
    "消费", "零售", "电商", "直播", "网红", "品牌",
    "餐饮", "旅游", "酒店", "航空",
    
    # 医药健康
    "医药", "疫苗", "医疗", "生物", "创新药",
    
    # 地产基建
    "房地产", "地产", "楼市", "房价", "基建", "建筑",
    
    # 农业食品
    "农业", "种子", "化肥", "养殖", "猪肉", "粮食",
    "小龙虾", "水产", "食品",
    
    # 军工
    "军工", "国防", "航天", "卫星", "导弹",
    
    # 其他热点
    "元宇宙", "区块链", "数字货币", "NFT",
    "碳中和", "环保", "新材料"
]

# 飞书配置
with open('/root/.openclaw/workspace/sunda-longtou/api_keys/feishu.json', 'r') as f:
    feishu_config = json.load(f)
    FEISHU_WEBHOOK = feishu_config['webhook']

def load_state():
    """加载上次检查的状态"""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {"last_article_ids": [], "last_news_ids": [], "last_hot_words": []}

def save_state(state):
    """保存当前状态"""
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def send_to_feishu(title, content):
    """发送到飞书"""
    msg = f"🔔 {title}\n\n{content}"
    payload = {
        "msg_type": "text",
        "content": {"text": msg}
    }
    try:
        resp = requests.post(FEISHU_WEBHOOK, json=payload, timeout=10)
        return resp.status_code == 200
    except Exception as e:
        print(f"飞书推送失败: {e}")
        return False

def parse_rss_feed(xml_content):
    """解析RSS XML"""
    try:
        root = ET.fromstring(xml_content)
        # RSS 2.0 格式
        if root.tag == 'rss':
            items = root.findall('.//item')
            articles = []
            for item in items:
                title = item.find('title')
                link = item.find('link')
                guid = item.find('guid')
                pub_date = item.find('pubDate')
                
                articles.append({
                    'id': guid.text if guid is not None else (link.text if link is not None else ''),
                    'title': title.text if title is not None else '无标题',
                    'link': link.text if link is not None else '',
                    'pub_date': pub_date.text if pub_date is not None else ''
                })
            return articles
        
        # Atom 格式
        elif 'feed' in root.tag:
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            entries = root.findall('atom:entry', ns)
            articles = []
            for entry in entries:
                title = entry.find('atom:title', ns)
                link = entry.find('atom:link', ns)
                entry_id = entry.find('atom:id', ns)
                updated = entry.find('atom:updated', ns)
                
                articles.append({
                    'id': entry_id.text if entry_id is not None else '',
                    'title': title.text if title is not None else '无标题',
                    'link': link.get('href') if link is not None else '',
                    'pub_date': updated.text if updated is not None else ''
                })
            return articles
        
        return []
    except Exception as e:
        print(f"解析RSS失败: {e}")
        return []

def check_wechat_articles():
    """检查公众号新文章"""
    try:
        # 获取订阅列表
        url = f"{WEWE_RSS_URL}/feeds?auth_code={AUTH_CODE}"
        resp = requests.get(url, timeout=15)
        feeds = resp.json()
        
        new_articles = []
        for feed in feeds:
            feed_id = feed.get('id')
            feed_name = feed.get('name', '未知公众号')
            
            # 获取该公众号的RSS feed
            feed_url = f"{WEWE_RSS_URL}/feeds/{feed_id}?auth_code={AUTH_CODE}"
            feed_resp = requests.get(feed_url, timeout=15)
            
            if feed_resp.status_code == 200:
                articles = parse_rss_feed(feed_resp.text)
                # 只取最新3篇
                for article in articles[:3]:
                    article['feed'] = feed_name
                    new_articles.append(article)
        
        return new_articles
    except Exception as e:
        print(f"获取公众号文章失败: {e}")
        return []

def check_news():
    """检查36氪新闻"""
    try:
        url = "https://www.36kr.com/api/newsflash"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        
        news_list = []
        if data.get('code') == 0:
            items = data.get('data', {}).get('items', [])
            for item in items[:5]:
                news_list.append({
                    "id": str(item['id']),
                    "title": item['title'],
                    "content": item.get('description', '')[:200]
                })
        
        return news_list
    except Exception as e:
        print(f"获取新闻失败: {e}")
        return []

def check_hot_search():
    """检查热搜（微博+抖音）"""
    try:
        matched_items = []
        
        # 微博热搜
        weibo_url = f"https://apis.tianapi.com/weibohot/index?key={TIANAPI_KEY}"
        weibo_resp = requests.get(weibo_url, timeout=10)
        weibo_data = weibo_resp.json()
        
        if weibo_data.get('code') == 200:
            for item in weibo_data['result']['list'][:20]:
                word = item.get('hotword', '')
                for keyword in HOT_KEYWORDS:
                    if keyword in word:
                        matched_items.append({
                            'id': f"weibo_{word}",
                            'platform': '微博',
                            'word': word,
                            'hotindex': item.get('hotwordnum', ''),
                            'tag': item.get('hottag', '')
                        })
                        break
        
        # 抖音热搜
        douyin_url = f"https://apis.tianapi.com/douyinhot/index?key={TIANAPI_KEY}"
        douyin_resp = requests.get(douyin_url, timeout=10)
        douyin_data = douyin_resp.json()
        
        if douyin_data.get('code') == 200:
            for item in douyin_data['result']['list'][:20]:
                word = item.get('word', '')
                for keyword in HOT_KEYWORDS:
                    if keyword in word:
                        matched_items.append({
                            'id': f"douyin_{word}",
                            'platform': '抖音',
                            'word': word,
                            'hotindex': str(item.get('hotindex', '')),
                            'tag': ''
                        })
                        break
        
        return matched_items
    except Exception as e:
        print(f"获取热搜失败: {e}")
        return []

def main():
    """主循环"""
    print(f"🚀 实时监控系统启动 - {datetime.now()}", flush=True)
    print(f"检查间隔: {CHECK_INTERVAL}秒", flush=True)
    print(f"飞书Webhook: {FEISHU_WEBHOOK[:50]}...", flush=True)
    
    state = load_state()
    
    while True:
        try:
            now = datetime.now()
            current_hour = now.hour
            print(f"\n⏰ 检查时间: {now.strftime('%H:%M:%S')}")
            
            # 检查是否在工作时间段内（7:00-21:00）
            if current_hour < CHECK_START_HOUR or current_hour >= CHECK_END_HOUR:
                print(f"  ⏸️  非工作时间（{CHECK_START_HOUR}:00-{CHECK_END_HOUR}:00），跳过检查")
                time.sleep(CHECK_INTERVAL)
                continue
            
            # 检查公众号文章
            articles = check_wechat_articles()
            new_articles = [a for a in articles if a['id'] and a['id'] not in state['last_article_ids']]
            
            if new_articles:
                print(f"📰 发现 {len(new_articles)} 篇新文章")
                for article in new_articles:
                    title = f"📱 {article['feed']}"
                    content = f"{article['title']}\n\n🔗 {article['link']}\n📅 {article['pub_date']}"
                    if send_to_feishu(title, content):
                        print(f"  ✅ 已推送: {article['title'][:30]}")
                        state['last_article_ids'].append(article['id'])
                
                # 只保留最近100条记录
                state['last_article_ids'] = state['last_article_ids'][-100:]
            
            # 检查新闻
            news = check_news()
            new_news = [n for n in news if n['id'] not in state['last_news_ids']]
            
            if new_news:
                print(f"📡 发现 {len(new_news)} 条新闻")
                for item in new_news:
                    title = "🔥 36氪快讯"
                    content = f"{item['title']}\n\n{item['content']}"
                    if send_to_feishu(title, content):
                        print(f"  ✅ 已推送: {item['title'][:30]}")
                        state['last_news_ids'].append(item['id'])
                
                state['last_news_ids'] = state['last_news_ids'][-100:]
            
            # 检查热搜
            hot_items = check_hot_search()
            new_hot = [h for h in hot_items if h['id'] not in state.get('last_hot_words', [])]
            
            if new_hot:
                print(f"🔥 发现 {len(new_hot)} 条财经热搜")
                # 按平台分组推送
                weibo_hot = [h for h in new_hot if h['platform'] == '微博']
                douyin_hot = [h for h in new_hot if h['platform'] == '抖音']
                
                if weibo_hot:
                    msg = "🔥 微博热搜 - 财经相关\n\n"
                    for i, h in enumerate(weibo_hot, 1):
                        msg += f"{i}. {h['word']}"
                        if h['hotindex']:
                            msg += f" (热度: {h['hotindex']})"
                        if h['tag']:
                            msg += f" [{h['tag']}]"
                        msg += "\n"
                    
                    if send_to_feishu("", msg.strip()):
                        print(f"  ✅ 已推送微博热搜 {len(weibo_hot)} 条")
                        for h in weibo_hot:
                            state.setdefault('last_hot_words', []).append(h['id'])
                
                if douyin_hot:
                    msg = "🎵 抖音热搜 - 财经相关\n\n"
                    for i, h in enumerate(douyin_hot, 1):
                        msg += f"{i}. {h['word']}"
                        if h['hotindex']:
                            msg += f" (热度: {h['hotindex']})"
                        msg += "\n"
                    
                    if send_to_feishu("", msg.strip()):
                        print(f"  ✅ 已推送抖音热搜 {len(douyin_hot)} 条")
                        for h in douyin_hot:
                            state.setdefault('last_hot_words', []).append(h['id'])
                
                # 只保留最近50条记录
                state['last_hot_words'] = state.get('last_hot_words', [])[-50:]
            
            # 保存状态
            save_state(state)
            
            if not new_articles and not new_news and not new_hot:
                print("  ✓ 无新内容", flush=True)
            
            # 等待下次检查
            print(f"💤 等待 {CHECK_INTERVAL} 秒...", flush=True)
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n\n👋 监控系统已停止")
            break
        except Exception as e:
            print(f"❌ 错误: {e}")
            time.sleep(60)  # 出错后等待1分钟再重试

if __name__ == "__main__":
    main()
