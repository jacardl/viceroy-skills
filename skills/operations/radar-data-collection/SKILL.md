---
name: radar-data-collection
description: 雷达数据采集 — 金价、TIPS、AIHOT、GitHub 写入 PostgreSQL（docker exec）。采集失败按 PATCH-2026-08-10-001 分类告警。
category: operations
---
# radar-data-collection

每日数据采集技能。写入 `radar-db` PostgreSQL。

## 环境

- DB: `docker exec radar-db psql -U radar -d radar -t -c "SQL"`
- 外部搜索/抓取：**不使用 9Router/Tavily/Firecrawl**（2026-10-28 起）。金价=腾讯/东财/treasury.gov 直连，AI=aihot API，GitHub=playwright+ungh.cc
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

### Playwright 报错截断 + Python 3.14 greenlet ABI 陷阱（2026-10-17 实测）

`gh_collect.py` 的 `fetch_trending_via_browser()` 在 Playwright 异常时输出截断的 traceback（只显示前 6 行到 `playwright/sync_ap` 路径中间），cron 报告里看不到真实根因。

**真实根因**（Python 3.14 venv `/Users/apple/.agent-reach-venv314`）：

```
File ".../playwright/_impl/_greenlets.py", line 17
  import greenlet
File ".../greenlet/__init__.py", line 26
  from ._greenlet import _C_API
ModuleNotFoundError: No module named 'greenlet._greenlet'
```

Python 3.14 + 已装 greenlet wheel C 扩展 ABI 不匹配 → Playwright sync_api **import 阶段就崩**，根本到不了 chromium 启动。

**完整诊断**（绕过脚本的截断，直接 import 拿全栈）：

```bash
/Users/apple/.agent-reach-venv314/bin/python3 -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(args=['--no-sandbox','--disable-dev-shm-usage'])
"
```

**修复**：

```bash
/Users/apple/.agent-reach-venv314/bin/pip install --upgrade --force-reinstall greenlet playwright
```

**修后验证**（端到端）：

```bash
/Users/apple/.agent-reach-venv314/bin/python3 ~/.shared-agent-skills/operations/radar-data-collection/scripts/gh_collect.py $(TZ=Asia/Shanghai date '+%Y-%m-%d')
```

应输出 `Inserted N repos (HP=1, trending=M)`，M > 0 表示 trending 恢复。

**HP 源只有 1 条 (ruanyf/weekly)**：trending 恢复前即使 HP 链路正常也只能给日报 1 条 GH，远不够 ≥10 目标。`playwright-chromium-missing.md` 描述的 "HP-only 模式" 是这种状态下的降级方案，不是终态。

**排查 SOP 升级**：Playwright 链路不通 → 先 `python3 -c "from playwright.sync_api import sync_playwright"` 直跑 import，看是 import 阶段崩（greenlet/cffi/typing_extensions 等依赖）还是 launch 阶段崩（chromium 真的缺）。脚本内的截断 traceback 不足以定位深根因。

详见 `references/playwright-chromium-missing.md`（已补充此根因章节）。

### gh_collect.py Playwright `networkidle` 永久超时（2026-10-23 实测，已修）

**症状**：Playwright 报 `TimeoutError: Page.goto: Timeout 20000ms exceeded ... waiting until "networkidle"`，脚本只打印截断 traceback，最终 `Inserted 0 repos (HP=0, trending=0)`。

**诊断**：这类超时**页面其实已经渲染完成**——`page.content()` 有 563KB HTML、9 个 `<article class="Box-row">` 节点。失败的是 `networkidle` 等待条件本身（GitHub Trending 长轮询/analytics 请求永不 idle），不是网络或 chromium 问题。

**关键区分**：
- `import` 阶段崩 → greenlet ABI 问题（见上一节）
- `launch` 阶段崩 → chromium 真缺
- `goto` 超时但 `page.content()` 有内容 → **networkidle 等待条件问题**，改 `wait_until` 即可

**修复**（已写入 `gh_collect.py` 源文件）：
```python
"    try:\n"
"        page.goto('https://github.com/trending', wait_until='domcontentloaded', timeout=30000)\n"
"    except Exception as ge:\n"
"        print('GOTO_WARN:' + type(ge).__name__)\n"
"    page.wait_for_timeout(5000)\n"
```
`domcontentloaded` + 5s 固定等待后，解析到 9 个 article（修复前 0 个）。

⚠️ 顺带发现：**GitHub Trending 页面当天只有 9 个 article**，过滤 sponsors 3 个 + 跨日去重 2 个 → trending 仅 4 条。这不是采集失败，属源数据不足，按规则不告警。

### HP 源 ungh.cc 429（2026-10-23 实测）

`ruanyf/weekly` 的 `ungh.cc/repos/...` 偶发 `HTTP Error 429: Too Many Requests`。**不重试**——直接失败跳过，HP 源缺失只少 1 条。raw.githubusercontent.com 仍可达（README + issue 文档链路正常）。

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

### 金价采集现状（2026-09-15 更新，2026-10-20 新增 fallback 链）

Eastmoney 国内源已恢复（2026-09-15 实测 ¥932.0/g 成功），但 **AU9999 secid=131.96 会随机报 "Remote end closed connection without response"**。
- Eastmoney GC 主源 → ✅ 可用（secid=129.96，国际金价）
- Eastmoney AU9999 → ⚠️ 随机失败，需 fallback
- 腾讯 kline → 未验证

**金价 fallback 采集顺序**（2026-10-20 实测）：
```python
# 1. 国际金价 GC=F（Yahoo Finance，可达）
url = "https://query1.finance.yahoo.com/v8/finance/chart/GC%3DF?interval=1d&range=1d"
# meta.regularMarketPrice → intl_price_usd

# 2. 国内 AU9999（Eastmoney secid=131.96，失败时跳过）
# 失败时 domestic_price=None，gold_note 标注"待采"

# 3. TIPS（Treasury.gov CSV，可达）
url = "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/2026/all?type=daily_treasury_yield_curve&field_tdr_date_value=2026&download=true"
# 10/19/2026 行，"10 Yr" 列 → tips_yield_10y
```

⚠️ **gold_prices UPDATE 必须显式 SET 所有字段**：
```sql
UPDATE gold_prices SET
  intl_price_usd=4161.2,
  domestic_price_cny=NULL,          -- 国内采不到时显式 NULL
  tips_yield_10y=5.15,
  gold_note=E'采集于 2026-10-20 | ...'
WHERE price_date='2026-10-20'
```
省略字段不会保留原值而是保持原样——但若行已存在且某字段之前有值，UPDATE 不带该字段会将其清空。**安全做法：UPDATE 时带齐所有字段**。

**金价缺失已非常态**。若采集失败仍标注「金价缺失」，但不再视为确定事件，需核查网络/源状态。

### 金价两个真实 bug（2026-10-24 实测并已修 `collect.py`）

**Bug 1：腾讯 `v_hf_GC` 昨收索引错 → 涨跌幅符号反向**

实测返回（04:06 CST）：
```
v_hf_GC="4007.94,-1.29,4009.70,4009.90,4050.20,3989.10,04:15:02,4060.40,4042.20,0,2,1,2026-10-24,纽约黄金"
```
字段实际含义：[0]=现价 [1]=涨跌额 [2]=买 [3]=卖 [4]=最高 [5]=**最低** [6]=时间 [7]=**昨结算价(prev_close)** [8]=开盘 [12]=日期

旧代码用 `fields[5]`（最低价）当 prev_close → 涨跌幅算成 `(4007.94-3989.10)/3989.10 = +0.47%`，方向反了（真实是 -1.29%）。
**已修为 `fields[7]`**。

**Bug 2：国内 AU9999 源全挂时无 fallback → gold 行写不进去**

2026-10-24 东财 `push2.eastmoney.com` / `push2his.eastmoney.com` 全部 "Remote end closed connection without response"（`secid=118.AU9999` 与 `131.96` 都空）。腾讯 `qt.gtimg.cn/q=hf_GC` 正常但**只给国际金价**。

**新增 fallback：新浪 `gds_AU9999`**（`~/.shared-agent-skills/operations/radar-data-collection/scripts/collect.py` 的 `_fetch_dom_gold()` 末尾）：
```python
raw = http_get("https://hq.sinajs.cn/list=gds_AU9999",
               headers={"Referer": "https://finance.sina.com.cn"}, timeout=10)
# var hq_str_gds_AU9999="862.99,0,862.99,863.80,872.99,855.00,02:30:00,864.00,865.00,17738,..."
# f[0]=现价  f[6]=时间  f[7]=昨收  f[8]=今开
```
2026-10-24 实测 ¥862.99/g (-0.12%)，源优先级现为：东财实时 → 东财 kline → **新浪 gds_AU9999**。

⚠️ **新浪源返回 GBK 编码**，但数值字段是纯 ASCII，Python 默认 utf-8 解码不会报错（仅尾部中文乱码），可安全直接用。

**其他可用源备忘**（2026-10-24 实测）：
- `https://qt.gtimg.cn/q=hf_XAU` → 伦敦金现货（= sina 同源），可用于交叉校验国际金价
- `https://hq.sinajs.cn/list=hf_GC` → 腾讯黄金同源
- `https://www.sge.com.cn/graph/quotations` → 上金所 Au99.99 分时 JSON（`now` / `data` / `delaystr`），但 **delaystr 显示的是隔日时间戳，凌晨调用拿到的是隔日数据**，不可直接用
- `query1.finance.yahoo.com` 常返 `Edge: Too Many Requests`；改用 `query2.finance.yahoo.com` + `User-Agent: Mozilla/5.0` 可通

**collect.py gold 步骤的 retry 代价**：RETRY_DELAY=300s × 3 次 = 900s 才放弃，且**失败时不写 gold 行**。东财全挂时这个等待纯属浪费——新浪 fallback 命中后单次即成功。若再有国内源全挂场景，直接跑单步：
```bash
cd ~/.shared-agent-skills/operations/radar-data-collection/scripts && python3 -c "
import sys; sys.argv=['collect.py','$(TZ=Asia/Shanghai date +%Y-%m-%d)']; sys.path.insert(0,'.')
import collect; collect.step_gold(); print('rows:', collect.count_gold())"
```

**`gold_note` 字段格式**（2026-09-05 实测）：
```
采集于 2026-09-05 | 国际GC=$4484.26 (+1.64%) | 国内AU9999=¥958.00 (-0.82%) | 美10Y TIPS=4.780% (+0.010pp)
```
验证金价时直接查 `gold_note` 即可获取完整汇总。

### collect.py GitHub 自检是假阴性

`collect.py` 的 self-check 显示 `❌ github 0/10`，但此时 gh_collect.py 已成功写入了 7 条数据到 DB。
原因：collect.py 内部 gh 路径错误（已于 2026-10-22 修复，见下节），导致它查 DB 得到 0 条，但数据实际已在 DB 中。

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
TODAY = "2026-10-20"
url = "https://aihot.virxact.com/api/public/items?mode=selected&take=10"
req = urllib.request.Request(url, headers={"User-Agent": "aihot-skill/0.2.0"})
with urllib.request.urlopen(req, timeout=15) as resp:
    items = json.loads(resp.read().decode()).get("items", [])
for it in items:
    title = (it.get("title") or "").replace("'", "''")
    desc = (it.get("description") or it.get("content") or "")[:500].replace("'", "''")
    src = (it.get("source") or "aihot").replace("'", "''")
    link = (it.get("url") or "").replace("'", "''")
    sql = f"INSERT INTO news_articles (category, title, content, source, url, lang, article_date, summary, description) VALUES ('ai', E'{title}', E'{desc}', E'{src}', E'{link}', 'zh', '{TODAY}', E'{desc[:200]}', E'{desc}')"
    subprocess.run(f"docker exec radar-db psql -U radar -d radar -t -c \"{sql}\"", shell=True)
```

⚠️ **psycopg2 直接连接无效**（端口映射问题），所有手动 INSERT 必须走 `docker exec radar-db psql -U radar -d radar -t -c "SQL"`。

### `news_articles` 表无 `score` 列（2026-08-28 实测）

`collect.py` 的 `insert_news()` 试图写入 `score` 列，但表里无此列（schema 以 `stars_count` 替代）。**手动 INSERT 时必须省略 `score`**，否则 500 报错。
正确列：`category, title, content, source, url, lang, article_date, summary, description`

### collect.py GitHub 步骤陷阱（2026-10-22 已修复）

`collect.py` 曾硬编码失效的 gh_collect.py 路径：
```
/Users/apple/.openclaw/workspace/scripts/radar/gh_collect.py  # 不存在！
```
**危害比「self-check 假阴性」更严重**：`step_github()` 先 `clean_news("github")` 删掉当日 GitHub 行，再调子脚本 → 子脚本不存在 → 3 次重试全失败 → **当日 GitHub 数据被清空**（不报错、不写回）。

**2026-10-22 修复**（`~/.shared-agent-skills/operations/radar-data-collection/scripts/collect.py`）：
- `GH_SCRIPT` → `/Users/apple/.shared-agent-skills/operations/radar-data-collection/scripts/gh_collect.py`
- subprocess 里的 `cd /Users/apple/.openclaw/workspace && python3 scripts/radar/gh_collect.py` → `cd /Users/apple/.shared-agent-skills/operations/radar-data-collection && python3 scripts/gh_collect.py`

修复后仍**按 SKILL.md 顺序先单独跑 gh_collect.py 再跑 collect.py**，避免竞态与清空风险。
改完必须 `python3 -m py_compile collect.py gh_collect.py` 验证语法。

### gh_collect.py repo 正则过度转义（2026-10-22 实测）

嵌入 Playwright 脚本里的 repo 匹配正则写成过度转义的字符类：
```python
# 错误：\\- 和 \\. 在字符类里变成字面反斜杠，连字符仓库全被丢弃
([a-zA-Z0-9_\\-\\.]+/[a-zA-Z0-9_\\-\\.]+)
# 正确
([a-zA-Z0-9_\-\.]+/[a-zA-Z0-9_\-\.]+)
```
**症状**：页面渲染了 12 个 article，解析器只匹配到 5 个 repo（连字符项目如 `security-audit-skill` 消失），GitHub 条目永远凑不满 10。

**排查 SOP**：解析数少于渲染数时，先打印页面 `article` 节点数与正则命中数对比，再 dump 生成的 `script_body` 检查正则源码（生成后的字符串里 `\\\\-` = 源码里的 `\\-` = 错的）。
**修复原则**：改**源文件** `gh_collect.py` 的正则，不要只改临时生成脚本——否则下次运行又退回坏正则。

### gh_collect.py 同日自去重（2026-10-22 实测）

`get_recently_pushed_repos(DEDUP_WINDOW_DAYS=2)` 查 DB 近 N 天已推过的 owner_repo 过滤 trending，但去重发生在 `cleanup_existing(TODAY)` **之前**，所以**当日已写入的行也被算进去** → 重跑时把自己的行过滤掉，条数从 7 塌到 2，且每次运行结果不稳定。

**修复**：SQL 加当日排除条件：
```sql
AND article_date < DATE '{TODAY}'
```
**修复后**：重复运行稳定输出 8 条（1 高优源 + 7 trending）。
**验收**：连续跑两次 gh_collect.py，条数必须一致；不一致说明仍有自去重。

### 中文改写链路与 `<think>` 清理（2026-10-22 实测）

AI/GitHub 两类 description 都必须落中文。**采集脚本不调任何 LLM**：中文改写由 06:00 日报 cron 轮次在 agent 侧用自身模型生成，经 `fill_ai_zh.py --list` → `/tmp/radar_zh_done.json` → `--apply` 写回（见 radar-daily-report SKILL）。

⚠️ **`cx/gpt-5.6-sol` 经常返回 HTTP 503**，不要当作链路故障，链上继续往下试即可。

⚠️ **模型输出会带 `<think>...</think>` 推理块**，直接入库会污染 description。入库前必须：
1. 剥掉 `<think>` 段；
2. 只取最后一行/最后一句作为中文摘要；
3. 校验：含中文、无 `<think>`、长度 ≥20 字。

**GitHub 类**直接复用 `~/.shared-agent-skills/operations/radar-daily-report/scripts/fill_ai_zh.py`（注意路径在 `.shared-agent-skills`，不是 `.hermes/skills`）：
```bash
python3 ~/.shared-agent-skills/operations/radar-daily-report/scripts/fill_ai_zh.py --days=1 --category=github
```
输出 `updated=N failed=0` 即通过。

⚠️ **`fill_ai_zh.py` 的 `--category` 只认 `ai` / `github`**，模型链 `cx/gpt-5.6-sol → minimax-cn/MiniMax-M3 → minimax-cn/MiniMax-M2.7 → ds/deepseek-chat`，`call_llm()` 里会剥 `<think>` 块 + 取最后一行。

⚠️ **`--days=1` 改写范围是「近 1 天」不是「今天」**（`CURRENT_DATE - INTERVAL '1 days'`），会连带改写前一天的行。要严格限定今天，只能 import 模块后 monkey-patch `sql()` 替换日期条件：
```python
orig = f.sql
f.sql = lambda q: orig(q.replace("article_date >= (CURRENT_DATE - INTERVAL '1 days')", "article_date = 'YYYY-MM-DD'"))
f.run_category('github', 1, False, False)
```

⚠️ **9Router key 来源**：`fill_ai_zh.py` 从 `~/.hermes/config.yaml` 的 `providers.9router.api_key` 读取（不是 sqlite）。

**验收查询**（两类都要跑，确认无 `<think>` / 无纯英文）：
```bash
docker exec radar-db psql -U radar -d radar -t -c "
SELECT title, left(description,50) FROM news_articles
WHERE article_date='$TODAY' AND category IN ('ai','github')"
```
全部 description 含中文即可；只要有一条落英文兜底，**必须**在飞书统计里标注该异常。

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

### 固定高优先级源（v9 升级 / 2026-10-11 验证：去重 + sponsors 过滤 + HP 降频）

`gh_collect.py` 顶部维护 `HIGH_PRIORITY_SOURCES` 列表。每天先于 trending 抓取，cleanup 后写入。

**v9 新行为**（2026-10-11 实测）：
- **HP 降频**：`spec` 支持 `dedup_window_days`（默认 7）+ `score_dedup`（默认 100）。若 `hp_pinned_recently()` 检测到该 owner_repo 近 N 天已以 `blacklist_score>=9999` 置顶过，score 改为 `score_dedup`（不再置顶但仍写入）。当前 `ruanyf/weekly` 已配置——`ruanyf/weekly` 周五更新，周一~周四置顶是浪费名额。
- **跨日去重**：trending 入榜前 `get_recently_pushed_repos(DEDUP_WINDOW_DAYS=2)` 查 DB 近 2 天已推过的 owner_repo，过滤掉。常驻霸榜项目（如 sponsors/* 大型工具、半年不变的热门框架）自然掉出。
- **sponsors/* 过滤**：`is_sponsor()` 默认过滤所有 `sponsors/*` 推广位，仅保留 `SPONSOR_WHITELIST`（当前仅 `sponsors/mattpocock`，Rust/Skills 专家有真价值）。

**配置常量**（`gh_collect.py` 顶部）：
```python
SPONSOR_WHITELIST = ["sponsors/mattpocock"]   # 保留白名单；其它 sponsors/* 全过滤
DEDUP_WINDOW_DAYS = 2                          # 跨日去重窗口（天）
```

**HP 源 spec 新字段**：
- `score_dedup`：降频后 score（默认 100）
- `dedup_window_days`：降频窗口（默认 7）

**新增 helpers**（`cleanup_existing` 之后）：
- `get_recently_pushed_repos(days)` → set — 查 DB 近 N 天已推过的 owner_repo
- `hp_pinned_recently(owner_repo, days)` → bool — HP 源近 N 天是否以置顶身份写过库
- `is_sponsor(repo_full)` → bool — sponsors/* 推广位判定（白名单豁免）

**采集链路（不依赖 gh CLI / GitHub API，防火墙环境可用）**：
1. `ungh.cc/repos/<owner>/<repo>` → 仓库元信息（stars / pushedAt）
2. `raw.githubusercontent.com/<owner>/<repo>/<branch>/README.md` → 找最新一期（正则匹配 `(docs/issue-NNN.md)`）
3. `raw.githubusercontent.com/<owner>/<repo>/<branch>/docs/issue-NNN.md` → 拿 H1 标题 + 首段摘要

**写入字段**：`category='github'` / `source='Markdown'` / `lang='zh'` / `is_new_project=false` / `blacklist_score=score 或 score_dedup`（v9 决定） / `stars_count=<repo.stars>` / `period_new_stars=0`。

**description 格式**：`第 N 期《主题》— 首段摘要（前 200 字）`。

**当前高优先级源**：
- `ruanyf/weekly` — 阮一峰科技爱好者周刊，每周五发布，中文科技资讯高优

**添加新源**：dict 加一项即可，branch 默认 master。若新源发布频率低于每日，建议同时配 `dedup_window_days` + `score_dedup` 启用 v9 降频逻辑。

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
- 2026-10-11：v9 加了 `dedup_window_days` / `score_dedup` / `SPONSOR_WHITELIST` / `DEDUP_WINDOW_DAYS` / 3 个 helper（`get_recently_pushed_repos` / `hp_pinned_recently` / `is_sponsor`），本节已更新；改完 SKILL.md 时必须同时改 gh_collect.py，反向亦然
- 2026-10-11：v9 加了 `dedup_window_days` / `score_dedup` / `SPONSOR_WHITELIST` / `DEDUP_WINDOW_DAYS` / 3 个 helper（`get_recently_pushed_repos` / `hp_pinned_recently` / `is_sponsor`），本节已更新；改完 SKILL.md 时必须同时改 gh_collect.py，反向亦然
- 2026-08-28：9Router key 读取（已修复）
- 2026-08-27：gh_collect.py 日期偏移（已修复）
- 2026-10-22：collect.py 的 GH_SCRIPT 路径 + subprocess cd 路径（已修复；修前会清空当日 GitHub 行）
- 2026-10-22：gh_collect.py 嵌入脚本 repo 正则过度转义（已修复，解析 5 → 12）
- 2026-10-22：get_recently_pushed_repos 同日自去重（已修复，重跑稳定 8 条）

排查任何不工作的功能时，**先用 grep 比对 SKILL.md 和脚本关键字是否一致**，能立刻定位「文档/代码漂移」类问题。

### Network-restricted environments 适配

GitHub 主网（`github.com` / `api.github.com` / `codeload.github.com` / `objects.githubusercontent.com`）被防火墙阻挡，但 `ungh.cc` 和 `raw.githubusercontent.com` 可直连。高优先级源正是利用这两条通道实现的回退链。新增高优源时若 pattern 不在「README 找最新一期」类（如非周刊型），需要调整 `fetch_high_priority_source()` 内部步骤，**不要**改成走 gh API 或 git clone（已被防火墙挡死）。

**采集链路（不依赖 gh CLI / GitHub API）**：
1. `ungh.cc/repos/<owner>/<repo>` → 仓库元信息（stars / pushedAt）
2. `raw.githubusercontent.com/<owner>/<repo>/<branch>/README.md` → 找最新一期（正则匹配 `(docs/issue-NNN.md)`）
3. `raw.githubusercontent.com/<owner>/<repo>/<branch>/docs/issue-NNN.md` → 拿 H1 标题 + 首段摘要

**写入字段**：`category='github'` / `source='Markdown'` / `lang='zh'` / `is_new_project=false` / `blacklist_score=score 或 score_dedup`（v9 决定） / `stars_count=<repo.stars>` / `period_new_stars=0`。

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

- `news_articles`: AI ≥8，GitHub ≥10
- `gold_prices`: 当日有行

**验证必须直查 DB**，不要依赖 collect.py 的 self-check 输出（github 行经常假阴性）。

```bash
docker exec radar-db psql -U radar -d radar -t -c "
SELECT
  (SELECT COUNT(*) FROM news_articles WHERE article_date = '$TODAY' AND category = 'ai') as ai,
  (SELECT COUNT(*) FROM news_articles WHERE article_date = '$TODAY' AND category = 'github') as gh,
  (SELECT COUNT(*) FROM gold_prices WHERE price_date = '$TODAY') as gold"

# 若 gold=1，查 gold_note 确认内容
docker exec radar-db psql -U radar -d radar -t -c "
SELECT price_date, intl_price_usd, domestic_price_cny, tips_yield_10y, gold_note
FROM gold_prices WHERE price_date = '$TODAY'"

# 验收中文改写（2026-10-23 加）：bad_desc 必须为 0，否则飞书统计要标「⚠️ 中文未改写」
docker exec radar-db psql -U radar -d radar -t -c "
SELECT COUNT(*) FROM news_articles WHERE article_date='$TODAY'
AND (description !~ '[一-龥]' OR description ~ '<think>' OR length(coalesce(description,''))<20)"
```

## 告警分类（PATCH-2026-08-10-001）

| 条件 | 标注 |
|------|------|
| 金价全失败 | 「金价缺失」 |
| AI <5 | 「AI不足」 |
| GitHub = 0（3次重试后） | 「GitHub失败」 |
| GitHub 1-9（3次重试后仍不足） | 接受，不告警（源数据不足，非采集失败） |

## 不完整数据处理规则（2026-09-01 新增）

当采集结果不满足「验证标准」时，**仍发送日报**，在对应消息中标注问题，不阻塞推送：

| 不达标项 | 日报处理 |
|----------|---------|
| 金价=0 | MSG1 显示「⚠️ 金价数据缺失」 |
| AI <5 | MSG2 显示「⚠️ AI热讯数据缺失」 |
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
- `references/playwright-chromium-missing.md` — gh_collect.py Playwright chromium 缺失场景，HP-only 模式降级处理
- `references/gh-collect-and-collect-py-fixes-2026-10-22.md` — 2026-10-22 修复记录：collect.py GitHub 路径失效（会清空当日数据）、repo 正则过度转义、同日自去重、改写 `<think>` 污染
- `references/collect-chain-fixes-2026-10-23.md` — 2026-10-23 修复记录：Playwright `networkidle` 永久超时、fill_ai_zh.py 模型链扩容、ungh.cc 429、验收 SQL 带 `bad_desc` 项
