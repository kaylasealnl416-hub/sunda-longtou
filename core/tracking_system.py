#!/usr/bin/env python3
"""
历史跟踪系统
Stock Tracking System

功能：
1. 跟踪首板涨停股
2. 如果次日断板，连续追踪3个交易日
3. 记录每日评分、涨跌幅、成交额等数据
4. 分析断板后的走势规律
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd


class TrackingSystem:
    """股票跟踪系统"""
    
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = os.path.join(
                os.path.dirname(__file__), 
                '../data/tracking'
            )
        
        self.data_dir = data_dir
        self.db_path = os.path.join(data_dir, 'tracking_db.json')
        
        # 确保目录存在
        os.makedirs(data_dir, exist_ok=True)
        
        # 加载数据库
        self.db = self._load_db()
    
    def _load_db(self) -> Dict:
        """加载跟踪数据库"""
        if os.path.exists(self.db_path):
            with open(self.db_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {
            'tracking_stocks': [],
            'completed_stocks': [],
            'last_update': None
        }
    
    def _save_db(self):
        """保存跟踪数据库"""
        self.db['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        with open(self.db_path, 'w', encoding='utf-8') as f:
            json.dump(self.db, f, ensure_ascii=False, indent=2)
    
    def add_first_board_stocks(self, stocks: List[Dict], date: str = None):
        """
        添加首板涨停股到跟踪列表
        
        Args:
            stocks: 首板股票列表 [{code, name, score, ...}]
            date: 日期，默认今天
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        print(f"📝 添加首板涨停股到跟踪列表 ({date})...")
        
        added_count = 0
        for stock in stocks:
            # 检查是否已在跟踪中
            if any(s['code'] == stock['code'] for s in self.db['tracking_stocks']):
                continue
            
            # 添加到跟踪列表
            tracking_item = {
                'code': stock['code'],
                'name': stock['name'],
                'first_board_date': date,
                'first_board_score': stock.get('score', 0),
                'break_board_date': None,
                'tracking_days_left': 0,
                'status': 'waiting',  # waiting, tracking, completed
                'daily_records': []
            }
            
            self.db['tracking_stocks'].append(tracking_item)
            added_count += 1
        
        self._save_db()
        print(f"✅ 已添加 {added_count} 只首板股票到跟踪列表")
    
    def check_and_update(self, today_zt_stocks: List[Dict], date: str = None):
        """
        检查并更新跟踪状态
        
        Args:
            today_zt_stocks: 今日涨停股列表
            date: 日期，默认今天
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        print("=" * 70)
        print(f"🔍 检查跟踪股票状态 ({date})")
        print("=" * 70)
        print()
        
        today_zt_codes = set(s['code'] for s in today_zt_stocks)
        
        for stock in self.db['tracking_stocks']:
            if stock['status'] == 'completed':
                continue
            
            code = stock['code']
            name = stock['name']
            
            # 检查是否继续涨停
            if code in today_zt_codes:
                # 继续涨停，不需要跟踪
                if stock['status'] == 'waiting':
                    print(f"✅ {name} ({code}) 继续涨停，无需跟踪")
                    stock['status'] = 'waiting'
            else:
                # 断板了
                if stock['status'] == 'waiting':
                    # 首次断板，启动3日跟踪
                    stock['break_board_date'] = date
                    stock['tracking_days_left'] = 3
                    stock['status'] = 'tracking'
                    print(f"⚠️  {name} ({code}) 断板！启动3日跟踪")
                
                elif stock['status'] == 'tracking':
                    # 继续跟踪
                    stock['tracking_days_left'] -= 1
                    print(f"📊 {name} ({code}) 跟踪中，剩余 {stock['tracking_days_left']} 天")
                    
                    if stock['tracking_days_left'] <= 0:
                        # 跟踪完成
                        stock['status'] = 'completed'
                        self.db['completed_stocks'].append(stock)
                        print(f"✅ {name} ({code}) 跟踪完成")
        
        # 移除已完成的股票
        self.db['tracking_stocks'] = [
            s for s in self.db['tracking_stocks'] 
            if s['status'] != 'completed'
        ]
        
        self._save_db()
        print()
    
    def record_daily_data(self, stock_code: str, data: Dict, date: str = None):
        """
        记录每日数据
        
        Args:
            stock_code: 股票代码
            data: 当日数据 {score, price, change_pct, turnover, ...}
            date: 日期，默认今天
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        # 查找股票
        stock = None
        for s in self.db['tracking_stocks']:
            if s['code'] == stock_code:
                stock = s
                break
        
        if not stock:
            # 在已完成列表中查找
            for s in self.db['completed_stocks']:
                if s['code'] == stock_code:
                    stock = s
                    break
        
        if not stock:
            print(f"⚠️  未找到股票 {stock_code}")
            return
        
        # 添加每日记录
        record = {
            'date': date,
            'score': data.get('score', 0),
            'price': data.get('price', 0),
            'change_pct': data.get('change_pct', 0),
            'turnover': data.get('turnover', 0),
            'turnover_rate': data.get('turnover_rate', 0),
            'status': data.get('status', '跟踪中')
        }
        
        stock['daily_records'].append(record)
        self._save_db()
    
    def get_tracking_stocks(self) -> List[Dict]:
        """获取正在跟踪的股票"""
        return [s for s in self.db['tracking_stocks'] if s['status'] == 'tracking']
    
    def get_waiting_stocks(self) -> List[Dict]:
        """获取等待中的股票（首板后等待次日）"""
        return [s for s in self.db['tracking_stocks'] if s['status'] == 'waiting']
    
    def get_completed_stocks(self, limit: int = None) -> List[Dict]:
        """获取已完成跟踪的股票"""
        completed = self.db['completed_stocks']
        if limit:
            return completed[-limit:]
        return completed
    
    def analyze_break_board_pattern(self) -> Dict:
        """
        分析断板后的走势规律
        
        Returns:
            统计数据
        """
        completed = self.db['completed_stocks']
        
        if not completed:
            return {
                'total': 0,
                'message': '暂无已完成的跟踪数据'
            }
        
        # 统计数据
        total = len(completed)
        
        # 断板后3日涨跌统计
        day1_up = 0
        day2_up = 0
        day3_up = 0
        
        # 断板后3日平均涨跌幅
        day1_changes = []
        day2_changes = []
        day3_changes = []
        
        for stock in completed:
            records = stock['daily_records']
            
            if len(records) >= 1:
                if records[0]['change_pct'] > 0:
                    day1_up += 1
                day1_changes.append(records[0]['change_pct'])
            
            if len(records) >= 2:
                if records[1]['change_pct'] > 0:
                    day2_up += 1
                day2_changes.append(records[1]['change_pct'])
            
            if len(records) >= 3:
                if records[2]['change_pct'] > 0:
                    day3_up += 1
                day3_changes.append(records[2]['change_pct'])
        
        return {
            'total': total,
            'day1': {
                'up_count': day1_up,
                'up_rate': day1_up / total * 100 if total > 0 else 0,
                'avg_change': sum(day1_changes) / len(day1_changes) if day1_changes else 0
            },
            'day2': {
                'up_count': day2_up,
                'up_rate': day2_up / total * 100 if total > 0 else 0,
                'avg_change': sum(day2_changes) / len(day2_changes) if day2_changes else 0
            },
            'day3': {
                'up_count': day3_up,
                'up_rate': day3_up / total * 100 if total > 0 else 0,
                'avg_change': sum(day3_changes) / len(day3_changes) if day3_changes else 0
            }
        }
    
    def print_status(self):
        """打印跟踪状态"""
        print("=" * 70)
        print("📊 股票跟踪系统状态")
        print("=" * 70)
        print()
        
        waiting = self.get_waiting_stocks()
        tracking = self.get_tracking_stocks()
        completed = self.get_completed_stocks()
        
        print(f"等待中: {len(waiting)}只")
        print(f"跟踪中: {len(tracking)}只")
        print(f"已完成: {len(completed)}只")
        print()
        
        if tracking:
            print("正在跟踪的股票:")
            for stock in tracking:
                print(f"  • {stock['name']} ({stock['code']}) - 剩余{stock['tracking_days_left']}天")
        
        print()
        print("=" * 70)
    
    def generate_report(self, output_path: str = None):
        """生成跟踪报告"""
        if output_path is None:
            output_path = os.path.join(
                self.data_dir,
                f'tracking_report_{datetime.now().strftime("%Y-%m-%d")}.txt'
            )
        
        report = f"""
{'=' * 70}
📊 股票跟踪系统报告
{'=' * 70}

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

一、跟踪概况
──────────────────────────────────────────────────────────────────────
等待中: {len(self.get_waiting_stocks())}只
跟踪中: {len(self.get_tracking_stocks())}只
已完成: {len(self.get_completed_stocks())}只

二、断板后走势分析
──────────────────────────────────────────────────────────────────────
"""
        
        analysis = self.analyze_break_board_pattern()
        
        if analysis['total'] > 0:
            report += f"""
样本数量: {analysis['total']}只

断板后第1天:
  上涨概率: {analysis['day1']['up_rate']:.2f}%
  平均涨跌: {analysis['day1']['avg_change']:.2f}%

断板后第2天:
  上涨概率: {analysis['day2']['up_rate']:.2f}%
  平均涨跌: {analysis['day2']['avg_change']:.2f}%

断板后第3天:
  上涨概率: {analysis['day3']['up_rate']:.2f}%
  平均涨跌: {analysis['day3']['avg_change']:.2f}%
"""
        else:
            report += "\n暂无已完成的跟踪数据\n"
        
        report += f"\n{'=' * 70}\n"
        
        # 保存报告
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"📄 跟踪报告已生成: {output_path}")
        return report


def main():
    """测试函数"""
    tracker = TrackingSystem()
    
    # 打印状态
    tracker.print_status()
    
    # 生成报告
    tracker.generate_report()


if __name__ == "__main__":
    main()
