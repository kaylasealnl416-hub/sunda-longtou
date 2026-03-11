#!/usr/bin/env python3
"""
美股行情监控 - 飞书推送
监控道琼斯、标普500、纳斯达克、科技7巨头
"""
import requests
import json
import os

for key in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY']:
    os.environ.pop(key, None)

# 读取API Key
cfg_path = '/root/.openclaw/workspace/sunda-longtou/api_keys/finnhub.json'
with open(cfg_path) as f:
    API_KEY = json.load(f)['finnhub']['api_key']

BASE_URL = "https://finnhub.io/api/v1"

# 监控列表
STOCKS = {
    # 指数ETF
    "SPY": "标普500",
    "QQQ": "纳斯达克",
    "DIA": "道琼斯",
    # 科技7巨头
    "AAPL": "苹果",
    "MSFT": "微软",
    "GOOGL": "谷歌",
    "AMZN": "亚马逊",
    "META": "Meta",
    "NVDA": "英伟达",
    "TSLA": "特斯拉",
}

def get_quote(symbol):
    """获取实时行情"""
    url = f"{BASE_URL}/quote?symbol={symbol}&token={API_KEY}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        
        if data.get('c', 0) == 0:
            return None
            
        return {
            'price': data.get('c', 0),
            'change': data.get('d', 0),
            'change_pct': data.get('dp', 0),
            'high': data.get('h', 0),
            'low': data.get('l', 0),
            'open': data.get('o', 0),
            'prev_close': data.get('pc', 0),
        }
    except Exception as e:
        print(f"获取 {symbol} 失败: {e}")
        return None

def get_news():
    """获取财经新闻"""
    url = f"{BASE_URL}/news?category=general&token={API_KEY}"
    print(f"  Debug: Getting news from {url}")
    try:
        resp = requests.get(url, timeout=10)
        resp.encoding = 'utf-8'
        news = resp.json()
        
        print(f"  Debug: Got {len(news)} news items, type: {type(news)}")
        
        if not isinstance(news, list):
            return []
            
        headlines = []
        for item in news[:5]:
            headline = item.get('headline', '')[:60]
            source = item.get('source', '')
            url = item.get('url', '')
            headlines.append({
                'headline': headline,
                'source': source,
                'url': url
            })
        return headlines
    except Exception as e:
        print(f"获取新闻失败: {e}")
        import traceback
        traceback.print_exc()
        return []

def send_to_feishu(content):
    """推送到飞书"""
    cfg_path = '/root/.openclaw/workspace/sunda-longtou/api_keys/feishu.json'
    webhook_url = None
    
    if os.path.exists(cfg_path):
        with open(cfg_path) as f:
            cfg = json.load(f)
            webhook_url = cfg.get('webhook')
    
    if not webhook_url:
        print("未配置飞书webhook")
        return False
    
    try:
        msg = {"msg_type": "text", "content": {"text": content}}
        resp = requests.post(webhook_url, json=msg, timeout=10)
        if resp.status_code == 200:
            print("飞书推送成功")
            return True
        else:
            print(f"飞书推送失败: {resp.status_code}")
    except Exception as e:
        print(f"飞书推送异常: {e}")
    return False

def main():
    print("=" * 60)
    print("📈 美股行情监控")
    print("=" * 60)
    
    # 获取行情
    print("\n📊 获取行情...")
    quotes = {}
    for symbol, name in STOCKS.items():
        quote = get_quote(symbol)
        if quote:
            quotes[name] = quote
            print(f"  {name}: ${quote['price']:.2f}")
    
    print(f"  Total quotes: {len(quotes)}")
    
    # 构建消息
    msg_text = "📈 美股今日行情\n\n"
    
    # 指数
    msg_text += "🟢 指数ETF\n"
    for name in ["标普500", "纳斯达克", "道琼斯"]:
        if name in quotes:
            q = quotes[name]
            change = f"+{q['change']:.2f}" if q['change'] >= 0 else f"{q['change']:.2f}"
            pct = f"+{q['change_pct']:.2f}%" if q['change_pct'] >= 0 else f"{q['change_pct']:.2f}%"
            msg_text += f"  {name}: ${q['price']:.2f} ({change} {pct})\n"
    
    # 科技7巨头
    msg_text += "\n🟢 科技7巨头\n"
    tech_names = ["苹果", "微软", "谷歌", "亚马逊", "Meta", "英伟达", "特斯拉"]
    for name in tech_names:
        if name in quotes:
            q = quotes[name]
            change = f"+{q['change']:.2f}" if q['change'] >= 0 else f"{q['change']:.2f}"
            pct = f"+{q['change_pct']:.2f}%" if q['change_pct'] >= 0 else f"{q['change_pct']:.2f}%"
            msg_text += f"  {name}: ${q['price']:.2f} ({change} {pct})\n"
    
    # 获取新闻
    print("\n📰 获取新闻...")
    news = get_news()
    print(f"  Got {len(news)} news items")
    if news:
        msg_text += "\n📰 财经要闻\n"
        for item in news[:3]:
            msg_text += f"  • {item['headline']}\n"
    
    print("\n📨 推送到飞书...")
    send_to_feishu(msg_text)
    
    print("\n" + "=" * 60)
    print("✅ 完成!")
    print("=" * 60)

if __name__ == "__main__":
    main()
