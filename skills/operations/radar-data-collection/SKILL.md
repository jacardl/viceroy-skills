---
name: radar-data-collection
description: "采集金价+TIPS/国际政治/AI热讯/GitHub Trending 写入 radar 数据库"
metadata: { "openclaw": { "emoji": "🛰️" } }
---

# 雷达数据采集

每日 06:00 北京时间执行。数据写入 `radar` 数据库 `news_articles`（新闻）和 `gold_prices`（金价）。

DB 连接：`docker exec radar-db psql -U radar -d radar`

## 执行顺序

**第一步：确认日期**
```bash
date -u '+%Y-%m-%d'
# UTC date = 北京 date（北京时间=UTC+8，取日一致）
```
`article_date` = 今天 UTC 日期字符串。

**第二步：金价 + TIPS**
见 `references/gold-tips.md`

**第三步：GitHub Trending**
用 sessions_spawn 独立采集，**禁止在 cron 里直接写 /tmp 文件**。

```bash
# 方式A（推荐）：sessions_spawn + agent-reach
sessions_spawn taskName=gh_collect runtime=subagent cleanup=delete <<EOF
export TZ=Asia/Shanghai && date '+%Y-%m-%d'   # 确认日期
~/.agent-reach-venv314/bin/python3 \
  /Users/apple/.openclaw/skills/operations/radar-data-collection/scripts/gh_collector.py
EOF
```

```bash
# 方式B（备选）：web_fetch 直接抓（无 API 补全）
web_fetch https://github.com/trending
```

入库字段：category=`github` / title=项目全名 / content=`⭐ {总⭐:,} | 📈 {今日⭐:,} stars today — {描述}` / source=语言 / url / blacklist_score=黑马分

**黑马分 = 今日新增⭐ × 小项目加成**
| 总⭐区间 | 加成 |
|---------|------|
| <5k | ×2.0 |
| 5k~20k | ×1.5 |
| 20k~100k | ×1.0 |
| ≥100k | ×0.8 |

入库前 blacklist_score 必须为整数。

**第四步：国际政治**
见 `references/politics-queries.md`

搜索链路：9Router search → baoyu-url-to-markdown → 9Router web/fetch

入库字段：category=`politics` / title=中文标题 / content=中英对照+事件介绍+背景影响 / lang=`zh` / url / source

目标：10~12 条（亚太 4 / 中东·欧洲 4 / 美洲 3）

**第五步：AI 热讯（aihot）**
```bash
curl -s -H "User-Agent: aihot-skill/0.2.0" \
  "https://aihot.virxact.com/api/public/items?mode=selected&take=10"
```
解析 JSON 取 title / publishedAt / summary / url。

备选A：Hacker News
```bash
curl -s "https://hn.algolia.com/api/v1/search?query=AI+OR+ML+OR+GPT+OR+LLM&tags=story&hitsPerPage=8"
```
备选B：ArXiv cs.AI/cs.LG
```bash
curl -s "https://export.arxiv.org/api/query?search_query=cat:cs.AI+OR+cat:cs.LG&sortBy=submittedDate&max_results=8"
```

入库：category=`ai` / lang=`zh`

**第六步：写入数据库**
```bash
# 新闻（每条一行）
docker exec radar-db psql -U radar -d radar -c \
  "INSERT INTO news_articles
    (article_date, category, title, content, source, url, lang, blacklist_score)
   VALUES
    ('${DATE}', '${CAT}', E'${TITLE}', E'${CONTENT}', '${SOURCE}',
     '${URL}', '${LANG}', ${SCORE:-NULL})
   ON CONFLICT DO NOTHING;"
```

## 验证

```bash
docker exec radar-db psql -U radar -d radar -c \
  "SELECT category, COUNT(*) FROM news_articles
   WHERE article_date='${DATE}' GROUP BY category ORDER BY category;"

docker exec radar-db psql -U radar -d radar -c \
  "SELECT * FROM gold_prices WHERE price_date='${DATE}';"
```

达标：国际政治≥10 / AI≥8 / github≥10 / 金价1条

## 异常处理

- 向量 embedding 失败 → 跳过，不阻塞写入
- 网络超时 → 重试2次，间隔30s
- 数据不足 → 补采，仍不足则发送飞书通知
- 完成后输出简洁统计
