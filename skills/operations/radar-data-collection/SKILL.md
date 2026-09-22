---
name: radar-data-collection
description: 雷达数据采集 — 金价、TIPS、AIHOT、GitHub 写入 PostgreSQL（docker exec）。采集失败按 PATCH-2026-08-10-001 分类告警。
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

# 金价 + TIPS + AI（collect.py 超时 360s，实测 2026-09-03）
# 超时后既不写数据也不抛异常，DB counts 完全不变
# 已知卡死环节：gold 步骤（国内源全挂后的网络重试）
python3 "$SCRIPT_DIR/collect.py"
```

**重试判定规则**：
- GitHub：count=0 时重试，count=1-9 且 ≥3 次重试后仍 <10 → 接受源数据不足，不告警
- 金价：国内源全挂属常态，无需重试，标注「金价缺失」
- AI：collect.py 超时后用 skill 内回退脚本补采

脚本路径：`~/.shared-agent-skills/operations/radar-data-collection/scripts/`。

## 关键陷阱

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

### politics 类别采集（2026-09-12 实测）

`collect.py` 不采集 politics 数据。该类别来自同一 aihot 端点，但 INSERT 时 category='politics' 而非 'ai'。
**手动补采 politics**（与 ai 补采脚本结构完全相同，仅 category 不同）：
```python
import urllib.request, json, subprocess
TODAY = "2026-09-12"
url = "https://aihot.virxact.com/api/public/items?mode=selected&take=10"
req = urllib.request.Request(url, headers={"User-Agent": "aihot-skill/0.2.0"})
with urllib.request.urlopen(req, timeout=15) as resp:
    items = json.loads(resp.read().decode()).get("items", [])
for it in items:
    title = (it.get("title") or "").replace("'", "''")
    desc = (it.get("description") or it.get("content") or "")[:500].replace("'", "''")
    src = (it.get("source") or "aihot").replace("'", "''")
    link = (it.get("url") or "").replace("'", "''")
    sql = f"INSERT INTO news_articles (category, title, content, source, url, lang, article_date, summary, description) VALUES ('politics', E'{title}', E'{desc}', E'{src}', E'{link}', 'zh', '{TODAY}', E'{desc[:200]}', E'{desc}')"
    subprocess.run(f"docker exec radar-db psql -U radar -d radar -t -c \"{sql}\"", shell=True)
```

⚠️ politics 采集阈值：≥10 达标，<5 标「AI不足」告警（同 AI 标准，仪表盘合并展示）。

### 金价采集现状（2026-09-15 更新）

Eastmoney 国内源已恢复（2026-09-15 实测 ¥932.0/g 成功）。
- Eastmoney `push2.eastmoney.com` → ✅ 可用
- 腾讯 kline → 未验证

**金价缺失已非常态**。若采集失败仍标注「金价缺失」，但不再视为确定事件，需核查网络/源状态。

**`gold_note` 字段格式**（2026-09-05 实测）：
```
采集于 2026-09-05 | 国际GC=$4484.26 (+1.64%) | 国内AU9999=¥958.00 (-0.82%) | 美10Y TIPS=4.780% (+0.010pp)
```
验证金价时直接查 `gold_note` 即可获取完整汇总。

### collect.py GitHub 自检是假阴性

`collect.py` 的 self-check 显示 `❌ github 0/10`，但此时 gh_collect.py 已成功写入了 7 条数据到 DB。
原因：collect.py 内部 gh 路径错误（见下），导致它查 DB 得到 0 条，但数据实际已在 DB 中。

**验证方法**：不要相信 collect.py 的 self-check github 行。采集完成后直接查 DB：
```bash
docker exec radar-db psql -U radar -d radar -t -c "
SELECT category, COUNT(*) FROM news_articles
WHERE article_date = '$TODAY' GROUP BY category"
```

### gh_collect.py 初采后 article_date 可能不匹配（2026-08-29 发现）

gh_collect.py 报告 "Inserted 10/10" 但 DB 查询 `$TODAY` 显示 github=0，同时存在昨日旧数据。

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

### collect.py 超时无回退（2026-09-01 实测 600s，2026-09-10 实测 420s）

collect.py 存在 600s 超时上限，超时后 **既不写数据也不抛异常**，DB counts 完全不变。
已知卡死环节：gold 步骤（国内源全挂后的网络重试）。

**处理流程**：
1. 超时后立刻查 DB：`SELECT COUNT(*) FROM news_articles WHERE article_date = '$TODAY'`
2. 若 ai 未达标 → 用「AI aihot 直接 fetch」补（见下方，已验证有效）
3. **不要重跑整个 collect.py**（会再次卡死）

⚠️ **2026-09-10 实测**：collect.py 在 420s 即超时（非 600s），gold 未写入，无任何数据变更。AI 可通过 aihot 直采补回，gold 标注「金价缺失」即可。

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
**正确做法**：先单独跑 gh_collect.py，再用 collect.py 跑其余两项（gold + ai），不要依赖 collect.py 内部调用 GitHub。

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

### 固定高优先级源（v8 实现 / 2026-09-22 验证）

`gh_collect.py` 顶部维护 `HIGH_PRIORITY_SOURCES` 列表。每天先于 trending 抓取，cleanup 后写入，强制 `blacklist_score=9999` 置顶。

**采集链路（不依赖 gh CLI / GitHub API，防火墙环境可用）**：
1. `ungh.cc/repos/<owner>/<repo>` → 仓库元信息（stars / pushedAt）
2. `raw.githubusercontent.com/<owner>/<repo>/<branch>/README.md` → 找最新一期（正则匹配 `(docs/issue-NNN.md)`）
3. `raw.githubusercontent.com/<owner>/<repo>/<branch>/docs/issue-NNN.md` → 拿 H1 标题 + 首段摘要

**写入字段**：`category='github'` / `source='Markdown'` / `lang='zh'` / `is_new_project=false` / `blacklist_score=9999` / `stars_count=<repo.stars>` / `period_new_stars=0`。

**description 格式**：`第 N 期《主题》— 首段摘要（前 200 字）`。

**当前高优先级源**：
- `ruanyf/weekly` — 阮一峰科技爱好者周刊，每周五发布，中文科技资讯高优

**添加新源**：dict 加一项即可，branch 默认 master。

**实施细节（2026-09-22 实测，main() 关键决策）**：

| 决策 | 错误做法 | 正确做法 |
|------|---------|---------|
| `cleanup_existing(TODAY)` 时机 | 在 write 之后做（HP 源被 truncate 覆盖丢失） | **在 write 之前做**：HP 先抓 → cleanup → HP 先写 → trending 后写 |
| `main()` 失败返回值 | `if not repos: return False`（trending 失败即整体失败，HP 源也不写入） | `return len(hp_articles) >= 1 or count >= 5`（HP 源独立完成日报） |
| `description` 主题提取 | 把 H1 整段（`科技爱好者周刊（第 N 期）：主题`）塞进 description，与 title 重复 | 正则 `^科技爱好者周刊（.+?）：\s*` 提取 `theme`，title 用 `repo — theme`，description 用 `第 N 期《theme》— 摘要` |
| 首段摘要提取 | 按行判断（`issue-NNN.md` 整段是单行，会抓全段含通知尾巴） | 按 `\n\s*\n` 段落级切分 + 截到首个 `。！？!?` 之前（去掉 `**[通知]**` 等括号通知） |
| Markdown 残留清理 | raw 端把 `**` 转义成 `** **`，原 `[*_`]+` 清理会留大量空格 | 单独 `re.sub(r"\*+", "", ...)` 清转义星号 + `re.sub(r"\s+", " ", ...)` 合并空白 |
| 写入幂等 | 直接 INSERT（重复跑会落重复行） | `ON CONFLICT DO NOTHING`（虽 cleanup 已删，但仍防御重跑） |

**验收命令**（每改 HP 源必跑）：
```bash
# 1. 单元测 fetch
python3 -c "import sys; sys.path.insert(0, '/Users/apple/.shared-agent-skills/operations/radar-data-collection/scripts'); import gh_collect; print(gh_collect.fetch_high_priority_source(gh_collect.HIGH_PRIORITY_SOURCES[0]))"

# 2. 验证 DB 置顶（blacklist_score=9999 应排第 1）
docker exec radar-db psql -U radar -d radar -t -c "
SELECT title, blacklist_score FROM news_articles
WHERE article_date='$TODAY' AND category='github'
ORDER BY blacklist_score DESC NULLS LAST LIMIT 3"

# 3. 验证 push.py 读取正确（应显示 ruanyf/weekly 在 #1）
python3 -c "import sys; sys.path.insert(0, '/Users/apple/.shared-agent-skills/operations/radar-daily-report/scripts'); import push; print(push.build_msg3())"
```

### SKILL.md 描述 ≠ 代码实现的排查陷阱（2026-09-22 实测）

**症状**：SKILL.md 明确写 `ruanyf/weekly` 是固定高优先级源、有 `HIGH_PRIORITY_SOURCES` 列表、有 `fetch_high_priority_source()` 函数，但 `gh_collect.py` 里**一个对应关键字都没有**（grep 0 hits）。`references/high-priority-sources.md` 也描述了完整设计。**这是「文档先行，代码未实现」漂移**，会让人误以为「已经加过了」而跳过实际集成。

**根因**：技能设计变更时，SKILL.md + references 先更新（设计阶段），但 `~/.shared-agent-skills/.../scripts/*.py` 在另一台机器/另一会话单独维护，代码改动滞后甚至被回滚。文档是「意图」，代码是「现实」。

**排查 SOP**（任何声称 SKILL.md 已描述的功能必跑）：
```bash
# 1. 在 SKILL.md 找目标关键字
grep -n "目标关键字" ~/.hermes/skills/<cat>/<skill>/SKILL.md

# 2. 在实际脚本里 grep 同关键字
grep -n "目标关键字" ~/.shared-agent-skills/<cat>/<skill>/scripts/*.py

# 3. 若 SKILL.md 有 hits 而脚本 0 hits → 文档先行漂移，需补代码
# 4. 若脚本有 hits 但行为对不上 → 可能是死代码或被新逻辑绕过
```

**修复策略**：
- 别只改 SKILL.md 就以为完成。**同时改** `~/.shared-agent-skills/<cat>/<skill>/scripts/*.py`。
- 改完跑端到端验证：脚本成功 + DB 字段正确 + 下游 push.py 读取正确，缺一不可。
- 验收后把版本号写到 SKILL.md（如 `v8 实现 / 2026-09-22 验证`），避免下次误判为「未实现」。

**相邻漂移案例**（同技能内已发现）：
- 2026-09-22：本节 HP 源设计（已修复）
- 2026-08-28：9Router key 读取（已修复）
- 2026-08-27：gh_collect.py 日期偏移（已修复）

排查任何不工作的功能时，**先用 grep 比对 SKILL.md 和脚本关键字是否一致**，能立刻定位「文档/代码漂移」类问题。

### Network-restricted environments 适配

GitHub 主网（`github.com` / `api.github.com` / `codeload.github.com` / `objects.githubusercontent.com`）被防火墙阻挡，但 `ungh.cc` 和 `raw.githubusercontent.com` 可直连。高优先级源正是利用这两条通道实现的回退链。新增高优源时若 pattern 不在「README 找最新一期」类（如非周刊型），需要调整 `fetch_high_priority_source()` 内部步骤，**不要**改成走 gh API 或 git clone（已被防火墙挡死）。

**采集链路（不依赖 gh CLI / GitHub API）**：
1. `ungh.cc/repos/<owner>/<repo>` → 仓库元信息（stars / pushedAt）
2. `raw.githubusercontent.com/<owner>/<repo>/<branch>/README.md` → 找最新一期（正则匹配 `(docs/issue-NNN.md)`）
3. `raw.githubusercontent.com/<owner>/<repo>/<branch>/docs/issue-NNN.md` → 拿 H1 标题 + 首段摘要

**写入字段**：`category='github'` / `source='Markdown'` / `lang='zh'` / `is_new_project=false` / `blacklist_score=9999` / `stars_count=<repo.stars>` / `period_new_stars=0`。

**description 格式**：`第 N 期《主题》— 首段摘要（前 200 字）`。

**当前高优先级源**：
- `ruanyf/weekly` — 阮一峰科技爱好者周刊，每周五发布，中文科技资讯高优

**添加新源**：dict 加一项即可，branch 默认 master。

**为什么不依赖 gh CLI**：GitHub 主网（`github.com` / `api.github.com`）被防火墙阻挡，`gh` CLI 全挂。`ungh.cc` + `raw.githubusercontent.com` 回退链可达（见 `references/github-fallback-chain.md`）。

### GitHub Trending 源数量波动

GitHub Trending 每日 repo 数量不固定（周末/节假日可能 <10），**≠ 采集失败**。判断标准：
- 条目 = 0 → GitHub 失败（告警）
- 条目 1-9 → 正常记录，不触发告警（技能阈值 ≥10 仅供参考，源本身不足时无法强求）

## 验证标准

- `news_articles`: AI ≥8，GitHub ≥10，politics ≥10
- `gold_prices`: 当日有行

**验证必须直查 DB**，不要依赖 collect.py 的 self-check 输出（github 行经常假阴性）。

```bash
docker exec radar-db psql -U radar -d radar -t -c "
SELECT
  (SELECT COUNT(*) FROM news_articles WHERE article_date = '$TODAY' AND category = 'ai') as ai,
  (SELECT COUNT(*) FROM news_articles WHERE article_date = '$TODAY' AND category = 'github') as gh,
  (SELECT COUNT(*) FROM news_articles WHERE article_date = '$TODAY' AND category = 'politics') as politics,
  (SELECT COUNT(*) FROM gold_prices WHERE price_date = '$TODAY') as gold"

# 若 gold=1，查 gold_note 确认内容
docker exec radar-db psql -U radar -d radar -t -c "
SELECT price_date, intl_price_usd, domestic_price_cny, tips_yield_10y, gold_note
FROM gold_prices WHERE price_date = '$TODAY'"
```

## 告警分类（PATCH-2026-08-10-001）

| 条件 | 标注 |
|------|------|
| 金价全失败 | 「金价缺失」 |
| AI <5 | 「AI不足」 |
| politics <5 | 「AI不足」 |
| GitHub = 0（3次重试后） | 「GitHub失败」 |
| GitHub 1-9（3次重试后仍不足） | 接受，不告警（源数据不足，非采集失败） |

## 不完整数据处理规则（2026-09-01 新增）

当采集结果不满足「验证标准」时，**仍发送日报**，在对应消息中标注问题，不阻塞推送：

| 不达标项 | 日报处理 |
|----------|---------|
| 金价=0 | MSG1 显示「⚠️ 金价数据缺失」 |
| AI <5 | MSG2 显示「⚠️ AI热讯数据缺失」 |
| politics <5 | MSG2 显示「⚠️ 政治热讯数据缺失」 |
| GitHub = 0（3次重试后） | MSG3 显示「⚠️ GitHub数据缺失」 |
| GitHub 1-9（3次重试后） | MSG3 正常发送，标注「⚠️ GitHub今日源数据仅N条」（不阻塞） |

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
  (SELECT COUNT(*) FROM news_articles WHERE article_date = '2026-08-26' AND category = 'github') as gh,
  (SELECT COUNT(*) FROM gold_prices WHERE price_date = '2026-08-26') as gold;
```

## 技能目录结构

```
~/.hermes/skills/operations/radar-data-collection/   ← cron 从这里加载 SKILL.md
- 脚本：`~/.shared-agent-skills/operations/radar-data-collection/scripts/`
```

## 相关 References

- `references/9router-key-pattern.md` — 9Router key 从 SQLite 动态读取
- `references/radar-db-schema.md` — DB 表结构 + 关键列名
- `references/gold-tips.md` — 金价/TIPS 数据源历史
- `references/production-changelog-v4.md` — v4.x 字段更新历史
- `references/github-fallback-chain.md` — GitHub 主网被墙时 ungh.cc + raw 回退链（固定高优先级源底层依赖）
```
