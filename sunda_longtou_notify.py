#!/usr/bin/env python3
"""
龙头股评分系统 - 飞书通知模块
"""

import json
from datetime import datetime

# 飞书机器人的webhook（需要在飞书后台配置机器人获取）
# 这里先创建模块，配置需要用户自己设置

FEISHU_WEBHOOK_URL = None  # TODO: 设置飞书机器人Webhook

def send_feishu_message(message: str) -> bool:
    """
    发送飞书消息
    需要先配置 FEISHU_WEBHOOK_URL
    """
    import requests
    
    if not FEISHU_WEBHOOK_URL:
        print("⚠️ 未配置飞书Webhook，跳过通知")
        return False
    
    try:
        headers = {"Content-Type": "application/json"}
        data = {"msg_type": "text", "content": {"text": message}}
        resp = requests.post(FEISHU_WEBHOOK_URL, headers=headers, json=data, timeout=10)
        return resp.status_code == 200
    except Exception as e:
        print(f"飞书通知失败: {e}")
        return False

def create_daily_doc(results: list, doc_token: str = None) -> str:
    """
    创建或更新每日评分文档
    """
    from feishu_doc import feishu_doc
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    title = f"龙头股评分 {date_str}"
    
    # 构建内容
    content_lines = [f"# 🐲 龙头股评分 {date_str}\n"]
    content_lines.append(f"**更新时间**: {datetime.now().strftime('%H:%M:%S')}\n")
    content_lines.append("---\n")
    content_lines.append("## 📊 TOP 8 龙头股\n\n")
    content_lines.append("| 排名 | 代码 | 名称 | 总分 | 热门 | 资金 | 技术 |\n")
    content_lines.append("|------|------|------|------|------|------|------|\n")
    
    for i, stock in enumerate(results[:8], 1):
        content_lines.append(f"| {i} | {stock['code']} | {stock['name']} | **{stock['总分']:.1f}** | {stock['热门排名分']:.0f} | {stock['资金面分']:.0f} | {stock['技术面分']:.0f} |\n")
    
    content_lines.append("\n---\n")
    content_lines.append("## 📈 评分说明\n")
    content_lines.append("- **热门排名**: 东方财富热度榜排名 (占10%)\n")
    content_lines.append("- **资金流向**: 净流入+大单净额 (占22.5%)\n")
    content_lines.append("- **技术形态**: 当日涨跌幅+涨停加成 (占22.5%)\n")
    content_lines.append("- **基本面前景**: 财务基本面 (占27%)\n")
    content_lines.append("- **政策利好**: 政策面支持 (占18%)\n")
    
    content = "".join(content_lines)
    
    try:
        # 尝试创建文档
        result = feishu_doc({
            "action": "create",
            "title": title,
            "content": content
        })
        if result.get("data"):
            print(f"✅ 文档已创建")
            return result.get("data", {}).get("document", {}).get("document_id")
    except Exception as e:
        print(f"创建文档失败: {e}")
    
    return None

def notify_top8(results: list) -> None:
    """
    通知TOP 8股票 - 同时发送飞书消息和创建文档
    """
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    # 构建消息
    lines = [f"🐲 龙头股评分 {date_str}\n"]
    lines.append("=" * 30 + "\n")
    lines.append("📊 TOP 8 龙头股\n\n")
    
    for i, stock in enumerate(results[:8], 1):
        emoji = "🔥" if i <= 3 else "📈"
        lines.append(f"{emoji} {i}. {stock['name']} ({stock['code']})\n")
        lines.append(f"   评分: {stock['总分']:.1f} | 热门:{stock['热门排名分']:.0f} 资金:{stock['资金面分']:.0f} 技术:{stock['技术面分']:.0f}\n\n")
    
    lines.append("---\n")
    lines.append("💡 评分系统: 热门10% + 资金22.5% + 技术22.5% + 基本面27% + 政策18%")
    
    message = "".join(lines)
    
    # 发送飞书消息
    print("\n📤 发送飞书通知...")
    
    # 使用OpenClaw的消息接口发送
    from message import message as msg_tool
    result = msg_tool({
        "action": "send",
        "message": message,
        "target": "ou_13cafc8c6a7df03546103f28981b61f7"  # 当前用户
    })
    
    if result.get("code") == 0 or "成功" in str(result):
        print("✅ 飞书消息已发送")
    else:
        print(f"发送结果: {result}")
    
    # 创建文档
    print("\n📄 创建评分文档...")
    create_daily_doc(results)

if __name__ == "__main__":
    # 测试
    with open("score_results.json", "r") as f:
        data = json.load(f)
    
    notify_top8(data["results"])
