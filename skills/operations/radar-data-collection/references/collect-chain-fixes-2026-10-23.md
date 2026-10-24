# 采集链路修复记录 — 2026-10-23

当日 cron `a37d67ec5987` 采集，三处新根因。全部已写入**源文件**并端到端验证。

---

## 1. `gh_collect.py` Playwright `networkidle` 永久超时

### 症状

```
[gh_collect] Playwright error: Traceback (most recent call last):
  File "/var/folders/.../tmpXXXX.py", line 7, in <module>
    page.goto('https://github.com/trending', wait_until='networkidle', timeout=20000)
    ~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
[gh_collect] WARN: Playwright returned no trending repos (will rely on HP sources only)
[gh_collect] Inserted 0 repos (HP=0, trending=0)
```

脚本内 traceback 被截断（只到 `page.goto` 那一行），看不出是 TimeoutError 还是别的。

### 真实根因

**页面其实已经渲染完成**。手工复现：

```python
with sync_playwright() as p:
    browser = p.chromium.launch(args=['--no-sandbox','--disable-dev-shm-usage'])
    page = browser.new_page()
    try:
        page.goto('https://github.com/trending', wait_until='networkidle', timeout=20000)
    except Exception as e:
        print("GOTO FAIL:", type(e).__name__)   # → TimeoutError
    page.wait_for_timeout(3000)
    html = page.content()
    print(len(html))                            # → 563348
    print(len(re.findall(r'<article[^>]*class="Box-row"[^>]*>(.*?)</article>', html, re.DOTALL)))  # → 9
```

`page.content()` 有 563KB HTML、9 个 `<article class="Box-row">` 节点。失败的只是
`networkidle` 这个**等待条件**本身 —— GitHub Trending 页有长轮询/analytics 请求，
连接永不 idle，于是 20s 超时。**不是网络问题、不是 chromium 缺失、不是 greenlet ABI 问题。**

### 三类故障的区分方法（重要，别再混）

| 现象 | 根因 | 修法 |
|------|------|------|
| `import` 阶段崩（`ModuleNotFoundError: greenlet._greenlet`） | Python 3.14 greenlet ABI | `pip install --upgrade --force-reinstall greenlet playwright` |
| `launch` 阶段崩（`Executable doesn't exist`） | chromium 真缺 | `playwright install chromium` |
| `goto` 超时但 `page.content()` 有内容 | `networkidle` 等待条件 | 改 `wait_until`（本次修复） |

### 修复（已写入 `scripts/gh_collect.py` 源文件）

```python
"    try:\n"
"        page.goto('https://github.com/trending', wait_until='domcontentloaded', timeout=30000)\n"
"    except Exception as ge:\n"
"        print('GOTO_WARN:' + type(ge).__name__)\n"
"    page.wait_for_timeout(5000)\n"
```

修复后：`Playwright parsed 9 repos` → 过滤 sponsors 3 → 去重 2 → trending 4 条。

⚠️ **GitHub Trending 页面当天只有 9 个 article**。这是源数据不足，不是采集失败，
按 PATCH-2026-08-10-001 不告警，只在飞书统计标「今日源数据仅 N 条」。

### 排查 SOP 升级

Playwright 链路不通 → 先跑 import 拿全栈（判 import 崩）→ 再跑 launch（判 chromium 缺）
→ 再跑 goto + `page.content()` 长度 + article 节点数（判等待条件问题）。
**脚本内截断 traceback 不足以定位深根因。**

---

## 2. `fill_ai_zh.py` 模型链太短

### 症状

`SYS_BY_CAT` 只有 `{"ai": ..., "github": ...}`。
模型链只有 `["ds/deepseek-chat"]` 一档。

### 修复（已写入 `scripts/fill_ai_zh.py`）

1. 模型链扩为：
   `cx/gpt-5.6-sol` → `minimax-cn/MiniMax-M3` → `minimax-cn/MiniMax-M2.7` → `ds/deepseek-chat`
   （`cx/gpt-5.6-sol` 经常 503，链上继续，不要当链路故障。）
2. `call_llm()` 里剥 `<think>` 块 + 取最后一行：

```python
out = resp["choices"][0]["message"]["content"].strip().strip('"').strip("'").strip()
if "<think>" in out:
    out = re.sub(r"<think>.*?</think>", "", out, flags=re.DOTALL).strip()
    lines = [l.strip() for l in out.splitlines() if l.strip()]
    if lines:
        out = lines[-1]
```

### 陷阱：`--days=1` ≠ 今天

SQL 条件是 `article_date >= (CURRENT_DATE - INTERVAL '1 days')` —— **近 1 天**，
会连带改写前一天的行。要严格限定今天，import 模块后 monkey-patch `sql()`：

```python
import importlib.util
spec = importlib.util.spec_from_file_location("f", "scripts/fill_ai_zh.py")
f = importlib.util.module_from_spec(spec); spec.loader.exec_module(f)
orig = f.sql
f.sql = lambda q: orig(q.replace(
    "article_date >= (CURRENT_DATE - INTERVAL '1 days')",
    "article_date = '2026-10-23'"))
f.run_category('github', 1, False, False)
```

### 9Router key 来源差异

- `collect.py` → `~/.9router/db/data.sqlite`（`SELECT key FROM apiKeys LIMIT 1`，sqlite3 默认返回 `str`）
- `fill_ai_zh.py` → `~/.hermes/config.yaml` 的 `providers.9router.api_key`

两个脚本取 key 路径不同，改任一边的鉴权时别只改一边。

---

## 3. HP 源 ungh.cc 429

`ruanyf/weekly` 首采报 `HTTP Error 429: Too Many Requests`（ungh.cc 限流）。
**不重试**，直接跳过，HP 源只少 1 条。重跑即恢复（v9 降频逻辑生效，score 100 不置顶）。
raw.githubusercontent.com 全程可达（README + issue 文档链路正常）。

---

## 验收 SQL（采集后必跑）

```bash
docker exec radar-db psql -U radar -d radar -t -c "
SELECT
  (SELECT COUNT(*) FROM news_articles WHERE article_date='$TODAY' AND category='ai') ai,
  (SELECT COUNT(*) FROM news_articles WHERE article_date='$TODAY' AND category='github') gh,
  (SELECT COUNT(*) FROM gold_prices WHERE price_date='$TODAY') gold,
  (SELECT COUNT(*) FROM news_articles WHERE article_date='$TODAY'
     AND (description !~ '[一-龥]' OR description ~ '<think>' OR length(coalesce(description,''))<20)) bad_desc;"
```

最后一项 `bad_desc` 必须是 0。非 0 → 飞书统计必须标「⚠️ 中文未改写」。

## 当日结果

ai=10 / github=5 / gold=1 / bad_desc=0。
