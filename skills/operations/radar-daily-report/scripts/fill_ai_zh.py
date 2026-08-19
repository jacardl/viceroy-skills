#!/usr/bin/env python3
"""
fill_ai_zh.py — AI 板块 description 字段中文改写

铁律（来自 operations/radar-daily-report SKILL.md STEP 0.5b）：
  - 仅文字操作，不爬取/补抓/改 schema
  - ❌ 不补抓缺失数据行
  - ❌ 不改已存在字段（UPDATE 仅命中 description IS NULL/''）
  - 失败不阻塞 — 任意一条失败时链尾兜底用 title[:200]，不写空值
  - 单条 30s 超时，整批 5min 硬上限
  - 并发 4 workers（实测 9Router 1s/条）

触发场景：aihot 接口偶发返英文 title/summary（如 2026-08-19 4:00 cron
  采的 10 条 AI 全是英文，但 aihot 当前 API 实测返中文），
  push.py MSG2 标题用 desc_zh 替代英文 title 后，必须先把 description
  填成中文才能让推送显示中文。

用法：
  python3 fill_ai_zh.py --days=1            # 补最近 1 天（默认 30 天）
  python3 fill_ai_zh.py --days=7            # 补最近 7 天
  python3 fill_ai_zh.py --days=1 --dry-run  # 只显示预览

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

MODELS = ["ds/deepseek-chat"]
TIMEOUT = 30
BATCH_BUDGET = 300

def call_llm(model, user_text):
    body = {
        "model": model,
        "max_tokens": 200,
        "stream": False,
        "messages": [
            {"role": "system", "content": SYS_AI},
            {"role": "user", "content": user_text},
        ],
    }
    req = ureq.Request(URL, data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {KEY}"})
    with ureq.urlopen(req, timeout=TIMEOUT) as r:
        resp = json.loads(r.read())
    return resp["choices"][0]["message"]["content"].strip().strip('"').strip("'").strip()

def rewrite(title, content):
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

def main():
    dry = "--dry-run" in sys.argv
    days = 30
    for a in sys.argv[1:]:
        if a.startswith("--days="):
            try:
                days = int(a.split("=", 1)[1])
            except ValueError:
                pass
    # 限定近 N 天（避免补远古烂数据）
    # 默认 description 为空才补；加 --all 覆盖所有（用于历史数据全是英文 summary 的情况）
    force = "--all" in sys.argv
    where_extra = "" if force else "AND (description IS NULL OR description='')"
    raw = sql(
        f"SELECT id, title, content FROM news_articles "
        f"WHERE category='ai' "
        f"AND article_date >= (CURRENT_DATE - INTERVAL '{days} days') "
        f"{where_extra} "
        f"ORDER BY article_date DESC, blacklist_score DESC NULLS LAST;"
    )
    if not raw:
        mode = "全部" if force else "description 为空"
        print(f"✅ AI 板块{mode}已无需改写（近 {days} 天）。")
        return

    mode = "全部强制" if force else "空 description"
    print(f"[fill_ai_zh] days={days} mode={mode} 待改写={len(raw.splitlines())} 条  dry_run={dry}")
    rows = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("|", 2)
        if len(parts) < 3:
            print(f"  ❌ skip 解析失败: {line[:80]}")
            continue
        uuid, title, content = parts[0].strip(), parts[1].strip(), parts[2].strip()
        if not title:
            print(f"  ❌ skip {uuid} title 空")
            continue
        rows.append((uuid, title, content))

    start = time.time()
    results = {}  # uuid -> (zh, model)

    # 并发调 9Router（实测 1s/条，4 workers 足够）
    with ThreadPoolExecutor(max_workers=4) as pool:
        futs = {pool.submit(rewrite, r[1], r[2]): r[0] for r in rows}
        for fut in as_completed(futs):
            uuid = futs[fut]
            try:
                zh, model = fut.result()
                results[uuid] = (zh, model)
            except Exception as e:
                print(f"  ❌ {uuid[:8]} 失败: {type(e).__name__}: {e}")
                results[uuid] = (None, None)

    # 打印预览
    for uuid, title, _ in rows:
        zh, model = results.get(uuid, (None, None))
        if zh is None:
            print(f"  ❌ {uuid[:8]}: {title[:50]!r} → 失败")
        else:
            print(f"  [{model}] {uuid[:8]}: {title[:50]!r}")
            print(f"    → {zh[:100]!r}")

    if dry:
        print(f"\n[dry-run] done elapsed={time.time()-start:.1f}s")
        return

    # 批量 UPDATE
    updated = 0
    failed = 0
    for uuid, _, _ in rows:
        if time.time() - start > BATCH_BUDGET:
            print(f"  ⏱️ 整批预算 {BATCH_BUDGET}s 耗尽，提前退出。已成功 {updated}")
            break
        zh, _ = results.get(uuid, (None, None))
        if zh is None:
            failed += 1
            continue
        zh_esc = zh.replace("'", "''")
        update_where = "" if force else "AND (description IS NULL OR description='')"
        upd = (
            f"UPDATE news_articles SET description='{zh_esc}' "
            f"WHERE id='{uuid}' {update_where};"
        )
        r = subprocess.run(DB_CMD + ["-c", upd], capture_output=True, text=True, timeout=15)
        if r.returncode != 0:
            print(f"  ❌ UPDATE 失败 {uuid[:8]}: {r.stderr.strip()[:200]}")
            failed += 1
        else:
            updated += 1

    # 验收
    cnt_empty = sql(
        f"SELECT COUNT(*) FROM news_articles "
        f"WHERE category='ai' "
        f"AND article_date >= (CURRENT_DATE - INTERVAL '{days} days') "
        f"AND (description IS NULL OR description='');"
    )
    print(f"\n[fill_ai_zh] done: updated={updated} failed={failed} "
          f"elapsed={time.time()-start:.1f}s  remaining_empty={cnt_empty}")

if __name__ == "__main__":
    main()
