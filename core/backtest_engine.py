#!/usr/bin/env python3
"""
回测框架
Backtesting Framework for Dragon Stock Scoring System

功能：
1. 历史数据回测
2. 评分系统验证
3. 收益率计算
4. 性能指标统计
5. 回测报告生成
"""

import json
import os
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import pandas as pd
from pathlib import Path


class BacktestEngine:
    """回测引擎"""
    
    def __init__(
        self,
        config_path: str = None,
        data_dir: str = None,
        output_dir: str = None
    ):
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__), 
                '../config/scoring_config.json'
            )
        if data_dir is None:
            data_dir = os.path.join(
                os.path.dirname(__file__), 
                '../data/historical'
            )
        if output_dir is None:
            output_dir = os.path.join(
                os.path.dirname(__file__), 
                '../output/backtest'
            )
        
        self.config_path = config_path
        self.data_dir = data_dir
        self.output_dir = output_dir
        
        # 确保目录存在
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)
        
        # 加载配置
        self.config = self._load_config()
        
        # 回测结果
        self.results = []
    
    def _load_config(self) -> Dict:
        """加载评分配置"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def run_backtest(
        self,
        start_date: str,
        end_date: str,
        score_threshold: float = 70.0,
        holding_days: int = 5,
        max_positions: int = 10
    ) -> Dict:
        """
        运行回测
        
        Args:
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            score_threshold: 评分阈值（只买入高于此分数的股票）
            holding_days: 持仓天数
            max_positions: 最大持仓数量
        
        Returns:
            回测结果字典
        """
        print("=" * 70)
        print("🔄 开始回测")
        print("=" * 70)
        print(f"回测区间: {start_date} ~ {end_date}")
        print(f"评分阈值: {score_threshold}")
        print(f"持仓天数: {holding_days}")
        print(f"最大持仓: {max_positions}")
        print("=" * 70)
        
        # 加载历史数据
        historical_data = self._load_historical_data(start_date, end_date)
        
        if not historical_data:
            print("❌ 没有找到历史数据")
            return {"error": "No historical data found"}
        
        # 按日期遍历
        trades = []
        current_positions = []
        
        for date in self._date_range(start_date, end_date):
            date_str = date.strftime('%Y-%m-%d')
            
            # 检查持仓是否到期
            current_positions = self._check_positions(
                current_positions, 
                date_str, 
                historical_data
            )
            
            # 如果有空位，选股买入
            if len(current_positions) < max_positions:
                # 获取当日候选股票
                candidates = self._get_candidates(date_str, historical_data)
                
                # 评分
                scored_stocks = []
                for stock in candidates:
                    score = self._calculate_score(stock)
                    if score >= score_threshold:
                        scored_stocks.append({
                            'stock': stock,
                            'score': score
                        })
                
                # 按分数排序
                scored_stocks.sort(key=lambda x: x['score'], reverse=True)
                
                # 买入
                available_slots = max_positions - len(current_positions)
                for item in scored_stocks[:available_slots]:
                    position = {
                        'stock_code': item['stock']['code'],
                        'stock_name': item['stock']['name'],
                        'score': item['score'],
                        'buy_date': date_str,
                        'buy_price': item['stock']['close'],
                        'sell_date': None,
                        'sell_price': None,
                        'return': None,
                        'holding_days': holding_days
                    }
                    current_positions.append(position)
                    print(f"📈 {date_str} 买入: {position['stock_name']} "
                          f"({position['stock_code']}) "
                          f"评分: {position['score']:.2f} "
                          f"价格: {position['buy_price']:.2f}")
        
        # 计算最终持仓收益（如果还未卖出）
        for position in current_positions:
            if position['sell_date'] is None:
                # 使用最后一天的价格
                last_price = self._get_price(
                    position['stock_code'], 
                    end_date, 
                    historical_data
                )
                if last_price:
                    position['sell_date'] = end_date
                    position['sell_price'] = last_price
                    position['return'] = (last_price - position['buy_price']) / position['buy_price'] * 100
                    trades.append(position)
        
        # 统计分析
        stats = self._calculate_statistics(trades)
        
        # 保存结果
        result = {
            'config': self.config,
            'parameters': {
                'start_date': start_date,
                'end_date': end_date,
                'score_threshold': score_threshold,
                'holding_days': holding_days,
                'max_positions': max_positions
            },
            'trades': trades,
            'statistics': stats,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        self.results.append(result)
        
        # 打印结果
        self._print_results(result)
        
        return result
    
    def _load_historical_data(self, start_date: str, end_date: str) -> Dict:
        """
        加载历史数据
        
        数据格式示例：
        {
            "2024-01-01": [
                {
                    "code": "600905",
                    "name": "三峡能源",
                    "close": 10.5,
                    "volume": 1000000,
                    "turnover": 10500000,
                    "emotion_cycle": "启动期",
                    "volume_ratio": 2.5,
                    ...
                }
            ]
        }
        """
        # TODO: 实际实现时需要从数据库或文件加载
        # 这里返回空字典，需要用户提供真实数据
        print("⚠️  需要加载历史数据，请确保数据文件存在于:", self.data_dir)
        return {}
    
    def _date_range(self, start_date: str, end_date: str):
        """生成日期范围"""
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        current = start
        while current <= end:
            yield current
            current += timedelta(days=1)
    
    def _check_positions(
        self, 
        positions: List[Dict], 
        current_date: str,
        historical_data: Dict
    ) -> List[Dict]:
        """检查持仓是否到期"""
        active_positions = []
        
        for position in positions:
            if position['sell_date'] is not None:
                continue
            
            # 计算持仓天数
            buy_date = datetime.strptime(position['buy_date'], '%Y-%m-%d')
            current = datetime.strptime(current_date, '%Y-%m-%d')
            days_held = (current - buy_date).days
            
            # 检查是否到期
            if days_held >= position['holding_days']:
                # 卖出
                sell_price = self._get_price(
                    position['stock_code'], 
                    current_date, 
                    historical_data
                )
                
                if sell_price:
                    position['sell_date'] = current_date
                    position['sell_price'] = sell_price
                    position['return'] = (sell_price - position['buy_price']) / position['buy_price'] * 100
                    
                    print(f"📉 {current_date} 卖出: {position['stock_name']} "
                          f"收益: {position['return']:.2f}%")
            else:
                active_positions.append(position)
        
        return active_positions
    
    def _get_candidates(self, date: str, historical_data: Dict) -> List[Dict]:
        """获取当日候选股票"""
        return historical_data.get(date, [])
    
    def _get_price(self, stock_code: str, date: str, historical_data: Dict) -> Optional[float]:
        """获取指定日期的股票价格"""
        stocks = historical_data.get(date, [])
        for stock in stocks:
            if stock['code'] == stock_code:
                return stock.get('close')
        return None
    
    def _calculate_score(self, stock: Dict) -> float:
        """
        计算股票评分
        
        这里需要调用实际的评分系统
        """
        # TODO: 集成 dragon_scorer_v6.py
        # 这里返回模拟分数
        return 75.0
    
    def _calculate_statistics(self, trades: List[Dict]) -> Dict:
        """计算统计指标"""
        if not trades:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'avg_return': 0,
                'total_return': 0,
                'max_return': 0,
                'min_return': 0,
                'sharpe_ratio': 0,
                'max_drawdown': 0
            }
        
        returns = [t['return'] for t in trades if t['return'] is not None]
        
        if not returns:
            return {'total_trades': len(trades), 'error': 'No valid returns'}
        
        wins = [r for r in returns if r > 0]
        losses = [r for r in returns if r <= 0]
        
        stats = {
            'total_trades': len(trades),
            'win_trades': len(wins),
            'loss_trades': len(losses),
            'win_rate': len(wins) / len(returns) * 100 if returns else 0,
            'avg_return': sum(returns) / len(returns),
            'avg_win': sum(wins) / len(wins) if wins else 0,
            'avg_loss': sum(losses) / len(losses) if losses else 0,
            'total_return': sum(returns),
            'max_return': max(returns),
            'min_return': min(returns),
            'profit_factor': abs(sum(wins) / sum(losses)) if losses and sum(losses) != 0 else 0
        }
        
        # 夏普比率（简化版）
        if returns:
            std_return = pd.Series(returns).std()
            stats['sharpe_ratio'] = (stats['avg_return'] / std_return) if std_return > 0 else 0
        
        # 最大回撤
        cumulative = [sum(returns[:i+1]) for i in range(len(returns))]
        max_drawdown = 0
        peak = cumulative[0]
        for value in cumulative:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak * 100 if peak > 0 else 0
            max_drawdown = max(max_drawdown, drawdown)
        
        stats['max_drawdown'] = max_drawdown
        
        return stats
    
    def _print_results(self, result: Dict):
        """打印回测结果"""
        stats = result['statistics']
        
        print("\n" + "=" * 70)
        print("📊 回测结果")
        print("=" * 70)
        
        print(f"\n交易统计:")
        print(f"  总交易次数: {stats['total_trades']}")
        print(f"  盈利次数: {stats.get('win_trades', 0)}")
        print(f"  亏损次数: {stats.get('loss_trades', 0)}")
        print(f"  胜率: {stats['win_rate']:.2f}%")
        
        print(f"\n收益统计:")
        print(f"  平均收益: {stats['avg_return']:.2f}%")
        print(f"  平均盈利: {stats.get('avg_win', 0):.2f}%")
        print(f"  平均亏损: {stats.get('avg_loss', 0):.2f}%")
        print(f"  总收益: {stats['total_return']:.2f}%")
        print(f"  最大收益: {stats['max_return']:.2f}%")
        print(f"  最小收益: {stats['min_return']:.2f}%")
        
        print(f"\n风险指标:")
        print(f"  盈亏比: {stats.get('profit_factor', 0):.2f}")
        print(f"  夏普比率: {stats.get('sharpe_ratio', 0):.2f}")
        print(f"  最大回撤: {stats.get('max_drawdown', 0):.2f}%")
        
        print("\n" + "=" * 70)
    
    def export_report(self, result: Dict, output_path: str = None):
        """导出回测报告"""
        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = os.path.join(
                self.output_dir,
                f'backtest_report_{timestamp}.json'
            )
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 回测报告已保存: {output_path}")
        
        # 同时导出Excel版本
        excel_path = output_path.replace('.json', '.xlsx')
        self._export_excel_report(result, excel_path)
    
    def _export_excel_report(self, result: Dict, output_path: str):
        """导出Excel格式报告"""
        try:
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # 1. 统计摘要
                stats = result['statistics']
                stats_df = pd.DataFrame([stats])
                stats_df.to_excel(writer, sheet_name='统计摘要', index=False)
                
                # 2. 交易明细
                trades = result['trades']
                if trades:
                    trades_df = pd.DataFrame(trades)
                    trades_df.to_excel(writer, sheet_name='交易明细', index=False)
                
                # 3. 参数配置
                params = result['parameters']
                params_df = pd.DataFrame([params])
                params_df.to_excel(writer, sheet_name='参数配置', index=False)
            
            print(f"✅ Excel报告已保存: {output_path}")
        except Exception as e:
            print(f"⚠️  Excel导出失败: {e}")
    
    def compare_configs(
        self,
        configs: List[Dict],
        start_date: str,
        end_date: str,
        **backtest_params
    ) -> pd.DataFrame:
        """
        对比多个配置的回测结果
        
        Args:
            configs: 配置列表
            start_date: 开始日期
            end_date: 结束日期
            **backtest_params: 其他回测参数
        
        Returns:
            对比结果DataFrame
        """
        print("🔄 开始配置对比回测...")
        
        results = []
        for i, config in enumerate(configs):
            print(f"\n测试配置 {i+1}/{len(configs)}...")
            
            # 临时保存配置
            temp_config_path = self.config_path + f'.temp_{i}'
            with open(temp_config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            # 运行回测
            original_config_path = self.config_path
            self.config_path = temp_config_path
            self.config = config
            
            result = self.run_backtest(start_date, end_date, **backtest_params)
            
            # 恢复配置路径
            self.config_path = original_config_path
            
            # 清理临时文件
            os.remove(temp_config_path)
            
            # 记录结果
            stats = result['statistics']
            stats['config_id'] = f"配置{i+1}"
            results.append(stats)
        
        # 创建对比表
        comparison_df = pd.DataFrame(results)
        
        print("\n" + "=" * 70)
        print("📊 配置对比结果")
        print("=" * 70)
        print(comparison_df.to_string())
        print("=" * 70)
        
        return comparison_df


def main():
    """测试函数"""
    engine = BacktestEngine()
    
    print("回测框架已初始化")
    print("\n使用示例:")
    print("result = engine.run_backtest(")
    print("    start_date='2024-01-01',")
    print("    end_date='2024-03-31',")
    print("    score_threshold=70.0,")
    print("    holding_days=5,")
    print("    max_positions=10")
    print(")")
    print("\nengine.export_report(result)")


if __name__ == "__main__":
    main()
