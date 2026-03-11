#!/usr/bin/env python3
"""测试飞书推送"""
import requests
import json

webhook_url = "https://open.feishu.cn/open-apis/bot/v2/hook/7f7a42b7-ed24-4be3-9253-9d4ea4cb0bee"

msg = {
    "msg_type": "text",
    "content": {
        "text": "🎉 飞书推送测试成功！\n\n这是来自开发者欧达的测试消息。"
    }
}

try:
    resp = requests.post(webhook_url, json=msg, timeout=10)
    print(f"状态码: {resp.status_code}")
    print(f"响应: {resp.text}")
    if resp.status_code == 200:
        print("\n✅ 飞书推送成功！")
    else:
        print("\n❌ 推送失败")
except Exception as e:
    print(f"❌ 异常: {e}")
