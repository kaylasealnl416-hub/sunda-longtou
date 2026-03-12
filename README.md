# 🎯 龙头股评分系统

基于威科夫量价理论的智能龙头股评分与监控系统

## 📋 目录

- [系统简介](#系统简介)
- [核心功能](#核心功能)
- [系统架构](#系统架构)
- [快速开始](#快速开始)
- [模块说明](#模块说明)
- [使用指南](#使用指南)
- [配置说明](#配置说明)
- [开发计划](#开发计划)

---

## 系统简介

龙头股评分系统是一个基于威科夫量价理论的智能股票评分系统，通过多维度分析为龙头股打分，帮助投资者识别优质标的。

### 核心理念

- **量价分析** - 基于威科夫百年验证的量价理论
- **多维评分** - 情绪、资金、技术、题材、基本面五大维度
- **动态调整** - 根据市场情绪周期动态调整评分
- **数据驱动** - 通过回测和A/B测试持续优化

### 评分维度

| 维度 | 权重 | 说明 |
|------|------|------|
| 📊 情绪面 | 30分 | 情绪周期 + 量比分析 |
| 💰 资金面 | 30分 | 威科夫量价 + 资金流向 + 大单占比 |
| 📈 技术面 | 25分 | 连板高度 + K线形态 + 趋势 |
| 🎯 题材面 | 10分 | 主线题材 + 人气热度 |
| 📋 基本面 | 5分 | 业绩连续性 + 业绩增长 |

---

## 核心功能

### 1. 📊 配置管理

- ✅ 可视化配置编辑器（Web界面）
- ✅ 树状图展示评分结构
- ✅ 实时修改权重和分数
- ✅ 配置验证和导出

**使用方式：**
```bash
# 打开Web配置器
open web/standalone.html

# 或使用命令行
python core/config_manager.py
```

### 2. 📚 版本管理

- ✅ 自动记录配置变更
- ✅ 版本对比和差异分析
- ✅ 一键回滚到历史版本
- ✅ 版本标签和备注

**使用方式：**
```python
from core.version_manager import VersionManager

manager = VersionManager()
manager.create_version(config, message="优化威科夫权重", tag="v1.1")
manager.print_history()
manager.rollback("v1")
```

### 3. 🧪 A/B测试

- ✅ 创建配置对比测试
- ✅ 记录测试结果
- ✅ 统计分析（胜率、收益率）
- ✅ 自动判断最优配置

**使用方式：**
```python
from core.ab_test_manager import ABTestManager

manager = ABTestManager()
test_id = manager.create_test("威科夫权重测试", config_a, config_b)
manager.add_result(test_id, "config_a", "600905", "三峡能源", 79.83, 15.2)
manager.print_comparison(test_id)
```

### 4. 🔧 自动优化

- ✅ 网格搜索最优参数
- ✅ 遗传算法优化
- ✅ 贝叶斯优化
- ✅ 保存优化结果

**使用方式：**
```python
from core.auto_optimizer import AutoOptimizer

optimizer = AutoOptimizer()
best_config, score = optimizer.genetic_algorithm(
    evaluate_fn=your_backtest_function,
    population_size=20,
    generations=50
)
```

### 5. 📤 导入导出

- ✅ Excel格式导入导出
- ✅ CSV格式导入导出
- ✅ 配置模板库
- ✅ 默认模板（保守型、激进型、平衡型）

**使用方式：**
```python
from core.import_export_manager import ImportExportManager

manager = ImportExportManager()
manager.export_to_excel(config, "config.xlsx")
config = manager.import_from_excel("config.xlsx")
manager.save_as_template(config, "my_template")
```

### 6. 🔄 回测验证

- ✅ 历史数据回测
- ✅ 评分系统验证
- ✅ 收益率计算
- ✅ 性能指标统计（胜率、夏普比率、最大回撤）
- ✅ 回测报告生成

**使用方式：**
```python
from core.backtest_engine import BacktestEngine

engine = BacktestEngine()
result = engine.run_backtest(
    start_date='2024-01-01',
    end_date='2024-03-31',
    score_threshold=70.0,
    holding_days=5
)
engine.export_report(result)
```

### 7. 📡 实时监控

- ✅ 实时监控龙头股
- ✅ 自动评分
- ✅ 异常预警
- ✅ 推送通知

**使用方式：**
```python
from core.realtime_monitor import RealtimeMonitor

monitor = RealtimeMonitor(check_interval=60)
monitor.add_to_watchlist('600905', '三峡能源')
monitor.start_monitoring()
```

### 8. 📝 报告生成

- ✅ 每日龙头股排行榜
- ✅ 市场情绪分析报告
- ✅ 个股详细分析报告
- ✅ 周报/月报生成
- ✅ 多格式导出（Markdown/HTML）

**使用方式：**
```python
from core.report_generator import ReportGenerator

generator = ReportGenerator()
generator.generate_daily_report(stocks_data)
generator.generate_weekly_report(start_date, end_date, daily_data)
generator.generate_stock_analysis(stock_data)
```

---

## 系统架构

```
sunda-longtou/
├── config/                          # 配置文件
│   ├── scoring_config.json          # 主配置文件
│   ├── versions/                    # 版本历史
│   ├── ab_tests/                    # A/B测试数据
│   └── templates/                   # 配置模板库
│
├── core/                            # 核心模块
│   ├── wyckoff_analyzer.py          # 威科夫量价分析
│   ├── dragon_scorer_v6.py          # 评分系统V6
│   ├── config_manager.py            # 配置管理器
│   ├── version_manager.py           # 版本管理
│   ├── ab_test_manager.py           # A/B测试
│   ├── auto_optimizer.py            # 自动优化
│   ├── import_export_manager.py     # 导入导出
│   ├── backtest_engine.py           # 回测引擎
│   ├── realtime_monitor.py          # 实时监控
│   └── report_generator.py          # 报告生成
│
├── web/                             # Web界面
│   ├── app.py                       # Flask服务器
│   ├── standalone.html              # 独立版配置器
│   └── templates/
│       └── index.html               # Web界面
│
├── data/                            # 数据目录
│   └── historical/                  # 历史数据
│
├── output/                          # 输出目录
│   ├── backtest/                    # 回测报告
│   └── reports/                     # 分析报告
│
├── main.py                          # 主控制器
└── README.md                        # 本文档
```

---

## 快速开始

### 1. 安装依赖

```bash
pip install pandas numpy openpyxl flask
```

### 2. 启动Web配置器

```bash
# 方式1：独立HTML版本（推荐）
open web/standalone.html

# 方式2：Flask服务器版本
cd web
python app.py
# 访问 http://localhost:5000
```

### 3. 使用主控制器

```bash
python main.py
```

### 4. 使用Python API

```python
from core.dragon_scorer_v6 import DragonScorer

scorer = DragonScorer()
score = scorer.calculate_score(stock_data)
print(f"评分: {score}")
```

---

## 模块说明

### 配置管理器 (config_manager.py)

管理评分系统的配置参数，提供可视化编辑和验证功能。

**主要方法：**
- `print_tree()` - 打印配置树
- `update_dimension_weight()` - 更新维度权重
- `validate_config()` - 验证配置合法性
- `export_markdown()` - 导出Markdown文档

### 版本管理器 (version_manager.py)

记录配置变更历史，支持版本对比和回滚。

**主要方法：**
- `create_version()` - 创建新版本
- `rollback()` - 回滚到指定版本
- `compare_versions()` - 对比两个版本
- `print_history()` - 打印版本历史

### A/B测试管理器 (ab_test_manager.py)

对比不同配置的效果，找出最优配置。

**主要方法：**
- `create_test()` - 创建A/B测试
- `add_result()` - 添加测试结果
- `compare_results()` - 对比测试结果
- `print_comparison()` - 打印对比结果

### 自动优化器 (auto_optimizer.py)

使用算法自动寻找最优配置参数。

**主要方法：**
- `grid_search()` - 网格搜索
- `genetic_algorithm()` - 遗传算法
- `bayesian_optimization()` - 贝叶斯优化

### 导入导出管理器 (import_export_manager.py)

支持多种格式的配置导入导出。

**主要方法：**
- `export_to_excel()` - 导出到Excel
- `import_from_excel()` - 从Excel导入
- `save_as_template()` - 保存为模板
- `load_template()` - 加载模板

### 回测引擎 (backtest_engine.py)

基于历史数据验证评分系统的有效性。

**主要方法：**
- `run_backtest()` - 运行回测
- `export_report()` - 导出回测报告
- `compare_configs()` - 对比多个配置

### 实时监控器 (realtime_monitor.py)

实时监控龙头股并发送预警。

**主要方法：**
- `start_monitoring()` - 启动监控
- `stop_monitoring()` - 停止监控
- `add_to_watchlist()` - 添加到监控列表
- `get_latest_scores()` - 获取最新评分

### 报告生成器 (report_generator.py)

自动生成各类分析报告。

**主要方法：**
- `generate_daily_report()` - 生成每日报告
- `generate_weekly_report()` - 生成周报
- `generate_stock_analysis()` - 生成个股分析

---

## 使用指南

### 场景1：调整评分配置

1. 打开 `web/standalone.html`
2. 修改各维度权重和评分规则
3. 点击"验证配置"确保合法性
4. 点击"下载配置"保存

### 场景2：回测验证配置

```python
from core.backtest_engine import BacktestEngine

engine = BacktestEngine()
result = engine.run_backtest(
    start_date='2024-01-01',
    end_date='2024-03-31',
    score_threshold=70.0
)

print(f"胜率: {result['statistics']['win_rate']:.2f}%")
print(f"平均收益: {result['statistics']['avg_return']:.2f}%")
```

### 场景3：A/B测试对比

```python
from core.ab_test_manager import ABTestManager

manager = ABTestManager()

# 创建测试
test_id = manager.create_test(
    name="威科夫权重测试",
    config_a=current_config,
    config_b=new_config
)

# 添加测试结果（需要实际交易数据）
manager.add_result(test_id, "config_a", "600905", "三峡能源", 79.83, 15.2)
manager.add_result(test_id, "config_b", "600905", "三峡能源", 82.50, 18.5)

# 对比结果
manager.print_comparison(test_id)
```

### 场景4：实时监控

```python
from core.realtime_monitor import RealtimeMonitor

monitor = RealtimeMonitor(check_interval=60)

# 添加监控股票
monitor.add_to_watchlist('600905', '三峡能源')
monitor.add_to_watchlist('000001', '平安银行')

# 启动监控
monitor.start_monitoring()

# 查看状态
monitor.print_status()
```

---

## 配置说明

### 评分配置文件 (scoring_config.json)

```json
{
  "version": "6.0",
  "total_score": 100,
  "dimensions": [
    {
      "id": "emotion",
      "name": "情绪面",
      "weight": 30,
      "sub_dimensions": [...]
    }
  ]
}
```

### 配置项说明

- `version` - 配置版本号
- `total_score` - 总分（固定100分）
- `dimensions` - 评分维度列表
  - `id` - 维度ID
  - `name` - 维度名称
  - `weight` - 维度权重
  - `sub_dimensions` - 子维度列表
    - `scoring_rules` - 评分规则

---

## 开发计划

### ✅ 已完成

- [x] 威科夫量价分析模块
- [x] 评分系统V6
- [x] Web可视化配置器
- [x] 版本管理系统
- [x] A/B测试系统
- [x] 自动优化系统
- [x] 导入导出系统
- [x] 回测框架
- [x] 实时监控系统
- [x] 报告生成系统
- [x] 主控制器

### 🚧 进行中

- [ ] 对接真实行情数据
- [ ] 完善回测数据准备
- [ ] 优化评分算法

### 📋 待开发

- [ ] 风险控制模块
- [ ] 仓位管理系统
- [ ] 交易信号生成
- [ ] 移动端App
- [ ] 数据可视化大屏
- [ ] 机器学习优化

---

## 贡献指南

欢迎提交Issue和Pull Request！

### 开发规范

1. 代码风格遵循PEP 8
2. 添加必要的注释和文档
3. 编写单元测试
4. 提交前运行测试

---

## 许可证

MIT License

---

## 联系方式

- GitHub: [your-repo]
- Email: [your-email]

---

**⚠️ 免责声明**

本系统仅供学习和研究使用，不构成任何投资建议。股市有风险，投资需谨慎。使用本系统进行投资决策的风险由使用者自行承担。
