---
name: radar-data-collection
description: 雷达数据采集 — 金价、TIPS、政治、AIHOT、GitHub 写入 PostgreSQL（docker exec）。采集失败按 PATCH-2026-08-10-001 分类告警。
category: operations
---
# radar-data-collection

每日数据采集技能。写入 `radar-db` PostgreSQL。

## 环境

- DB: `docker exec radar-db psql -U radar -d radar -t -c "SQL"`
- 9Router: `http://localhost:20128`
- 9Router key: **不要硬编码** — 从 `~/.9router/db/data.sqlite` 动态读取
- TZ: `Asia/Shanghai`

## 采集顺序（含重试规则）

```bash
TODAY=$(TZ=Asia/Shanghai date '+%Y-%m-%d')
SCRIPT_DIR="/Users/apple/.shared-agent-skills/operations/radar-data-collection/scripts"

# GitHub trending：至少重试 3 次，每次间隔 ≥30s
for i in 1 2 3; do
  python3 "$SCRIPT_DIR/gh_collect.py" "$TODAY" && break
  [ $i -lt 3 ] && sleep 30
done

# 金价 + TIPS + 政治 + AI（collect.py 超时 300s，超时后用对应回退脚本补数据）
python3 "$SCRIPT_DIR/collect.py"
```

**重试判定规则**：
- GitHub：count=0 时重试，count=1-9 且 ≥3 次重试后仍 <10 → 接受源数据不足，不告警
- 金价：国内源全挂属常态，无需重试，标注「金价缺失」
- 政治/AI：collect.py 超时后用 skill 内回退脚本补采

脚本路径：`~/.shared-agent-skills/operations/radar-data-collection/scripts/`。**不要用 collect.py 内置的 gh 路径**，见下方陷阱。

## 关键陷阱

### 9Router `/v1/search` 彻底失效（2026-08-28 实测）

9Router key 验证已重新启用，`~/.9router/db/data.sqlite` 中存储完整 key（35 字符，格式 `sk-0d6...`）传入 `/v1/search` 返回 **401 Unauthorized**（旧 hardcoded 截断值 `"sk-0d6...a7da"` 同样失效）。`collect.py` 已修复为从 SQLite 动态读取完整 key。

**政治采集回退链**（已验证可行）：
1. 直接解析公开 RSS feed：BBC World、BBC Asia、Al Jazeera（59 条原始 → 12 条去重）
2. 若 RSS 也不通：走 `gpt-5.6-sol → MiniMax-M3 → sonnet → src[:200]` 中文改写链
3. 全失败：description 落英文，飞书标注「⚠️ 政治中文未改写」

⚠️ **不要**在 politics 步骤上反复重试 collect.py（每次 60s 间隔会迅速耗尽超时）。超时后直接用 RSS 回退脚本。

**可用 RSS 源**：
```
BBC World:    https://feeds.bbci.co.uk/news/world/rss.xml
BBC Asia:     https://feeds.bbci.co.uk/news/world/asia/rss.xml
Al Jazeera:   https://www.aljazeera.com/xml/rss/all.xml
```

### 9Router Key 读取方式（已修复 2026-08-28）

`collect.py` 已修复：从 `~/.9router/db/data.sqlite` 动态读取完整 key，不再硬编码截断值。

**正确代码**（sqlite3 默认返回 `str`，无需 `text_factory = bytes`）：
```python
import sqlite3
conn = sqlite3.connect(os.path.expanduser("~/.9router/db/data.sqlite"))
cur = conn.cursor()
cur.execute("SELECT key FROM apiKeys LIMIT 1")
NINE_ROUTER_KEY = cur.fetchone()[0]  # 直接 str，无须 decode
conn.close()
```

⚠️ `text_factory = bytes` 是**错误**做法——加了它会返回 bytes 而非 str，后续 Bearer 拼接会出错。

### Cron 技能加载时机陷阱

**cron job 的 skill 必须在 cron 执行前已存在于 `~/.hermes/skills/`**。
2026-08-26 04:22 cron 运行时 skill 目录于 04:23 才创建，导致 cron 找不到 skill，触发 fallback 手动执行，最终 RuntimeError。
排查类似问题时先查 `~/.hermes/skills/operations/radar-data-collection/` 是否存在 + mtime 是否早于 cron 时间。

### AIHOT 响应结构与可用 API（2026-08-28 实测）

aihot.virxact.com 返回 `items` 而非 `data`：
```python
items = data.get("items", [])   # 不是 data.get("data", [])
```
**正确 API 端点**：`https://aihot.virxact.com/api/public/items?mode=selected&take=10`
**必需 UA**：`aihot-skill/0.2.0`（带此 UA 才能返回 200，不带则 404）

### 金价采集现状（2026-08-27 实测）

所有国内源全部失败：
- Eastmoney `push2.eastmoney.com` → `Remote end closed connection`
- 腾讯 kline → `Remote end closed connection`
- 3 次重试全挂，无国际金价备用源写入

**金价缺失已是常态，非偶发**。当前 collect.py 无自动国际金价兜底，飞书标注「金价缺失」即可，无需人工干预。

### collect.py GitHub 自检是假阴性

`collect.py` 的 self-check 显示 `❌ github 0/10`，但此时 gh_collect.py 已成功写入了 7 条数据到 DB。
原因：collect.py 内部 gh 路径错误（见下），导致它查 DB 得到 0 条，但数据实际已在 DB 中。

**验证方法**：不要相信 collect.py 的 self-check github 行。采集完成后直接查 DB：
```bash
docker exec radar-db psql -U radar -d radar -t -c "
SELECT category, COUNT(*) FROM news_articles
WHERE article_date = '$TODAY' GROUP BY category"
```
若 ai/politics 达标但 github=0，进一步确认：
```bash
docker exec radar-db psql -U radar -d radar -t -c "
SELECT category, article_date, COUNT(*) FROM news_articles
WHERE category = 'github' ORDER BY article_date DESC LIMIT 3"
```
若有昨日旧数据无今日数据 → 确认 github 采集失败，走告警流程。
若有今日数据（gh_collect.py 已写）→ 自检误报，跳过 github 告警。

### gh_collect.py 初采后 article_date 可能不匹配（2026-08-29 发现）

gh_collect.py 报告 "Inserted 10/10" 但 DB 查询 `$TODAY` 显示 github=0，同时存在昨日旧数据。
原因未定位（可能是 playwright 异步写帧竞争、docker exec date 与 python datetime 小幅偏差累积）。

**补采流程**（2026-08-29 实测可行）：
```bash
# 1. 确认 github 条目存在但日期错误
docker exec radar-db psql -U radar -d radar -t -c "
SELECT article_date, COUNT(*) FROM news_articles
WHERE category = 'github' GROUP BY article_date
ORDER BY article_date DESC LIMIT 3"

# 2. 若有数据但 article_date 非目标日期，删掉错误日期数据
docker exec radar-db psql -U radar -d radar -t -c "
DELETE FROM news_articles WHERE category='github' AND article_date='<错误日期>';"

# 3. 重新运行 gh_collect.py，传入目标日期
TODAY=$(TZ=Asia/Shanghai date '+%Y-%m-%d')
python3 "$SCRIPT_DIR/gh_collect.py" "$TODAY"

# 4. 验证：article_date = 目标日期，count ≥ 1
docker exec radar-db psql -U radar -d radar -t -c "
SELECT article_date, COUNT(*) FROM news_articles
WHERE category = 'github' AND article_date = '$TODAY'"
```

⚠️ **验证必须检查 article_date**，不能只查 count。count>0 不代表日期正确。

### collect.py 超时无回退（2026-09-01 实测 600s）

collect.py 存在 600s 超时上限，超时后 **既不写数据也不抛异常**，DB counts 完全不变。
已知卡死环节：gold 步骤（国内源全挂后的网络重试）、politics 步骤（9Router 搜索无响应时 60s × 3 次重试间隔）。

**处理流程**：
1. 超时后立刻查 DB：`SELECT COUNT(*) FROM news_articles WHERE article_date = '$TODAY'`
2. 若 ai/政治已达标 → 只补 gold；若 ai/政治未达标 → 用 RSS 回退补 politics（见上方「政治采集回退链」）
3. **不要重跑整个 collect.py**（会再次卡死）

**超时后手动补采 AI（aihot 直接 fetch）**：
```python
import urllib.request, json, subprocess
TODAY = "2026-09-01"
url = "https://aihot.virxact.com/api/public/items?mode=selected&take=10"
req = urllib.request.Request(url, headers={"User-Agent": "aihot-skill/0.2.0"})
with urllib.request.urlopen(req, timeout=15) as resp:
    items = json.loads(resp.read().decode()).get("items", [])
for it in items:
    title = (it.get("title") or "").replace("'", "''")
    desc = (it.get("description") or it.get("content") or "").replace("'", "''")[:500]
    src = (it.get("source") or "aihot").replace("'", "''")
    link = (it.get("url") or "").replace("'", "''")
    sql = f"INSERT INTO news_articles (category, title, content, source, url, lang, article_date, summary, description) VALUES ('ai', E'{title}', E'{desc}', E'{src}', E'{link}', 'zh', '{TODAY}', E'{desc[:200]}', E'{desc}')"
    subprocess.run(f"docker exec radar-db psql -U radar -d radar -t -c \"{sql}\"", shell=True)
```

**超时后手动补采 politics（RSS → docker exec insert）**：
```python
import urllib.request, xml.etree.ElementTree as ET, json, subprocess
TODAY = "2026-09-01"
rss_sources = [("BBC World","https://feeds.bbci.co.uk/news/world/rss.xml"),("BBC Asia","https://feeds.bbci.co.uk/news/world/asia/rss.xml"),("Al Jazeera","https://www.aljazeera.com/xml/rss/all.xml")]
all_items, seen_titles = [], set()
for src_name, url in rss_sources:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        root = ET.fromstring(resp.read().decode("utf-8", errors="ignore"))
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        desc = (item.findtext("description") or "").strip()
        link = (item.findtext("link") or "").strip()
        if title and title not in seen_titles:
            seen_titles.add(title)
            all_items.append({"title": title, "description": desc, "link": link, "source": src_name})
unique, seen_content = [], set()
for it in all_items:
    cp = it["description"][:100].lower()
    if cp and cp not in seen_content:
        seen_content.add(cp); unique.append(it)
for it in unique[:15]:
    t,d,s,l = it["title"].replace("'","''"), it["description"].replace("'","''")[:500], it["source"].replace("'","''"), it["link"].replace("'","''")
    sql = f"INSERT INTO news_articles (category, title, content, source, url, lang, article_date, summary, description) VALUES ('politics', E'{t}', E'{d}', E'{s}', E'{l}', 'en', '{TODAY}', E'{d[:200]}', E'{d}')"
    subprocess.run(f"docker exec radar-db psql -U radar -d radar -t -c \"{sql}\"", shell=True)
```

⚠️ **psycopg2 直接连接无效**（端口映射问题），所有手动 INSERT 必须走 `docker exec radar-db psql -U radar -d radar -t -c "SQL"`。

### `news_articles` 表无 `score` 列（2026-08-28 实测）

`collect.py` 的 `insert_news()` 试图写入 `score` 列，但表里无此列（schema 以 `stars_count` 替代）。**手动 INSERT 时必须省略 `score`**，否则 500 报错。
正确列：`category, title, content, source, url, lang, article_date, summary, description`

### collect.py GitHub 步骤陷阱

`collect.py` 内部硬编码了错误的 gh_collect.py 路径：
```
/Users/apple/.openclaw/workspace/scripts/radar/gh_collect.py  # 不存在！
```
会导致 GitHub 采集 `Attempt 3/3 FAILED`，但数据实际已被外部 gh_collect.py 写入，**self-check 会漏报 github=0**。
**正确做法**：先单独跑 gh_collect.py，再用 collect.py 跑其余三项，不要依赖 collect.py 内部调用 GitHub。

### gh_collect.py 日期偏移陷阱（2026-08-27 发现）

gh_collect.py 第 17-20 行内部用 `docker exec radar-db date` 取 CST 日期作为 `TODAY`，但 GitHub Trending 页面实际展示的是**上一个日历年日期**（GitHub UTC~00:00 更新 = CST ~8:00）。

**后果**：凌晨 4-6AM 运行时，脚本取到今日 CST 日期（如 08-27），但 GitHub 页面仍是 08-26 的数据，最终数据以错误日期（08-27）写入 DB——之后 push.py 按 08-27 查 DB 找不到数据，误判 GitHub 失败。

**复现场景**：
```bash
# 这两个命令结果不同！
TZ=Asia/Shanghai python3 gh_collect.py         # 写 2026-08-26（错误）
TZ=Asia/Shanghai python3 gh_collect.py 2026-08-27  # 写 2026-08-27（正确）
```

**正确调用方式**：始终显式传入目标日期：
```bash
TODAY=$(TZ=Asia/Shanghai date '+%Y-%m-%d')
python3 "$SCRIPT_DIR/gh_collect.py" "$TODAY"
```

**验证**：运行后直查 DB：
```bash
docker exec radar-db psql -U radar -d radar -t -c "
SELECT article_date, COUNT(*) FROM news_articles
WHERE category = 'github' GROUP BY article_date
ORDER BY article_date DESC LIMIT 3"
```
若今日有数据且条数合理 → 成功。若只有昨日数据 → 需删旧数据后重新运行并传参。

### GitHub Trending 源数量波动

GitHub Trending 每日 repo 数量不固定（周末/节假日可能 <10），**≠ 采集失败**。判断标准：
- 条目 = 0 → GitHub 失败（告警）
- 条目 1-9 → 正常记录，不触发告警（技能阈值 ≥10 仅供参考，源本身不足时无法强求）

## 验证标准

- `news_articles`: AI ≥8，政治 ≥10，GitHub ≥10
- `gold_prices`: 当日有行

**验证必须直查 DB**，不要依赖 collect.py 的 self-check 输出（github 行经常假阴性）。

```bash
docker exec radar-db psql -U radar -d radar -t -c "
SELECT
  (SELECT COUNT(*) FROM news_articles WHERE article_date = '$TODAY' AND category = 'ai') as ai,
  (SELECT COUNT(*) FROM news_articles WHERE article_date = '$TODAY' AND category = 'politics') as pol,
  (SELECT COUNT(*) FROM news_articles WHERE article_date = '$TODAY' AND category = 'github') as gh,
  (SELECT COUNT(*) FROM gold_prices WHERE price_date = '$TODAY') as gold"
```

## 告警分类（PATCH-2026-08-10-001）

| 条件 | 标注 |
|------|------|
| 政治 <5 | 🚨 告警 |
| 金价全失败 | 「金价缺失」 |
| AI <5 | 「AI不足」 |
| GitHub = 0（3次重试后） | 「GitHub失败」 |
| GitHub 1-9（3次重试后仍不足） | 接受，不告警（源数据不足，非采集失败） |
| 政治中文改写全失败 | 「⚠️ 政治中文未改写」 |

## 不完整数据处理规则（2026-09-01 新增）

当采集结果不满足「验证标准」时，**仍发送日报**，在对应消息中标注问题，不阻塞推送：

| 不达标项 | 日报处理 |
|----------|---------|
| 金价=0 | MSG1 显示「⚠️ 金价数据缺失」 |
| AI <5 | MSG2 显示「⚠️ AI热讯数据缺失」 |
| 政治 <5 | MSG3 显示「⚠️ 国际政治数据缺失」 |
| GitHub = 0（3次重试后） | MSG4 显示「⚠️ GitHub数据缺失」 |
| GitHub 1-9（3次重试后） | MSG4 正常发送，标注「⚠️ GitHub今日源数据仅N条」（不阻塞） |
| 政治全英文无改写 | MSG3 正常发送，标注「⚠️ 政治中文未改写」 |

## 中文改写 fallback 链

`gpt-5.6-sol → MiniMax-M3 → sonnet → src[:200]`

全失败时 description 落英文，**飞书标注「⚠️ 政治中文未改写」**。

## DB Schema（已验证 2026-08-26，关键列名修正）

| 表 | 正确列名 | ⚠️ 旧错误 |
|----|---------|---------|
| news_articles | `article_date` | ❌ `date` |
| gold_prices | `price_date` | ❌ `date` |
| TIPS | `gold_prices.tips_yield_10y` | ❌ `tips_rates` 表不存在 |

```sql
-- 综合验证
SELECT
  (SELECT COUNT(*) FROM news_articles WHERE article_date = '2026-08-26' AND category = 'ai') as ai,
  (SELECT COUNT(*) FROM news_articles WHERE article_date = '2026-08-26' AND category = 'politics') as pol,
  (SELECT COUNT(*) FROM news_articles WHERE article_date = '2026-08-26' AND category = 'github') as gh,
  (SELECT COUNT(*) FROM gold_prices WHERE price_date = '2026-08-26') as gold;
```

## 技能目录结构

```
~/.hermes/skills/operations/radar-data-collection/   ← cron 从这里加载 SKILL.md
- 脚本：`~/.shared-agent-skills/operations/radar-data-collection/scripts/`
- `references/9router-key-pattern.md` — 9Router key 格式说明（已过时，见上方陷阱）
```

⚠️ `~/.hermes/skills/.../radar-data-collection/` 只有 SKILL.md + references/，**无 scripts/**。
cron prompt 里引用 `~/.shared-agent-skills/.../scripts/` 是正确的。

技能名在两个目录均有，hermes 优先用 `~/.hermes/skills/` 下的版本。
