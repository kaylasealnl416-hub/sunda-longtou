#!/usr/bin/env python3
"""
评分系统版本管理器
Version Control System for Scoring Configuration

功能：
1. 自动版本记录
2. 版本对比
3. 版本回滚
4. 版本历史查看
5. 版本标签和备注
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import difflib
from pathlib import Path


class VersionManager:
    """版本管理器"""
    
    def __init__(self, config_path: str = None, versions_dir: str = None):
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__), 
                '../config/scoring_config.json'
            )
        if versions_dir is None:
            versions_dir = os.path.join(
                os.path.dirname(__file__), 
                '../config/versions'
            )
        
        self.config_path = config_path
        self.versions_dir = versions_dir
        self.metadata_path = os.path.join(versions_dir, 'metadata.json')
        
        # 确保版本目录存在
        os.makedirs(versions_dir, exist_ok=True)
        
        # 初始化元数据
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict:
        """加载版本元数据"""
        if os.path.exists(self.metadata_path):
            with open(self.metadata_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "versions": [],
            "current_version": None,
            "next_version_id": 1
        }
    
    def _save_metadata(self):
        """保存版本元数据"""
        with open(self.metadata_path, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)
    
    def create_version(
        self, 
        config: Dict, 
        message: str = "", 
        tag: str = None,
        author: str = "system"
    ) -> str:
        """
        创建新版本
        
        Args:
            config: 配置内容
            message: 版本说明
            tag: 版本标签（如 v1.0, stable, test）
            author: 作者
        
        Returns:
            版本ID
        """
        version_id = f"v{self.metadata['next_version_id']}"
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 保存配置文件
        version_file = os.path.join(self.versions_dir, f'{version_id}.json')
        with open(version_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        # 计算与上一版本的差异
        changes = []
        if self.metadata['current_version']:
            prev_config = self.load_version(self.metadata['current_version'])
            changes = self._calculate_changes(prev_config, config)
        
        # 添加版本记录
        version_info = {
            "version_id": version_id,
            "timestamp": timestamp,
            "message": message,
            "tag": tag,
            "author": author,
            "changes": changes,
            "file": version_file
        }
        
        self.metadata['versions'].append(version_info)
        self.metadata['current_version'] = version_id
        self.metadata['next_version_id'] += 1
        
        self._save_metadata()
        
        print(f"✅ 已创建版本: {version_id}")
        if message:
            print(f"   说明: {message}")
        if changes:
            print(f"   变更: {len(changes)} 项")
        
        return version_id
    
    def _calculate_changes(self, old_config: Dict, new_config: Dict) -> List[Dict]:
        """计算配置变更"""
        changes = []
        
        # 比较维度权重
        old_dims = {d['id']: d for d in old_config.get('dimensions', [])}
        new_dims = {d['id']: d for d in new_config.get('dimensions', [])}
        
        for dim_id, new_dim in new_dims.items():
            if dim_id in old_dims:
                old_dim = old_dims[dim_id]
                
                # 权重变化
                if old_dim['weight'] != new_dim['weight']:
                    changes.append({
                        "type": "weight_change",
                        "dimension": new_dim['name'],
                        "old_value": old_dim['weight'],
                        "new_value": new_dim['weight']
                    })
                
                # 子维度变化
                if 'sub_dimensions' in new_dim:
                    old_subs = {s['id']: s for s in old_dim.get('sub_dimensions', [])}
                    new_subs = {s['id']: s for s in new_dim['sub_dimensions']}
                    
                    for sub_id, new_sub in new_subs.items():
                        if sub_id in old_subs:
                            old_sub = old_subs[sub_id]
                            
                            # 子维度权重变化
                            if old_sub['weight'] != new_sub['weight']:
                                changes.append({
                                    "type": "sub_weight_change",
                                    "dimension": new_dim['name'],
                                    "sub_dimension": new_sub['name'],
                                    "old_value": old_sub['weight'],
                                    "new_value": new_sub['weight']
                                })
                            
                            # 评分规则变化
                            old_rules = {r['condition']: r for r in old_sub.get('scoring_rules', [])}
                            new_rules = {r['condition']: r for r in new_sub.get('scoring_rules', [])}
                            
                            for condition, new_rule in new_rules.items():
                                if condition in old_rules:
                                    old_rule = old_rules[condition]
                                    if old_rule['score'] != new_rule['score']:
                                        changes.append({
                                            "type": "rule_change",
                                            "dimension": new_dim['name'],
                                            "sub_dimension": new_sub['name'],
                                            "condition": condition,
                                            "old_value": old_rule['score'],
                                            "new_value": new_rule['score']
                                        })
        
        return changes
    
    def load_version(self, version_id: str) -> Dict:
        """加载指定版本"""
        version_file = os.path.join(self.versions_dir, f'{version_id}.json')
        
        if not os.path.exists(version_file):
            raise FileNotFoundError(f"版本 {version_id} 不存在")
        
        with open(version_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def rollback(self, version_id: str) -> Dict:
        """回滚到指定版本"""
        config = self.load_version(version_id)
        
        # 保存当前配置为新版本（回滚前备份）
        current_config = self._load_current_config()
        self.create_version(
            current_config, 
            f"回滚前自动备份（回滚到 {version_id}）",
            tag="auto_backup"
        )
        
        # 应用回滚
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        self.metadata['current_version'] = version_id
        self._save_metadata()
        
        print(f"✅ 已回滚到版本: {version_id}")
        return config
    
    def _load_current_config(self) -> Dict:
        """加载当前配置"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def list_versions(self, limit: int = None, tag: str = None) -> List[Dict]:
        """列出版本历史"""
        versions = self.metadata['versions']
        
        # 按标签过滤
        if tag:
            versions = [v for v in versions if v.get('tag') == tag]
        
        # 限制数量
        if limit:
            versions = versions[-limit:]
        
        return versions
    
    def compare_versions(self, version_id1: str, version_id2: str) -> Dict:
        """对比两个版本"""
        config1 = self.load_version(version_id1)
        config2 = self.load_version(version_id2)
        
        changes = self._calculate_changes(config1, config2)
        
        return {
            "version1": version_id1,
            "version2": version_id2,
            "changes": changes,
            "total_changes": len(changes)
        }
    
    def get_version_info(self, version_id: str) -> Optional[Dict]:
        """获取版本信息"""
        for version in self.metadata['versions']:
            if version['version_id'] == version_id:
                return version
        return None
    
    def add_tag(self, version_id: str, tag: str):
        """为版本添加标签"""
        for version in self.metadata['versions']:
            if version['version_id'] == version_id:
                version['tag'] = tag
                self._save_metadata()
                print(f"✅ 已为版本 {version_id} 添加标签: {tag}")
                return
        
        print(f"❌ 版本 {version_id} 不存在")
    
    def print_history(self, limit: int = 10):
        """打印版本历史"""
        versions = self.list_versions(limit=limit)
        
        print("=" * 70)
        print("📚 版本历史")
        print("=" * 70)
        
        for version in reversed(versions):
            is_current = version['version_id'] == self.metadata['current_version']
            current_mark = " ← 当前版本" if is_current else ""
            
            print(f"\n{version['version_id']}{current_mark}")
            print(f"  时间: {version['timestamp']}")
            print(f"  作者: {version['author']}")
            
            if version.get('tag'):
                print(f"  标签: {version['tag']}")
            
            if version.get('message'):
                print(f"  说明: {version['message']}")
            
            if version.get('changes'):
                print(f"  变更: {len(version['changes'])} 项")
                for change in version['changes'][:3]:  # 只显示前3项
                    if change['type'] == 'weight_change':
                        print(f"    • {change['dimension']}: {change['old_value']} → {change['new_value']}分")
                    elif change['type'] == 'rule_change':
                        print(f"    • {change['dimension']}/{change['sub_dimension']}/{change['condition']}: {change['old_value']} → {change['new_value']}分")
                
                if len(version['changes']) > 3:
                    print(f"    ... 还有 {len(version['changes']) - 3} 项变更")
        
        print("\n" + "=" * 70)
    
    def export_version(self, version_id: str, output_path: str):
        """导出版本"""
        config = self.load_version(version_id)
        version_info = self.get_version_info(version_id)
        
        export_data = {
            "version_info": version_info,
            "config": config
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 版本 {version_id} 已导出到: {output_path}")


def main():
    """测试函数"""
    manager = VersionManager()
    
    # 显示版本历史
    manager.print_history()
    
    # 创建新版本示例
    # current_config = manager._load_current_config()
    # manager.create_version(
    #     current_config,
    #     message="初始版本",
    #     tag="v1.0",
    #     author="小欧"
    # )


if __name__ == "__main__":
    main()
