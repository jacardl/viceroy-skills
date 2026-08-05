---
name: radar-daily-report
description: "从 radar DB 读取今日数据，发送金价+AI+政治+GitHub 四条飞书消息"
metadata: { "openclaw": { "emoji": "📡" } }
---

# 雷达每日报告推送

执行入口：直接运行本 skill，由 cron `9055e9a4`（每日 06:00 CST）触发。

## 执行脚本

```
python3 ~/.openclaw/skills/operations/radar-daily-report/scripts/push.py
```

脚本输出格式（stdout）：
```
===MSG1===
<金价消息>

===MSG2===
<AI消息>

===MSG3===
<国际政治消息>

===MSG4===
<GitHub消息>

===META===
date=YYYY-MM-DD dow=N report_type=daily|weekly|monthly ai=X po=X gh=X gold_ok=true|false
```

## 数据字段映射（push.py 读取规则）

### gold_prices 表

| DB 字段 | push.py 读取 | 显示 |
|---------|-------------|------|
| `intl_price_usd` | float | $X,XXX.XX /盎司 |
| `intl_price_change` | float（**百分比%**） | ±X.XX% |
| `domestic_price_cny` | float | ¥XXX.XX /克 |
| `domestic_price_change` | float（**百分比%**） | ±X.XX% |
| `tips_yield_10y` | float | X.XXX% |
| `tips_yield_change` | float（基点差 pp） | ±X.XXXpp |
| `gold_note` | text | 附在表格下方 |

> ⚠️ `intl_price_change` / `domestic_price_change` 存的是**百分比值**，非绝对额。\
> 由 collect.py 在入库时计算：**(今-昨)/昨 × 100%**

### news_articles 表（所有 category）

读取方式：`SELECT row_to_json(...)` — 按字段名访问，不依赖分隔符。

| category | 读取字段 | 显示 |
|----------|---------|------|
| `ai` | title / **description** / source / url / blacklist_score | 序号 · 标题 · 热度分 · 来源 + 摘要（v4.1：description 是主显示，summary 备用） |
| `politics` | content(=摘要) / source / url / **region** | 🔴亚太 / 🔵中东·欧洲 / 🟢美洲 三段（v4.1：region 写入由 collect.py step_politics 传递） |
| `github` | title / **description** / source(=lang) / url / **stars_count** / **period_new_stars** / blacklist_score | 黑马分 · 今日+⭐ · 总⭐ + 中文简介（v4.1：description 改干净 desc，不含 ⭐ 统计数字） |

> 字段变更记录（v4.1，2026-08-05）：
> - `ai.description` 成为 push 主显示字段，summary 备用
> - `politics.region` 由 collect.py 写入，DB 默认值 🟢 仅作兜底
> - `github.description` 改干净中文 desc（v4 之前是 `* N today | total* N | lang | desc[:80]`，v4.1 改为纯 desc[:300]）
> - `growth_rate` / `is_new_project`：采集时写入，push 预留字段

## 消息发送

解析脚本输出后，逐条发送飞书：
- ===MSG1=== → message tool（金价）
- ===MSG2=== → message tool（AI）
- ===MSG3=== → message tool（国际政治）
- ===MSG4=== → message tool（GitHub）

## 存档

```
mkdir -p ~/.openclaw/workspace/daily-reports
# 消息内容存档到 ~/.openclaw/workspace/daily-reports/YYYY-MM-DD.md
```

## 异常处理铁律

- gold_ok=false → MSG1 显示「⚠️ 金价数据缺失」
- ai=0 → MSG2 显示「⚠️ AI热讯数据缺失」
- po=0 → MSG3 显示「⚠️ 国际政治数据缺失」
- gh=0 → MSG4 显示「⚠️ GitHub数据缺失」
- **禁止独立抓取补充数据 / 禁止 fallback 旧数据**

## 版式参考

见 `references/approved-template.md`。

版式铁律（佳哥拍板，2026-06-17）：
- ❌ 代码块 ❌ English Headline ❌ 中英对照
- ✅ 每条政治「事件 / 背景 / 影响」三段
- ✅ 🔴亚太 🔵中东·欧洲 🟢美洲 三区域
- ✅ 金价用 Markdown 表格（**涨跌列为百分比%**）
- ✅ GitHub 必须含今日新增⭐ + 总⭐ + 中文简介（取 description 字段）
