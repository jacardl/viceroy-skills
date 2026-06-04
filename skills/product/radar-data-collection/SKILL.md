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
| 国内金价 | 权威国内平台（沪金现货，CNY/克）| 1 条 |
| 国际政治 | RSS 聚合（BBC/Guardian/FT/NYT/Al Jazeera）+ 9Router 补充搜索 | 10 条 |
| AI热讯 | aihot.virxact.com 精选 | 10 条 |

## RSS 数据源总表

| 来源 | 状态 | RSS URL | 策略 |
|------|------|---------|------|
| **BBC News** | ✅ 直连可用 | `https://feeds.bbci.co.uk/news/world/rss.xml` | 直接 `curl` 获取 |
| **The Guardian** | ✅ 直连可用 | `https://www.theguardian.com/world/rss` | 直接 `curl` 获取 |
| **FT** | ⚠️ 301跳转但内容完整 | `https://www.ft.com/rss/home` | `curl -sL` 跟进 301 即可获取完整 RSS |
| **NYT** | ✅ 直连可用 | `https://rss.nytimes.com/services/xml/rss/nyt/World.xml` | 直接 `curl` 获取 |
| **Al Jazeera** | ✅ 直连可用 | `https://www.aljazeera.com/xml/rss/all.xml` | 直接 `curl` 获取 |
| **France24** | ✅ 直连可用 | `https://www.france24.com/en/rss` | 直接 `curl` 获取 |
| **Reuters** | ❌ RSS 通道被关 | `https://news.google.com/rss/search?q=site:reuters.com&hl=en-US&gl=US&ceid=US:en` | Google News RSS 过滤 `site:reuters.com` |
| **AP News** | ❌ RSS 通道被关 | `https://news.google.com/rss/search?q=site:apnews.com+world&hl=en-US&gl=US&ceid=US:en` | Google News RSS 过滤 `site:apnews.com` |
| **CNN** | ⚠️ CNN 官方 RSS 已关闭 | `https://news.google.com/rss/search?q=site:cnn.com+world&hl=en-US&gl=US&ceid=US:en` | Google News RSS 过滤 `site:cnn.com` |

## 采集步骤

### 第一步：确认日期
```bash
date -d '+8 hour' '+%Y-%m-%d'
```
article_date = 北京时间今天日期

### 第二步：采集金价（browser CDP）

1. 用 browser 工具打开 https://www.kitco.com/charts/livegold.html
2. 提取伦敦现货金价（USD/盎司）
3. 国内金价用 9Router 搜索"沪金现货 今日价格"
4. 计算涨跌幅度

字段：`intl_price_usd`, `intl_price_change`, `domestic_price_cny`, `domestic_price_change`

### 第三步：采集国际政治（RSS 主链路 + 搜索补充）

**采集顺序（强制）**：RSS 批量拉取 → 按发布日期筛选 → 不足 10 条时用 9Router 搜索补采

#### 3a. RSS 批量采集（主链路）

同时拉取以下所有 RSS feed（使用 `curl -sL` 并行获取）：

```bash
# 示例：一次性批量获取 RSS
RSS_URLS=(
  "https://feeds.bbci.co.uk/news/world/rss.xml"
  "https://www.theguardian.com/world/rss"
  "https://www.ft.com/rss/home"
  "https://rss.nytimes.com/services/xml/rss/nyt/World.xml"
  "https://www.aljazeera.com/xml/rss/all.xml"
  "https://www.france24.com/en/rss"
  "https://news.google.com/rss/search?q=site:reuters.com&hl=en-US&gl=US&ceid=US:en"
  "https://news.google.com/rss/search?q=site:apnews.com+world&hl=en-US&gl=US&ceid=US:en"
  "https://news.google.com/rss/search?q=site:cnn.com+world&hl=en-US&gl=US&ceid=US:en"
)

for url in "${RSS_URLS[@]}"; do
  response=$(curl -sL --max-time 8 "$url")
  # 解析 XML，提取 title, description, pubDate, link
  # pubDate 用于时效性筛选，description 可作为事件摘要
  # FT 要用 curl -sL（自动跟随 301）
done
```

**Python 解析 RSS XML**（每条 RSS 返回标准格式）：
```python
import xml.etree.ElementTree as ET

root = ET.fromstring(xml_data)
for item in root.findall('.//item'):
    title = item.findtext('title', '')
    desc = item.findtext('description', '')   # 事件摘要
    pub_date = item.findtext('pubDate', '')    # RFC 2822 格式
    link = item.findtext('link', '')
    source = item.findtext('source', '') or extract_domain(link)
```

**时效性筛选**：取 `pubDate` 在当天/前 1 天范围内的 RSS 条目

#### 3b. 9Router 搜索补充（兜底，RSS 不足 10 条时执行）

搜索 query：`international political news today`
筛选来源：Reuters / AP / AFP / Al Jazeera / BBC / FT
验证：每条必须附来源 URL，缺失则丢弃

### 时效性验证（强制、不可跳过）

每条候选新闻入库前必须验证发布时间。时效性是硬约束，禁止将过时新闻写入当日数据。

**验证方法（按优先级）**：
1. **web_fetch 工具**：抓取 URL 头部，提取发布时间信息
   - 检查页面标题/内容中的日期、URL 中的日期路径（如 `/2026/5/13`）
   - 如果 URL 路径或页面标题指向的日期早于 `article_date - 2天`，则**丢弃该条**
2. **9Router web/fetch**：当 web_fetch 失败时，改用 9Router fetch-combo 抓取
3. **URL 路径检查**：如果 URL 中包含 `/年/月/日` 或 `/年-月-日/` 格式的日期路径，直接提取并判断：
   - 日期早于 article_date - 2 天 → 丢弃
   - 无法提取日期 → 标记为"待验证"，用 baoyu-url-to-markdown 补全

**验证规则**：
- 新闻发布时间必须在 `article_date` 或 `article_date - 1天`（允许前一天的夜间新闻）
- 超过 2 天前的新闻 → **直接丢弃**，不可入库
- 验证失败的链接 → 丢弃，从候选池中移除
- 以 Al Jazeera 为例，URL 中的 `/2026/5/13/` 直接暴露发布日期为 2026-05-13，远早于当天，必须丢弃
- BBC URL 中 `/articles/xxxxx` 无显式日期但页面 title 会标注时间（如 "3 hours ago"），用 web_fetch 提取

**落地实现**：
```
# 伪代码流程
candidates = 9Router search
validated = []
for each candidate:
    # 方法1：URL路径分析
    date_from_url = extract_date_from_url(candidate.url)
    if date_from_url and date_from_url < article_date - 1:
        continue  # 丢弃旧新闻
    
    # 方法2：web_fetch 抓取验证
    result = web_fetch(candidate.url, extractMode='markdown', maxChars=300)
    if "hours ago" in result or "minutes ago" in result:
        validated.append(candidate)  # 大概率当天新闻
    elif specific_date_in_page < article_date - 1:
        continue  # 明确过时
    else:
        # 无法判断的，用 baoyu 或 9Router 兜底验证
        result2 = baoyu/9router_fetch(candidate.url)
        # 仍无法判断 → 丢弃（宁缺毋滥）
    
    validated.append(candidate)  # 通过验证
```

**达标要求**：至少采集 ≥10 条通过时效性验证的新闻。不足时重新搜索补采。

---

**采集策略（落地版，强制按顺序执行）**
1. **主链路：RSS 聚合并行拉取**（BBC/Guardian/FT/NYT/Al Jazeera/France24 + Google News 过滤 Reuters/AP/CNN）
   - RSS 自带 pubDate 无需额外验证时效性
   - RSS 自带 description/摘要，可直接用作入库内容
2. **正文补全：9Router fetch-combo**（当 RSS 的 description 过于简短时取具体页面完整内容）
3. **补充链路：9Router search**（当 RSS 当日新闻不足 10 条时用搜索补采）
4. **兜底正文：baoyu-url-to-markdown**（当 9Router fetch 失败时用 Chrome CDP 渲染）
5. **终极兜底：9Router web/fetch**（当以上都失败时）

> 说明：RSS 主链路的优势——无反爬墙、完整标题+摘要+发布时间+URL、纯文本低开销。
> Google News RSS 的局限：标题可能被截断，source 字段保留原始来源。
> 候选链接如果是频道页/聚合页，必须继续下钻到具体事件稿；不能直接入库。

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

### 第四步：采集 AI 热讯（aihot.virxact.com）

```bash
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 aihot-skill/0.2.0"
curl -s -H "User-Agent: $UA" \
  "https://aihot.virxact.com/api/public/items?mode=selected&take=10"
```

解析返回的 JSON，取 `title`、`publishedAt`、`summary`、`source`、`url`
字段：`category='ai'`, `lang='zh'`

### 第五步：向量 embedding（Ollama 本地）

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

### 第六步：写入数据库

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

# 新闻写入（每条一条INSERT）
docker exec radar-db psql -U radar -d radar -c \
  "INSERT INTO news_articles (article_date, category, title, content, source, url, lang, embedding)
   VALUES ('${ARTICLE_DATE}', '${CATEGORY}', '${TITLE}', '${CONTENT}', '${SOURCE}', '${URL}', '${LANG}',
           '[${EMBEDDING}]');"
```

### 第七步：验证数据

采集完成后执行：
```sql
SELECT article_date, category, COUNT(*) FROM news_articles GROUP BY article_date, category;
SELECT * FROM gold_prices WHERE price_date = '${ARTICLE_DATE}';
```
确认条数符合预期（国际政治≥10条，aihot≥8条），缺条则补采。

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
⏱️ 耗时：${SEC}s
```