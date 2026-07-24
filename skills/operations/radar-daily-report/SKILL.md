---
name: radar-daily-report
description: "从 radar DB 读取今日数据，发送金价+AI+政治+GitHub 四条飞书消息"
metadata: { "openclaw": { "emoji": "📡" } }
---

# 雷达每日报告推送

每日 06:00 北京时间执行。发送 **4 条独立飞书消息**。

DB 连接：`docker exec radar-db psql -U radar -d radar`

版式参考：`references/approved-template.md`

---

## 执行步骤

### 第 0 步：时区同步 + 判断报告类型

```bash
export TZ=Asia/Shanghai && date '+%Y-%m-%d %u %d' && cal -m $(date '+%m') | tail -1 | awk '{print NF}'
```

- AD = 今天日期（YYYY-MM-DD）
- DAY = 星期几（1=周一 ... 6=周六, 7=周日）
- LAST_DAY = cal 判断本月最后一天

报告类型：
- LAST_DAY && DAY == 今天日期 → 月报（`?since=monthly`）
- DAY == 6（周六）→ 周报（`?since=weekly`）
- 其他 → 日报（无参数）

### 第 1 步：查询今日数据量

```bash
export TZ=Asia/Shanghai && AD=$(date '+%Y-%m-%d') && \
docker exec radar-db psql -U radar -d radar -t -c \
  "SELECT COUNT(*) FROM gold_prices WHERE price_date='${AD}';" | tr -d ' \n' && echo '' && \
docker exec radar-db psql -U radar -d radar -t -c \
  "SELECT COUNT(*) FROM news_articles WHERE category='ai' AND article_date='${AD}';" | tr -d ' \n' && echo '' && \
docker exec radar-db psql -U radar -d radar -t -c \
  "SELECT COUNT(*) FROM news_articles WHERE category='politics' AND article_date='${AD}';" | tr -d ' \n' && echo '' && \
docker exec radar-db psql -U radar -d radar -t -c \
  "SELECT COUNT(*) FROM news_articles WHERE category='github' AND article_date='${AD}';" | tr -d ' \n'
```

全部为 0 → 查最近有数据的日期作为 USE_DATE，标题加 `⚠️ 半成品` 前缀。

### 第 2 步：发送消息一 · 金价

```bash
docker exec radar-db psql -U radar -d radar -t -c \
  "SELECT intl_price_usd, intl_price_change, domestic_price_cny, domestic_price_change,
          tips_yield_10y, tips_yield_change
   FROM gold_prices WHERE price_date='${USE_DATE}';"
```

版式：`references/approved-template.md` 第一节，**不用代码块**，Markdown 表格。

### 第 3 步：发送消息二 · AI 热讯

```bash
docker exec radar-db psql -U radar -d radar -t -c \
  "SELECT title, LEFT(content, 400), source, url, COALESCE(summary, '')
   FROM news_articles
   WHERE article_date='${USE_DATE}' AND category='ai'
   ORDER BY blacklist_score DESC NULLS LAST LIMIT 10;"
```

按热度分降序。每条附：热度分 + 来源 + 1句摘要。

### 第 4 步：发送消息三 · 国际政治

```bash
docker exec radar-db psql -U radar -d radar -t -c \
  "SELECT LEFT(content, 800), source, url
   FROM news_articles
   WHERE article_date='${USE_DATE}' AND category='politics'
   ORDER BY blacklist_score DESC NULLS LAST LIMIT 12;"
```

版式：`references/approved-template.md` 第三节

**版式铁律（佳哥拍板）**：
- ❌ 代码块 ❌ English Headline ❌ 中英对照
- ✅ 每条「事件 / 背景 / 影响」三段
- ✅ 🔴亚太 🔵中东·欧洲 🟢美洲 三区域

### 第 5 步：发送消息四 · GitHub 黑马

采集：agent-reach WebChannel（sessions_spawn 独立执行）
黑马分 = 今日新增⭐ × 小项目加成：
| 总⭐区间 | 加成 |
|---------|------|
| <5k | ×2.0 |
| 5k~20k | ×1.5 |
| 20k~100k | ×1.0 |
| ≥100k | ×0.8 |

版式：`references/approved-template.md` 第四节

**铁律**：必须含 `owner/repo` 完整路径 + 今日新增⭐

### 第 6 步：存档 + 回报

```bash
mkdir -p workspace/daily-reports && \
cat > workspace/daily-reports/${USE_DATE}.md << 'REPORT'
（4条消息完整内容）
REPORT
```

输出完成统计：
```
📡 雷达日报推送完成
- 消息一 金价：OK/FAIL
- 消息二 AI热讯：OK/FAIL（N条）
- 消息三 国际政治：OK/FAIL（N条）
- 消息四 GitHub：OK/FAIL（N条）
- 数据日期：YYYY-MM-DD
```

---

## 错误处理

- 4 类全 0 → 查最近日期，标题加 `⚠️ 半成品`
- 国际政治 < 10 条 → 标注数量，不阻塞
- AI < 8 条 → 标注数量，不阻塞
- 单条消息失败 → 重试 1 次
- 所有异常记录 `memory/YYYY-MM-DD.md`
