# 股票数据API接口汇总

## 📊 数据需求与API对应关系

### 1. 基础行情数据 ✅ (已有)

**数据源: AkShare (免费)**
- 涨停板数据 ✅
- 基本行情数据 ✅
- 连板数据 ✅

```python
import akshare as ak

# 涨停板数据
df = ak.stock_zt_pool_em(date='20260312')

# 实时行情
df = ak.stock_zh_a_spot_em()

# 个股行情
df = ak.stock_zh_a_hist(symbol="601016", period="daily")
```

---

### 2. 分时图数据 (威科夫量价分析)

#### 方案A: AkShare (免费) ⭐ 推荐
```python
import akshare as ak

# 分时图数据
df = ak.stock_intraday_em(symbol="601016")
# 返回: 时间、价格、成交量、成交额
```

#### 方案B: Tushare (需注册，有积分限制)
```python
import tushare as ts

pro = ts.pro_api('你的token')
df = pro.stk_mins(ts_code='601016.SH', freq='1min')
```

---

### 3. 资金流向数据

#### 方案A: AkShare (免费) ⭐ 推荐
```python
import akshare as ak

# 个股资金流
df = ak.stock_individual_fund_flow_rank(symbol="即时")

# 主力资金流向
df = ak.stock_main_fund_flow_em(symbol="601016")
```

#### 方案B: 东方财富网API (免费，需爬虫)
```python
import requests

url = "http://push2.eastmoney.com/api/qt/stock/fflow/kline/get"
params = {
    'secid': '1.601016',  # 1.上证 0.深证
    'fields1': 'f1,f2,f3,f7',
    'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63'
}
resp = requests.get(url, params=params)
```

---

### 4. 大单数据

#### 方案A: AkShare (免费) ⭐ 推荐
```python
import akshare as ak

# 大单追踪
df = ak.stock_changes_em(symbol="大单")

# 龙虎榜数据
df = ak.stock_lhb_detail_em(symbol="601016", start_date="20260301", end_date="20260312")
```

#### 方案B: 新浪财经API (免费)
```python
import requests

url = f"http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_Bill.GetBillList"
params = {
    'symbol': 'sh601016',
    'num': 60,
    'sort': 'ticktime',
    'asc': 0
}
```

---

### 5. K线历史数据

#### 方案A: AkShare (免费) ⭐ 推荐
```python
import akshare as ak

# 日K线
df = ak.stock_zh_a_hist(symbol="601016", period="daily", adjust="qfq")

# 周K线
df = ak.stock_zh_a_hist(symbol="601016", period="weekly", adjust="qfq")

# 月K线
df = ak.stock_zh_a_hist(symbol="601016", period="monthly", adjust="qfq")
```

#### 方案B: Tushare (需注册)
```python
import tushare as ts

pro = ts.pro_api('你的token')
df = pro.daily(ts_code='601016.SH', start_date='20260101', end_date='20260312')
```

---

### 6. 题材标签数据

#### 方案A: AkShare (免费) ⭐ 推荐
```python
import akshare as ak

# 概念板块
df = ak.stock_board_concept_name_em()

# 个股所属概念
df = ak.stock_board_concept_cons_em(symbol="风电")

# 行业板块
df = ak.stock_board_industry_name_em()
```

#### 方案B: 东方财富网 (爬虫)
```python
import requests

url = "http://push2.eastmoney.com/api/qt/slist/get"
params = {
    'spt': 3,
    'secid': '1.601016',
    'fields': 'f12,f13,f14,f62,f184,f225'
}
```

---

### 7. 财务数据 (基本面)

#### 方案A: AkShare (免费) ⭐ 推荐
```python
import akshare as ak

# 业绩报表
df = ak.stock_financial_report_sina(stock="sh601016", symbol="业绩报表")

# 利润表
df = ak.stock_profit_sheet_by_report_em(symbol="601016")

# 资产负债表
df = ak.stock_balance_sheet_by_report_em(symbol="601016")

# 现金流量表
df = ak.stock_cash_flow_sheet_by_report_em(symbol="601016")
```

#### 方案B: Tushare (需注册)
```python
import tushare as ts

pro = ts.pro_api('你的token')

# 利润表
df = pro.income(ts_code='601016.SH', period='20231231')

# 资产负债表
df = pro.balancesheet(ts_code='601016.SH', period='20231231')
```

---

### 8. 市场情绪数据

#### 方案A: AkShare (免费) ⭐ 推荐
```python
import akshare as ak

# 市场总貌
df = ak.stock_market_activity_legu()

# 涨跌停统计
df = ak.stock_zt_pool_em(date='20260312')
df_dt = ak.stock_dt_pool_em(date='20260312')

# 两市成交额
df = ak.stock_market_fund_flow()
```

---

### 9. 社交媒体热度 (人气)

#### 方案A: 雪球API (需爬虫)
```python
import requests

# 股票热度
url = f"https://stock.xueqiu.com/v5/stock/hot_stock/list.json"
headers = {
    'User-Agent': 'Mozilla/5.0',
    'Cookie': '你的cookie'
}
```

#### 方案B: 东方财富股吧 (爬虫)
```python
import requests

url = f"http://guba.eastmoney.com/list,601016.html"
```

---

## 🎯 推荐方案

### 方案1: 纯AkShare (免费，推荐) ⭐⭐⭐⭐⭐

**优点:**
- ✅ 完全免费
- ✅ 无需注册
- ✅ 数据全面
- ✅ 更新及时
- ✅ 易于使用

**缺点:**
- ⚠️ 部分数据可能有延迟
- ⚠️ 依赖网络稳定性

**覆盖率:**
- 基础行情 ✅
- 分时图 ✅
- 资金流向 ✅
- 大单数据 ✅
- K线数据 ✅
- 题材标签 ✅
- 财务数据 ✅
- 市场情绪 ✅

---

### 方案2: AkShare + Tushare (部分收费)

**优点:**
- ✅ 数据更全面
- ✅ 历史数据更完整
- ✅ 数据质量更高

**缺点:**
- ❌ Tushare需要积分
- ❌ 高级数据需要付费
- ❌ 需要注册认证

---

### 方案3: 自建爬虫 (不推荐)

**优点:**
- ✅ 数据最全
- ✅ 可定制化

**缺点:**
- ❌ 开发成本高
- ❌ 维护成本高
- ❌ 容易被封IP
- ❌ 法律风险

---

## 📝 实施建议

### 第一阶段: 使用AkShare (立即可用)

```python
# 安装
pip install akshare

# 测试
import akshare as ak
df = ak.stock_zh_a_spot_em()
print(df.head())
```

### 第二阶段: 集成到评分系统

1. 创建数据获取模块 `data_fetcher.py`
2. 封装各类数据获取函数
3. 添加缓存机制（避免频繁请求）
4. 集成到 `dragon_scorer_v6.py`

### 第三阶段: 优化与扩展

1. 添加数据验证
2. 异常处理
3. 数据更新策略
4. 性能优化

---

## 🔗 相关资源

- **AkShare文档**: https://akshare.akfamily.xyz/
- **Tushare文档**: https://tushare.pro/document/2
- **东方财富API**: (需要自己抓包分析)

---

## ⚠️ 注意事项

1. **频率限制**: 不要频繁请求，建议加缓存
2. **数据延迟**: 免费数据可能有1-5分钟延迟
3. **法律合规**: 仅用于个人学习研究
4. **数据准确性**: 建议多源验证
5. **IP封禁**: 使用代理池或限制请求频率

---

## 💡 下一步

需要我帮你：
1. 创建数据获取模块？
2. 集成到评分系统？
3. 测试数据接口？
