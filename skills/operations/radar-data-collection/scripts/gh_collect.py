#!/usr/bin/env python3
"""
GitHub Trending 采集 — v10（多视图 trending + ungh 替代 gh CLI + HP retry + 等待加强）

v9 → v10 变更 (2026-10-24):
  A. trending 抓 3 个视图（daily/weekly/monthly），合并去重扩大候选池；
     weekly/monthly 的 stars 按 /7 /30 估算 stars_today
  B. DEDUP_WINDOW_DAYS 2 → 1，缓解候选池过窄
  C. gh_api_fetch_created_at 改用 ungh.cc（绕开 github.com 主网墙）
  D. HP 源 HTTP 请求加 retry + 指数 backoff（429/5xx）
  E. Playwright 抓 trending 时 wait_for_function 等 ≥10 个 article 渲染

v8 → v9 变更 (2026-10-11):
  A. 跨日去重：trending 入榜前查 DB 近 2 天已推过的 owner_repo，过滤掉
  B. sponsors/* 推广位过滤：默认全过滤，仅白名单（mattpocock）保留
  D. HP 源降频：ruanyf/weekly 近 7 天若已置顶过，score 9999→100（不再置顶）

CRON调用:
  export TZ=Asia/Shanghai && python3 /Users/apple/.openclaw/workspace/scripts/radar/gh_collect.py [YYYY-MM-DD]
"""

import os, sys, subprocess, re, tempfile, json, time, urllib.request, urllib.error
from datetime import datetime

PYTHON_BIN = "/Users/apple/.agent-reach-venv314/bin/python3"
PLAYWRIGHT_PATH = "/Users/apple/.agent-reach-venv314/lib/python3.14/site-packages"

# ─── 固定高优先级源（每日必入榜） ──────────────────────────────
# 采集链路: ungh.cc + raw.githubusercontent.com（不依赖 gh CLI / GitHub API，
# GitHub 主网被墙时仍可用）。main() 先抓这些，再抓 trending，
# push.py v4.5+ 按 blacklist_score DESC 排序，HP 源天然置顶。
HIGH_PRIORITY_SOURCES = [
    {
        "owner_repo": "ruanyf/weekly",
        "branch": "master",
        "score": 9999.0,
        "score_dedup": 100.0,   # v9: 近 7 天若已置顶过，score 降为此值（不再置顶但仍写入）
        "dedup_window_days": 7,  # 降频窗口
        "reason": "阮一峰科技爱好者周刊，每周五发布，中文科技资讯高优",
    },
]

# v9: sponsors/* 推广位白名单（GitHub Trending 反复推赞助项目，白名单保留真价值源）
SPONSOR_WHITELIST = ["sponsors/mattpocock"]

# v10: 跨日去重窗口（天）— 由 2 改为 1，避免候选池过窄
DEDUP_WINDOW_DAYS = 1

TODAY = sys.argv[1] if len(sys.argv) > 1 else None
if not TODAY:
    r = subprocess.run(
        ["docker", "exec", "radar-db", "date", "+%Y-%m-%d"],
        capture_output=True, text=True, timeout=5
    )
    TODAY = r.stdout.strip() or datetime.now().strftime("%Y-%m-%d")

DB_PSQL = lambda sql: subprocess.run(
    ["docker", "exec", "radar-db", "psql", "-U", "radar", "-d", "radar", "-t", "-c", sql],
    capture_output=True, text=True, timeout=30
)

# ─── Playwright 抓取 ────────────────────────────────────────

def fetch_trending_via_browser():
    """用 playwright 抓 GitHub Trending 3 个视图（daily/weekly/monthly），合并去重。
    weekly/monthly 的 stars 是周期累计，估算 stars_today = weekly/7 或 monthly/30。
    """
    script_body = (
        "import sys, re\n"
        "sys.path.insert(0, '%s')\n"
        "from playwright.sync_api import sync_playwright\n"
        "SINCE_LIST = [('daily', 1), ('weekly', 7), ('monthly', 30)]\n"
        "merged = {}\n"
        "with sync_playwright() as p:\n"
        "    browser = p.chromium.launch(args=['--no-sandbox', '--disable-dev-shm-usage'])\n"
        "    page = browser.new_page()\n"
        "    for since, divisor in SINCE_LIST:\n"
        "        url = 'https://github.com/trending?since=' + since\n"
        "        try:\n"
        "            page.goto(url, wait_until='domcontentloaded', timeout=30000)\n"
        "            try:\n"
        "                page.wait_for_function(\n"
        "                    \"document.querySelectorAll('article.Box-row').length >= 10\",\n"
        "                    timeout=15000\n"
        "                )\n"
        "            except Exception:\n"
        "                pass\n"
        "        except Exception as ge:\n"
        "            print('GOTO_WARN:' + since + ':' + type(ge).__name__)\n"
        "            continue\n"
        "        html = page.content()\n"
        "        articles = re.findall(r'<article[^>]*class=\"Box-row\"[^>]*>(.*?)</article>', html, re.DOTALL)\n"
        "        print('PARSE_' + since.upper() + ':' + str(len(articles)))\n"
        "        for art in articles:\n"
        "            repo_m = re.search(r'href=\\\"/([a-zA-Z0-9_\\-\\.]+/[a-zA-Z0-9_\\-\\.]+)\\\"', art)\n"
        "            if not repo_m:\n"
        "                continue\n"
        "            owner_repo = repo_m.group(1)\n"
        "            desc_m = re.search(r'<p[^>]*class=\"[^\"]*color-fg-muted[^\"]*\"[^>]*>(.*?)</p>', art, re.DOTALL)\n"
        "            desc = re.sub(r'<[^>]+>', '', (desc_m.group(1) if desc_m else '')).strip()[:300]\n"
        "            lang_m = re.search(r'programmingLanguage[\\\"\\s>]+([^<]+)', art)\n"
        "            lang = lang_m.group(1).strip() if lang_m else ''\n"
        "            today_m = re.search(r'([0-9,]+)\\s*stars?\\s*(?:today|this week|this month)', art, re.IGNORECASE)\n"
        "            period_stars = int(today_m.group(1).replace(',', '')) if today_m else 0\n"
        "            stars_today = period_stars if divisor == 1 else max(1, period_stars // divisor)\n"
        "            all_star_nodes = re.findall(r'([0-9,]+)\\s*stars?', art, re.IGNORECASE)\n"
        "            total_stars = int(all_star_nodes[-2].replace(',', '')) if len(all_star_nodes) >= 2 else 0\n"
        "            if owner_repo not in merged or stars_today > merged[owner_repo][2]:\n"
        "                merged[owner_repo] = (desc, lang, stars_today, total_stars, since)\n"
        "    browser.close()\n"
        "    results = [(k,) + v for k, v in merged.items()]\n"
        "print('PARSE_OK:' + str(len(results)))\n"
        "for row in results:\n"
        "    print('REPO:' + row[0] + '|DESC:' + row[1][:80] + '|LANG:' + row[2] + '|TODAY:' + str(row[3]) + '|TOTAL:' + str(row[4]) + '|SINCE:' + row[5])\n"
    ) % PLAYWRIGHT_PATH

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        f.write(script_body)
        script_path = f.name

    try:
        r = subprocess.run(
            [PYTHON_BIN, script_path],
            capture_output=True, text=True, timeout=55
        )
    finally:
        os.unlink(script_path)

    if r.returncode != 0:
        print("[gh_collect] Playwright error: " + (r.stderr or r.stdout)[:300])
        return None

    lines = r.stdout.strip().split("\n")
    repos = []
    for line in lines:
        if line.startswith("REPO:"):
            parts = line[5:].split("|")
            data = {"owner_repo": "", "description": "", "language": "",
                    "stars_today": 0, "total_stars": 0, "since": ""}
            for p in parts:
                if p.startswith("DESC:"): data["description"] = p[5:]
                elif p.startswith("LANG:"): data["language"] = p[5:]
                elif p.startswith("TODAY:"): data["stars_today"] = int(p[6:]) if p[6:] else 0
                elif p.startswith("TOTAL:"): data["total_stars"] = int(p[6:]) if p[6:] else 0
                elif p.startswith("SINCE:"): data["since"] = p[6:]
                else: data["owner_repo"] = p
            if data["owner_repo"] and "/" in data["owner_repo"]:
                repos.append(data)
        elif line.startswith("PARSE_OK:"):
            print("[gh_collect] Playwright parsed " + line.split(":")[1] + " repos")
    return repos

# ─── 固定高优先级源采集（ungh.cc + raw 回退链） ──────────────────

def _http_get(url, timeout=10):
    """简单 GET，返回 (status, bytes)。"""
    req = urllib.request.Request(url, headers={"User-Agent": "radar-gh-collect/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status, resp.read()

def _http_get_retry(url, timeout=10, max_retry=3):
    """带指数 backoff 的 GET。429/5xx/网络异常重试 max_retry 次。"""
    last_err = None
    for attempt in range(max_retry):
        try:
            return _http_get(url, timeout=timeout)
        except urllib.error.HTTPError as e:
            last_err = e
            if e.code in (429, 500, 502, 503, 504) and attempt < max_retry - 1:
                wait = 3 * (2 ** attempt)
                print(f"[gh_collect] HTTP {e.code} {url[:80]}, retry in {wait}s ({attempt+1}/{max_retry})")
                time.sleep(wait)
                continue
            raise
        except Exception as e:
            last_err = e
            if attempt < max_retry - 1:
                wait = 3 * (2 ** attempt)
                print(f"[gh_collect] {type(e).__name__} {url[:80]}, retry in {wait}s ({attempt+1}/{max_retry})")
                time.sleep(wait)
                continue
            raise
    raise last_err

def fetch_high_priority_source(spec):
    """采集单个固定高优先级源（不依赖 gh CLI / GitHub API）。

    返回 dict: {owner_repo, issue_num, title, first_para, stars, score}
    失败抛异常，调用方负责捕获并跳过该源。
    """
    owner_repo = spec["owner_repo"]
    owner, repo = owner_repo.split("/", 1)
    branch = spec.get("branch", "master")

    status, body = _http_get_retry(f"https://ungh.cc/repos/{owner}/{repo}")
    if status != 200:
        raise RuntimeError(f"ungh.cc returned {status}")
    meta = json.loads(body.decode("utf-8")).get("repo", {}) or {}
    stars = int(meta.get("stars", 0) or 0)

    status, body = _http_get_retry(
        f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/README.md"
    )
    if status != 200:
        raise RuntimeError(f"README fetch returned {status}")
    readme = body.decode("utf-8")
    m = re.search(r"\(docs/(issue-\d+\.md)\)", readme)
    if not m:
        raise RuntimeError("no issue link found in README")
    issue_slug = m.group(1)
    issue_num = re.search(r"issue-(\d+)", issue_slug).group(1)

    status, body = _http_get_retry(
        f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/docs/{issue_slug}"
    )
    if status != 200:
        raise RuntimeError(f"issue fetch returned {status}")
    issue_text = body.decode("utf-8")

    h1_m = re.search(r"^#\s+(.+?)\s*$", issue_text, re.MULTILINE)
    title = (h1_m.group(1) if h1_m else f"issue-{issue_num}").strip()
    theme = re.sub(r"^科技爱好者周刊（.+?）：\s*", "", title).strip() or title

    first_para = ""
    for para in re.split(r"\n\s*\n", issue_text):
        s = para.strip()
        if not s:
            continue
        if s.startswith(("#", "!", ">", "<")):
            continue
        if s.startswith("```") or "```" in s[:6]:
            continue
        first_para = s
        break
    first_para = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", first_para)
    first_para = re.sub(r"\[[^\]]+\]", "", first_para)
    first_para = re.sub(r"\*+", "", first_para)
    first_para = re.sub(r"[`_]+", "", first_para)
    first_para = re.sub(r"\s+", " ", first_para).strip()
    sentence_end = re.search(r"[。！？!?]", first_para)
    if sentence_end:
        first_para = first_para[:sentence_end.end()]
    if len(first_para) > 200:
        first_para = first_para[:200].rstrip() + "…"

    return {
        "owner_repo": owner_repo,
        "issue_num": issue_num,
        "title": theme,
        "first_para": first_para,
        "stars": stars,
        "score": float(spec.get("score", 9999.0)),
    }


def insert_hp_to_db(spec, article, date):
    """写入一条 HP 源记录（schema 与 trending repo 一致，字段微调）。"""
    owner_repo = article["owner_repo"]
    issue_num = article["issue_num"]
    theme = article["title"]
    first_para = article["first_para"]
    stars = article["stars"]
    score = article["score"]

    title_full = f"{owner_repo} — {theme[:80]}"
    desc_clean = f"第 {issue_num} 期《{theme}》— {first_para}"
    content = (
        f"Source: HIGH_PRIORITY\n"
        f"Reason: {spec.get('reason', '')}\n"
        f"Issue: {issue_num}\n"
        f"Issue Theme: {theme}\n"
        f"Total Stars: {stars:,}\n"
        f"Black Horse Score: {score}\n"
        f"Description: {desc_clean}\n"
        f"\n--- raw excerpt ---\n"
        + desc_clean
    )

    sql = f"""INSERT INTO news_articles
        (article_date, category, title, description, content, source, url, lang,
         blacklist_score, stars_count, period_new_stars, is_new_project)
    VALUES
        ('{date}', 'github', {_esc(title_full)}, {_esc(desc_clean)}, {_esc(content)},
         'Markdown', 'https://github.com/{owner_repo}',
         'zh', {score}, {stars}, 0, false)
    ON CONFLICT DO NOTHING;"""
    DB_PSQL(sql)


# ─── gh CLI ────────────────────────────────────────────────

def gh_api_fetch_created_at(owner_repo):
    """经 ungh.cc 拿 created_at 和 stars（绕开 github.com 主网墙，替代 gh CLI）。
    返回 (created_at_iso, stars)；失败返回 (None, None)。
    """
    try:
        status, body = _http_get_retry(f"https://ungh.cc/repos/{owner_repo}", timeout=10)
        if status != 200:
            return None, None
        meta = json.loads(body.decode("utf-8")).get("repo", {}) or {}
        created = meta.get("createdAt")  # ungh 返回 ISO8601 camelCase
        stars = int(meta.get("stars", 0) or 0)
        return created, stars
    except Exception:
        return None, None

# ─── 黑马分 ────────────────────────────────────────────────

def calc_score(stars_today, total_stars, created_at=None):
    if total_stars < 5000:
        bonus = 2.0
    elif total_stars < 20000:
        bonus = 1.5
    elif total_stars < 100000:
        bonus = 1.0
    else:
        bonus = 0.8
    score = stars_today * bonus
    if created_at:
        try:
            created = datetime.fromisoformat(created_at.replace("Z", "+00:00").split("+")[0])
            age_days = (datetime.now(created.tzinfo) - created).days
            if age_days < 30:
                score *= 1.5
        except Exception:
            pass
    return round(score, 2)

# ─── DB 写入 ──────────────────────────────────────────────

def _esc(s):
    if s is None:
        return "NULL"
    v = str(s).replace("'", "''").replace("\n", " ")[:500]
    return f"'{v}'"

def insert_to_db(repos, date):
    """字段含义（铁律，对齐 push.py build_msg4）：
      title            = "owner/repo — desc[:80]"（含简介前缀）
      description      = 干净的中文 desc（≤300字），不含统计数字  ← 关键
      content          = 完整 metadata（语言/stars today/total/黑马分/是否新项目/desc 全文）
      stars_count      = total_stars（GitHub 总 star）
      period_new_stars = stars_today（今日新增）
      blacklist_score  = 黑马分（push 按此排序取 top 10）
      source           = language（如 "Python"/"TypeScript"）
      url              = https://github.com/{owner_repo}
    """
    for repo in repos:
        repo_full  = repo['owner_repo']
        desc_clean = (repo.get('description') or '').strip()[:300]
        lang       = repo.get('language', '') or ''
        total      = int(repo.get('total_stars', 0) or 0)
        today      = int(repo.get('stars_today', 0) or 0)
        score      = float(repo.get('black_horse_score', 0) or 0)
        is_new     = bool(repo.get('is_new'))

        title = f"{repo_full} — {desc_clean[:80]}" if desc_clean else repo_full
        content = (
            f"Language: {lang}\n"
            f"Total Stars: {total:,}\n"
            f"Stars Today: {today:,}\n"
            f"Black Horse Score: {score}\n"
            f"New Project: {'Yes' if is_new else 'No'}\n"
            f"Description: {desc_clean}"
        )
        sql = f"""INSERT INTO news_articles
            (article_date, category, title, description, content, source, url, lang,
             blacklist_score, stars_count, period_new_stars, is_new_project)
        VALUES
            ('{date}', 'github', {_esc(title)}, {_esc(desc_clean)}, {_esc(content)},
             {_esc(lang)}, 'https://github.com/{repo_full}',
             'en', {score}, {total}, {today}, {is_new})
        ON CONFLICT DO NOTHING;"""
        DB_PSQL(sql)

def cleanup_existing(date):
    DB_PSQL(f"DELETE FROM news_articles WHERE article_date='{date}' AND category='github';")


# ─── v9: 去重 / 过滤 helpers ─────────────────────────────────────

def get_recently_pushed_repos(days):
    """查 DB 返回近 N 天 (含今日) 已推过的 owner_repo set。
    匹配模式：title 以 'owner/repo' 开头（insert_to_db 写库格式）。"""
    sql = (
        f"SELECT DISTINCT split_part(title, ' —', 1) "
        f"FROM news_articles "
        f"WHERE category='github' "
        f"  AND article_date >= (DATE '{TODAY}' - INTERVAL '{days} day') "
        f"  AND title LIKE '% — %';"
    )
    r = DB_PSQL(sql)
    rows = set()
    for line in (r.stdout or "").splitlines():
        s = line.strip()
        if s and "/" in s:
            rows.add(s)
    return rows


def hp_pinned_recently(owner_repo, days):
    """HP 源是否近 N 天以置顶身份（blacklist_score >= 9999）写过库。
    用于 HP 源降频判定。"""
    sql = (
        f"SELECT COUNT(*) FROM news_articles "
        f"WHERE category='github' "
        f"  AND article_date >= (DATE '{TODAY}' - INTERVAL '{days} day') "
        f"  AND split_part(title, ' —', 1) = '{owner_repo}' "
        f"  AND blacklist_score >= 9999;"
    )
    r = DB_PSQL(sql)
    try:
        return int((r.stdout or "0").strip()) > 0
    except Exception:
        return False


def is_sponsor(repo_full):
    """是否 sponsors/* 推广位 + 不在白名单。"""
    return repo_full.startswith("sponsors/") and repo_full not in SPONSOR_WHITELIST

# ─── 主流程 ───────────────────────────────────────────────

def main():
    print(f"[gh_collect] Fetching GitHub data for {TODAY}...")

    # 0. v9 跨日去重池：近 DEDUP_WINDOW_DAYS 天已推过的 owner_repo
    recent = get_recently_pushed_repos(DEDUP_WINDOW_DAYS)
    if recent:
        sample = sorted(recent)[:5]
        print(f"[gh_collect] Dedup pool ({DEDUP_WINDOW_DAYS}d): {len(recent)} repos, "
              f"sample={sample}{'...' if len(recent) > 5 else ''}")

    # 1. 固定高优先级源（先抓，trending 失败也能独立完成日报）
    hp_articles = []
    for spec in HIGH_PRIORITY_SOURCES:
        try:
            art = fetch_high_priority_source(spec)
            # v9 降频：近 N 天若已置顶过该源，score 降为 score_dedup
            window = int(spec.get("dedup_window_days", 7))
            if hp_pinned_recently(spec["owner_repo"], window):
                art["score"] = float(spec.get("score_dedup", 100.0))
                print(f"[gh_collect] HP DEDUP: {spec['owner_repo']} score→{art['score']} "
                      f"(近 {window} 天已置顶过)")
            hp_articles.append((spec, art))
            print(f"[gh_collect] HP OK: {spec['owner_repo']} "
                  f"issue-{art['issue_num']} 《{art['title']}》 ⭐{art['stars']} score={art['score']}")
        except Exception as e:
            print(f"[gh_collect] HP FAIL: {spec['owner_repo']}: {e}")

    # 2. GitHub Trending（失败不阻断 HP 源入榜）
    repos = fetch_trending_via_browser()
    if not repos:
        print("[gh_collect] WARN: Playwright returned no trending repos "
              "(will rely on HP sources only)")
        repos = []

    # 2a. v9 过滤 sponsors/* 推广位（仅白名单保留）
    pre = len(repos)
    repos = [r for r in repos if not is_sponsor(r["owner_repo"])]
    if len(repos) < pre:
        print(f"[gh_collect] Filtered {pre - len(repos)} sponsors/* "
              f"(whitelist={SPONSOR_WHITELIST})")

    # 2b. v9 跨日去重：近 DEDUP_WINDOW_DAYS 天已推过的过滤
    pre = len(repos)
    repos = [r for r in repos if r["owner_repo"] not in recent]
    if len(repos) < pre:
        print(f"[gh_collect] Deduped {pre - len(repos)} repos pushed in last {DEDUP_WINDOW_DAYS} days")

    for repo in repos:
        created_at, gh_stars = gh_api_fetch_created_at(repo["owner_repo"])
        if gh_stars:
            repo["total_stars"] = gh_stars
        repo["created_at"] = created_at
        repo["is_new"] = False
        repo["black_horse_score"] = calc_score(
            repo["stars_today"], repo["total_stars"], created_at)
        if created_at:
            try:
                created = datetime.fromisoformat(created_at.replace("Z", "+00:00").split("+")[0])
                repo["is_new"] = (datetime.now(created.tzinfo) - created).days < 30
            except Exception:
                pass

    repos.sort(key=lambda r: r["black_horse_score"], reverse=True)
    top10 = repos[:10]

    # 3. cleanup 后 HP 先写、trending 后写
    #    注：HP 源降频后 score=100，不再置顶；trending 第一名 score 仍可超过 100（黑马分通常数千）
    cleanup_existing(TODAY)
    for spec, art in hp_articles:
        insert_hp_to_db(spec, art, TODAY)
    insert_to_db(top10, TODAY)

    r = DB_PSQL(f"SELECT COUNT(*) FROM news_articles WHERE article_date='{TODAY}' AND category='github';")
    count = int(r.stdout.strip()) if r.stdout.strip().isdigit() else 0

    print(f"[gh_collect] Inserted {count} repos "
          f"(HP={len(hp_articles)}, trending={len(top10)})")
    for i, repo in enumerate(top10, 1):
        new_tag = " (NEW)" if repo.get("is_new") else ""
        print(f"  {i}. {repo['owner_repo']} - "
              f"*{repo.get('stars_today', 0)}today/*{repo.get('total_stars', 0)}total "
              f"[{repo.get('language', '')}] "
              f"score={repo['black_horse_score']:.0f}{new_tag}")

    return len(hp_articles) >= 1 or count >= 5

if __name__ == "__main__":
    main()
    sys.exit(0)
