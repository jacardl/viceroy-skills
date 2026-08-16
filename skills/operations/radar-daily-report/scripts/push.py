#!/usr/bin/env python3
"""
radar-daily-report 推送脚本 v4.5

铁律：
  - 不 fallback 旧数据，数据缺失直接告警
  - 所有字段按 DB schema 硬编码，不走 LLM 补字段
  - 与 collect.py / gh_collect.py 字段含义严格对齐（LRN-20260805-001/002）

变更记录（v4.5, 2026-08-15）：
  - 配合 P0-2 → P1-1 策略切换：预检查不达标时 push.py 仍运行
  - 新增 fmt_cny() / fmt_usd() 助手：None 字段不再触发 TypeError
  - 缺国内金价时显示 "N/A（采集未完成）"（东财 API 关闭场景）

变更记录（v4.4, 2026-08-13）：
  - MSG2: description 优先（v4.1 铁律字段对齐，原代码只读 summary/content）
  - MSG3: 政治新闻改"事件/背景/影响"三段式（佳哥拍板 2026-06-17 铁律）
  - MSG4: 标题/分数分两行；desc/url 缺时显示（暂无简介）/（链接待补）兜底
  - MSG1: gold_note fallback 标识"（无趋势点评）"
  - 缺数据点诊断更友好，便于定位 collect.py / gh_collect.py 采集 bug

输出：===MSG1=== ~ ===MSG4=== + ===META=== 五段到 stdout

字段映射（与 collect.py / gh_collect.py 同步）：
  gold_prices:
    intl_price_usd | intl_price_change | domestic_price_cny |
    domestic_price_change | tips_yield_10y | tips_yield_change | gold_note
  news_articles:
    title | content | summary | description | source | url | lang |
    stars_count | period_new_stars | blacklist_score | region | is_new_project
"""

import subprocess, json, re, sys, os
from datetime import datetime

TZ_CST = "Asia/Shanghai"

# ═══════════════════════════════════════════════════════════
# DB helpers
# ═══════════════════════════════════════════════════════════

DB_CMD = ["docker", "exec", "radar-db", "psql", "-U", "radar", "-d", "radar", "-t", "-q"]

def sql(q):
    r = subprocess.run(DB_CMD + ["-c", q], capture_output=True, text=True, timeout=30)
    return r.stdout.strip()

# ═══════════════════════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════════════════════

def cst_date_today():
    r = subprocess.run(
        ["bash", "-c", f"export TZ={TZ_CST} && date '+%Y-%m-%d %u %d'"],
        capture_output=True, text=True
    )
    parts = r.stdout.strip().split()
    return parts[0], int(parts[1]), int(parts[2])  # date_str, dow, day_of_month

DATE_CST, DOW, DAY_OF_MONTH = cst_date_today()
is_monthly = (DAY_OF_MONTH == DOW)
is_weekly  = (DOW == 6)
report_type = "月报" if is_monthly else ("周报" if is_weekly else "日报")

def safe(s):
    """SQL 输出清洗：去空白、还原换行、去掉单引号转义残渣。"""
    if s is None:
        return ""
    return str(s).replace("\\n", "\n").replace("\\r", "").strip()

def pct(v):
    """涨跌百分比格式化，None → N/A。"""
    if v is None:
        return "N/A"
    sign = "+" if v >= 0 else ""
    return f"{sign}{v:.2f}%"

def pp_diff(v):
    """基点差值格式化，None → N/A。"""
    if v is None:
        return "N/A"
    sign = "+" if v >= 0 else ""
    return f"{sign}{v:.3f}pp"

def fmt_stars(n):
    """star 数千分位格式化。"""
    if n is None or n == 0:
        return "N/A"
    return f"{n:,}"

def fmt_cny(v):
    """国内金价 CNY/克 格式化，None → N/A（采集未完成）。"""
    if v is None:
        return "N/A（采集未完成）"
    return f"¥{v:,.2f}"

def fmt_usd(v):
    """国际金价 USD/盎司 格式化，None → N/A。"""
    if v is None:
        return "N/A"
    return f"${v:,.2f}"

# ═══════════════════════════════════════════════════════════
# news_articles 解析（用 url 锚点定位）
# DB 字段（全部）：
#   title | content | summary | source | url | lang |
#   stars_count | period_new_stars | growth_rate | is_new_project |
#   blacklist_score | region | description
# ═══════════════════════════════════════════════════════════

def parse_news_row(raw):
    """用 ROW_TO_JSON 解析，字段名访问，彻底规避 | 分隔符问题。"""
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None

# ═══════════════════════════════════════════════════════════
# MSG1：金价（gold_prices 表）
# 字段：price_date | intl_price_usd | intl_price_change |
#       domestic_price_cny | domestic_price_change |
#       tips_yield_10y | tips_yield_change | gold_note
# ═══════════════════════════════════════════════════════════

GOLD_SQL = (
    f"SELECT intl_price_usd, intl_price_change, domestic_price_cny, "
    f"domestic_price_change, tips_yield_10y, tips_yield_change, gold_note "
    f"FROM gold_prices WHERE price_date='{DATE_CST}';"
)

def build_msg1():
    raw = sql(GOLD_SQL)
    vals = [v.strip() for v in raw.split("|")]
    if not vals or not vals[0]:
        return None, f"💰 金价速览（{DATE_CST}）\n\n⚠️ 金价数据缺失。"

    def gf(i):
        try:
            return float(vals[i]) if vals[i] else None
        except (ValueError, IndexError):
            return None

    intl_usd  = gf(0)
    intl_chg  = gf(1)
    dom_cny   = gf(2)
    dom_chg   = gf(3)
    tips_y     = gf(4)
    tips_chg   = gf(5)
    gold_note  = vals[6].strip() if len(vals) > 6 else ""

    table = (
        f"| 指标 | 价格 | 涨跌 |\n"
        f"|---|---|---|\n"
        f"| 国际金价（USD/盎司） | {fmt_usd(intl_usd)} | {pct(intl_chg)} |\n"
        f"| 国内金价（CNY/克） | {fmt_cny(dom_cny)} | {pct(dom_chg)} |\n"
        f"| 美10年TIPS收益率 | {(f'{tips_y:.3f}%') if tips_y is not None else 'N/A'} | {pp_diff(tips_chg)} |"
    )
    if gold_note:
        note = f"📊 {gold_note}"
    else:
        note = f"📊 数据日期：{DATE_CST}（无趋势点评）"
    body = (
        f"💰 雷达每日报告 · 金价速览（{DATE_CST} · {report_type}）\n\n"
        f"{table}\n\n"
        f"{note}"
    )
    return True, body

# ═══════════════════════════════════════════════════════════
# MSG2：AI 热讯（news_articles category='ai'）
# 字段：title | summary | source | blacklist_score
# ═══════════════════════════════════════════════════════════

AI_SQL = (
    "SELECT row_to_json(t) FROM ("
    "  SELECT title, content, summary, source, url, lang, "
    "    stars_count, period_new_stars, blacklist_score, region, description "
    "  FROM news_articles "
    "  WHERE article_date='{DATE_CST}' AND category='ai' "
    "  ORDER BY blacklist_score DESC NULLS LAST LIMIT 10"
    ") t;"
).format(DATE_CST=DATE_CST)

def build_msg2():
    raw = sql(AI_SQL)
    items = []
    for line in raw.split("\n"):
        line = line.strip()
        if not line:
            continue
        p = parse_news_row(line)
        if p:
            items.append(p)

    header = f"🤖 雷达每日报告 · AI 热讯（{DATE_CST}）\n"
    if not items:
        return len(items), header + "\n⚠️ AI热讯数据缺失。"

    lines = [header]
    for i, p in enumerate(items, 1):
        score = int(p["blacklist_score"]) if p["blacklist_score"] else 0
        src = p["source"] or "Web"
        # v4.1 铁律：description 是主显示字段，summary/content 兜底
        text = p["description"] or p["summary"] or p["content"] or ""
        lines.append(f"{i}. **{safe(p['title'])}** | 热度 {score} | {safe(src)}")
        if text:
            lines.append(f"   {text[:150]}")
        else:
            lines.append(f"   （暂无摘要）")
        if p["url"]:
            lines.append(f"   {p['url']}")
        lines.append("")
    return len(items), "\n".join(lines).strip()

# ═══════════════════════════════════════════════════════════
# MSG3：国际政治（news_articles category='politics'）
# 字段：content | source | url | region
# 展示：🔴亚太 | 🔵中东·欧洲 | 🟢美洲
# ═══════════════════════════════════════════════════════════

PO_SQL = (
    "SELECT row_to_json(t) FROM ("
    "  SELECT title, content, summary, source, url, lang, "
    "    stars_count, period_new_stars, blacklist_score, region, description "
    "  FROM news_articles "
    "  WHERE article_date='{DATE_CST}' AND category='politics' "
    "  ORDER BY blacklist_score DESC NULLS LAST LIMIT 12"
    ") t;"
).format(DATE_CST=DATE_CST)

def build_msg3():
    raw = sql(PO_SQL)
    by_region = {"🔴": [], "🔵": [], "🟢": []}
    for line in raw.split("\n"):
        line = line.strip()
        if not line:
            continue
        p = parse_news_row(line)
        if p:
            # DB region 可能存 "🔴 亚太" / "🔵 中东·欧洲" / "🟢 美洲" 或纯 emoji
            # 用第一个字符（即 emoji）作为 key
            reg = (p["region"] or "🟢").strip()
            reg_key = reg[0] if reg else "🟢"
            if reg_key not in by_region:
                reg_key = "🟢"
            by_region[reg_key].append(p)

    header = f"🌍 雷达每日报告 · 国际政治（{DATE_CST}）\n"
    has_any = any(by_region[r] for r in by_region)
    if not has_any:
        return 0, header + "\n⚠️ 国际政治数据缺失。"

    lines = [header]
    region_meta = [("🔴", "亚太"), ("🔵", "中东 · 欧洲"), ("🟢", "美洲")]
    for emoji, name in region_meta:
        items = by_region[emoji]
        lines.append(f"**{emoji} {name}**")
        if items:
            for p in items:
                title    = safe(p["title"])
                # v4.2：政治主显示字段改为 description（中文改写）
                desc_zh  = safe(p["description"])
                summary  = safe(p["summary"])
                content  = safe(p["content"])
                src      = p["source"] or "Web"
                # 三段式：事件 / 背景 / 影响（铁律：佳哥拍板 2026-06-17）
                # 标题行用 desc_zh（中文事件）替代英文 title（铁律：❌ English Headline）
                title_zh = desc_zh[:60] if desc_zh else title
                lines.append(f"- **{title_zh}**")
                if desc_zh:
                    lines.append(f"  - 事件：{desc_zh[:200]}")
                if summary:
                    lines.append(f"  - 背景：{summary[:200]}")
                if content:
                    lines.append(f"  - 影响：{content[:200]}")
                if p["url"]:
                    lines.append(f"  - 来源：{src} | {p['url']}")
                else:
                    lines.append(f"  - 来源：{src}")
                lines.append("")
        else:
            lines.append("暂无数据\n")
    return sum(len(v) for v in by_region.values()), "\n".join(lines).strip()

# ═══════════════════════════════════════════════════════════
# MSG4：GitHub 黑马（news_articles category='github'）
# 字段：title | description | source(lang) | url |
#       stars_count | period_new_stars | blacklist_score
# 展示：⭐ 黑马分 | 今日+⭐ | 总⭐ + description(中文简介)
# ═══════════════════════════════════════════════════════════

GH_SQL = (
    "SELECT row_to_json(t) FROM ("
    "  SELECT title, content, summary, source, url, lang, "
    "    stars_count, period_new_stars, blacklist_score, region, description "
    "  FROM news_articles "
    "  WHERE article_date='{DATE_CST}' AND category='github' "
    "  ORDER BY blacklist_score DESC NULLS LAST LIMIT 10"
    ") t;"
).format(DATE_CST=DATE_CST)

def build_msg4():
    raw = sql(GH_SQL)
    repos = []
    for line in raw.split("\n"):
        line = line.strip()
        if not line:
            continue
        p = parse_news_row(line)
        if p:
            repos.append(p)

    # gh_repos.json 兜底补充（不重复已有 URL）
    gh_json = "/tmp/gh_repos.json"
    if os.path.exists(gh_json):
        with open(gh_json) as f:
            extra = json.load(f)
        existing_urls = {r["url"] for r in repos if r.get("url")}
        for r in extra:
            url = r.get("url", "")
            if url and url not in existing_urls:
                repos.append({
                    "title":           r.get("name", ""),
                    "description":     r.get("desc_zh", r.get("desc", "")),
                    "source":          r.get("lang", ""),
                    "url":             url,
                    "stars_count":     r.get("stars_count") or r.get("total", 0),
                    "period_new_stars": r.get("today", 0),
                    "blacklist_score": float(r.get("score", 0)),
                    "region":          "🟢",
                })

    repos.sort(key=lambda x: (x["blacklist_score"] if x["blacklist_score"] is not None else -999), reverse=True)
    repos = repos[:10]

    header = f"💻 雷达每日报告 · GitHub 黑马（{DATE_CST}）\n"
    if not repos:
        return 0, header + "\n⚠️ GitHub数据缺失。"

    lines = [header]
    for i, p in enumerate(repos, 1):
        title    = safe(p["title"])
        score    = int(p["blacklist_score"]) if p["blacklist_score"] else 0
        today    = p["period_new_stars"]
        total    = p["stars_count"]
        desc     = safe(p["description"])
        lang     = safe(p["source"])
        url      = p["url"]

        today_str  = fmt_stars(today)  if today  else "N/A"
        total_str  = fmt_stars(total) if total else "N/A"

        # 标题单独成行（贴近 approved-template.md 样式）
        # 仅保留 owner/repo，去掉 "— English desc" 尾巴（铁律：❌ English Headline）
        title_short = title.split(' — ')[0].split(' -- ')[0].strip()
        lines.append(f"{i}. **{title_short}**")
        lines.append(f"   黑马分 {score} | 今日+{today_str}⭐ 总⭐{total_str}")
        if lang:
            lines.append(f"   语言：{lang}")
        if desc:
            lines.append(f"   {desc[:120]}")
        else:
            lines.append(f"   （暂无简介）")
        if url:
            lines.append(f"   {url}")
        else:
            lines.append(f"   （链接待补）")
        lines.append("")

    return len(repos), "\n".join(lines).strip()

# ═══════════════════════════════════════════════════════════
# 主流程
# ═══════════════════════════════════════════════════════════

def main():
    gold_ok,  msg1 = build_msg1()
    ai_count, msg2 = build_msg2()
    po_count, msg3 = build_msg3()
    gh_count, msg4 = build_msg4()

    print(f"===MSG1===\n{msg1}")
    print(f"\n===MSG2===\n{msg2}")
    print(f"\n===MSG3===\n{msg3}")
    print(f"\n===MSG4===\n{msg4}")
    print(f"\n===META===\n"
          f"date={DATE_CST} "
          f"dow={DOW} "
          f"report_type={'monthly' if is_monthly else ('weekly' if is_weekly else 'daily')} "
          f"ai={ai_count} "
          f"po={po_count} "
          f"gh={gh_count} "
          f"gold_ok={'true' if gold_ok else 'false'}")

if __name__ == "__main__":
    main()
