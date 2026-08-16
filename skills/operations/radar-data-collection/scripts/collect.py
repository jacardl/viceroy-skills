#!/usr/bin/env python3
"""
雷达数据采集 v4.0 — 确定性脚本，无 LLM 自由发挥。

铁律：
  1. 所有字段映射、来源 URL、解析规则全部硬编码在本文件
  2. cron 只负责执行 `python3 collect.py`，不塞 prompt 指令
  3. 任何业务判断（选哪条新闻、翻译什么）必须走固定 API/规则，不走 LLM

CRON调用:
  export TZ=Asia/Shanghai && python3 /Users/apple/.openclaw/workspace/scripts/radar/collect.py [YYYY-MM-DD]
"""

import os, sys, time, subprocess, json, re
from datetime import datetime

# ═══════════════════════════════════════════════════════════
# 运行时配置（北京时间固定，不依赖 LLM 判断）
# ═══════════════════════════════════════════════════════════

os.environ["TZ"] = "Asia/Shanghai"

TODAY = sys.argv[1] if len(sys.argv) > 1 else None
if not TODAY:
    r = subprocess.run(
        ["docker", "exec", "radar-db", "date", "+%Y-%m-%d"],
        capture_output=True, text=True, timeout=5
    )
    TODAY = r.stdout.strip() or datetime.now().strftime("%Y-%m-%d")

# 网络
NINE_ROUTER_URL     = "http://localhost:20128/v1/web/fetch"
NINE_ROUTER_SEARCH  = "http://localhost:20128/v1/search"
NINE_ROUTER_KEY     = "sk-0d68daa6645450e7-bc1xz4-8ac6a7da"
AIHOT_API           = "https://aihot.virxact.com/api/public/items?mode=selected&take=10"
AIHOT_UA            = "aihot-skill/0.2.0"

# GitHub 外部脚本
GH_SCRIPT = "/Users/apple/.openclaw/workspace/scripts/radar/gh_collect.py"

# 重试
MAX_RETRIES = 3
RETRY_DELAY = 300  # 5 min

# ═══════════════════════════════════════════════════════════
# DB helpers（确定性，无 LLM）
# ═══════════════════════════════════════════════════════════

def psql(sql):
    r = subprocess.run(
        ["docker", "exec", "radar-db", "psql", "-U", "radar", "-d", "radar",
         "-t", "-c", sql],
        capture_output=True, text=True, timeout=30
    )
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip())
    return r.stdout.strip()

def count_news(cat):
    raw = psql(f"SELECT COUNT(*) FROM news_articles WHERE article_date='{TODAY}' AND category='{cat}';").strip()
    return int(raw) if raw else 0

def count_gold():
    raw = psql(f"SELECT COUNT(*) FROM gold_prices WHERE price_date='{TODAY}';").strip()
    return int(raw) if raw else 0

def clean_news(cat):
    psql(f"DELETE FROM news_articles WHERE article_date='{TODAY}' AND category='{cat}';")

def clean_gold():
    psql(f"DELETE FROM gold_prices WHERE price_date='{TODAY}';")

def esc(s):
    if s is None: return "NULL"
    v = str(s).replace("'", "''").replace("\n", " ")[:10000]
    return f"'{v}'"

def insert_news(cat, title, content, source, url, lang, score=1.0, summary="", description="", region=None):
    """确定性 INSERT — 全字段硬编码，不走 LLM 决策。
    字段：
      cat:        github/ai/politics
      region:     🔴亚太 / 🔵中东·欧洲 / 🟢美洲（仅 politics 用），默认 🟢
    """
    if not region:
        region = "🟢"
    psql(f"""INSERT INTO news_articles
        (article_date, category, title, content, source, url, lang,
         blacklist_score, summary, description, region)
    VALUES
        ('{TODAY}', {esc(cat)}, {esc(title)}, {esc(content)},
         {esc(source)}, {esc(url)}, {esc(lang)},
         {score}, {esc(summary)}, {esc(description[:300] if description else '')},
         {esc(region)})
    ON CONFLICT DO NOTHING;""")

def insert_gold(intl_price, intl_change_pct, dom_price, dom_change_pct,
                tips_yield, tips_change, gold_note=""):
    """金价 INSERT — 字段含义固定（铁律）：
      intl_price_change   = (今-昨)/昨 × 100  (百分比)
      domestic_price_change = (今-昨)/昨 × 100 (百分比)
      shanghai_gold_rmb_per_gram = 同 domestic_price_cny
      gold_note = 采集说明（数据源/时间/异常）
    """
    if not gold_note:
        gold_note = f"采集于 {TODAY} | 腾讯GC + 东财AU9999 + Treasury.gov"
    psql(f"""INSERT INTO gold_prices
        (price_date, intl_price_usd, intl_price_change,
         domestic_price_cny, domestic_price_change,
         tips_yield_10y, tips_yield_change, shanghai_gold_rmb_per_gram,
         gold_note)
    VALUES
        ('{TODAY}', {intl_price}, {intl_change_pct},
         {dom_price}, {dom_change_pct}, {tips_yield}, {tips_change}, {dom_price},
         {esc(gold_note)})
    ON CONFLICT (price_date) DO UPDATE SET
        intl_price_usd=EXCLUDED.intl_price_usd,
        intl_price_change=EXCLUDED.intl_price_change,
        domestic_price_cny=EXCLUDED.domestic_price_cny,
        domestic_price_change=EXCLUDED.domestic_price_change,
        tips_yield_10y=EXCLUDED.tips_yield_10y,
        tips_yield_change=EXCLUDED.tips_yield_change,
        shanghai_gold_rmb_per_gram=EXCLUDED.shanghai_gold_rmb_per_gram,
        gold_note=EXCLUDED.gold_note;""")

def lock_set(tag):
    psql(f"""INSERT INTO push_locks (lock_date, locked_by)
    VALUES ('{TODAY}', '{tag}')
    ON CONFLICT (lock_date) DO UPDATE SET locked_at=NOW(), locked_by='{tag}';""")

# ═══════════════════════════════════════════════════════════
# 网络 helpers（确定性，无 LLM）
# ═══════════════════════════════════════════════════════════

import urllib.request
from urllib.error import URLError, HTTPError

def http_post(url, payload, timeout=60):
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body,
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {NINE_ROUTER_KEY}"},
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  WARN http_post {url[-30:]}: {e}")
        return None

def http_get(url, headers=None, timeout=30):
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  WARN http_get {url[-30:]}: {e}")
        return None

def http_json(url, headers=None, timeout=30):
    txt = http_get(url, headers=headers, timeout=timeout)
    return json.loads(txt) if txt else None

# ═══════════════════════════════════════════════════════════
# 重试 wrapper
# ═══════════════════════════════════════════════════════════

def retry(fn, max_retries=MAX_RETRIES, delay_sec=RETRY_DELAY):
    for attempt in range(1, max_retries + 1):
        try:
            if fn() is not False:
                return True
        except Exception as e:
            print(f"  Attempt {attempt}/{max_retries} FAILED: {e}")
        if attempt < max_retries:
            print(f"  Retry in {delay_sec}s...")
            time.sleep(delay_sec)
    return False

# ═══════════════════════════════════════════════════════════
# 业务规则（铁律，全部硬编码，不走 LLM）
# ═══════════════════════════════════════════════════════════

# ── 规则 1：黄金 ──────────────────────────────────────────
RULE_GOLD = {
    "required_count": 1,
    # 国际金价：腾讯行情（COMEX 期货 USD/oz）
    "intl_url":    "https://qt.gtimg.cn/q=hf_GC",
    "intl_header":  {"Referer": "https://gu.qq.com/"},
    # 国内金价：东财沪金现货 AU9999（CNY/g）
    "dom_secid":   "118.AU9999",
    "dom_url":     "https://push2.eastmoney.com/api/qt/stock/get",
    # TIPS 十年期国债收益率：treasury.gov CSV
    "tips_url":    ("https://home.treasury.gov/resource-center/data-chart-center/"
                    "interest-rates/daily-treasury-rates.csv/2026/all"
                    "?type=daily_treasury_yield_curve"
                    "&field_tdr_date_value=2026&download=true"),
    "tips_header": {"User-Agent": "Mozilla/5.0", "Accept": "text/csv"},
}

def _fetch_intl_gold():
    """国际金价：腾讯 hf_GC（COMEX 期货 USD/oz），字段以逗号分隔。"""
    raw = http_get(RULE_GOLD["intl_url"], headers=RULE_GOLD["intl_header"])
    if not raw:
        raise ValueError("Tencent hf_GC empty")
    # 格式: v_hf_GC="4109.90,0.05,..."
    m = re.search(r'v_hf_GC\s*=\s*"([^"]+)"', raw)
    if not m:
        raise ValueError(f"No v_hf_GC in response: {raw[:200]}")
    fields = m.group(1).split(',')
    if len(fields) < 5:
        raise ValueError(f"hf_GC fields too few: {fields}")
    price = float(fields[0])
    if price < 1000 or price > 10000:  # sanity check
        raise ValueError(f"hf_GC price suspect: {price}")
    # 涨跌额: fields[1] (USD/oz) — 仅供日志，不入库
    change_abs = float(fields[1]) if fields[1] else 0.0
    # 涨跌幅%: (今-昨)/昨 × 100
    # 腾讯 v_hf_GC 字段索引（实测 2026-08-05 12:10 CST）：
    #   [0]=当前价 [1]=涨跌额 [2]=开盘 [3]=最高 [4]=振幅/最新?
    #   [5]=昨收(prev_close) [6]=时间 [7]=今日开盘(?)
    #   [8]=?? [9-12]=其他
    # prev_close 正确索引是 [5]，不是 [4]
    prev = float(fields[5]) if len(fields) > 5 and fields[5] else None
    if not prev or prev <= 0:
        # 兜底：用 change_abs 反推
        if change_abs:
            prev = price - change_abs
        else:
            prev = None
    change_pct = round((price - prev) / prev * 100, 2) if prev else 0.0
    return price, change_abs, change_pct

def _fetch_dom_gold():
    """国内金价：东财沪金现货 AU9999（分/g），转元/g。
    主接口失败则用 kline 备用接口。"""
    import time as _time

    # ── 主接口：push2.eastmoney.com 实时报价 ──
    # 字段含义（东财 secid=118.AU9999，实测 2026-08-05 12:10 CST）：
    #   f43  = 最新价（分/g，÷100 转元/g）
    #   f44  = 最高（分）
    #   f45  = 开盘（分）
    #   f46  = 最低（分）
    #   f60  = 昨收（分，÷100 转元/g）  ← 用于 change_pct 兜底
    #   f169 = 涨跌额（分，÷100 转元/g）
    #   f170 = 涨跌幅（原始 = pct × 100，÷100 转 %）  ← 主要用这个
    try:
        ts = str(int(_time.time() * 1000))
        url = (f"{RULE_GOLD['dom_url']}?secid={RULE_GOLD['dom_secid']}"
               f"&fields=f43,f44,f60,f169,f170&_={ts}")
        raw = http_get(url, headers={
            "Referer": "https://quote.eastmoney.com/",
            "User-Agent": "Mozilla/5.0"
        }, timeout=8)
        if raw:
            data = json.loads(raw)
            info = data.get("data", {})
            price_fen = float(info.get("f43", 0) or 0)
            if price_fen > 0:
                price = round(price_fen / 100, 2)
                # 优先用 f170（涨跌幅 × 100），除以 100 得百分比
                pct_raw = info.get("f170", 0)
                if pct_raw:
                    change_pct = round(float(pct_raw) / 100, 2)
                else:
                    # 兜底：f60 昨收（分）反推
                    yest_fen = float(info.get("f60", 0) or 0)
                    if yest_fen > 0:
                        change_pct = round((price - yest_fen/100) / (yest_fen/100) * 100, 2)
                    else:
                        change_pct = 0.0
                print(f"  [DOM_GOLD] Eastmoney OK: ¥{price}/g ({change_pct:+.2f}%)")
                return price, change_pct
    except Exception as e:
        print(f"  [DOM_GOLD] Eastmoney failed: {e}")

    # ── 备用接口：kline 历史收盘价 ──
    try:
        ts = str(int(_time.time() * 1000))
        kline_url = (
            f"https://push2his.eastmoney.com/api/qt/stock/kline/get"
            f"?secid=118.AU9999"
            f"&fields1=f1,f2,f3,f4,f5"
            f"&fields2=f51,f52,f53,f54,f55,f56"
            f"&klt=101&fqt=1&end=20501231&lmt=1&_={ts}"
        )
        raw = http_get(kline_url, headers={
            "Referer": "https://quote.eastmoney.com/",
            "User-Agent": "Mozilla/5.0"
        }, timeout=8)
        if raw:
            data = json.loads(raw)
            klines = data.get("data", {}).get("klines", [])
            if klines:
                # kline: "YYYY-MM-DD,开盘,收盘,最高,最低,成交量"
                last = klines[0].split(",")
                price = round(float(last[2]), 2)  # 收盘价
                print(f"  [DOM_GOLD] Kline fallback OK: ¥{price}/g (close)")
                return price, None  # change_pct=None 表示用不到
    except Exception as e:
        print(f"  [DOM_GOLD] Kline failed: {e}")

    raise ValueError("All domestic gold sources failed")

def _fetch_tips():
    """TIPS 十年期国债真实收益率：treasury.gov CSV，取最新交易日。"""
    raw = http_get(RULE_GOLD["tips_url"], headers=RULE_GOLD["tips_header"])
    if not raw:
        raise ValueError("Treasury.gov empty")
    lines = raw.strip().split("\n")
    if len(lines) < 2:
        raise ValueError(f"Treasury CSV too short: {len(lines)}")
    # 第一行是 header
    header = [h.strip().strip('"') for h in lines[0].split(",")]
    # 找到 '10 Yr' 列
    col_name = "10 Yr"
    if col_name not in header:
        # 尝试替代列名
        for h in header:
            if "10" in h and "Yr" in h:
                col_name = h
                break
        else:
            raise ValueError(f"No '10 Yr' in header: {header}")
    col_idx = header.index(col_name)
    # 从最后一行读（最新交易日）
    last = [h.strip().strip('"') for h in lines[1].split(",")]
    tips_yield = float(last[col_idx])
    # 读倒数第二行（昨日）算涨跌
    prev_tips = 0.0
    if len(lines) >= 3:
        prev = [h.strip().strip('"') for h in lines[2].split(",")]
        prev_tips = float(prev[col_idx])
    tips_change = round(tips_yield - prev_tips, 3)
    return tips_yield, tips_change

def step_gold():
    print(f"[GOLD] Fetching for {TODAY}")
    clean_gold()

    def attempt():
        intl_price, intl_change_abs, intl_change_pct = _fetch_intl_gold()
        dom_price, dom_change_pct  = _fetch_dom_gold()
        dom_change_pct = dom_change_pct if dom_change_pct is not None else 0.0
        tips_yield, tips_change = _fetch_tips()

        # 采集说明：异常源标出，避免 push.py 误判
        gold_note = (
            f"采集于 {TODAY} | "
            f"国际GC=${intl_price:.2f} ({intl_change_pct:+.2f}%) | "
            f"国内AU9999=¥{dom_price:.2f} ({dom_change_pct:+.2f}%) | "
            f"美10Y TIPS={tips_yield:.3f}% ({tips_change:+.3f}pp)"
        )
        insert_gold(intl_price, intl_change_pct, dom_price, dom_change_pct,
                    tips_yield, tips_change, gold_note=gold_note)

        cnt = count_gold()
        if cnt < RULE_GOLD["required_count"]:
            raise ValueError(f"Gold row not inserted: {cnt}")
        print(f"  ✅ Gold: ${intl_price:.2f}/oz ({intl_change_pct:+.2f}%) "
              f"| ¥{dom_price:.2f}/g ({dom_change_pct:+.2f}%) "
              f"| TIPS10Y: {tips_yield:.3f}% ({tips_change:+.3f}pp)")
    return retry(attempt)


# ── 规则 2：AI 热讯 ──────────────────────────────────────
RULE_AI = {
    "required_count": 10,
    "api_url": AIHOT_API,
    "ua": AIHOT_UA,
    "take": 10,
    "score_field": "score",     # aihot 热度分字段
    "title_field": "title",
    "summary_field": "summary",  # 用于 content + summary 双写
    "source_field": "source",
    "url_field": "url",
}

def step_ai():
    print(f"[AI] Fetching for {TODAY}")
    clean_news("ai")

    def attempt():
        resp = http_get(RULE_AI["api_url"],
                        headers={"User-Agent": RULE_AI["ua"]}, timeout=30)
        if not resp:
            raise ValueError("aihot empty")
        data = json.loads(resp)
        items = data.get("items", [])
        if not items:
            raise ValueError("No items")

        for entry in items[:RULE_AI["take"]]:
            title   = entry.get(RULE_AI["title_field"], "")
            summary = entry.get(RULE_AI["summary_field"], "")
            content = summary  # summary 即 content
            source  = entry.get(RULE_AI["source_field"], "aihot")
            url     = entry.get(RULE_AI["url_field"], "")
            score   = float(entry.get(RULE_AI["score_field"], 0)) or 0.0
            insert_news("ai", title, content, source, url, "zh", score,
                        summary=summary, description=summary[:100])

        cnt = count_news("ai")
        if cnt < RULE_AI["required_count"]:
            raise ValueError(f"Only {cnt}/{RULE_AI['required_count']} AI items")
        print(f"  ✅ AI: {cnt} items")
    return retry(attempt)


# ── 规则 3：国际政治 ────────────────────────────────────
# 铁律：只采权威媒体（Reuters/AP/AFP/BBC/Al Jazeera/FT），不用通用搜索
RULE_POLITICS = {
    "required_count": 10,
    # 分区关键词（用于结构化搜索，不是泛搜索）
    "queries": {
        "🔴 亚太": [
            "site:reuters.com OR site:apnews.com OR site:afpbb.com China Japan Korea Taiwan news",
            "site:reuters.com OR site:apnews.com South China Sea Philippines Vietnam",
        ],
        "🔵 中东·欧洲": [
            "site:reuters.com OR site:apnews.com OR site:bbc.com Middle East Russia Ukraine Europe",
            "site:reuters.com OR site:ft.com OR site:aljazeera.com EU Nato Turkey Iran",
        ],
        "🟢 美洲": [
            "site:reuters.com OR site:apnews.com OR site:bbc.com United States Mexico Brazil",
        ],
    },
    "max_per_query": 4,   # 每个子查询最多取几条
    "score": 1.0,         # 政治新闻统一分
}

def step_politics():
    """采集国际政治新闻。
    重试策略：3次 × 60s，不降间隔（politics 比 gold/ai 更需要多样性）。
    """
    print(f"[POLITICS] Fetching for {TODAY}")
    clean_news("politics")

    def attempt():
        all_hits = []
        seen_urls = set()

        for region, queries in RULE_POLITICS["queries"].items():
            for q in queries:
                raw = http_post(NINE_ROUTER_SEARCH, {
                    "model": "tavily",
                    "query": q,
                    "max_results": RULE_POLITICS["max_per_query"],
                }, timeout=30)  # 缩短到30s，超时即记录
                if not raw:
                    print(f"  WARN politics query failed (no response): {q[:60]}")
                    continue
                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    print(f"  WARN politics JSON parse failed: {q[:60]}")
                    continue
                for r in (data.get("results", []) or []):
                    url = r.get("url", "")
                    if url and url not in seen_urls and any(
                        d in url for d in ["reuters.com","apnews.com","afpbb.com",
                                           "bbc.com","aljazeera.com","ft.com"]
                    ):
                        seen_urls.add(url)
                        all_hits.append({
                            "region": region,
                            "title":   r.get("title", ""),
                            "content": r.get("content", r.get("snippet", "")),
                            "url":     url,
                            "domain":  url.split("/")[2] if "/" in url else "",
                        })

        if not all_hits:
            raise ValueError("No authoritative politics hits")

        for h in all_hits[:RULE_POLITICS["required_count"]]:
            title   = (h.get("title") or "").strip()[:200]
            content = (h.get("content") or "").strip()[:5000]
            source  = h.get("domain", "")
            region  = h.get("region", "🟢")  # ← 关键：按搜索分区写入 region
            # push.py build_msg3 用 `summary or content or ""`
            # description 也用，但 push 优先 summary
            summary = content[:200] if content else title
            description = summary  # 政治新闻 desc ≡ summary
            insert_news("politics", title, content, source, h["url"], "zh",
                        score=RULE_POLITICS["score"],
                        summary=summary,
                        description=description,
                        region=region)

        cnt = count_news("politics")
        print(f"  ✅ Politics: {cnt} items collected ({len(all_hits)} total hits)")
        # politics 放宽最低要求：至少3条即可（权威媒体质量 > 数量）
        if cnt < 3:
            raise ValueError(f"Only {cnt}/3 politics items")
    return retry(attempt, max_retries=3, delay_sec=60)


# ── 规则 4：GitHub 黑马 ─────────────────────────────────
RULE_GITHUB = {
    "required_count": 10,
    "script": GH_SCRIPT,
    "black_horse_formula": {
        "<5k":   2.0,
        "5k-20k": 1.5,
        "20k-100k": 1.0,
        "≥100k":  0.8,
    },
}

def step_github():
    print(f"[GITHUB] Fetching for {TODAY}")
    clean_news("github")

    def attempt():
        if not os.path.exists(RULE_GITHUB["script"]):
            raise FileNotFoundError(RULE_GITHUB["script"])
        r = subprocess.run(
            ["bash", "-c",
             f'export TZ=Asia/Shanghai && cd /Users/apple/.openclaw/workspace && '
             f'python3 scripts/radar/gh_collect.py "{TODAY}"'],
            capture_output=True, text=True, timeout=600
        )
        cnt = count_news("github")
        if cnt < RULE_GITHUB["required_count"]:
            raise ValueError(f"github {cnt}/{RULE_GITHUB['required_count']}: {r.stdout[-300:]}")
        print(f"  ✅ GitHub: {cnt} items (description 字段已写入)")
    return retry(attempt, max_retries=MAX_RETRIES, delay_sec=60)


# ═══════════════════════════════════════════════════════════
# 主流程
# ═══════════════════════════════════════════════════════════

def run():
    print("=" * 60)
    print(f"Radar Collector v4.0 | {TODAY} | TZ=Asia/Shanghai")
    print("=" * 60)

    lock_set("collector")

    results = {}
    results["gold"]     = step_gold()
    results["ai"]       = step_ai()
    results["politics"] = step_politics()
    results["github"]   = step_github()

    # 自检
    print("")
    print("FINAL SELF-CHECK")
    checks = [
        ("gold",     count_gold,         RULE_GOLD["required_count"]),
        ("ai",       lambda: count_news("ai"),       RULE_AI["required_count"]),
        ("politics", lambda: count_news("politics"), RULE_POLITICS["required_count"]),
        ("github",   lambda: count_news("github"),   RULE_GITHUB["required_count"]),
    ]

    all_pass = True
    for name, count_fn, min_cnt in checks:
        cnt = count_fn()
        ok = cnt >= min_cnt
        icon = "✅" if ok else "❌"
        print(f"  {icon} {name:<10} {cnt}/{min_cnt}")
        if not ok:
            all_pass = False

    lock_set("collector-done" if all_pass else "collector-partial")
    print("=" * 60)
    return True

if __name__ == "__main__":
    run()
