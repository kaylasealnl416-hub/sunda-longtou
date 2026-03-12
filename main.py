#!/usr/bin/env python3
"""
龙头股评分系统 - 主控制器
Dragon Stock Scoring System - Main Controller

整合所有模块，提供统一的接口
"""

import os
import sys
from typing import Dict, List, Optional
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

# 导入所有模块
from config_manager import ScoringConfigManager
from version_manager import VersionManager
from ab_test_manager import ABTestManager
from auto_optimizer import AutoOptimizer
from import_export_manager import ImportExportManager
from backtest_engine import BacktestEngine
from realtime_monitor import RealtimeMonitor
from report_generator import ReportGenerator


class DragonStockSystem:
    """龙头股评分系统主控制器"""
    
    def __init__(self, workspace_dir: str = None):
        if workspace_dir is None:
            workspace_dir = os.path.join(
                os.path.dirname(__file__),
                '..'
            )
        
        self.workspace_dir = os.path.abspath(workspace_dir)
        self.config_path = os.path.join(workspace_dir, 'config/scoring_config.json')
        
        print("=" * 70)
        print("🎯 龙头股评分系统")
        print("=" * 70)
        print(f"工作目录: {self.workspace_dir}")
        print(f"配置文件: {self.config_path}")
        print("=" * 70)
        
        # 初始化所有模块
        self._init_modules()
    
    def _init_modules(self):
        """初始化所有模块"""
        print("\n📦 正在初始化模块...")
        
        try:
            self.config_manager = ScoringConfigManager(self.config_path)
            print("  ✅ 配置管理器")
        except Exception as e:
            print(f"  ❌ 配置管理器初始化失败: {e}")
            self.config_manager = None
        
        try:
            self.version_manager = VersionManager(self.config_path)
            print("  ✅ 版本管理器")
        except Exception as e:
            print(f"  ❌ 版本管理器初始化失败: {e}")
            self.version_manager = None
        
        try:
            self.ab_test_manager = ABTestManager()
            print("  ✅ A/B测试管理器")
        except Exception as e:
            print(f"  ❌ A/B测试管理器初始化失败: {e}")
            self.ab_test_manager = None
        
        try:
            self.optimizer = AutoOptimizer(self.config_path)
            print("  ✅ 自动优化器")
        except Exception as e:
            print(f"  ❌ 自动优化器初始化失败: {e}")
            self.optimizer = None
        
        try:
            self.import_export = ImportExportManager(self.config_path)
            print("  ✅ 导入导出管理器")
        except Exception as e:
            print(f"  ❌ 导入导出管理器初始化失败: {e}")
            self.import_export = None
        
        try:
            self.backtest_engine = BacktestEngine(self.config_path)
            print("  ✅ 回测引擎")
        except Exception as e:
            print(f"  ❌ 回测引擎初始化失败: {e}")
            self.backtest_engine = None
        
        try:
            self.monitor = RealtimeMonitor(self.config_path)
            print("  ✅ 实时监控器")
        except Exception as e:
            print(f"  ❌ 实时监控器初始化失败: {e}")
            self.monitor = None
        
        try:
            self.report_generator = ReportGenerator(self.config_path)
            print("  ✅ 报告生成器")
        except Exception as e:
            print(f"  ❌ 报告生成器初始化失败: {e}")
            self.report_generator = None
        
        print("\n✅ 模块初始化完成\n")
    
    def show_menu(self):
        """显示主菜单"""
        print("\n" + "=" * 70)
        print("🎯 龙头股评分系统 - 主菜单")
        print("=" * 70)
        print("\n📊 配置管理")
        print("  1. 查看当前配置")
        print("  2. 修改配置权重")
        print("  3. 导入/导出配置")
        print("  4. 配置模板管理")
        
        print("\n📚 版本管理")
        print("  5. 查看版本历史")
        print("  6. 创建新版本")
        print("  7. 回滚到指定版本")
        
        print("\n🧪 测试与优化")
        print("  8. 创建A/B测试")
        print("  9. 查看测试结果")
        print("  10. 自动优化配置")
        
        print("\n🔄 回测验证")
        print("  11. 运行回测")
        print("  12. 查看回测报告")
        print("  13. 对比多个配置")
        
        print("\n📡 实时监控")
        print("  14. 启动实时监控")
        print("  15. 查看监控状态")
        print("  16. 管理监控列表")
        
        print("\n📝 报告生成")
        print("  17. 生成每日报告")
        print("  18. 生成周报")
        print("  19. 生成个股分析")
        
        print("\n🔥 新增功能")
        print("  22. 查看人气榜单")
        print("  23. 历史跟踪管理")
        print("  24. 自动化任务状态")
        
        print("\n🔧 系统管理")
        print("  20. 系统状态")
        print("  21. 帮助文档")
        print("  0. 退出系统")
        
        print("\n" + "=" * 70)
    
    def run(self):
        """运行主程序"""
        while True:
            self.show_menu()
            
            try:
                choice = input("\n请选择功能 (0-21): ").strip()
                
                if choice == '0':
                    print("\n👋 感谢使用龙头股评分系统！")
                    break
                
                elif choice == '1':
                    self._view_config()
                
                elif choice == '2':
                    self._modify_config()
                
                elif choice == '3':
                    self._import_export_config()
                
                elif choice == '4':
                    self._manage_templates()
                
                elif choice == '5':
                    self._view_version_history()
                
                elif choice == '6':
                    self._create_version()
                
                elif choice == '7':
                    self._rollback_version()
                
                elif choice == '8':
                    self._create_ab_test()
                
                elif choice == '9':
                    self._view_test_results()
                
                elif choice == '10':
                    self._auto_optimize()
                
                elif choice == '11':
                    self._run_backtest()
                
                elif choice == '12':
                    self._view_backtest_report()
                
                elif choice == '13':
                    self._compare_configs()
                
                elif choice == '14':
                    self._start_monitoring()
                
                elif choice == '15':
                    self._view_monitor_status()
                
                elif choice == '16':
                    self._manage_watchlist()
                
                elif choice == '17':
                    self._generate_daily_report()
                
                elif choice == '18':
                    self._generate_weekly_report()
                
                elif choice == '19':
                    self._generate_stock_analysis()
                
                elif choice == '20':
                    self._show_system_status()
                
                elif choice == '21':
                    self._show_help()
                
                elif choice == '22':
                    self._view_popularity_rank()
                
                elif choice == '23':
                    self._manage_tracking()
                
                elif choice == '24':
                    self._view_automation_status()
                
                else:
                    print("❌ 无效的选择，请重新输入")
                
                input("\n按回车键继续...")
                
            except KeyboardInterrupt:
                print("\n\n👋 感谢使用龙头股评分系统！")
                break
            except Exception as e:
                print(f"\n❌ 发生错误: {e}")
                input("\n按回车键继续...")
    
    def _view_config(self):
        """查看当前配置"""
        if self.config_manager:
            self.config_manager.print_tree()
        else:
            print("❌ 配置管理器未初始化")
    
    def _modify_config(self):
        """修改配置"""
        print("\n功能开发中...")
        print("请使用Web界面修改配置: standalone.html")
    
    def _import_export_config(self):
        """导入导出配置"""
        if not self.import_export:
            print("❌ 导入导出管理器未初始化")
            return
        
        print("\n1. 导出到Excel")
        print("2. 从Excel导入")
        print("3. 导出到CSV")
        
        choice = input("\n请选择: ").strip()
        
        if choice == '1':
            output_path = input("输出文件路径 (默认: config.xlsx): ").strip() or "config.xlsx"
            config = self.config_manager.config
            self.import_export.export_to_excel(config, output_path)
        
        elif choice == '2':
            input_path = input("输入文件路径: ").strip()
            if os.path.exists(input_path):
                config = self.import_export.import_from_excel(input_path)
                print("✅ 配置已导入")
            else:
                print("❌ 文件不存在")
    
    def _manage_templates(self):
        """管理模板"""
        if not self.import_export:
            print("❌ 导入导出管理器未初始化")
            return
        
        print("\n1. 查看所有模板")
        print("2. 保存当前配置为模板")
        print("3. 加载模板")
        print("4. 创建默认模板")
        
        choice = input("\n请选择: ").strip()
        
        if choice == '1':
            templates = self.import_export.list_templates()
            if templates:
                print("\n可用模板:")
                for t in templates:
                    print(f"  • {t['name']}: {t['description']}")
            else:
                print("暂无模板")
        
        elif choice == '2':
            name = input("模板名称: ").strip()
            desc = input("模板描述: ").strip()
            config = self.config_manager.config
            self.import_export.save_as_template(config, name, desc)
        
        elif choice == '3':
            name = input("模板名称: ").strip()
            try:
                config = self.import_export.load_template(name)
                print("✅ 模板已加载")
            except FileNotFoundError:
                print("❌ 模板不存在")
        
        elif choice == '4':
            self.import_export.create_default_templates()
    
    def _view_version_history(self):
        """查看版本历史"""
        if self.version_manager:
            self.version_manager.print_history()
        else:
            print("❌ 版本管理器未初始化")
    
    def _create_version(self):
        """创建新版本"""
        if not self.version_manager:
            print("❌ 版本管理器未初始化")
            return
        
        message = input("版本说明: ").strip()
        tag = input("版本标签 (可选): ").strip() or None
        
        config = self.config_manager.config
        self.version_manager.create_version(config, message, tag)
    
    def _rollback_version(self):
        """回滚版本"""
        if not self.version_manager:
            print("❌ 版本管理器未初始化")
            return
        
        self.version_manager.print_history(limit=10)
        version_id = input("\n输入要回滚的版本ID: ").strip()
        
        confirm = input(f"确认回滚到 {version_id}? (y/n): ").strip().lower()
        if confirm == 'y':
            self.version_manager.rollback(version_id)
    
    def _create_ab_test(self):
        """创建A/B测试"""
        print("\n功能开发中...")
    
    def _view_test_results(self):
        """查看测试结果"""
        if self.ab_test_manager:
            tests = self.ab_test_manager.list_tests()
            if tests:
                print(f"\n共有 {len(tests)} 个测试")
                for test in tests:
                    print(f"  • {test['test_id']}: {test['name']}")
            else:
                print("暂无测试")
        else:
            print("❌ A/B测试管理器未初始化")
    
    def _auto_optimize(self):
        """自动优化"""
        print("\n功能开发中...")
        print("需要提供评估函数（基于回测结果）")
    
    def _run_backtest(self):
        """运行回测"""
        print("\n功能开发中...")
        print("需要提供历史数据")
    
    def _view_backtest_report(self):
        """查看回测报告"""
        print("\n功能开发中...")
    
    def _compare_configs(self):
        """对比配置"""
        print("\n功能开发中...")
    
    def _start_monitoring(self):
        """启动监控"""
        if not self.monitor:
            print("❌ 实时监控器未初始化")
            return
        
        if self.monitor.is_running:
            print("⚠️  监控已在运行中")
        else:
            self.monitor.start_monitoring()
    
    def _view_monitor_status(self):
        """查看监控状态"""
        if self.monitor:
            self.monitor.print_status()
        else:
            print("❌ 实时监控器未初始化")
    
    def _manage_watchlist(self):
        """管理监控列表"""
        if not self.monitor:
            print("❌ 实时监控器未初始化")
            return
        
        print("\n1. 添加股票")
        print("2. 移除股票")
        print("3. 查看列表")
        
        choice = input("\n请选择: ").strip()
        
        if choice == '1':
            code = input("股票代码: ").strip()
            name = input("股票名称: ").strip()
            self.monitor.add_to_watchlist(code, name)
        
        elif choice == '2':
            code = input("股票代码: ").strip()
            self.monitor.remove_from_watchlist(code)
        
        elif choice == '3':
            self.monitor.print_status()
    
    def _generate_daily_report(self):
        """生成每日报告"""
        print("\n功能开发中...")
        print("需要提供当日股票数据")
    
    def _generate_weekly_report(self):
        """生成周报"""
        print("\n功能开发中...")
    
    def _generate_stock_analysis(self):
        """生成个股分析"""
        print("\n功能开发中...")
    
    def _show_system_status(self):
        """显示系统状态"""
        print("\n" + "=" * 70)
        print("🔧 系统状态")
        print("=" * 70)
        
        modules = [
            ("配置管理器", self.config_manager),
            ("版本管理器", self.version_manager),
            ("A/B测试管理器", self.ab_test_manager),
            ("自动优化器", self.optimizer),
            ("导入导出管理器", self.import_export),
            ("回测引擎", self.backtest_engine),
            ("实时监控器", self.monitor),
            ("报告生成器", self.report_generator)
        ]
        
        for name, module in modules:
            status = "🟢 正常" if module else "🔴 未初始化"
            print(f"{name}: {status}")
        
        print("=" * 70)
    
    def _show_help(self):
        """显示帮助"""
        print("\n" + "=" * 70)
        print("📖 帮助文档")
        print("=" * 70)
        print("\n系统功能说明:")
        print("\n1. 配置管理 - 管理评分系统的配置参数")
        print("2. 版本管理 - 记录配置变更历史，支持回滚")
        print("3. A/B测试 - 对比不同配置的效果")
        print("4. 自动优化 - 使用算法自动寻找最优配置")
        print("5. 回测验证 - 基于历史数据验证评分系统")
        print("6. 实时监控 - 实时监控龙头股并预警")
        print("7. 报告生成 - 自动生成各类分析报告")
        print("\n详细文档请访问: https://github.com/your-repo")
        print("=" * 70)
    
    def _view_popularity_rank(self):
        """查看人气榜单"""
        print("\n" + "=" * 70)
        print("🔥 人气榜单")
        print("=" * 70)
        
        try:
            sys.path.insert(0, os.path.join(self.workspace_dir, 'core'))
            from popularity_fetcher import PopularityFetcher
            
            fetcher = PopularityFetcher()
            rank_data = fetcher.fetch_eastmoney_rank(limit=50)
            
            if rank_data:
                print("\n📊 东方财富人气榜 TOP 50:")
                print("-" * 70)
                
                for item in rank_data:
                    rank = item['rank']
                    name = item['name']
                    code = item['code']
                    
                    # 格式化输出
                    print(f"  {rank:2d}. {name:8s} ({code:10s})")
                
                print("-" * 70)
                print(f"✅ 共 {len(rank_data)} 只股票")
            else:
                print("⚠️  暂无人气榜数据")
        
        except ImportError:
            print("❌ 人气榜模块未安装")
        except Exception as e:
            print(f"❌ 获取人气榜失败: {e}")
    
    def _manage_tracking(self):
        """历史跟踪管理"""
        print("\n" + "=" * 70)
        print("📍 历史跟踪管理")
        print("=" * 70)
        
        try:
            sys.path.insert(0, os.path.join(self.workspace_dir, 'core'))
            from tracking_system import TrackingSystem
            
            tracker = TrackingSystem()
            
            # 显示状态
            tracker.print_status()
            
            print("\n请选择操作:")
            print("  1. 查看等待跟踪的股票")
            print("  2. 查看跟踪中的股票")
            print("  3. 查看已完成的跟踪")
            print("  4. 生成跟踪报告")
            print("  0. 返回")
            
            choice = input("\n请选择: ").strip()
            
            if choice == '1':
                print("\n等待跟踪的股票:")
                waiting = tracker.get_waiting_stocks()
                if waiting:
                    for stock in waiting:
                        print(f"  • {stock['name']} ({stock['code']})")
                else:
                    print("  暂无等待跟踪的股票")
            
            elif choice == '2':
                print("\n跟踪中的股票:")
                tracking = tracker.get_tracking_stocks()
                if tracking:
                    for stock in tracking:
                        days_left = stock.get('tracking_days_left', 0)
                        print(f"  • {stock['name']} ({stock['code']}) - 剩余{days_left}天")
                else:
                    print("  暂无跟踪中的股票")
            
            elif choice == '3':
                print("\n已完成的跟踪 (最近10只):")
                completed = tracker.get_completed_stocks(limit=10)
                if completed:
                    for stock in completed:
                        print(f"  • {stock['name']} ({stock['code']}) - 已完成")
                else:
                    print("  暂无已完成的跟踪")
            
            elif choice == '4':
                print("\n生成跟踪报告...")
                tracker.generate_report()
                print("✅ 报告已生成")
        
        except ImportError:
            print("❌ 跟踪系统模块未安装")
        except Exception as e:
            print(f"❌ 操作失败: {e}")
    
    def _view_automation_status(self):
        """查看自动化任务状态"""
        print("\n" + "=" * 70)
        print("🤖 自动化任务状态")
        print("=" * 70)
        
        try:
            import subprocess
            
            # 检查定时任务
            result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
            
            print("\n📅 定时任务:")
            print("-" * 70)
            
            if 'fetch_data.py' in result.stdout:
                print("✅ 数据获取任务: 每天15:55运行")
            else:
                print("❌ 数据获取任务: 未配置")
            
            if 'daily_auto_scoring.py' in result.stdout:
                print("✅ 自动评分任务: 每天16:00运行")
            else:
                print("❌ 自动评分任务: 未配置")
            
            if 'daily_hotsearch.py' in result.stdout:
                print("✅ 热搜推送任务: 每天08:30运行")
            else:
                print("❌ 热搜推送任务: 未配置")
            
            # 检查最近运行日志
            print("\n📄 最近运行日志:")
            print("-" * 70)
            
            log_files = [
                ('/tmp/fetch_data.log', '数据获取'),
                ('/tmp/daily_scoring.log', '自动评分'),
                ('/tmp/daily_hotsearch.log', '热搜推送')
            ]
            
            for log_path, log_name in log_files:
                if os.path.exists(log_path):
                    print(f"\n{log_name} ({log_path}):")
                    with open(log_path, 'r') as f:
                        lines = f.readlines()
                        # 显示最后5行
                        for line in lines[-5:]:
                            print(f"  {line.rstrip()}")
                else:
                    print(f"\n{log_name}: 暂无日志")
            
            print("-" * 70)
        
        except Exception as e:
            print(f"❌ 获取状态失败: {e}")


def main():
    """主函数"""
    system = DragonStockSystem()
    system.run()


if __name__ == "__main__":
    main()
