#!/usr/bin/env python3
"""
网页内容提取工具
优先使用Jina Reader（格式干净，速度快）
备用web_fetch
"""
import requests
import sys
import os

os.environ['http_proxy'] = 'http://127.0.0.1:7890'
os.environ['https_proxy'] = 'http://127.0.0.1:7890'

def jina_fetch(url, max_chars=30000):
    """用Jina Reader提取网页内容"""
    jina_url = f"https://r.jina.ai/{url}"
    try:
        resp = requests.get(jina_url, timeout=30)
        if resp.status_code == 200:
            content = resp.text
            # 截断到指定长度
            if len(content) > max_chars:
                content = content[:max_chars] + "\n\n... [内容已截断]"
            return content
        else:
            return f"Jina返回状态码: {resp.status_code}"
    except Exception as e:
        return f"Jina失败: {e}"

def web_fetch_fallback(url, max_chars=30000):
    """备用：直接用requests获取"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        resp = requests.get(url, headers=headers, timeout=30)
        # 简单提取正文（移除HTML标签）
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # 移除脚本和样式
        for script in soup(["script", "style"]):
            script.decompose()
        
        content = soup.get_text()
        # 清理空白
        lines = [line.strip() for line in content.split('\n')]
        content = '\n'.join(line for line in lines if line)
        
        if len(content) > max_chars:
            content = content[:max_chars] + "\n\n... [内容已截断]"
        return content
    except Exception as e:
        return f"备用方案也失败: {e}"

def fetch_url(url, max_chars=30000, use_jina=True):
    """
    获取网页内容
    use_jina=True: 优先用Jina Reader
    use_jina=False: 直接获取
    """
    print(f"📥 正在获取: {url}")
    
    if use_jina:
        content = jina_fetch(url, max_chars)
        # 检查是否成功
        if "失败" in content or "错误" in content or "返回状态码" in content:
            print("⚠️ Jina失败，尝试备用方案...")
            content = web_fetch_fallback(url, max_chars)
    else:
        content = web_fetch_fallback(url, max_chars)
    
    print(f"✅ 获取成功! 内容长度: {len(content)} 字符")
    return content

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 fetch_page.py <URL> [max_chars]")
        sys.exit(1)
    
    url = sys.argv[1]
    max_chars = int(sys.argv[2]) if len(sys.argv) > 2 else 30000
    
    content = fetch_url(url, max_chars)
    print("\n" + "="*50)
    print(content[:2000])
    if len(content) > 2000:
        print(f"\n... 共 {len(content)} 字符")
