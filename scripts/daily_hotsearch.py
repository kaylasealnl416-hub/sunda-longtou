#!/usr/bin/env python3
"""
每日热搜TOP榜推送
每天早上8:30推送微博、抖音热搜TOP20
"""
import requests
import json
from datetime import datetime

TIANAPI_KEY = "1c0f3329c582a3258098ab63c6a214dd"
FEISHU_WEBHOOK = "https://open.feishu.cn/open-apis/bot/v2/hook/7f7a42b7-ed24-4be3-9253-9d4ea4cb0bee"

def get_weibo_hot():
    """获取微博热搜TOP20"""
    try:
        url = f"https://apis.tianapi.com/weibohot/index?key={TIANAPI_KEY}"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        
        if data['code'] == 200:
            return data['result']['list'][:20]
        return []
    except Exception as e:
        print(f"获取微博热搜失败: {e}")
        return []

def get_douyin_hot():
    """获取抖音热搜TOP20"""
    try:
        url = f"https://apis.tianapi.com/douyinhot/index?key={TIANAPI_KEY}"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        
        if data['code'] == 200:
            return data['result']['list'][:20]
        return []
    except Exception as e:
        print(f"获取抖音热搜失败: {e}")
        return []

def send_to_feishu(content):
    """发送到飞书"""
    payload = {
        "msg_type": "text",
        "content": {"text": content}
    }
    
    try:
        resp = requests.post(FEISHU_WEBHOOK, json=payload, timeout=10)
        return resp.status_code == 200
    except Exception as e:
        print(f"飞书推送失败: {e}")
        return False

def main():
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"📊 每日热搜TOP榜推送 - {now}")
    
    # 微博热搜
    print("\n📱 获取微博热搜TOP20...")
    weibo_hot = get_weibo_hot()
    
    if weibo_hot:
        msg = f"📱 微博热搜TOP20 ({now})\n\n"
        for i, item in enumerate(weibo_hot, 1):
            word = item.get('hotword', '')
            hotnum = item.get('hotwordnum', '').strip()
            tag = item.get('hottag', '')
            
            msg += f"{i}. {word}"
            if hotnum:
                msg += f" ({hotnum})"
            if tag:
                msg += f" [{tag}]"
            msg += "\n"
        
        if send_to_feishu(msg):
            print(f"  ✅ 微博热搜已推送")
    
    # 抖音热搜
    print("\n🎵 获取抖音热搜TOP20...")
    douyin_hot = get_douyin_hot()
    
    if douyin_hot:
        msg = f"🎵 抖音热搜TOP20 ({now})\n\n"
        for i, item in enumerate(douyin_hot, 1):
            word = item.get('word', '')
            hotindex = item.get('hotindex', '')
            
            msg += f"{i}. {word}"
            if hotindex:
                msg += f" ({hotindex})"
            msg += "\n"
        
        if send_to_feishu(msg):
            print(f"  ✅ 抖音热搜已推送")
    
    print(f"\n✅ 完成")

if __name__ == "__main__":
    main()
