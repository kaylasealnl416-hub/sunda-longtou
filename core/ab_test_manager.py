#!/usr/bin/env python3
"""
A/B测试系统
A/B Testing System for Scoring Configuration

功能：
1. 创建A/B测试
2. 对比不同配置的效果
3. 统计分析
4. 最优配置推荐
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import pandas as pd
from pathlib import Path


class ABTestManager:
    """A/B测试管理器"""
    
    def __init__(self, tests_dir: str = None):
        if tests_dir is None:
            tests_dir = os.path.join(
                os.path.dirname(__file__), 
                '../config/ab_tests'
            )
        
        self.tests_dir = tests_dir
        self.metadata_path = os.path.join(tests_dir, 'tests_metadata.json')
        
        # 确保目录存在
        os.makedirs(tests_dir, exist_ok=True)
        
        # 初始化元数据
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict:
        """加载测试元数据"""
        if os.path.exists(self.metadata_path):
            with open(self.metadata_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "tests": [],
            "next_test_id": 1
        }
    
    def _save_metadata(self):
        """保存测试元数据"""
        with open(self.metadata_path, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)
    
    def create_test(
        self,
        name: str,
        config_a: Dict,
        config_b: Dict,
        description: str = "",
        author: str = "system"
    ) -> str:
        """
        创建A/B测试
        
        Args:
            name: 测试名称
            config_a: 配置A
            config_b: 配置B
            description: 测试描述
            author: 创建者
        
        Returns:
            测试ID
        """
        test_id = f"test_{self.metadata['next_test_id']}"
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 保存配置文件
        test_dir = os.path.join(self.tests_dir, test_id)
        os.makedirs(test_dir, exist_ok=True)
        
        config_a_path = os.path.join(test_dir, 'config_a.json')
        config_b_path = os.path.join(test_dir, 'config_b.json')
        
        with open(config_a_path, 'w', encoding='utf-8') as f:
            json.dump(config_a, f, ensure_ascii=False, indent=2)
        
        with open(config_b_path, 'w', encoding='utf-8') as f:
            json.dump(config_b, f, ensure_ascii=False, indent=2)
        
        # 创建测试记录
        test_info = {
            "test_id": test_id,
            "name": name,
            "description": description,
            "author": author,
            "created_at": timestamp,
            "status": "running",
            "config_a_path": config_a_path,
            "config_b_path": config_b_path,
            "results": {
                "config_a": {"scores": [], "stats": {}},
                "config_b": {"scores": [], "stats": {}}
            }
        }
        
        self.metadata['tests'].append(test_info)
        self.metadata['next_test_id'] += 1
        
        self._save_metadata()
        
        print(f"✅ 已创建A/B测试: {test_id}")
        print(f"   名称: {name}")
        if description:
            print(f"   描述: {description}")
        
        return test_id
    
    def add_result(
        self,
        test_id: str,
        config_name: str,  # 'config_a' or 'config_b'
        stock_code: str,
        stock_name: str,
        score: float,
        actual_return: float = None,  # 实际收益率
        metadata: Dict = None
    ):
        """
        添加测试结果
        
        Args:
            test_id: 测试ID
            config_name: 配置名称（config_a 或 config_b）
            stock_code: 股票代码
            stock_name: 股票名称
            score: 评分
            actual_return: 实际收益率（可选）
            metadata: 其他元数据
        """
        test = self._get_test(test_id)
        if not test:
            print(f"❌ 测试 {test_id} 不存在")
            return
        
        result = {
            "stock_code": stock_code,
            "stock_name": stock_name,
            "score": score,
            "actual_return": actual_return,
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "metadata": metadata or {}
        }
        
        test['results'][config_name]['scores'].append(result)
        self._save_metadata()
    
    def calculate_statistics(self, test_id: str):
        """计算测试统计数据"""
        test = self._get_test(test_id)
        if not test:
            print(f"❌ 测试 {test_id} 不存在")
            return
        
        for config_name in ['config_a', 'config_b']:
            scores = test['results'][config_name]['scores']
            
            if not scores:
                continue
            
            # 提取数据
            score_values = [s['score'] for s in scores]
            returns = [s['actual_return'] for s in scores if s['actual_return'] is not None]
            
            # 计算统计指标
            stats = {
                "count": len(scores),
                "avg_score": sum(score_values) / len(score_values) if score_values else 0,
                "max_score": max(score_values) if score_values else 0,
                "min_score": min(score_values) if score_values else 0,
            }
            
            if returns:
                stats.update({
                    "avg_return": sum(returns) / len(returns),
                    "max_return": max(returns),
                    "min_return": min(returns),
                    "win_rate": len([r for r in returns if r > 0]) / len(returns) * 100,
                    "total_return": sum(returns)
                })
            
            test['results'][config_name]['stats'] = stats
        
        self._save_metadata()
        print(f"✅ 已计算测试 {test_id} 的统计数据")
    
    def compare_results(self, test_id: str) -> Dict:
        """对比测试结果"""
        test = self._get_test(test_id)
        if not test:
            return {"error": f"测试 {test_id} 不存在"}
        
        # 确保统计数据是最新的
        self.calculate_statistics(test_id)
        
        stats_a = test['results']['config_a']['stats']
        stats_b = test['results']['config_b']['stats']
        
        comparison = {
            "test_id": test_id,
            "test_name": test['name'],
            "config_a": stats_a,
            "config_b": stats_b,
            "winner": None,
            "improvements": {}
        }
        
        # 判断胜者
        if stats_a.get('avg_return', 0) > stats_b.get('avg_return', 0):
            comparison['winner'] = 'config_a'
        elif stats_b.get('avg_return', 0) > stats_a.get('avg_return', 0):
            comparison['winner'] = 'config_b'
        else:
            comparison['winner'] = 'tie'
        
        # 计算改进幅度
        if stats_a and stats_b:
            if stats_a.get('avg_return') and stats_b.get('avg_return'):
                improvement = ((stats_b['avg_return'] - stats_a['avg_return']) / 
                              abs(stats_a['avg_return']) * 100)
                comparison['improvements']['avg_return'] = round(improvement, 2)
            
            if stats_a.get('win_rate') and stats_b.get('win_rate'):
                improvement = stats_b['win_rate'] - stats_a['win_rate']
                comparison['improvements']['win_rate'] = round(improvement, 2)
        
        return comparison
    
    def print_comparison(self, test_id: str):
        """打印对比结果"""
        comparison = self.compare_results(test_id)
        
        if 'error' in comparison:
            print(f"❌ {comparison['error']}")
            return
        
        print("=" * 70)
        print(f"📊 A/B测试对比: {comparison['test_name']}")
        print("=" * 70)
        
        print(f"\n配置A:")
        self._print_stats(comparison['config_a'])
        
        print(f"\n配置B:")
        self._print_stats(comparison['config_b'])
        
        print(f"\n🏆 胜者: {comparison['winner']}")
        
        if comparison['improvements']:
            print(f"\n📈 改进幅度:")
            for metric, value in comparison['improvements'].items():
                sign = "+" if value > 0 else ""
                print(f"  {metric}: {sign}{value}%")
        
        print("\n" + "=" * 70)
    
    def _print_stats(self, stats: Dict):
        """打印统计数据"""
        if not stats:
            print("  暂无数据")
            return
        
        print(f"  样本数: {stats.get('count', 0)}")
        print(f"  平均评分: {stats.get('avg_score', 0):.2f}")
        
        if 'avg_return' in stats:
            print(f"  平均收益: {stats['avg_return']:.2f}%")
            print(f"  胜率: {stats['win_rate']:.2f}%")
            print(f"  最大收益: {stats['max_return']:.2f}%")
            print(f"  最小收益: {stats['min_return']:.2f}%")
    
    def _get_test(self, test_id: str) -> Optional[Dict]:
        """获取测试信息"""
        for test in self.metadata['tests']:
            if test['test_id'] == test_id:
                return test
        return None
    
    def list_tests(self, status: str = None) -> List[Dict]:
        """列出所有测试"""
        tests = self.metadata['tests']
        
        if status:
            tests = [t for t in tests if t['status'] == status]
        
        return tests
    
    def finish_test(self, test_id: str):
        """结束测试"""
        test = self._get_test(test_id)
        if test:
            test['status'] = 'completed'
            test['completed_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self._save_metadata()
            print(f"✅ 测试 {test_id} 已完成")
    
    def export_results(self, test_id: str, output_path: str):
        """导出测试结果"""
        test = self._get_test(test_id)
        if not test:
            print(f"❌ 测试 {test_id} 不存在")
            return
        
        # 计算最新统计
        self.calculate_statistics(test_id)
        
        # 导出
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(test, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 测试结果已导出到: {output_path}")


def main():
    """测试函数"""
    manager = ABTestManager()
    
    # 示例：创建测试
    # config_a = {...}  # 当前配置
    # config_b = {...}  # 新配置
    # test_id = manager.create_test(
    #     name="威科夫量价权重测试",
    #     config_a=config_a,
    #     config_b=config_b,
    #     description="测试威科夫量价分析权重从10分提升到12分的效果"
    # )
    
    # 列出所有测试
    tests = manager.list_tests()
    print(f"共有 {len(tests)} 个测试")


if __name__ == "__main__":
    main()
