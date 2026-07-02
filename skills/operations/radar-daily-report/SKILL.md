---
name: radar-daily-report
description: "从 PostgreSQL 读取今日雷达数据，分 4 条飞书消息发送（金价+AI+政治+GitHub），周六周报，月末月报"
metadata: { "openclaw": { "emoji": "📡" } }
---

# 雷达每日报告推送 Skill

每日 06:00 北京时间执行。从 `radar` 数据库读取今日数据，发送 **4 条独立飞书消息**。

## 核心铁律

⚠️ **禁止伪执行**：❌ 禁止用 bash `$()` 变量替换猜数据。✅ 每一步实际调 `exec` tool，读真实 `stdout`，基于真实数据组装消息。

## 消息结构（v4.2）

| 序号 | 板块 | 内容 |
|------|------|------|
| 消息一 | 💰 金价速览 | Markdown 表格：国际金价 + 国内金价 + 美10年TIPS收益率 |
| 消息二 | 🤖 AI 热讯 | 最近 24 小时热度最高 10 条，**每条附摘要**，按 `blacklist_score DESC` 排序 |
| 消息三 | 🌍 国际政治 | 按区域分类，每条「事件/背景/影响」三段展开 |
| 消息四 | 💻 GitHub 黑马 | 按黑马分排序 Top 10，**必须含 owner/repo 完整路径** |

## 执行步骤

### 第 0 步：时区同步

```bash
export TZ=Asia/Shanghai && date '+%Y-%m-%d %u'
```

- AD = 今日日期（YYYY-MM-DD）
- DAY_OF_WEEK = 星期几（1=周一 ... 6=周六, 7=周日）
- 月末判断：date '+%d' == 当月最后一天？

报告类型：
- 月末最后一天 → 月报（`?since=monthly`）
- 周六 → 周报（`?since=weekly`）
- 其他 → 日报（无参数）

### 第 1 步：查询今日 DB 数据量

```bash
export TZ=Asia/Shanghai && AD=$(date '+%Y-%m-%d') && \
docker exec radar-db psql -U radar -d radar -t -c "SELECT COUNT(*) FROM gold_prices WHERE price_date='${AD}';" | tr -d ' \n' && echo '' && \
docker exec radar-db psql -U radar -d radar -t -c "SELECT COUNT(*) FROM news_articles WHERE category='ai' AND article_date='${AD}';" | tr -d ' \n' && echo '' && \
docker exec radar-db psql -U radar -d radar -t -c "SELECT COUNT(*) FROM news_articles WHERE category='politics' AND article_date='${AD}';" | tr -d ' \n' && echo '' && \
docker exec radar-db psql -U radar -d radar -t -c "SELECT COUNT(*) FROM news_articles WHERE category='github' AND article_date='${AD}';" | tr -d ' \n'
```

**读 stdout 的 4 个数字**。全部为 0 → 查找最近一个有数据的日期作为 USE_DATE，并标注 `⚠️ 半成品 - 补采中`。

### 第 2 步：发送消息一 · 金价速览

```bash
docker exec radar-db psql -U radar -d radar -t -c \
  "SELECT intl_price_usd, intl_price_change, domestic_price_cny, domestic_price_change,
          tips_yield_10y, tips_yield_change
   FROM gold_prices WHERE price_date='${USE_DATE}';"
```

格式（Markdown 表格，**不要代码块包装**）：

```
💰 雷达每日报告 · 金价速览（YYYY-MM-DD · 报告类型）

| 指标 | 价格 | 涨跌 |
|---|---|---|
| 国际金价（USD/盎司） | $X,XXX.XX | +/-XX% |
| 国内金价（CNY/克） | ¥XXX.XX | +/-XX% |
| 美10年TIPS收益率 | X.XX% | +/-X.XXpp |

📊 一句话趋势点评
💡 定投建议（可选）
```

> TIPS 收益率（DFII10）= 扣除通胀后的实际利率。上升 → 持有黄金机会成本增加 → 金价承压；下降 → 黄金相对吸引力上升。

通过 `message tool action=send` 发送，失败重试 1 次。

### 第 3 步：发送消息二 · AI 热讯

```bash
docker exec radar-db psql -U radar -d radar -t -c \
  "SELECT title, LEFT(content, 500), source, url, COALESCE(summary, '')
   FROM news_articles
   WHERE article_date='${USE_DATE}' AND category='ai'
   ORDER BY blacklist_score DESC NULLS LAST LIMIT 10;"
```

**从 stdout 读真实数据**，按热度分降序排列。

格式：

```
🤖 雷达每日报告 · AI 热讯（YYYY-MM-DD · 报告类型）

**按热度排序 Top 10**

1. **标题** | 热度 XX | 来源
   摘要一句话（优先从 summary 列取；为空则从 content 的"事件介绍："后提取前 50 字）

2. ...
```

- 摘要优先从 `summary` 列取
- summary 为空时从 content 的"事件介绍："后提取前 50 字
- 按 `blacklist_score`（热度分）降序，最高热度排第 1
- 每条附来源和链接
- 通过 `message tool action=send` 发送，失败重试 1 次

### 第 4 步：发送消息三 · 国际政治

```bash
docker exec radar-db psql -U radar -d radar -t -c \
  "SELECT title, LEFT(content, 800), source, url
   FROM news_articles
   WHERE article_date='${USE_DATE}' AND category='politics'
   ORDER BY blacklist_score DESC NULLS LAST LIMIT 12;"
```

**版式铁律（佳哥拍板）**：
- ❌ 不要代码块包装
- ❌ 不要中英对照（不要 English Headline）
- ✅ 每条「事件 / 背景 / 影响」三段展开
- ✅ 按 🔴亚太 / 🔵中东·欧洲 / 🟢美洲 三个区域分类

格式：

```
🌍 雷达每日报告 · 国际政治（YYYY-MM-DD）

#### 🔴 亚太
- **标题**
  - 事件：发生了什么（1~2 句）
  - 背景：为什么发生 / 来龙去脉（1~2 句）
  - 影响：后续影响 / 关联（1~2 句）
  - 来源 | 链接

#### 🔵 中东 · 欧洲
...

#### 🟢 美洲
...
```

- 每条总长 60~120 字中文
- 至少 10 条（不足则标注"今日可验证国际政治事件不足"）
- 通过 `message tool action=send` 发送，失败重试 1 次

### 第 5 步：发送消息四 · GitHub 黑马

采集方式：`~/.agent-reach-venv314/bin/python3` 抓取 GitHub Trending（用 `bash --noprofile --norc -c '...'` 绕开 git alias）。

黑马分算法：
```
黑马分 = 周期新增⭐ × 小项目加成 × 新项目加权
小项目加成：<5k ×2.0 | 5k~20k ×1.5 | 20k~100k ×1.0 | ≥100k ×0.8
新项目加权（创建<30天）：×1.5
```

格式：

```
💻 雷达每日报告 · GitHub 黑马（YYYY-MM-DD · 报告类型）

**按黑马分排序 Top 10**

1. **owner/repo** ⭐ 总stars (+周期新增)
   简要描述（从 README 提取，1~2 句）
   https://github.com/owner/repo

2. ...
```

⚠️ **地址铁律**：必须包含完整 `owner/repo`，不能只写 repo 名。链接必须可打开。

通过 `message tool action=send` 发送，失败重试 1 次。

### 第 6 步：存档

将 4 条消息内容合并存档：

```bash
mkdir -p workspace/daily-reports && cat > workspace/daily-reports/YYYY-MM-DD.md
```

存档后发送完成回报（**即使有部分失败也要发**）：

```
📡 雷达日报推送完成
- 消息一 金价：OK/FAIL
- 消息二 AI热讯：OK/FAIL（N条）
- 消息三 国际政治：OK/FAIL（N条）
- 消息四 GitHub：OK/FAIL（N条）
- 数据日期：YYYY-MM-DD
```

## 数据库连接

```bash
docker exec radar-db psql -U radar -d radar
```

## 错误处理

- 数据全为 0：查找最近有数据的日期作为 USE_DATE，标题加 `⚠️ 半成品` 前缀
- GitHub 抓取失败：最多重试 2 次
- 单条消息发送失败：重试 1 次
- 国际政治 < 10 条：标注数量即可，不阻塞
- AI < 8 条：标注数量即可，不阻塞
- 所有异常记录到 `memory/YYYY-MM-DD.md`

## 参考模板

完整版式参考：`templates/approved-template-2026-06-17.md`
