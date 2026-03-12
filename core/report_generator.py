#!/usr/bin/env python3
"""
自动报告生成系统
Auto Report Generator for Dragon Stocks

功能：
1. 每日龙头股排行榜
2. 市场情绪分析报告
3. 个股详细分析报告
4. 周报/月报生成
5. 多格式导出（Markdown/HTML/PDF）
"""

import json
import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import pandas as pd
from pathlib import Path


class ReportGenerator:
    """报告生成器"""
    
    def __init__(
        self,
        config_path: str = None,
        output_dir: str = None,
        template_dir: str = None
    ):
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__), 
                '../config/scoring_config.json'
            )
        if output_dir is None:
            output_dir = os.path.join(
                os.path.dirname(__file__), 
                '../output/reports'
            )
        if template_dir is None:
            template_dir = os.path.join(
                os.path.dirname(__file__), 
                '../templates/reports'
            )
        
        self.config_path = config_path
        self.output_dir = output_dir
        self.template_dir = template_dir
        
        # 确保目录存在
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(template_dir, exist_ok=True)
        
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """加载配置"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def generate_daily_report(
        self,
        stocks_data: List[Dict],
        date: str = None
    ) -> str:
        """
        生成每日龙头股报告
        
        Args:
            stocks_data: 股票数据列表
            date: 日期，默认今天
        
        Returns:
            报告文件路径
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        print(f"📝 生成每日报告: {date}")
        
        # 按评分排序
        stocks_data.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        # 生成Markdown报告
        report = self._generate_daily_markdown(stocks_data, date)
        
        # 保存报告
        output_path = os.path.join(
            self.output_dir,
            f'daily_report_{date}.md'
        )
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"✅ 报告已生成: {output_path}")
        
        # 同时生成HTML版本
        html_path = output_path.replace('.md', '.html')
        self._markdown_to_html(report, html_path, f"龙头股日报 - {date}")
        
        return output_path
    
    def _generate_daily_markdown(self, stocks_data: List[Dict], date: str) -> str:
        """生成每日Markdown报告"""
        report = f"""# 🎯 龙头股日报

**日期:** {date}  
**生成时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**评分系统版本:** {self.config.get('version', 'N/A')}

---

## 📊 市场概况

- **监控股票数:** {len(stocks_data)}只
- **S级以上:** {len([s for s in stocks_data if s.get('score', 0) >= 80])}只
- **A级以上:** {len([s for s in stocks_data if s.get('score', 0) >= 70])}只
- **平均评分:** {sum(s.get('score', 0) for s in stocks_data) / len(stocks_data):.2f}分

---

## 🏆 龙头股排行榜 TOP 20

| 排名 | 股票代码 | 股票名称 | 评分 | 等级 | 涨幅 | 连板 | 情绪周期 |
|------|----------|----------|------|------|------|------|----------|
"""
        
        for i, stock in enumerate(stocks_data[:20], 1):
            score = stock.get('score', 0)
            grade = self._get_grade(score)
            
            report += f"| {i} | {stock.get('code', 'N/A')} | {stock.get('name', 'N/A')} | "
            report += f"{score:.2f} | {grade} | "
            report += f"{stock.get('change_pct', 0):.2f}% | "
            report += f"{stock.get('boards', 0)} | "
            report += f"{stock.get('emotion_cycle', 'N/A')} |\n"
        
        report += "\n---\n\n"
        
        # 详细分析 TOP 5
        report += "## 📈 重点关注 TOP 5\n\n"
        
        for i, stock in enumerate(stocks_data[:5], 1):
            report += f"### {i}. {stock.get('name', 'N/A')} ({stock.get('code', 'N/A')})\n\n"
            report += f"**综合评分:** {stock.get('score', 0):.2f}分 ({self._get_grade(stock.get('score', 0))})\n\n"
            
            # 各维度得分
            report += "**维度得分:**\n"
            report += f"- 📊 情绪面: {stock.get('emotion_score', 0):.2f}分\n"
            report += f"- 💰 资金面: {stock.get('capital_score', 0):.2f}分\n"
            report += f"- 📈 技术面: {stock.get('technical_score', 0):.2f}分\n"
            report += f"- 🎯 题材面: {stock.get('theme_score', 0):.2f}分\n"
            report += f"- 📋 基本面: {stock.get('fundamental_score', 0):.2f}分\n\n"
            
            # 关键指标
            report += "**关键指标:**\n"
            report += f"- 涨幅: {stock.get('change_pct', 0):.2f}%\n"
            report += f"- 连板: {stock.get('boards', 0)}天\n"
            report += f"- 量比: {stock.get('volume_ratio', 0):.2f}\n"
            report += f"- 换手率: {stock.get('turnover_rate', 0):.2f}%\n"
            report += f"- 情绪周期: {stock.get('emotion_cycle', 'N/A')}\n\n"
            
            # 操作建议
            report += "**操作建议:**\n"
            report += self._generate_suggestion(stock) + "\n\n"
            
            report += "---\n\n"
        
        # 市场情绪分析
        report += "## 🌡️ 市场情绪分析\n\n"
        report += self._analyze_market_emotion(stocks_data) + "\n\n"
        
        # 风险提示
        report += "## ⚠️ 风险提示\n\n"
        report += "- 本报告仅供参考，不构成投资建议\n"
        report += "- 股市有风险，投资需谨慎\n"
        report += "- 请根据自身风险承受能力做出投资决策\n\n"
        
        report += "---\n\n"
        report += f"*报告由龙头股评分系统自动生成 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
        
        return report
    
    def _get_grade(self, score: float) -> str:
        """获取评分等级"""
        if score >= 90:
            return "SSS"
        elif score >= 85:
            return "SS"
        elif score >= 80:
            return "S"
        elif score >= 75:
            return "A+"
        elif score >= 70:
            return "A"
        elif score >= 65:
            return "B+"
        elif score >= 60:
            return "B"
        else:
            return "C"
    
    def _generate_suggestion(self, stock: Dict) -> str:
        """生成操作建议"""
        score = stock.get('score', 0)
        emotion = stock.get('emotion_cycle', '')
        boards = stock.get('boards', 0)
        
        if score >= 85:
            if emotion == '冰点期':
                return "💎 **强烈关注** - 评分极高且处于冰点期，是最佳买入时机"
            elif emotion == '启动期':
                return "🚀 **积极买入** - 评分优秀且处于启动期，确定性高"
            elif emotion == '发酵期':
                return "📈 **持有为主** - 处于主升浪，可继续持有"
            elif emotion == '高潮期':
                return "⚠️  **谨慎追高** - 已进入高潮期，风险增加，建议观望"
            else:
                return "🔍 **密切关注** - 评分优秀，等待更好的入场时机"
        
        elif score >= 75:
            if boards >= 3:
                return "🎯 **适度参与** - 连板高度较高，可小仓位参与"
            else:
                return "👀 **观察为主** - 评分良好，可加入自选观察"
        
        elif score >= 60:
            return "📝 **列入备选** - 评分中等，可作为备选标的"
        
        else:
            return "❌ **暂不关注** - 评分较低，建议观望"
    
    def _analyze_market_emotion(self, stocks_data: List[Dict]) -> str:
        """分析市场情绪"""
        # 统计各情绪周期的股票数量
        emotion_count = {}
        for stock in stocks_data:
            emotion = stock.get('emotion_cycle', '未知')
            emotion_count[emotion] = emotion_count.get(emotion, 0) + 1
        
        total = len(stocks_data)
        
        analysis = "**情绪周期分布:**\n\n"
        
        for emotion, count in sorted(emotion_count.items(), key=lambda x: x[1], reverse=True):
            pct = count / total * 100 if total > 0 else 0
            analysis += f"- {emotion}: {count}只 ({pct:.1f}%)\n"
        
        analysis += "\n**市场判断:**\n\n"
        
        # 判断市场整体情绪
        if emotion_count.get('冰点期', 0) / total > 0.3:
            analysis += "🧊 市场处于冰点期，是布局良机\n"
        elif emotion_count.get('启动期', 0) / total > 0.3:
            analysis += "🚀 市场处于启动期，可积极参与\n"
        elif emotion_count.get('发酵期', 0) / total > 0.3:
            analysis += "📈 市场处于发酵期，主升浪行情\n"
        elif emotion_count.get('高潮期', 0) / total > 0.3:
            analysis += "⚠️  市场处于高潮期，注意风险\n"
        elif emotion_count.get('退潮期', 0) / total > 0.3:
            analysis += "📉 市场处于退潮期，建议观望\n"
        else:
            analysis += "🔄 市场情绪分化，结构性机会\n"
        
        return analysis
    
    def _markdown_to_html(self, markdown: str, output_path: str, title: str):
        """将Markdown转换为HTML"""
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{ color: #333; border-bottom: 3px solid #667eea; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; }}
        h3 {{ color: #666; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #667eea;
            color: white;
            font-weight: 600;
        }}
        tr:hover {{ background: #f5f5f5; }}
        code {{
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #999;
            font-size: 14px;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <pre style="white-space: pre-wrap; font-family: inherit;">{markdown}</pre>
        <div class="footer">
            报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </div>
</body>
</html>
"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"✅ HTML报告已生成: {output_path}")
    
    def generate_weekly_report(
        self,
        start_date: str,
        end_date: str,
        daily_data: Dict[str, List[Dict]]
    ) -> str:
        """
        生成周报
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            daily_data: 每日数据 {date: [stocks]}
        
        Returns:
            报告文件路径
        """
        print(f"📝 生成周报: {start_date} ~ {end_date}")
        
        report = f"""# 📅 龙头股周报

**周期:** {start_date} ~ {end_date}  
**生成时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 📊 本周概况

"""
        
        # 统计本周数据
        all_stocks = []
        for stocks in daily_data.values():
            all_stocks.extend(stocks)
        
        # 找出本周明星股（出现次数最多的前10）
        stock_count = {}
        for stock in all_stocks:
            code = stock.get('code')
            if code:
                if code not in stock_count:
                    stock_count[code] = {
                        'name': stock.get('name'),
                        'count': 0,
                        'max_score': 0,
                        'avg_score': 0,
                        'scores': []
                    }
                stock_count[code]['count'] += 1
                stock_count[code]['scores'].append(stock.get('score', 0))
                stock_count[code]['max_score'] = max(
                    stock_count[code]['max_score'],
                    stock.get('score', 0)
                )
        
        # 计算平均分
        for data in stock_count.values():
            data['avg_score'] = sum(data['scores']) / len(data['scores'])
        
        # 按出现次数排序
        top_stocks = sorted(
            stock_count.items(),
            key=lambda x: (x[1]['count'], x[1]['avg_score']),
            reverse=True
        )[:10]
        
        report += "## 🌟 本周明星股 TOP 10\n\n"
        report += "| 排名 | 股票代码 | 股票名称 | 上榜次数 | 最高评分 | 平均评分 |\n"
        report += "|------|----------|----------|----------|----------|----------|\n"
        
        for i, (code, data) in enumerate(top_stocks, 1):
            report += f"| {i} | {code} | {data['name']} | "
            report += f"{data['count']}次 | {data['max_score']:.2f} | {data['avg_score']:.2f} |\n"
        
        report += "\n---\n\n"
        report += "*周报由龙头股评分系统自动生成*\n"
        
        # 保存报告
        output_path = os.path.join(
            self.output_dir,
            f'weekly_report_{start_date}_to_{end_date}.md'
        )
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"✅ 周报已生成: {output_path}")
        
        return output_path
    
    def generate_stock_analysis(self, stock_data: Dict) -> str:
        """
        生成个股详细分析报告
        
        Args:
            stock_data: 股票数据
        
        Returns:
            报告文件路径
        """
        code = stock_data.get('code', 'N/A')
        name = stock_data.get('name', 'N/A')
        
        print(f"📝 生成个股分析: {name} ({code})")
        
        report = f"""# 📊 个股分析报告

## {name} ({code})

**生成时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 🎯 综合评分

**总分:** {stock_data.get('score', 0):.2f}分 / 100分  
**等级:** {self._get_grade(stock_data.get('score', 0))}

---

## 📈 各维度得分

| 维度 | 得分 | 权重 | 加权得分 |
|------|------|------|----------|
| 📊 情绪面 | {stock_data.get('emotion_score', 0):.2f} | 30% | {stock_data.get('emotion_score', 0) * 0.3:.2f} |
| 💰 资金面 | {stock_data.get('capital_score', 0):.2f} | 30% | {stock_data.get('capital_score', 0) * 0.3:.2f} |
| 📈 技术面 | {stock_data.get('technical_score', 0):.2f} | 25% | {stock_data.get('technical_score', 0) * 0.25:.2f} |
| 🎯 题材面 | {stock_data.get('theme_score', 0):.2f} | 10% | {stock_data.get('theme_score', 0) * 0.1:.2f} |
| 📋 基本面 | {stock_data.get('fundamental_score', 0):.2f} | 5% | {stock_data.get('fundamental_score', 0) * 0.05:.2f} |

---

## 💡 操作建议

{self._generate_suggestion(stock_data)}

---

*报告由龙头股评分系统自动生成*
"""
        
        # 保存报告
        output_path = os.path.join(
            self.output_dir,
            f'stock_analysis_{code}_{datetime.now().strftime("%Y%m%d")}.md'
        )
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"✅ 个股分析已生成: {output_path}")
        
        return output_path


def main():
    """测试函数"""
    generator = ReportGenerator()
    
    print("报告生成系统已初始化")
    print("\n功能列表:")
    print("1. generate_daily_report() - 生成每日报告")
    print("2. generate_weekly_report() - 生成周报")
    print("3. generate_stock_analysis() - 生成个股分析")


if __name__ == "__main__":
    main()
