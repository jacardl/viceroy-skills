---
name: radar-data-collection
description: 雷达数据采集 Skill — 采集金价、国际政治、AI热讯，写入 PostgreSQL 向量数据库，验证新闻真实性，按日期归档。
metadata: { "openclaw": { "emoji": "🛰️" } }
---

# 雷达数据采集 Skill

每日 06:00 北京时间执行。采集金价、国际政治、AI热讯，写入 `radar` 数据库的 `news_articles` 和 `gold_prices` 表。

## 数据源

| 类型 | 来源 | 数量 |
|------|------|------|
| 国际金价 | Kitco（伦敦现货，USD/盎司）| 1 条 |
| 国内金价 | 雪球（SGE:au99.99 上海金交所 Au99.99 现货，CNY/克）| 1 条 |
| 国际政治 | 9Router tavily 搜索 | 10 条 |
| AI热讯 | aihot.virxact.com 精选 | 10 条 |
| 补充信源 | Twitter/X（英文AI/科技动态）、Reddit（AI社区讨论）| 各3~5条 |

## 采集步骤

### 第一步：确认日期
```bash
date -d '+8 hour' '+%Y-%m-%d'
```
article_date = 北京时间今天日期

### 第二步：采集金价

1. **国际金价**：用 browser 工具打开 https://www.kitco.com/charts/livegold.html，提取伦敦现货金价（USD/盎司），计算涨跌幅度
2. **国内金价**（主选）：用 agent-reach 雪球通道
   ```bash
   export PATH="$PATH:/Users/apple/.npm-global/bin"
   ~/.agent-reach-venv314/bin/python3 -c "
   from agent_reach.channels.xueqiu import XueqiuChannel
   ch = XueqiuChannel()
   q = ch.get_stock_quote('SGE:au99.99')  # 上海金交所 Au99.99 现货
   # 注：SGE:au99.99 返回 price=1.55（单位未知），需乘以换算系数得出 CNY/克
   # 沪金现货参考价 ≈ 雪球价格 × 换算系数（约 1000/31.1035 ≈ 32.15）
   # 实际以 Kitco 国际金价(USD) × FX_USDCNY ÷ 31.1035 交叉验证
   print(q['current'], q['percent'])
   "
   ```
   >⚠️ 雪球 SGE:au99.99 返回 `price=1.55`（原始单位），实际 CNY/克价值需通过
   > `国际金价(USD/盎司) × USD/CNY汇率 ÷ 31.1035` 换算得出，或以权威平台沪金现货报价为准。
   > 若雪球 SGE 返回值异常，用 `SH518880` ETF 价格 × 32.15 估算沪金现货价作为备选。
3. **国内金价**（备选）：9Router 搜索"沪金现货 今日价格"

字段：`intl_price_usd`, `intl_price_change`, `domestic_price_cny`, `domestic_price_change`

### 第三步：采集国际政治（分区域链路）

搜索 query：分3 组执行，覆盖亚太 / 中东·欧洲 / 美洲：
| 区域 | 搜索 query | 目标条数 |
|------|-----------|---------|
| 亚太 | `Asia Pacific political news today` | 3~4 条 |
| 中东·欧洲 | `Middle East Europe geopolitical news today` | 3~4 条 |
| 美洲 | `Americas Latin America political news today` | 3~4 条 |

筛选来源：Reuters / AP / AFP / Al Jazeera / BBC / FT / Bloomberg
验证：每条必须附来源 URL，缺失则丢弃

**采集策略（落地版，强制按顺序执行）**
1. **主链路：9Router search**（先拿候选链接）
2. **补全正文：baoyu-url-to-markdown**（把候选链接转 markdown，提取事件细节）
3. **兜底：9Router web/fetch**（当 baoyu 链路失败时）

> 说明：候选链接如果是频道页/聚合页（如 Reuters world/china 目录页），必须继续下钻到具体事件稿；不能直接入库。

**内容增强要求（强制，服务下游推送）**
1. 每条必须生成 **中英对照标题**：
   - 中文标题（意译清楚）
   - English Headline（保留原文）
2. 每条必须生成 **事件介绍**（至少2句）：
   - 第1句：发生了什么（核心事实）
   - 第2句：背景或潜在影响（为什么值得关注）
3. 国际政治采集目标：**10~12条**（优先覆盖亚太 / 中东·欧洲 / 美洲）

字段写入规范：
- `title`：写中文标题（便于推送直读）
- `content`：按固定模板存储：
  ```
  中文标题：...
  English Headline: ...
  事件介绍：...
  背景/影响：...
  ```
- `source`, `url`, `category='politics'`, `lang='zh'`

### 第四步：采集 AI 热讯（aihot + 备选源）

**主选：aihot.virxact.com**
```bash
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 aihot-skill/0.2.0"
curl -s -H "User-Agent: $UA" \
  "https://aihot.virxact.com/api/public/items?mode=selected&take=10"
```

**备选A：Hacker News（AI/ML 相关）**
```bash
curl -s "https://hn.algolia.com/api/v1/search?query=AI+OR+ML+OR+GPT+OR+LLM&tags=story&hitsPerPage=8"
```

**备选B：ArXiv cs.AI/cs.LG 最新论文**
```bash
curl -s "https://export.arxiv.org/api/query?search_query=cat:cs.AI+OR+cat:cs.LG&sortBy=submittedDate&sortOrder=descending&max_results=8"
```

> 按优先级顺序调用：主选成功则跳过备选；主选失败再试备选A，备选A失败再试备选B。
> 三级均失败时，发送飞书通知并记录错误。

解析返回的 JSON，取 `title`、`publishedAt`、`summary`、`source`、`url`
字段：`category='ai'`, `lang='zh'`

### 第五步：采集 Twitter/X AI/科技动态

```bash
export PATH="$PATH:/Users/apple/.npm-global/bin"
# 搜索 AI 相关推文
twitter search "AI OR artificial intelligence OR GPT OR LLM OR AI agent" -n 5
```

解析返回的 JSON，取 `text`、`author.screenName`、`metrics.likes`、`metrics.retweets`、`createdAtISO`
字段：`category='twitter'`, `lang='en'`

**内容增强要求：**
- 标题：推文正文（截取前80字，超长截断）
- content 格式：
  ```
  推文内容：...
  作者：@screenName
  点赞：N 转发：N
  发布时间：ISO时间
  原文链接：https://x.com/screenName/status/id
  ```

### 第六步：采集 Reddit AI 社区讨论

```bash
export PATH="$PATH:/Users/apple/.npm-global/bin"
# 搜索 AI agents 相关帖子
rdt search "AI agent OR AI agents OR autonomous AI" -n 5
```

解析返回的 JSON，取 `title`、`selftext`（正文）、`author`、`ups`、`num_comments`、`permalink`
字段：`category='reddit'`, `lang='en'`

**内容增强要求：**
- 标题：帖子标题
- content 格式：
  ```
  帖子标题：...
  作者：u/author
  点赞：N 评论：N
  正文：...(selftext，截取前300字)
  原文链接：https://reddit.com/permalink
  ```

### 第七步：SimHash 去重（写入前质检）

每条新闻入库前，用 SimHash 检测与已有文章的相似度：

```bash
# 计算 SimHash（Python stdlib 实现）
python3 << 'PYEOF'
import hashlib, struct

def simhash(tokens, bits=64):
    v = [0] * bits
    for t in tokens:
        h = int(hashlib.md5(t.encode()).hexdigest(), 16)
        for i in range(bits):
            v[i] += 1 if h & (1 << i) else -1
    return sum(1 << i for i in range(bits) if v[i] > 0)

def hamming(h1, h2):
    return bin(h1 ^ h2).count('1')

# 示例：title + content 前200字作为 token
text = "TITLE CONTENT 前200字"
tokens = text.split()
sh = simhash(tokens)
print(sh)  # 写入 news_articles.simhash字段
PYEOF
```

**入库查重逻辑**：
```sql
-- 查询 Haming距离 < 3 的近似重复（64位 SimHash）
WITH new_hash AS (VALUES(${NEW_SIMHASH}))
SELECT article_date, title, source,
       ${NEW_SIMHASH} # hash AS distance
FROM news_articles, new_hash
WHERE length(simhash) = 16
  AND abs(length(replace(simhash, '-', '')) - 64) < 3  -- 近似匹配
LIMIT 5;
```
> Hamming距离 < 3 判定为近似重复，入库前比对：若发现重复，问是否覆盖或跳过。

**字段**：`simhash`（64位十六进制字符串，可为空），写入 `news_articles.simhash`。

### 第八步：向量 embedding（Ollama 本地）

```bash
# Ollama 地址（nomic-embed-text，768维）
OLLAMA_URL="http://localhost:11434/api/embeddings"
MODEL="nomic-embed-text"

# 对每条 title+content（前500字）调用 embedding
curl -s -X POST "$OLLAMA_URL" \
  -H "Content-Type: application/json" \
  -d "{\"model\":\"$MODEL\",\"prompt\":\"$TEXT\"}" \
  | python3 -c "import sys,json; print(','.join(map(str,json.load(sys.stdin)['embedding'])))"
```

维度 768，写入 `embedding` 字段（格式：`'[v1,v2,...]'`）。

### 第九步：写入数据库

```bash
# 金价写入
docker exec radar-db psql -U radar -d radar -c \
  "INSERT INTO gold_prices (price_date, intl_price_usd, intl_price_change, domestic_price_cny, domestic_price_change)
   VALUES ('${ARTICLE_DATE}', ${INTL_PRICE}, ${INTL_CHANGE}, ${DOMESTIC_PRICE}, ${DOMESTIC_CHANGE})
   ON CONFLICT (price_date) DO UPDATE SET
     intl_price_usd = EXCLUDED.intl_price_usd,
     intl_price_change = EXCLUDED.intl_price_change,
     domestic_price_cny = EXCLUDED.domestic_price_cny,
     domestic_price_change = EXCLUDED.domestic_price_change;"

# 新闻写入（每条一条INSERT，支持 category='twitter' / 'reddit'）
docker exec radar-db psql -U radar -d radar -c \
  "INSERT INTO news_articles (article_date, category, title, content, source, url, lang, embedding)
   VALUES ('${ARTICLE_DATE}', '${CATEGORY}', '${TITLE}', '${CONTENT}', '${SOURCE}', '${URL}', '${LANG}',
           '[${EMBEDDING}]');"
```

> Twitter 的 `source` 填推文作者 `@screenName`，Reddit 的 `source` 填 `u/author`。

### 第十步：验证数据

采集完成后执行：
```sql
SELECT article_date, category, COUNT(*) FROM news_articles GROUP BY article_date, category;
SELECT * FROM gold_prices WHERE price_date = '${ARTICLE_DATE}';
```
确认条数符合预期（国际政治≥10条，aihot≥8条，twitter≥3条，reddit≥3条），缺条则补采。

并抽查国际政治结构完整性（必须含中英对照+事件介绍）：
```sql
SELECT COUNT(*) FROM news_articles
WHERE article_date='${ARTICLE_DATE}' AND category='politics'
  AND content LIKE '%English Headline:%'
  AND content LIKE '%事件介绍：%';
```
若不达标，继续补采并覆盖更新。

## 数据库连接

```
Host: localhost:5444
Database: radar
User: radar
Password: radar
```

连接方式：`docker exec radar-db psql -U radar -d radar -c "SQL"`

## 错误处理

- 向量API失败：跳过 embedding，先写入文本数据，稍后重试
- 网络超时：最多重试2次，间隔30秒
- 数据不足：发送飞书通知给用户，说明缺条原因
- 所有异常记录到 `memory/YYYY-MM-DD.md`

## 输出

完成后输出简洁报告：
```
🛰️ 数据采集完成 [日期]
✅ 金价：国际 ${INTL_PRICE} (${CHANGE}) / 国内 ${DOMESTIC_PRICE}
✅ 国际政治：${N} 条
✅ AI热讯：${N} 条
✅ Twitter：${N} 条
✅ Reddit：${N} 条
⏱️ 耗时：${SEC}s
```