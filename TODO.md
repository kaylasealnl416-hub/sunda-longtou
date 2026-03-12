# 龙头股评分系统 - 待开发功能清单

## 📋 任务列表

### 1. ✅ 历史跟踪功能（重要！）

**需求描述：**
- 对首板涨停股进行跟踪
- 如果次日断板，需要连续追踪3个交易日
- 记录每日的评分变化
- 分析断板后的走势

**实现要点：**
- 建立跟踪数据库（tracking_db.json）
- 每日自动检查昨日首板今日是否断板
- 断板后启动3日追踪计划
- 记录每日评分、涨跌幅、成交额等关键数据

**数据结构：**
```json
{
  "tracking_stocks": [
    {
      "code": "601016",
      "name": "节能风电",
      "first_board_date": "2026-03-12",
      "break_board_date": "2026-03-13",
      "tracking_days": 3,
      "daily_records": [
        {
          "date": "2026-03-13",
          "score": 65,
          "change_pct": -5.2,
          "turnover": 15.5,
          "status": "断板"
        }
      ]
    }
  ]
}
```

**文件位置：**
- `/root/.openclaw/workspace/sunda-longtou/core/tracking_system.py`
- `/root/.openclaw/workspace/sunda-longtou/data/tracking_db.json`

---

### 2. ⏸️ 赚钱效应统计（暂缓）

**需求描述：**
- 获取首板晋级成功率数据
- 通过API接口直接获取

**实现方案：**
- 优先尝试从AkShare获取
- 备选：东方财富API
- 备选：同花顺API

**API探索：**
```python
import akshare as ak

# 尝试获取涨停统计数据
df = ak.stock_zt_pool_em(date='20260312')
# 查看是否有晋级成功率字段

# 或者通过历史数据计算
# 统计昨日首板今日表现
```

**状态：** 待API探索

---

### 3. ✅ 自动化每日复盘（必须功能）

**需求描述：**
- 每天收盘后自动运行评分系统
- 生成TOP榜单
- 发送报告到飞书

**实现方案：**
- 使用crontab定时任务
- 每天15:30（收盘后）自动运行

**Crontab配置：**
```bash
# 每日龙头股评分 - 每天15:30
30 15 * * 1-5 cd /root/.openclaw/workspace/sunda-longtou && python3 scripts/daily_auto_scoring.py >> /tmp/daily_scoring.log 2>&1
```

**脚本功能：**
1. 获取当日涨停板数据
2. 对所有涨停股评分
3. 生成TOP 8详细报告
4. 发送到飞书
5. 更新历史跟踪数据

**文件位置：**
- `/root/.openclaw/workspace/sunda-longtou/scripts/daily_auto_scoring.py`

---

### 4. 🔍 人气榜单集成

**需求描述：**
- 获取当天人气榜TOP 50数据
- 至少集成3个数据源

**数据源：**
1. **AkShare** - 优先尝试
2. **开盘啦** - 备选
3. **东方财富** - 备选
4. **同花顺** - 备选

**实现步骤：**

#### Step 1: 探索AkShare
```python
import akshare as ak

# 尝试查找人气榜相关接口
# 可能的函数名：
# - stock_hot_rank_em()
# - stock_hot_rank_latest_em()
# - stock_attention_em()
```

#### Step 2: 东方财富API
```python
import requests

url = "http://push2.eastmoney.com/api/qt/clist/get"
params = {
    'pn': 1,
    'pz': 50,
    'po': 1,
    'fid': 'f3',  # 人气排序
    'fields': 'f12,f13,f14,f62,f184'
}
```

#### Step 3: 同花顺API
```python
# 需要抓包分析同花顺人气榜接口
```

#### Step 4: 开盘啦API
```python
# 需要抓包分析开盘啦人气榜接口
```

**数据结构：**
```json
{
  "date": "2026-03-12",
  "source": "eastmoney",
  "popularity_rank": [
    {
      "rank": 1,
      "code": "601016",
      "name": "节能风电",
      "popularity_score": 98.5,
      "attention_count": 125000
    }
  ]
}
```

**文件位置：**
- `/root/.openclaw/workspace/sunda-longtou/core/popularity_fetcher.py`
- `/root/.openclaw/workspace/sunda-longtou/data/popularity_rank.json`

---

## 📊 优先级排序

1. **P0 - 必须立即做**
   - ✅ 自动化每日复盘（任务3）

2. **P1 - 高优先级**
   - ✅ 历史跟踪功能（任务1）
   - 🔍 人气榜单集成（任务4）

3. **P2 - 中优先级**
   - ⏸️ 赚钱效应统计（任务2）- 依赖API探索

---

## 🗓️ 开发计划

### 第一阶段（今天完成）
- [x] 评分系统V6.0
- [x] TOP 8详细报告
- [ ] 自动化每日复盘脚本

### 第二阶段（明天）
- [ ] 历史跟踪功能
- [ ] 人气榜单集成（AkShare探索）

### 第三阶段（后天）
- [ ] 人气榜单集成（多数据源）
- [ ] 赚钱效应统计（API探索）

---

## 📝 注意事项

1. **历史跟踪功能**
   - 用户特别强调：首板断板后要追踪3个交易日
   - 这是之前提到过的需求，不要忘记

2. **自动化复盘**
   - 这是系统的基础功能，必须有
   - 每天15:30自动运行

3. **人气榜单**
   - 至少要有3个数据源
   - 优先尝试AkShare

4. **数据持久化**
   - 所有历史数据都要保存
   - 便于后续分析和回测

---

## 🔗 相关文件

- 主配置：`/root/.openclaw/workspace/sunda-longtou/config/scoring_config.json`
- 评分系统：`/root/.openclaw/workspace/sunda-longtou/core/dragon_scorer_v6.py`
- 威科夫分析：`/root/.openclaw/workspace/sunda-longtou/core/wyckoff_analyzer.py`
- 数据API文档：`/root/.openclaw/workspace/sunda-longtou/docs/DATA_API.md`

---

**最后更新：** 2026-03-12 18:07  
**状态：** 任务已记录，等待开发
