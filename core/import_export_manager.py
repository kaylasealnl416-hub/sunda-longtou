#!/usr/bin/env python3
"""
导入导出系统
Import/Export System for Scoring Configuration

功能：
1. Excel格式导入导出
2. CSV格式导入导出
3. 批量配置管理
4. 模板库
"""

import json
import os
from typing import Dict, List
import pandas as pd
from datetime import datetime


class ImportExportManager:
    """导入导出管理器"""
    
    def __init__(self, config_path: str = None, templates_dir: str = None):
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__), 
                '../config/scoring_config.json'
            )
        if templates_dir is None:
            templates_dir = os.path.join(
                os.path.dirname(__file__), 
                '../config/templates'
            )
        
        self.config_path = config_path
        self.templates_dir = templates_dir
        
        # 确保模板目录存在
        os.makedirs(templates_dir, exist_ok=True)
    
    def export_to_excel(self, config: Dict, output_path: str):
        """
        导出配置到Excel
        
        Args:
            config: 配置字典
            output_path: 输出文件路径
        """
        print(f"📤 导出配置到Excel: {output_path}")
        
        # 创建Excel writer
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # 1. 概览表
            overview_data = {
                '版本': [config.get('version', 'N/A')],
                '总分': [config.get('total_score', 100)],
                '更新时间': [config.get('last_updated', 'N/A')],
                '描述': [config.get('description', '')]
            }
            pd.DataFrame(overview_data).to_excel(writer, sheet_name='概览', index=False)
            
            # 2. 维度权重表
            dimensions_data = []
            for dim in config.get('dimensions', []):
                dimensions_data.append({
                    'ID': dim['id'],
                    '名称': dim['name'],
                    'Emoji': dim.get('emoji', ''),
                    '权重': dim['weight'],
                    '启用': dim.get('enabled', True)
                })
            pd.DataFrame(dimensions_data).to_excel(writer, sheet_name='维度权重', index=False)
            
            # 3. 每个维度的详细配置
            for dim in config.get('dimensions', []):
                if 'sub_dimensions' not in dim:
                    continue
                
                sheet_data = []
                for sub in dim['sub_dimensions']:
                    # 子维度基本信息
                    base_row = {
                        '子维度ID': sub['id'],
                        '子维度名称': sub['name'],
                        '子维度权重': sub['weight'],
                        '启用': sub.get('enabled', True)
                    }
                    
                    # 评分规则
                    if 'scoring_rules' in sub:
                        for rule in sub['scoring_rules']:
                            row = base_row.copy()
                            row.update({
                                '条件': rule['condition'],
                                '分数': rule['score'],
                                '说明': rule.get('description', ''),
                                '逻辑': rule.get('logic', '')
                            })
                            sheet_data.append(row)
                    else:
                        sheet_data.append(base_row)
                
                if sheet_data:
                    df = pd.DataFrame(sheet_data)
                    # Excel sheet名称限制31字符
                    sheet_name = dim['name'][:31]
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        print(f"✅ 导出完成")
    
    def import_from_excel(self, excel_path: str) -> Dict:
        """
        从Excel导入配置
        
        Args:
            excel_path: Excel文件路径
        
        Returns:
            配置字典
        """
        print(f"📥 从Excel导入配置: {excel_path}")
        
        # 读取Excel
        excel_file = pd.ExcelFile(excel_path)
        
        # 1. 读取概览
        overview_df = pd.read_excel(excel_file, sheet_name='概览')
        config = {
            'version': str(overview_df['版本'].iloc[0]),
            'total_score': int(overview_df['总分'].iloc[0]),
            'last_updated': str(overview_df['更新时间'].iloc[0]),
            'description': str(overview_df['描述'].iloc[0]),
            'dimensions': []
        }
        
        # 2. 读取维度权重
        dimensions_df = pd.read_excel(excel_file, sheet_name='维度权重')
        
        for _, row in dimensions_df.iterrows():
            dim = {
                'id': row['ID'],
                'name': row['名称'],
                'emoji': row.get('Emoji', '📊'),
                'weight': float(row['权重']),
                'enabled': bool(row.get('启用', True)),
                'sub_dimensions': []
            }
            
            # 3. 读取该维度的详细配置
            sheet_name = dim['name'][:31]
            if sheet_name in excel_file.sheet_names:
                detail_df = pd.read_excel(excel_file, sheet_name=sheet_name)
                
                # 按子维度分组
                sub_dims = {}
                for _, detail_row in detail_df.iterrows():
                    sub_id = detail_row['子维度ID']
                    
                    if sub_id not in sub_dims:
                        sub_dims[sub_id] = {
                            'id': sub_id,
                            'name': detail_row['子维度名称'],
                            'weight': float(detail_row['子维度权重']),
                            'enabled': bool(detail_row.get('启用', True)),
                            'scoring_rules': []
                        }
                    
                    # 添加评分规则
                    if pd.notna(detail_row.get('条件')):
                        rule = {
                            'condition': detail_row['条件'],
                            'score': float(detail_row['分数']),
                        }
                        if pd.notna(detail_row.get('说明')):
                            rule['description'] = detail_row['说明']
                        if pd.notna(detail_row.get('逻辑')):
                            rule['logic'] = detail_row['逻辑']
                        
                        sub_dims[sub_id]['scoring_rules'].append(rule)
                
                dim['sub_dimensions'] = list(sub_dims.values())
            
            config['dimensions'].append(dim)
        
        print(f"✅ 导入完成")
        return config
    
    def export_to_csv(self, config: Dict, output_dir: str):
        """
        导出配置到CSV文件（多个文件）
        
        Args:
            config: 配置字典
            output_dir: 输出目录
        """
        print(f"📤 导出配置到CSV: {output_dir}")
        
        os.makedirs(output_dir, exist_ok=True)
        
        # 1. 维度权重
        dimensions_data = []
        for dim in config.get('dimensions', []):
            dimensions_data.append({
                'id': dim['id'],
                'name': dim['name'],
                'emoji': dim.get('emoji', ''),
                'weight': dim['weight'],
                'enabled': dim.get('enabled', True)
            })
        
        pd.DataFrame(dimensions_data).to_csv(
            os.path.join(output_dir, 'dimensions.csv'),
            index=False,
            encoding='utf-8-sig'
        )
        
        # 2. 每个维度的详细配置
        for dim in config.get('dimensions', []):
            if 'sub_dimensions' not in dim:
                continue
            
            rows = []
            for sub in dim['sub_dimensions']:
                for rule in sub.get('scoring_rules', []):
                    rows.append({
                        'dimension_id': dim['id'],
                        'dimension_name': dim['name'],
                        'sub_id': sub['id'],
                        'sub_name': sub['name'],
                        'sub_weight': sub['weight'],
                        'condition': rule['condition'],
                        'score': rule['score'],
                        'description': rule.get('description', ''),
                        'logic': rule.get('logic', '')
                    })
            
            if rows:
                pd.DataFrame(rows).to_csv(
                    os.path.join(output_dir, f'{dim["id"]}.csv'),
                    index=False,
                    encoding='utf-8-sig'
                )
        
        print(f"✅ 导出完成")
    
    def save_as_template(self, config: Dict, template_name: str, description: str = ""):
        """
        保存为模板
        
        Args:
            config: 配置字典
            template_name: 模板名称
            description: 模板描述
        """
        template_path = os.path.join(self.templates_dir, f'{template_name}.json')
        
        template = {
            'name': template_name,
            'description': description,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'config': config
        }
        
        with open(template_path, 'w', encoding='utf-8') as f:
            json.dump(template, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 模板已保存: {template_name}")
    
    def load_template(self, template_name: str) -> Dict:
        """
        加载模板
        
        Args:
            template_name: 模板名称
        
        Returns:
            配置字典
        """
        template_path = os.path.join(self.templates_dir, f'{template_name}.json')
        
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"模板 {template_name} 不存在")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            template = json.load(f)
        
        print(f"✅ 已加载模板: {template_name}")
        return template['config']
    
    def list_templates(self) -> List[Dict]:
        """列出所有模板"""
        templates = []
        
        for filename in os.listdir(self.templates_dir):
            if filename.endswith('.json'):
                template_path = os.path.join(self.templates_dir, filename)
                with open(template_path, 'r', encoding='utf-8') as f:
                    template = json.load(f)
                    templates.append({
                        'name': template['name'],
                        'description': template.get('description', ''),
                        'created_at': template.get('created_at', 'N/A')
                    })
        
        return templates
    
    def create_default_templates(self):
        """创建默认模板"""
        # 加载当前配置
        with open(self.config_path, 'r', encoding='utf-8') as f:
            current_config = json.load(f)
        
        # 1. 保守型模板（基本面权重高）
        conservative_config = current_config.copy()
        for dim in conservative_config['dimensions']:
            if dim['id'] == 'fundamental':
                dim['weight'] = 15
            elif dim['id'] == 'emotion':
                dim['weight'] = 20
        
        self.save_as_template(
            conservative_config,
            'conservative',
            '保守型配置：注重基本面，降低情绪面权重'
        )
        
        # 2. 激进型模板（情绪面权重高）
        aggressive_config = current_config.copy()
        for dim in aggressive_config['dimensions']:
            if dim['id'] == 'emotion':
                dim['weight'] = 40
            elif dim['id'] == 'fundamental':
                dim['weight'] = 5
        
        self.save_as_template(
            aggressive_config,
            'aggressive',
            '激进型配置：注重情绪面和技术面'
        )
        
        # 3. 平衡型模板（当前配置）
        self.save_as_template(
            current_config,
            'balanced',
            '平衡型配置：各维度权重均衡'
        )
        
        print("✅ 已创建3个默认模板")


def main():
    """测试函数"""
    manager = ImportExportManager()
    
    print("导入导出系统已初始化")
    print("\n功能列表:")
    print("1. export_to_excel() - 导出到Excel")
    print("2. import_from_excel() - 从Excel导入")
    print("3. export_to_csv() - 导出到CSV")
    print("4. save_as_template() - 保存为模板")
    print("5. load_template() - 加载模板")
    print("6. list_templates() - 列出所有模板")
    print("7. create_default_templates() - 创建默认模板")


if __name__ == "__main__":
    main()
