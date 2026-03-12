#!/usr/bin/env python3
"""
实时监控系统
Real-time Monitoring System for Dragon Stocks

功能：
1. 实时监控龙头股
2. 自动评分
3. 异常预警
4. 推送通知
"""

import json
import os
import time
from typing import Dict, List, Callable, Optional
from datetime import datetime
import threading
from queue import Queue


class RealtimeMonitor:
    """实时监控器"""
    
    def __init__(
        self,
        config_path: str = None,
        alert_callback: Callable = None,
        check_interval: int = 60
    ):
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__), 
                '../config/scoring_config.json'
            )
        
        self.config_path = config_path
        self.config = self._load_config()
        self.alert_callback = alert_callback
        self.check_interval = check_interval
        
        # 监控状态
        self.is_running = False
        self.monitor_thread = None
        
        # 监控列表
        self.watchlist = []
        
        # 历史记录
        self.history = []
        
        # 预警队列
        self.alert_queue = Queue()
    
    def _load_config(self) -> Dict:
        """加载配置"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def add_to_watchlist(self, stock_code: str, stock_name: str = None):
        """添加到监控列表"""
        if not any(s['code'] == stock_code for s in self.watchlist):
            self.watchlist.append({
                'code': stock_code,
                'name': stock_name or stock_code,
                'added_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            print(f"✅ 已添加到监控: {stock_name or stock_code} ({stock_code})")
    
    def remove_from_watchlist(self, stock_code: str):
        """从监控列表移除"""
        self.watchlist = [s for s in self.watchlist if s['code'] != stock_code]
        print(f"✅ 已移除监控: {stock_code}")
    
    def start_monitoring(self):
        """开始监控"""
        if self.is_running:
            print("⚠️  监控已在运行中")
            return
        
        self.is_running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        print("🚀 实时监控已启动")
        print(f"   监控间隔: {self.check_interval}秒")
        print(f"   监控股票: {len(self.watchlist)}只")
    
    def stop_monitoring(self):
        """停止监控"""
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        print("⏹️  实时监控已停止")
    
    def _monitor_loop(self):
        """监控循环"""
        while self.is_running:
            try:
                self._check_all_stocks()
                time.sleep(self.check_interval)
            except Exception as e:
                print(f"❌ 监控出错: {e}")
                time.sleep(self.check_interval)
    
    def _check_all_stocks(self):
        """检查所有股票"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        for stock in self.watchlist:
            try:
                # 获取实时数据
                data = self._fetch_realtime_data(stock['code'])
                
                if not data:
                    continue
                
                # 计算评分
                score = self._calculate_score(data)
                
                # 记录历史
                record = {
                    'timestamp': timestamp,
                    'stock_code': stock['code'],
                    'stock_name': stock['name'],
                    'score': score,
                    'price': data.get('price'),
                    'change_pct': data.get('change_pct'),
                    'volume_ratio': data.get('volume_ratio')
                }
                self.history.append(record)
                
                # 检查预警条件
                self._check_alerts(record, data)
                
            except Exception as e:
                print(f"❌ 检查 {stock['code']} 失败: {e}")
    
    def _fetch_realtime_data(self, stock_code: str) -> Optional[Dict]:
        """
        获取实时数据
        
        TODO: 实际实现时需要对接行情API
        """
        # 这里返回模拟数据
        return {
            'code': stock_code,
            'price': 10.5,
            'change_pct': 5.2,
            'volume': 1000000,
            'volume_ratio': 2.5,
            'turnover_rate': 8.5,
            'emotion_cycle': '启动期'
        }
    
    def _calculate_score(self, data: Dict) -> float:
        """
        计算评分
        
        TODO: 集成 dragon_scorer_v6.py
        """
        return 75.0
    
    def _check_alerts(self, record: Dict, data: Dict):
        """检查预警条件"""
        alerts = []
        
        # 1. 高分预警
        if record['score'] >= 80:
            alerts.append({
                'type': 'high_score',
                'level': 'info',
                'message': f"🌟 {record['stock_name']} 评分达到 {record['score']:.2f}"
            })
        
        # 2. 涨停预警
        if data.get('change_pct', 0) >= 9.9:
            alerts.append({
                'type': 'limit_up',
                'level': 'warning',
                'message': f"📈 {record['stock_name']} 涨停！涨幅 {data['change_pct']:.2f}%"
            })
        
        # 3. 放量预警
        if data.get('volume_ratio', 0) >= 3.0:
            alerts.append({
                'type': 'high_volume',
                'level': 'info',
                'message': f"📊 {record['stock_name']} 放量！量比 {data['volume_ratio']:.2f}"
            })
        
        # 4. 评分下降预警
        recent_scores = [h['score'] for h in self.history[-10:] 
                        if h['stock_code'] == record['stock_code']]
        if len(recent_scores) >= 2:
            if recent_scores[-1] < recent_scores[-2] - 10:
                alerts.append({
                    'type': 'score_drop',
                    'level': 'warning',
                    'message': f"⚠️  {record['stock_name']} 评分下降 {recent_scores[-2] - recent_scores[-1]:.2f}分"
                })
        
        # 发送预警
        for alert in alerts:
            alert['timestamp'] = record['timestamp']
            alert['stock_code'] = record['stock_code']
            alert['stock_name'] = record['stock_name']
            alert['score'] = record['score']
            
            self.alert_queue.put(alert)
            self._send_alert(alert)
    
    def _send_alert(self, alert: Dict):
        """发送预警"""
        # 打印到控制台
        level_emoji = {
            'info': 'ℹ️',
            'warning': '⚠️',
            'error': '❌'
        }
        emoji = level_emoji.get(alert['level'], 'ℹ️')
        print(f"{emoji} [{alert['timestamp']}] {alert['message']}")
        
        # 调用回调函数
        if self.alert_callback:
            try:
                self.alert_callback(alert)
            except Exception as e:
                print(f"❌ 预警回调失败: {e}")
    
    def get_latest_scores(self, limit: int = 10) -> List[Dict]:
        """获取最新评分"""
        # 按时间戳分组，取每只股票的最新记录
        latest = {}
        for record in reversed(self.history):
            code = record['stock_code']
            if code not in latest:
                latest[code] = record
        
        # 按评分排序
        result = sorted(latest.values(), key=lambda x: x['score'], reverse=True)
        return result[:limit]
    
    def get_alerts(self, limit: int = 20) -> List[Dict]:
        """获取最近的预警"""
        alerts = []
        while not self.alert_queue.empty() and len(alerts) < limit:
            alerts.append(self.alert_queue.get())
        return alerts
    
    def get_stock_history(self, stock_code: str, limit: int = 100) -> List[Dict]:
        """获取股票历史记录"""
        records = [r for r in self.history if r['stock_code'] == stock_code]
        return records[-limit:]
    
    def export_history(self, output_path: str):
        """导出历史记录"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)
        print(f"✅ 历史记录已导出: {output_path}")
    
    def print_status(self):
        """打印监控状态"""
        print("=" * 70)
        print("📊 实时监控状态")
        print("=" * 70)
        print(f"运行状态: {'🟢 运行中' if self.is_running else '🔴 已停止'}")
        print(f"监控股票: {len(self.watchlist)}只")
        print(f"历史记录: {len(self.history)}条")
        print(f"待处理预警: {self.alert_queue.qsize()}条")
        
        if self.watchlist:
            print("\n监控列表:")
            for stock in self.watchlist:
                print(f"  • {stock['name']} ({stock['code']})")
        
        # 显示最新评分
        latest = self.get_latest_scores(5)
        if latest:
            print("\n最新评分 TOP 5:")
            for i, record in enumerate(latest, 1):
                print(f"  {i}. {record['stock_name']} ({record['stock_code']}) "
                      f"评分: {record['score']:.2f} "
                      f"涨幅: {record.get('change_pct', 0):.2f}%")
        
        print("=" * 70)


class AlertManager:
    """预警管理器"""
    
    def __init__(self):
        self.rules = []
    
    def add_rule(
        self,
        name: str,
        condition: Callable[[Dict], bool],
        message_template: str,
        level: str = 'info'
    ):
        """
        添加预警规则
        
        Args:
            name: 规则名称
            condition: 判断函数，返回True时触发预警
            message_template: 消息模板
            level: 预警级别 (info/warning/error)
        """
        self.rules.append({
            'name': name,
            'condition': condition,
            'message_template': message_template,
            'level': level
        })
    
    def check(self, data: Dict) -> List[Dict]:
        """检查所有规则"""
        alerts = []
        
        for rule in self.rules:
            try:
                if rule['condition'](data):
                    alert = {
                        'rule': rule['name'],
                        'level': rule['level'],
                        'message': rule['message_template'].format(**data),
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    alerts.append(alert)
            except Exception as e:
                print(f"❌ 规则 {rule['name']} 检查失败: {e}")
        
        return alerts


def example_alert_callback(alert: Dict):
    """示例预警回调函数"""
    # 这里可以实现：
    # 1. 发送邮件
    # 2. 发送微信/钉钉通知
    # 3. 写入日志
    # 4. 触发交易信号
    pass


def main():
    """测试函数"""
    monitor = RealtimeMonitor(check_interval=10)
    
    # 添加监控股票
    monitor.add_to_watchlist('600905', '三峡能源')
    monitor.add_to_watchlist('000001', '平安银行')
    
    # 打印状态
    monitor.print_status()
    
    print("\n使用示例:")
    print("monitor.start_monitoring()  # 开始监控")
    print("monitor.stop_monitoring()   # 停止监控")
    print("monitor.get_latest_scores() # 获取最新评分")
    print("monitor.get_alerts()        # 获取预警")


if __name__ == "__main__":
    main()
