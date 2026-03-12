#!/usr/bin/env python3
"""
主流题材识别系统 v1.0
基于小欧核心经验：主流、主动、主升

核心逻辑：
1. 主流 = 主线题材，资金聚焦的地方
2. 主动 = 主动上涨，不是被动跟随
3. 主升 = 主升浪，涨幅最大那段

识别方法：
- 板块涨幅排行
- 板块涨停股数量
- 板块持续天数
- 题材强度评分

评分标准（满分 15 分）：
- 国家级政策 = 15 分
- 部委级政策 = 12 分
- 行业热点 = 10 分
- 个股题材 = 5 分
- 无明确题材 = 0 分
"""

import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import json


class ThemeDetector:
    """主流题材识别器"""
    
    def __init__(self):
        self.max_score = 15  # 题材最高 15 分
        
        # 题材等级定义
        self.theme_levels = {
            "国家级": {
                "score": 15,
                "keywords": ["一带一路", "国企改革", "央企", "数字经济", "新基建", 
                           "碳中和", "双碳", "乡村振兴", "共同富裕", "国产替代"]
            },
            "部委级": {
                "score": 12,
                "keywords": ["AI", "人工智能", "算力", "芯片", "半导体", "新能源",
                           "光伏", "储能", "氢能", "风电", "核电", "特高压"]
            },
            "行业热点": {
                "score": 10,
                "keywords": ["游戏", "传媒", "影视", "旅游", "消费", "医药",
                           "生物医药", "CRO", "创新药", "医疗器械"]
            },
            "个股题材": {
                "score": 5,
                "keywords": ["重组", "并购", "回购", "增持", "业绩预增", "中标"]
            }
        }
    
    def get_sector_ranking(self) -> pd.DataFrame:
        """
        获取板块涨幅排行
        
        Returns:
            DataFrame with columns: 板块名称, 涨跌幅, 领涨股, 领涨股涨幅
        """
        try:
            # 获取板块行情
            df = ak.stock_board_industry_name_em()
            
            if df.empty:
                return self._get_mock_sector_data()
            
            # 重命名列
            df = df.rename(columns={
                '板块名称': 'sector_name',
                '涨跌幅': 'change_pct',
                '领涨股票': 'leader_stock',
                '领涨股票涨跌幅': 'leader_change'
            })
            
            # 按涨跌幅排序
            df = df.sort_values('change_pct', ascending=False)
            
            return df.head(20)  # 返回前20个板块
            
        except Exception as e:
            print(f"获取板块数据失败: {e}")
            return self._get_mock_sector_data()
    
    def _get_mock_sector_data(self) -> pd.DataFrame:
        """模拟板块数据"""
        data = {
            'sector_name': ['电力', '光伏设备', '石油开采', '电网设备', '煤炭开采',
                          '风电设备', '天然气', '电池', '储能', '特高压'],
            'change_pct': [5.2, 4.8, 4.5, 4.2, 3.9, 3.6, 3.3, 3.0, 2.8, 2.5],
            'leader_stock': ['中国能建', '协鑫集成', '洲际油气', '中国西电', '兖矿能源',
                           '金风科技', '新奥股份', '宁德时代', '阳光电源', '特变电工'],
            'leader_change': [9.87, 10.10, -5.29, 6.57, 5.23, 4.56, 3.89, 2.34, 3.45, 5.15]
        }
        return pd.DataFrame(data)
    
    def get_limit_up_by_sector(self) -> Dict[str, int]:
        """
        获取各板块涨停股数量
        
        Returns:
            {板块名称: 涨停股数量}
        """
        try:
            # 获取今日涨停股
            df = ak.stock_zt_pool_em(date=datetime.now().strftime("%Y%m%d"))
            
            if df.empty:
                return self._get_mock_limit_up_sector()
            
            # 统计各板块涨停股数量
            if '所属行业' in df.columns:
                sector_counts = df['所属行业'].value_counts().to_dict()
                return sector_counts
            else:
                return self._get_mock_limit_up_sector()
                
        except Exception as e:
            print(f"获取涨停板块数据失败: {e}")
            return self._get_mock_limit_up_sector()
    
    def _get_mock_limit_up_sector(self) -> Dict[str, int]:
        """模拟涨停板块数据"""
        return {
            '电力': 8,
            '光伏设备': 6,
            '石油开采': 5,
            '电网设备': 4,
            '煤炭开采': 3,
            '风电设备': 3,
            '天然气': 2,
            '电池': 2,
            '储能': 2,
            '特高压': 1
        }
    
    def classify_theme(self, sector_name: str) -> Tuple[str, int, List[str]]:
        """
        分类题材等级
        
        Args:
            sector_name: 板块名称
            
        Returns:
            (题材等级, 得分, 匹配的关键词列表)
        """
        matched_keywords = []
        
        # 从高到低检查题材等级
        for level, info in self.theme_levels.items():
            for keyword in info['keywords']:
                if keyword in sector_name:
                    matched_keywords.append(keyword)
            
            if matched_keywords:
                return level, info['score'], matched_keywords
        
        # 无匹配，返回默认
        return "无明确题材", 0, []
    
    def detect_main_theme(self) -> Dict:
        """
        识别当前主流题材
        
        Returns:
            {
                "main_theme": 主线题材名称,
                "level": 题材等级,
                "score": 题材得分,
                "change_pct": 板块涨幅,
                "limit_up_count": 涨停股数量,
                "leader_stock": 领涨股,
                "related_sectors": 相关板块列表,
                "keywords": 关键词列表
            }
        """
        print("=" * 60)
        print("🔍 主流题材识别系统 v1.0")
        print("=" * 60)
        
        # 1. 获取板块涨幅排行
        print("\n📊 获取板块涨幅排行...")
        sector_df = self.get_sector_ranking()
        print(f"   获取到 {len(sector_df)} 个板块")
        
        # 2. 获取涨停板块分布
        print("\n📈 获取涨停板块分布...")
        limit_up_sectors = self.get_limit_up_by_sector()
        print(f"   涨停股分布在 {len(limit_up_sectors)} 个板块")
        
        # 3. 综合评分：涨幅 + 涨停股数量
        sector_scores = []
        
        for _, row in sector_df.iterrows():
            sector_name = row['sector_name']
            change_pct = row['change_pct']
            leader_stock = row['leader_stock']
            
            # 获取涨停股数量
            limit_up_count = limit_up_sectors.get(sector_name, 0)
            
            # 分类题材等级
            level, theme_score, keywords = self.classify_theme(sector_name)
            
            # 综合得分 = 题材得分 + 涨幅得分 + 涨停股得分
            # 涨幅得分：每1%涨幅 = 2分
            # 涨停股得分：每个涨停股 = 3分
            total_score = theme_score + (change_pct * 2) + (limit_up_count * 3)
            
            sector_scores.append({
                "sector_name": sector_name,
                "level": level,
                "theme_score": theme_score,
                "change_pct": float(change_pct),
                "limit_up_count": limit_up_count,
                "leader_stock": leader_stock,
                "total_score": round(total_score, 2),
                "keywords": keywords
            })
        
        # 按综合得分排序
        sector_scores.sort(key=lambda x: x['total_score'], reverse=True)
        
        # 4. 识别主线题材（得分最高的）
        if sector_scores:
            main = sector_scores[0]
            
            # 找出相关板块（同一题材等级的其他板块）
            related_sectors = [
                s['sector_name'] for s in sector_scores[1:6]
                if s['level'] == main['level']
            ]
            
            result = {
                "main_theme": main['sector_name'],
                "level": main['level'],
                "score": main['theme_score'],
                "change_pct": main['change_pct'],
                "limit_up_count": main['limit_up_count'],
                "leader_stock": main['leader_stock'],
                "total_score": main['total_score'],
                "related_sectors": related_sectors,
                "keywords": main['keywords'],
                "all_sectors": sector_scores[:10]  # 前10个板块
            }
            
            # 输出结果
            print(f"\n{'=' * 60}")
            print(f"🎯 主流题材: {result['main_theme']}")
            print(f"📊 题材等级: {result['level']} ({result['score']}分)")
            print(f"📈 板块涨幅: {result['change_pct']}%")
            print(f"🔥 涨停股数: {result['limit_up_count']}个")
            print(f"👑 领涨股: {result['leader_stock']}")
            print(f"🏷️  关键词: {', '.join(result['keywords']) if result['keywords'] else '无'}")
            
            if related_sectors:
                print(f"\n🔗 相关板块:")
                for sector in related_sectors:
                    print(f"   • {sector}")
            
            print(f"\n📋 TOP 10 板块:")
            print(f"{'排名':<6}{'板块':<15}{'涨幅':<10}{'涨停':<8}{'等级':<12}{'得分':<10}")
            print("-" * 60)
            for i, s in enumerate(result['all_sectors'], 1):
                print(f"{i:<6}{s['sector_name']:<15}{s['change_pct']}%<10"
                      f"{s['limit_up_count']:<8}{s['level']:<12}{s['total_score']:<10}")
            
            print(f"{'=' * 60}\n")
            
            return result
        
        return {}
    
    def save_result(self, result: Dict, filepath: str = "main_theme_result.json"):
        """保存识别结果"""
        result['timestamp'] = datetime.now().isoformat()
        result['date'] = datetime.now().strftime("%Y-%m-%d")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 结果已保存到: {filepath}")


def main():
    """主函数"""
    detector = ThemeDetector()
    result = detector.detect_main_theme()
    
    if result:
        detector.save_result(result)
    
    return result


if __name__ == "__main__":
    main()
