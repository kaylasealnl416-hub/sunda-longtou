#!/usr/bin/env python3
"""
评分系统配置管理器
Scoring System Configuration Manager

功能：
1. 加载/保存配置文件
2. 动态添加/删除评分维度
3. 修改评分规则和权重
4. 可视化评分树状图
5. 验证配置合法性
"""

import json
import os
from typing import Dict, List, Optional
from pathlib import Path


class ScoringConfigManager:
    """评分系统配置管理器"""
    
    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__), 
                '../config/scoring_config.json'
            )
        self.config_path = config_path
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"❌ 配置文件不存在: {self.config_path}")
            return self._default_config()
    
    def save_config(self):
        """保存配置文件"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
        print(f"✅ 配置已保存到: {self.config_path}")
    
    def _default_config(self) -> Dict:
        """默认配置"""
        return {
            "version": "6.0",
            "total_score": 100,
            "dimensions": []
        }
    
    # ==================== 查询功能 ====================
    
    def get_dimension(self, dimension_id: str) -> Optional[Dict]:
        """获取指定维度"""
        for dim in self.config['dimensions']:
            if dim['id'] == dimension_id:
                return dim
        return None
    
    def get_sub_dimension(self, dimension_id: str, sub_id: str) -> Optional[Dict]:
        """获取指定子维度"""
        dim = self.get_dimension(dimension_id)
        if dim:
            for sub in dim.get('sub_dimensions', []):
                if sub['id'] == sub_id:
                    return sub
        return None
    
    def list_dimensions(self) -> List[Dict]:
        """列出所有维度"""
        return self.config['dimensions']
    
    def get_total_weight(self) -> float:
        """计算总权重"""
        return sum(dim['weight'] for dim in self.config['dimensions'] if dim['enabled'])
    
    # ==================== 修改功能 ====================
    
    def add_dimension(
        self, 
        dimension_id: str, 
        name: str, 
        weight: float,
        emoji: str = "📊",
        enabled: bool = True
    ):
        """添加新维度"""
        if self.get_dimension(dimension_id):
            print(f"❌ 维度 {dimension_id} 已存在")
            return False
        
        new_dim = {
            "id": dimension_id,
            "name": name,
            "emoji": emoji,
            "weight": weight,
            "enabled": enabled,
            "sub_dimensions": []
        }
        
        self.config['dimensions'].append(new_dim)
        print(f"✅ 已添加维度: {name} ({weight}分)")
        return True
    
    def remove_dimension(self, dimension_id: str):
        """删除维度"""
        self.config['dimensions'] = [
            dim for dim in self.config['dimensions'] 
            if dim['id'] != dimension_id
        ]
        print(f"✅ 已删除维度: {dimension_id}")
    
    def update_dimension_weight(self, dimension_id: str, new_weight: float):
        """修改维度权重"""
        dim = self.get_dimension(dimension_id)
        if dim:
            old_weight = dim['weight']
            dim['weight'] = new_weight
            print(f"✅ {dim['name']} 权重: {old_weight} → {new_weight}")
            return True
        print(f"❌ 维度 {dimension_id} 不存在")
        return False
    
    def toggle_dimension(self, dimension_id: str):
        """启用/禁用维度"""
        dim = self.get_dimension(dimension_id)
        if dim:
            dim['enabled'] = not dim['enabled']
            status = "启用" if dim['enabled'] else "禁用"
            print(f"✅ {dim['name']} 已{status}")
            return True
        return False
    
    def add_sub_dimension(
        self,
        dimension_id: str,
        sub_id: str,
        name: str,
        weight: float,
        scoring_rules: List[Dict] = None
    ):
        """添加子维度"""
        dim = self.get_dimension(dimension_id)
        if not dim:
            print(f"❌ 维度 {dimension_id} 不存在")
            return False
        
        if self.get_sub_dimension(dimension_id, sub_id):
            print(f"❌ 子维度 {sub_id} 已存在")
            return False
        
        new_sub = {
            "id": sub_id,
            "name": name,
            "weight": weight,
            "enabled": True,
            "scoring_rules": scoring_rules or []
        }
        
        if 'sub_dimensions' not in dim:
            dim['sub_dimensions'] = []
        
        dim['sub_dimensions'].append(new_sub)
        print(f"✅ 已添加子维度: {name} ({weight}分)")
        return True
    
    def remove_sub_dimension(self, dimension_id: str, sub_id: str):
        """删除子维度"""
        dim = self.get_dimension(dimension_id)
        if dim and 'sub_dimensions' in dim:
            dim['sub_dimensions'] = [
                sub for sub in dim['sub_dimensions']
                if sub['id'] != sub_id
            ]
            print(f"✅ 已删除子维度: {sub_id}")
            return True
        return False
    
    def add_scoring_rule(
        self,
        dimension_id: str,
        sub_id: str,
        condition: str,
        score: float,
        description: str = "",
        logic: str = ""
    ):
        """添加评分规则"""
        sub = self.get_sub_dimension(dimension_id, sub_id)
        if not sub:
            print(f"❌ 子维度不存在")
            return False
        
        new_rule = {
            "condition": condition,
            "score": score,
            "description": description
        }
        if logic:
            new_rule["logic"] = logic
        
        sub['scoring_rules'].append(new_rule)
        print(f"✅ 已添加评分规则: {condition} → {score}分")
        return True
    
    def update_scoring_rule(
        self,
        dimension_id: str,
        sub_id: str,
        condition: str,
        new_score: float
    ):
        """修改评分规则的分数"""
        sub = self.get_sub_dimension(dimension_id, sub_id)
        if not sub:
            return False
        
        for rule in sub['scoring_rules']:
            if rule['condition'] == condition:
                old_score = rule['score']
                rule['score'] = new_score
                print(f"✅ {condition}: {old_score} → {new_score}分")
                return True
        
        print(f"❌ 规则 {condition} 不存在")
        return False
    
    # ==================== 验证功能 ====================
    
    def validate(self) -> bool:
        """验证配置合法性"""
        errors = []
        
        # 1. 检查总权重
        total_weight = self.get_total_weight()
        if abs(total_weight - self.config['total_score']) > 0.01:
            errors.append(f"总权重({total_weight})不等于满分({self.config['total_score']})")
        
        # 2. 检查每个维度
        for dim in self.config['dimensions']:
            if not dim['enabled']:
                continue
            
            # 检查子维度权重
            if 'sub_dimensions' in dim:
                sub_total = sum(sub['weight'] for sub in dim['sub_dimensions'] if sub['enabled'])
                if abs(sub_total - dim['weight']) > 0.01:
                    errors.append(
                        f"{dim['name']}: 子维度权重({sub_total})不等于维度权重({dim['weight']})"
                    )
        
        if errors:
            print("❌ 配置验证失败:")
            for error in errors:
                print(f"  - {error}")
            return False
        
        print("✅ 配置验证通过")
        return True
    
    # ==================== 可视化功能 ====================
    
    def print_tree(self, show_disabled: bool = False):
        """打印评分树状图"""
        print("=" * 70)
        print(f"📊 评分系统配置树 v{self.config['version']}")
        print(f"总分: {self.config['total_score']}分")
        print("=" * 70)
        
        for dim in self.config['dimensions']:
            if not dim['enabled'] and not show_disabled:
                continue
            
            status = "" if dim['enabled'] else " [已禁用]"
            print(f"\n{dim['emoji']} {dim['name']} {dim['weight']}分{status}")
            
            if 'sub_dimensions' not in dim:
                continue
            
            for i, sub in enumerate(dim['sub_dimensions']):
                if not sub['enabled'] and not show_disabled:
                    continue
                
                is_last_sub = (i == len(dim['sub_dimensions']) - 1)
                sub_prefix = "└─" if is_last_sub else "├─"
                sub_status = "" if sub['enabled'] else " [已禁用]"
                
                print(f"  {sub_prefix} {sub['name']} {sub['weight']}分{sub_status}")
                
                # 打印评分规则
                if 'scoring_rules' in sub:
                    for j, rule in enumerate(sub['scoring_rules']):
                        is_last_rule = (j == len(sub['scoring_rules']) - 1)
                        rule_prefix = "   └─" if is_last_sub else "   │ "
                        if is_last_rule:
                            rule_prefix += "└─"
                        else:
                            rule_prefix += "├─"
                        
                        desc = f" ({rule.get('description', '')})" if rule.get('description') else ""
                        print(f"{rule_prefix} {rule['condition']} → {rule['score']}分{desc}")
        
        print("\n" + "=" * 70)
        print(f"总权重: {self.get_total_weight()}分")
        print("=" * 70)
    
    def export_markdown(self, output_path: str = None):
        """导出为Markdown格式"""
        if output_path is None:
            output_path = self.config_path.replace('.json', '.md')
        
        lines = []
        lines.append(f"# 评分系统配置 v{self.config['version']}\n")
        lines.append(f"**总分:** {self.config['total_score']}分\n")
        lines.append(f"**更新时间:** {self.config.get('last_updated', 'N/A')}\n")
        lines.append("\n---\n")
        
        for dim in self.config['dimensions']:
            if not dim['enabled']:
                continue
            
            lines.append(f"\n## {dim['emoji']} {dim['name']} ({dim['weight']}分)\n")
            
            if 'sub_dimensions' not in dim:
                continue
            
            for sub in dim['sub_dimensions']:
                if not sub['enabled']:
                    continue
                
                lines.append(f"\n### {sub['name']} ({sub['weight']}分)\n")
                
                if 'scoring_rules' in sub:
                    lines.append("\n| 条件 | 分数 | 说明 |\n")
                    lines.append("|------|------|------|\n")
                    
                    for rule in sub['scoring_rules']:
                        condition = rule['condition']
                        score = rule['score']
                        desc = rule.get('description', '')
                        lines.append(f"| {condition} | {score} | {desc} |\n")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        print(f"✅ 已导出到: {output_path}")


def interactive_menu():
    """交互式菜单"""
    manager = ScoringConfigManager()
    
    while True:
        print("\n" + "=" * 70)
        print("📊 评分系统配置管理器")
        print("=" * 70)
        print("1. 查看配置树")
        print("2. 添加维度")
        print("3. 删除维度")
        print("4. 修改维度权重")
        print("5. 启用/禁用维度")
        print("6. 添加子维度")
        print("7. 修改评分规则")
        print("8. 验证配置")
        print("9. 保存配置")
        print("10. 导出Markdown")
        print("0. 退出")
        print("=" * 70)
        
        choice = input("\n请选择操作 (0-10): ").strip()
        
        if choice == '0':
            print("👋 再见！")
            break
        
        elif choice == '1':
            manager.print_tree(show_disabled=True)
        
        elif choice == '2':
            dim_id = input("维度ID: ").strip()
            name = input("维度名称: ").strip()
            weight = float(input("权重: ").strip())
            emoji = input("Emoji (默认📊): ").strip() or "📊"
            manager.add_dimension(dim_id, name, weight, emoji)
        
        elif choice == '3':
            dim_id = input("要删除的维度ID: ").strip()
            confirm = input(f"确认删除 {dim_id}? (y/n): ").strip().lower()
            if confirm == 'y':
                manager.remove_dimension(dim_id)
        
        elif choice == '4':
            dim_id = input("维度ID: ").strip()
            new_weight = float(input("新权重: ").strip())
            manager.update_dimension_weight(dim_id, new_weight)
        
        elif choice == '5':
            dim_id = input("维度ID: ").strip()
            manager.toggle_dimension(dim_id)
        
        elif choice == '6':
            dim_id = input("父维度ID: ").strip()
            sub_id = input("子维度ID: ").strip()
            name = input("子维度名称: ").strip()
            weight = float(input("权重: ").strip())
            manager.add_sub_dimension(dim_id, sub_id, name, weight)
        
        elif choice == '7':
            dim_id = input("维度ID: ").strip()
            sub_id = input("子维度ID: ").strip()
            condition = input("条件: ").strip()
            new_score = float(input("新分数: ").strip())
            manager.update_scoring_rule(dim_id, sub_id, condition, new_score)
        
        elif choice == '8':
            manager.validate()
        
        elif choice == '9':
            manager.save_config()
        
        elif choice == '10':
            output = input("输出路径 (默认同目录.md): ").strip()
            manager.export_markdown(output if output else None)
        
        else:
            print("❌ 无效选择")


def main():
    """主函数"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'interactive':
        interactive_menu()
    else:
        # 默认：打印配置树
        manager = ScoringConfigManager()
        manager.print_tree()
        print("\n提示: 运行 'python config_manager.py interactive' 进入交互模式")


if __name__ == "__main__":
    main()
