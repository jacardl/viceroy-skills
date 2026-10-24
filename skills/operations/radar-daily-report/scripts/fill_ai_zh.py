#!/usr/bin/env python3
"""
fill_ai_zh.py — AI / GitHub 板块 description 中文改写的 DB 读写助手

⚠️ 本脚本不做任何模型调用（2026-10-24 起，原 9router 直连已移除）。
中文摘要由调用方 AI agent（Mavis cron 轮次）用自己的模型生成；
本脚本只负责两件事：

  --list   列出待改写行，stdout 输出 JSON：
           [{"id","cat","title","content"}]（content 截断 400 字）
  --apply  把 agent 生成的 [{"id","zh"}] 写回 news_articles.description

用法：
  python3 fill_ai_zh.py --list --category=all --days=1 [--all] > /tmp/radar_zh_todo.json
  # agent 读 todo，逐条生成 ≤80 字中文 description，存 /tmp/radar_zh_done.json
  python3 fill_ai_zh.py --apply /tmp/radar_zh_done.json [--force]

铁律（不变）：
  - 仅文字操作，不爬取/补抓/改 schema
  - 默认只处理坏数据（description 为空 / URL / 无中文），--all(list) / --force(apply) 才全覆盖
  - apply 非 force 模式带坏数据守卫：只更新仍是坏数据的行，避免覆盖已修好的中文

附注（2026-10-24 修复）：旧版用 LIKE '%[一-龥]%' 判中文，LIKE 不支持字符区间，
该条件永不命中 → 默认模式实际等于全量。现改用正则操作符 !~ '[一-龥]'。
"""
import sys, json, subprocess

DB_CMD = ["docker", "exec", "radar-db", "psql", "-U", "radar", "-d", "radar", "-t", "-q", "-A"]

BAD_DESC_SQL = ("(description IS NULL OR description='' OR description LIKE '&lt;%' "
                "OR description LIKE '<a %' OR description !~ '[一-龥]')")

def sql(q):
    r = subprocess.run(DB_CMD + ["-c", q], capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise RuntimeError(f"psql error: {r.stderr.strip()[:300]}")
    return r.stdout.strip()

def list_rows(cats, days, force):
    where_bad = "" if force else f"AND {BAD_DESC_SQL}"
    cat_in = ",".join(f"'{c}'" for c in cats)
    out = sql(
        "SELECT coalesce(json_agg(json_build_object("
        "'id', id::text, 'cat', category, 'title', title, "
        "'content', substr(coalesce(content,''),1,400)"
        ") ORDER BY article_date DESC, category)::text, '[]') "
        "FROM news_articles "
        f"WHERE category IN ({cat_in}) "
        f"AND article_date >= (CURRENT_DATE - INTERVAL '{days} days') "
        f"{where_bad};"
    )
    return json.loads(out) if out else []

def apply(path, force):
    items = json.load(open(path, encoding="utf-8"))
    if not items:
        print("[apply] 空列表，0 更新"); return
    stmts, skipped = [], 0
    for it in items:
        uid, zh = (it.get("id") or "").strip(), (it.get("zh") or "").strip()
        if not uid or not zh:
            skipped += 1; continue
        zh = zh.replace("'", "''")
        guard = "" if force else f" AND {BAD_DESC_SQL}"
        stmts.append(f"UPDATE news_articles SET description='{zh}' WHERE id='{uid}'{guard};")
    if stmts:
        sql("BEGIN;\n" + "\n".join(stmts) + "\nCOMMIT;")
    print(f"[apply] 提交 {len(stmts)} 条 UPDATE（{'force 全覆盖' if force else '带坏数据守卫'}），跳过空 id/zh {skipped} 条")

def main():
    args = sys.argv[1:]
    cats, days = ["ai"], 1
    force = "--all" in args or "--force" in args
    apply_file = None
    for i, a in enumerate(args):
        if a.startswith("--category="):
            v = a.split("=", 1)[1]
            cats = ["ai", "github"] if v == "all" else [v]
        elif a.startswith("--days="):
            days = int(a.split("=", 1)[1])
        elif a == "--apply" and i + 1 < len(args):
            apply_file = args[i + 1]
    if apply_file:
        apply(apply_file, "--force" in args)
    elif "--list" in args:
        rows = list_rows(cats, days, force)
        print(json.dumps(rows, ensure_ascii=False, indent=1))
        print(f"[list] {len(rows)} 条待改写 cats={cats} days={days} force={force}", file=sys.stderr)
    else:
        print(__doc__); sys.exit(2)

if __name__ == "__main__":
    main()
