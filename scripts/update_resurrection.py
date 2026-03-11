#!/usr/bin/env python3
"""
复活文档自动更新脚本
每周日凌晨3点运行，更新RESURRECTION.md
"""
import os
import json
import subprocess
from datetime import datetime

WORKSPACE = "/root/.openclaw/workspace"
RESURRECTION_FILE = f"{WORKSPACE}/RESURRECTION.md"

def get_crontab():
    """获取当前定时任务"""
    try:
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        return result.stdout
    except:
        return ""

def get_skills():
    """获取已安装的skills"""
    skills_dir = f"{WORKSPACE}/skills"
    extra_skills = os.path.expanduser("~/.openclaw/skills")
    
    skills = []
    
    # 标准skills
    if os.path.exists(skills_dir):
        skills.extend([d for d in os.listdir(skills_dir) if not d.startswith('.')])
    
    # 额外skills
    if os.path.exists(extra_skills):
        skills.extend([d for d in os.listdir(extra_skills) if not d.startswith('.')])
    
    return sorted(set(skills))

def get_qveris_status():
    """检查QVeris状态"""
    skill_file = os.path.expanduser("~/.openclaw/skills/qveris/SKILL.md")
    tool_file = os.path.expanduser("~/.openclaw/skills/qveris/scripts/qveris_tool.mjs")
    
    if os.path.exists(skill_file) and os.path.exists(tool_file):
        return "✅ 已安装"
    return "❌ 未安装"

def get_projects():
    """获取项目列表"""
    projects = []
    for item in os.listdir(WORKSPACE):
        path = os.path.join(WORKSPACE, item)
        if os.path.isdir(path) and not item.startswith('.') and not item.startswith('memory'):
            projects.append(item)
    return projects

def update_resurrection_doc():
    """更新复活文档"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    skills = get_skills()
    crontab = get_crontab()
    qveris_status = get_qveris_status()
    projects = get_projects()
    
    # 读取现有文档
    try:
        with open(RESURRECTION_FILE, 'r') as f:
            content = f.read()
    except:
        content = ""
    
    # 更新技能列表
    skills_section = "## 📦 Skill安装列表\n\n### 标准Skills\n```\n" + "\n".join([f"- {s}" for s in skills if s not in ['qveris']]) + "\n```\n\n### QVeris\n" + qveris_status
    
    if "## 📦 Skill安装列表" in content:
        # 更新现有文档
        import re
        # 简单替换 - 实际可以更精确
        content = re.sub(r'## 📦 Skill安装列表.*?(?=\n## )', skills_section, content, flags=re.DOTALL)
    else:
        content += f"\n\n{skills_section}"
    
    # 更新日期
    content = content.replace("## 📅 更新日志", f"## 📅 更新日志\n- {today}: 自动更新")
    
    # 写回
    with open(RESURRECTION_FILE, 'w') as f:
        f.write(content)
    
    print(f"✅ 复活文档已更新: {today}")
    print(f"  Skills: {len(skills)}个")
    print(f"  Projects: {len(projects)}个")

if __name__ == "__main__":
    update_resurrection_doc()
