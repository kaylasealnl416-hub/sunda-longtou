#!/usr/bin/env python3
"""
自动优化系统
Auto Optimization System for Scoring Configuration

功能：
1. 基于回测结果自动调整权重
2. 网格搜索最优参数
3. 遗传算法优化
4. 梯度下降优化
"""

import json
import os
from typing import Dict, List, Tuple, Callable
import numpy as np
from datetime import datetime
import random


class AutoOptimizer:
    """自动优化器"""
    
    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__), 
                '../config/scoring_config.json'
            )
        
        self.config_path = config_path
        self.config = self._load_config()
        self.optimization_history = []
    
    def _load_config(self) -> Dict:
        """加载配置"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _save_config(self, config: Dict):
        """保存配置"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    
    def grid_search(
        self,
        param_ranges: Dict[str, List[float]],
        evaluate_fn: Callable[[Dict], float],
        max_iterations: int = 100
    ) -> Tuple[Dict, float]:
        """
        网格搜索最优参数
        
        Args:
            param_ranges: 参数范围，如 {'emotion.weight': [25, 30, 35]}
            evaluate_fn: 评估函数，输入配置，返回得分
            max_iterations: 最大迭代次数
        
        Returns:
            (最优配置, 最优得分)
        """
        print("🔍 开始网格搜索...")
        print(f"参数范围: {param_ranges}")
        
        best_config = None
        best_score = float('-inf')
        iteration = 0
        
        # 生成所有参数组合
        param_names = list(param_ranges.keys())
        param_values = list(param_ranges.values())
        
        def generate_combinations(index=0, current_params=None):
            nonlocal iteration, best_config, best_score
            
            if current_params is None:
                current_params = {}
            
            if index == len(param_names):
                # 评估当前参数组合
                if iteration >= max_iterations:
                    return
                
                iteration += 1
                test_config = self._apply_params(self.config.copy(), current_params)
                score = evaluate_fn(test_config)
                
                print(f"  迭代 {iteration}: 得分 {score:.4f}")
                
                if score > best_score:
                    best_score = score
                    best_config = test_config
                    print(f"  ✨ 发现更优配置！得分: {best_score:.4f}")
                
                return
            
            # 递归生成组合
            param_name = param_names[index]
            for value in param_values[index]:
                current_params[param_name] = value
                generate_combinations(index + 1, current_params.copy())
        
        generate_combinations()
        
        print(f"\n✅ 网格搜索完成")
        print(f"最优得分: {best_score:.4f}")
        
        return best_config, best_score
    
    def genetic_algorithm(
        self,
        evaluate_fn: Callable[[Dict], float],
        population_size: int = 20,
        generations: int = 50,
        mutation_rate: float = 0.1
    ) -> Tuple[Dict, float]:
        """
        遗传算法优化
        
        Args:
            evaluate_fn: 评估函数
            population_size: 种群大小
            generations: 代数
            mutation_rate: 变异率
        
        Returns:
            (最优配置, 最优得分)
        """
        print("🧬 开始遗传算法优化...")
        print(f"种群大小: {population_size}, 代数: {generations}")
        
        # 初始化种群
        population = [self._mutate_config(self.config.copy()) for _ in range(population_size)]
        
        best_config = None
        best_score = float('-inf')
        
        for gen in range(generations):
            # 评估种群
            scores = [evaluate_fn(config) for config in population]
            
            # 更新最优解
            max_score_idx = np.argmax(scores)
            if scores[max_score_idx] > best_score:
                best_score = scores[max_score_idx]
                best_config = population[max_score_idx].copy()
                print(f"  代 {gen+1}: 最优得分 {best_score:.4f} ✨")
            else:
                print(f"  代 {gen+1}: 最优得分 {best_score:.4f}")
            
            # 选择
            selected = self._selection(population, scores, population_size // 2)
            
            # 交叉
            offspring = []
            for i in range(0, len(selected), 2):
                if i + 1 < len(selected):
                    child1, child2 = self._crossover(selected[i], selected[i+1])
                    offspring.extend([child1, child2])
            
            # 变异
            for config in offspring:
                if random.random() < mutation_rate:
                    self._mutate_config(config)
            
            # 新一代种群
            population = selected + offspring
            population = population[:population_size]
        
        print(f"\n✅ 遗传算法优化完成")
        print(f"最优得分: {best_score:.4f}")
        
        return best_config, best_score
    
    def _apply_params(self, config: Dict, params: Dict[str, float]) -> Dict:
        """应用参数到配置"""
        for param_path, value in params.items():
            parts = param_path.split('.')
            
            if len(parts) == 2:
                # 维度权重: emotion.weight
                dim_id, attr = parts
                for dim in config['dimensions']:
                    if dim['id'] == dim_id:
                        dim[attr] = value
            
            elif len(parts) == 3:
                # 子维度权重: emotion.volume_ratio.weight
                dim_id, sub_id, attr = parts
                for dim in config['dimensions']:
                    if dim['id'] == dim_id:
                        for sub in dim.get('sub_dimensions', []):
                            if sub['id'] == sub_id:
                                sub[attr] = value
        
        return config
    
    def _mutate_config(self, config: Dict) -> Dict:
        """随机变异配置"""
        # 随机选择一个维度
        dim = random.choice(config['dimensions'])
        
        # 随机调整权重（±20%）
        mutation = random.uniform(-0.2, 0.2)
        dim['weight'] = max(1, dim['weight'] * (1 + mutation))
        
        # 调整子维度权重以保持总和
        if 'sub_dimensions' in dim:
            total = sum(sub['weight'] for sub in dim['sub_dimensions'])
            scale = dim['weight'] / total if total > 0 else 1
            for sub in dim['sub_dimensions']:
                sub['weight'] = sub['weight'] * scale
        
        return config
    
    def _selection(self, population: List[Dict], scores: List[float], n: int) -> List[Dict]:
        """选择操作（轮盘赌）"""
        # 归一化得分
        min_score = min(scores)
        adjusted_scores = [s - min_score + 1 for s in scores]
        total = sum(adjusted_scores)
        probs = [s / total for s in adjusted_scores]
        
        # 选择
        indices = np.random.choice(len(population), size=n, replace=False, p=probs)
        return [population[i] for i in indices]
    
    def _crossover(self, config1: Dict, config2: Dict) -> Tuple[Dict, Dict]:
        """交叉操作"""
        child1 = config1.copy()
        child2 = config2.copy()
        
        # 随机交换一些维度的权重
        for i in range(len(child1['dimensions'])):
            if random.random() < 0.5:
                child1['dimensions'][i]['weight'], child2['dimensions'][i]['weight'] = \
                    child2['dimensions'][i]['weight'], child1['dimensions'][i]['weight']
        
        return child1, child2
    
    def bayesian_optimization(
        self,
        evaluate_fn: Callable[[Dict], float],
        n_iterations: int = 30
    ) -> Tuple[Dict, float]:
        """
        贝叶斯优化（简化版）
        
        Args:
            evaluate_fn: 评估函数
            n_iterations: 迭代次数
        
        Returns:
            (最优配置, 最优得分)
        """
        print("🎯 开始贝叶斯优化...")
        
        best_config = self.config.copy()
        best_score = evaluate_fn(best_config)
        
        history = [(best_config, best_score)]
        
        for i in range(n_iterations):
            # 生成候选配置（基于历史最优配置）
            candidate = self._generate_candidate(best_config, history)
            score = evaluate_fn(candidate)
            
            print(f"  迭代 {i+1}: 得分 {score:.4f}")
            
            history.append((candidate, score))
            
            if score > best_score:
                best_score = score
                best_config = candidate.copy()
                print(f"  ✨ 发现更优配置！得分: {best_score:.4f}")
        
        print(f"\n✅ 贝叶斯优化完成")
        print(f"最优得分: {best_score:.4f}")
        
        return best_config, best_score
    
    def _generate_candidate(self, base_config: Dict, history: List) -> Dict:
        """生成候选配置"""
        candidate = base_config.copy()
        
        # 基于历史数据生成候选
        # 简化版：随机扰动
        for dim in candidate['dimensions']:
            # 小幅度随机调整
            perturbation = random.gauss(0, 0.05)  # 均值0，标准差5%
            dim['weight'] = max(1, dim['weight'] * (1 + perturbation))
        
        return candidate
    
    def save_optimization_result(
        self,
        method: str,
        best_config: Dict,
        best_score: float,
        output_path: str = None
    ):
        """保存优化结果"""
        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = os.path.join(
                os.path.dirname(self.config_path),
                f'optimized_{method}_{timestamp}.json'
            )
        
        result = {
            "method": method,
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "best_score": best_score,
            "config": best_config
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 优化结果已保存到: {output_path}")


def example_evaluate_fn(config: Dict) -> float:
    """
    示例评估函数
    
    实际使用时，应该基于回测结果计算得分
    例如：胜率 * 平均收益率 - 最大回撤
    """
    # 这里只是示例，返回随机分数
    return random.random()


def main():
    """测试函数"""
    optimizer = AutoOptimizer()
    
    print("自动优化系统已初始化")
    print("\n使用示例:")
    print("1. 网格搜索:")
    print("   best_config, score = optimizer.grid_search(")
    print("       param_ranges={'emotion.weight': [25, 30, 35]},")
    print("       evaluate_fn=your_evaluate_function")
    print("   )")
    print("\n2. 遗传算法:")
    print("   best_config, score = optimizer.genetic_algorithm(")
    print("       evaluate_fn=your_evaluate_function,")
    print("       population_size=20,")
    print("       generations=50")
    print("   )")


if __name__ == "__main__":
    main()
