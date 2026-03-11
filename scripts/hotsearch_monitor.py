#!/usr/bin/env python3
"""
热搜监控系统 - 微博、抖音热搜实时追踪
"""
import requests
import json
import time
from datetime import datetime

TIANAPI_KEY = "1c0f3329c582a3258098ab63c6a214dd"
FEISHU_WEBHOOK = "https://open.feishu.cn/open-apis/bot/v2/hook/7f7a42b7-ed24-4be3-9253-9d4ea4cb0bee"

# 关键词列表（股票相关）
KEYWORDS = [
    "股市", "A股", "上证", "深证", "创业板", "科创板",
    "涨停", "跌停", "龙头股", "游资", "主力",
    "证监会", "央行", "降息", "降准", "IPO",
    "新能源", "芯片", "人工智能", "AI", "ChatGPT",
    "房地产", "地产", "楼市", "房价"
]

def get_weibo_hot():
    """获取微博热搜"""
    try:
        url = f"https://apis.tianapi.com/weibohot/index?key={TIANAPI_KEY}"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        
        if data['code'] == 200:
            return data['result']['list'][:20]  # 前20条
        return []
    except Exception as e:
        print(f"获取微博热搜失败: {e}")
        return []

def get_douyin_hot():
    """获取抖音热搜"""
    try:
        url = f"https://apis.tianapi.com/douyinhot/index?key={TIANAPI_KEY}"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        
        if data['code'] == 200:
            return data['result']['list'][:20]  # 前20条
        return []
    except Exception as e:
        print(f"获取抖音热搜失败: {e}")
        return []

def filter_by_keywords(hot_list, platform):
    """根据关键词过滤热搜"""
    matched = []
    for item in hot_list:
        word = item.get('hotword') or item.get('word', '')
        
        # 检查是否包含关键词
        for keyword in KEYWORDS:
            if keyword in word:
                matched.append({
                    'platform': platform,
                    'word': word,
                    'hotindex': item.get('hotwordnum') or item.get('hotindex', ''),
                    'tag': item.get('hottag') or item.get('label', '')
                })
                break
    
    return matched

def send_to_feishu(title, items):
    """发送到飞书"""
    if not items:
        return
    
    msg = f"🔥 {title}\n\n"
    for i, item in enumerate(items, 1):
        word = item['word']
        hotindex = item['hotindex']
        tag = item.get('tag', '')
        
        msg += f"{i}. {word}"
        if hotindex:
            msg += f" (热度: {hotindex})"
        if tag:
            msg += f" [{tag}]"
        msg += "\n"
    
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

def main():
    """主函数"""
    print(f"🔥 热搜监控启动 - {datetime.now()}")
    print(f"关键词: {', '.join(KEYWORDS[:10])}...")
    
    # 获取微博热搜
    print("\n📱 获取微博热搜...")
    weibo_hot = get_weibo_hot()
    weibo_matched = filter_by_keywords(weibo_hot, '微博')
    print(f"  微博热搜: {len(weibo_hot)} 条，匹配: {len(weibo_matched)} 条")
    
    # 获取抖音热搜
    print("\n🎵 获取抖音热搜...")
    douyin_hot = get_douyin_hot()
    douyin_matched = filter_by_keywords(douyin_hot, '抖音')
    print(f"  抖音热搜: {len(douyin_hot)} 条，匹配: {len(douyin_matched)} 条")
    
    # 推送到飞书
    if weibo_matched:
        print(f"\n📤 推送微博热搜...")
        send_to_feishu("微博热搜 - 财经相关", weibo_matched)
    
    if douyin_matched:
        print(f"\n📤 推送抖音热搜...")
        send_to_feishu("抖音热搜 - 财经相关", douyin_matched)
    
    if not weibo_matched and not douyin_matched:
        print("\n✓ 暂无匹配的财经热搜")
    
    print(f"\n✅ 完成 - {datetime.now()}")

if __name__ == "__main__":
    main()
