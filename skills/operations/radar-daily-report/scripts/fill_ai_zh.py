#!/usr/bin/env python3
"""
fill_ai_zh.py — AI / Politics / GitHub 板块 description 字段中文改写

铁律（来自 operations/radar-daily-report SKILL.md STEP 0.5b）：
  - 仅文字操作，不爬取/补抓/改 schema
  - ❌ 不补抓缺失数据行
  - ❌ 不改"已存在的好中文"字段
      → 默认 UPDATE 仅命中 description 为空 / 是英文/URL 坏数据
      → 加 --all 覆盖所有（含已写好的中文）
  - 失败不阻塞 — 任意一条失败时链尾兜底用 title[:200]，不写空值
  - 单条 30s 超时，整批 5min 硬上限
  - 并发 4 workers（实测 9Router 1s/条）

触发场景：
  - AI 板块：aihot 接口偶发返英文 summary（如 2026-08-19 cron）
  - Politics 板块：collect.py 偶发把 raw URL HTML 实体写入 description
  - GitHub 板块：gh_collect.py 中文改写偶发失败，desc 残留英文

用法：
  python3 fill_ai_zh.py --days=1                              # 补 AI 板块
  python3 fill_ai_zh.py --days=1 --category=politics          # 补政治
  python3 fill_ai_zh.py --days=1 --category=github            # 补 GitHub
  python3 fill_ai_zh.py --days=1 --category=all               # 三类全补
  python3 fill_ai_zh.py --days=1 --category=ai --dry-run      # 只预览

模型链：ds/deepseek-chat → 失败 fallback 用 title 前 200 字符
"""
import sys, json, subprocess, time
import urllib.request as ureq
import yaml
from concurrent.futures import ThreadPoolExecutor, as_completed

DATE_CST = subprocess.run(
    ["bash", "-c", "export TZ=Asia/Shanghai && date '+%Y-%m-%d'"],
    capture_output=True, text=True
).stdout.strip()

DB_CMD = ["docker", "exec", "radar-db", "psql", "-U", "radar", "-d", "radar", "-t", "-q"]
def sql(q):
    r = subprocess.run(DB_CMD + ["-c", q], capture_output=True, text=True, timeout=30)
    return r.stdout.strip()

KEY = yaml.safe_load(open('/Users/apple/.hermes/config.yaml'))['providers']['9router']['api_key']
URL = "http://127.0.0.1:20128/v1/chat/completions"

SYS_AI = (
    "你是 AI 行业编辑。根据英文标题+英文摘要生成 1 句中文摘要 ≤80 字。"
    "要求: 客观陈述核心信息；不要'本文'开头；不要英文。"
    "输出仅 1 行纯中文文本，不要引号/前缀/解释。"
)
SYS_POLITICS = (
    "你是国际政治新闻编辑。根据英文标题+英文摘要生成 1 句中文事件摘要 ≤80 字。"
    "要求: 客观陈述核心事件；不要'本文'开头；不要英文；不要 HTML。"
    "输出仅 1 行纯中文文本，不要引号/前缀/解释。"
)
SYS_GITHUB = (
    "你是技术编辑。根据英文项目标题+英文描述生成 1 句中文项目简介 ≤80 字。"
    "要求: 客观陈述项目功能；不要'本文/此项目'开头；不要英文；不要 HTML。"
    "输出仅 1 行纯中文文本，不要引号/前缀/解释。"
)
SYS_BY_CAT = {"ai": SYS_AI, "politics": SYS_POLITICS, "github": SYS_GITHUB}

MODELS = ["ds/deepseek-chat"]
TIMEOUT = 30
BATCH_BUDGET = 300

def call_llm(model, user_text, sys_prompt=SYS_AI):
    body = {
        "model": model,
        "max_tokens": 200,
        "stream": False,
        "messages": [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_text},
        ],
    }
    req = ureq.Request(URL, data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {KEY}"})
    with ureq.urlopen(req, timeout=TIMEOUT) as r:
        resp = json.loads(r.read())
    return resp["choices"][0]["message"]["content"].strip().strip('"').strip("'").strip()

def rewrite(title, content, sys_prompt=SYS_AI):
    user = f"Title: {title}\nSummary: {content[:400]}"
    for m in MODELS:
        try:
            out = call_llm(m, user)
            if out and any('\u4e00' <= c <= '\u9fff' for c in out):
                return out, m
        except Exception as e:
            print(f"  ⚠️ {m} fail: {type(e).__name__}: {str(e)[:100]}")
            continue
    # 兜底：英文 title 前 200 字符（不写空）
    return title[:200].strip(), "fallback-title"

def is_bad_desc(desc: str) -> bool:
    """description 坏数据：空 / 是 URL HTML 实体 / 全英文/无中文"""
    if not desc or not desc.strip():
        return True
    d = desc.strip()
    # URL HTML 实体开头（&lt;a href=...）
    if d.startswith("&lt;") or d.startswith("<a ") or d.lower().startswith("http"):
        return True
    # 无任何中文字符 → 当作英文
    if not any('\u4e00' <= c <= '\u9fff' for c in d):
        return True
    return False

def run_category(cat: str, days: int, dry: bool, force: bool):
    """处理一个 category，返回 (待改写条数, 成功条数)"""
    if cat not in SYS_BY_CAT:
        print(f"  ❌ unknown category: {cat}")
        return 0, 0
    sys_p = SYS_BY_CAT[cat]
    # 默认：只改坏数据（空/URL/全英文）
    # force: 覆盖所有（即便已有中文 desc）
    if force:
        where_extra = ""
        mode = "全部强制"
    else:
        where_extra = "AND (description IS NULL OR description='' OR description LIKE '&lt;%' OR description LIKE '<a %' OR description NOT LIKE '%[\u4e00-\u9fff]%')"
        mode = "坏数据(空/URL/无中文)"

    raw = sql(
        f"SELECT id, title, content, description FROM news_articles "
        f"WHERE category='{cat}' "
        f"AND article_date >= (CURRENT_DATE - INTERVAL '{days} days') "
        f"{where_extra} "
        f"ORDER BY article_date DESC, blacklist_score DESC NULLS LAST;"
    )
    if not raw:
        print(f"  ✅ {cat} 板块{mode}已无需改写（近 {days} 天）。")
        return 0, 0

    rows = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("|", 3)
        if len(parts) < 4:
            print(f"  ❌ skip 解析失败: {line[:80]}")
            continue
        uuid, title, content, desc = parts[0].strip(), parts[1].strip(), parts[2].strip(), parts[3].strip()
        if not title:
            print(f"  ❌ skip {uuid} title 空")
            continue
        rows.append((uuid, title, content, desc))

    print(f"  [{cat}] 待改写={len(rows)} 条  mode={mode}  dry_run={dry}")
    start = time.time()
    results = {}

    with ThreadPoolExecutor(max_workers=4) as pool:
        futs = {pool.submit(rewrite, r[1], r[2], sys_p): r[0] for r in rows}
        for fut in as_completed(futs):
            uuid = futs[fut]
            try:
                zh, model = fut.result()
                results[uuid] = (zh, model)
            except Exception as e:
                print(f"  ❌ {uuid[:8]} 失败: {type(e).__name__}: {e}")
                results[uuid] = (None, None)

    for uuid, title, _, old_desc in rows:
        zh, model = results.get(uuid, (None, None))
        if zh is None:
            print(f"    ❌ {uuid[:8]}: {title[:40]!r} → 失败")
        else:
            print(f"    [{model}] {uuid[:8]}: {title[:40]!r}")
            print(f"      old: {old_desc[:60]!r}")
            print(f"      →   {zh[:80]!r}")

    if dry:
        print(f"  [{cat}] [dry-run] done elapsed={time.time()-start:.1f}s")
        return len(rows), 0

    updated = 0
    failed = 0
    for uuid, _, _, _ in rows:
        if time.time() - start > BATCH_BUDGET:
            print(f"  ⏱️ 整批预算 {BATCH_BUDGET}s 耗尽，提前退出。已成功 {updated}")
            break
        zh, _ = results.get(uuid, (None, None))
        if zh is None:
            failed += 1
            continue
        zh_esc = zh.replace("'", "''")
        if force:
            upd = f"UPDATE news_articles SET description='{zh_esc}' WHERE id='{uuid}';"
        else:
            upd = (
                f"UPDATE news_articles SET description='{zh_esc}' "
                f"WHERE id='{uuid}' AND (description IS NULL OR description='' "
                f"OR description LIKE '&lt;%' OR description LIKE '<a %' "
                f"OR description NOT LIKE '%[\u4e00-\u9fff]%');"
            )
        r = subprocess.run(DB_CMD + ["-c", upd], capture_output=True, text=True, timeout=15)
        if r.returncode != 0:
            print(f"  ❌ UPDATE 失败 {uuid[:8]}: {r.stderr.strip()[:200]}")
            failed += 1
        else:
            updated += 1

    elapsed = time.time() - start
    print(f"  [{cat}] updated={updated} failed={failed} elapsed={elapsed:.1f}s")
    return len(rows), updated

def main():
    dry = "--dry-run" in sys.argv
    days = 30
    cats = ["ai"]
    for a in sys.argv[1:]:
        if a.startswith("--days="):
            try:
                days = int(a.split("=", 1)[1])
            except ValueError:
                pass
        elif a.startswith("--category="):
            v = a.split("=", 1)[1]
            if v == "all":
                cats = ["ai", "politics", "github"]
            else:
                cats = [v]
    force = "--all" in sys.argv
    print(f"[fill_ai_zh] days={days} cats={cats} force={force} dry_run={dry}")
    total = 0
    for cat in cats:
        n, _ = run_category(cat, days, dry, force)
        total += n
    print(f"[fill_ai_zh] 总待改写={total} 条  done.")

if __name__ == "__main__":
    main()
