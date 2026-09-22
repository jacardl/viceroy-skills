#!/usr/bin/env python3
"""
GitHub Trending 采集 — v8（playwright + 高优先级源）

CRON调用:
  export TZ=Asia/Shanghai && python3 /Users/apple/.openclaw/workspace/scripts/radar/gh_collect.py [YYYY-MM-DD]
"""

import os, sys, subprocess, re, tempfile, json, urllib.request
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
        "reason": "阮一峰科技爱好者周刊，每周五发布，中文科技资讯高优",
    },
]

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
    """用 playwright 抓 GitHub Trending JS 渲染页面，返回 repo 列表。"""
    script_body = (
        "import sys, re\n"
        "sys.path.insert(0, '%s')\n"
        "from playwright.sync_api import sync_playwright\n"
        "with sync_playwright() as p:\n"
        "    browser = p.chromium.launch(args=['--no-sandbox', '--disable-dev-shm-usage'])\n"
        "    page = browser.new_page()\n"
        "    page.goto('https://github.com/trending', wait_until='networkidle', timeout=20000)\n"
        "    page.wait_for_timeout(3000)\n"
        "    html = page.content()\n"
        "    browser.close()\n"
        "articles = re.findall(r'<article[^>]*class=\"Box-row\"[^>]*>(.*?)</article>', html, re.DOTALL)\n"
        "results = []\n"
        "for art in articles:\n"
        "    repo_m = re.search(r'href=\"/([a-zA-Z0-9_\\\\-\\\\.]+/[a-zA-Z0-9_\\\\-\\\\.]+)\"', art)\n"
        "    if not repo_m:\n"
        "        continue\n"
        "    owner_repo = repo_m.group(1)\n"
        "    desc_m = re.search(r'<p[^>]*class=\"[^\"]*color-fg-muted[^\"]*\"[^>]*>(.*?)</p>', art, re.DOTALL)\n"
        "    desc = re.sub(r'<[^>]+>', '', (desc_m.group(1) if desc_m else '')).strip()[:300]\n"
        "    lang_m = re.search(r'programmingLanguage[\"\\s>]+([^<]+)', art)\n"
        "    lang = lang_m.group(1).strip() if lang_m else ''\n"
        "    today_m = re.search(r'([0-9,]+)\\s*stars?\\s*today', art, re.IGNORECASE)\n"
        "    stars_today = int(today_m.group(1).replace(',', '')) if today_m else 0\n"
        "    all_star_nodes = re.findall(r'([0-9,]+)\\s*stars?(?:\\s+today)?', art, re.IGNORECASE)\n"
        "    total_stars = int(all_star_nodes[-2].replace(',', '')) if len(all_star_nodes) >= 2 else 0\n"
        "    results.append((owner_repo, desc, lang, stars_today, total_stars))\n"
        "print('PARSE_OK:' + str(len(results)))\n"
        "for row in results:\n"
        "    print('REPO:' + row[0] + '|DESC:' + row[1][:80] + '|LANG:' + row[2] + '|TODAY:' + str(row[3]) + '|TOTAL:' + str(row[4]))\n"
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
                    "stars_today": 0, "total_stars": 0}
            for p in parts:
                if p.startswith("DESC:"): data["description"] = p[5:]
                elif p.startswith("LANG:"): data["language"] = p[5:]
                elif p.startswith("TODAY:"): data["stars_today"] = int(p[6:]) if p[6:] else 0
                elif p.startswith("TOTAL:"): data["total_stars"] = int(p[6:]) if p[6:] else 0
                else: data["owner_repo"] = p
            if data["owner_repo"]:
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

def fetch_high_priority_source(spec):
    """采集单个固定高优先级源（不依赖 gh CLI / GitHub API）。

    返回 dict: {owner_repo, issue_num, title, first_para, stars, score}
    失败抛异常，调用方负责捕获并跳过该源。
    """
    owner_repo = spec["owner_repo"]
    owner, repo = owner_repo.split("/", 1)
    branch = spec.get("branch", "master")

    status, body = _http_get(f"https://ungh.cc/repos/{owner}/{repo}")
    if status != 200:
        raise RuntimeError(f"ungh.cc returned {status}")
    meta = json.loads(body.decode("utf-8")).get("repo", {}) or {}
    stars = int(meta.get("stars", 0) or 0)

    status, body = _http_get(
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

    status, body = _http_get(
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
    r = subprocess.run(
        ["gh", "api", f"repos/{owner_repo}", "--jq", ".created_at,.stargazers_count"],
        capture_output=True, text=True, timeout=15
    )
    if r.returncode != 0:
        return None, None
    parts = r.stdout.strip().split("\n")
    if len(parts) >= 2:
        created = parts[0]
        stars = int(parts[1]) if parts[1].strip().isdigit() else 0
        return created, stars
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

# ─── 主流程 ───────────────────────────────────────────────

def main():
    print(f"[gh_collect] Fetching GitHub data for {TODAY}...")

    # 1. 固定高优先级源（先抓，trending 失败也能独立完成日报）
    hp_articles = []
    for spec in HIGH_PRIORITY_SOURCES:
        try:
            art = fetch_high_priority_source(spec)
            hp_articles.append((spec, art))
            print(f"[gh_collect] HP OK: {spec['owner_repo']} "
                  f"issue-{art['issue_num']} 《{art['title']}》 ⭐{art['stars']}")
        except Exception as e:
            print(f"[gh_collect] HP FAIL: {spec['owner_repo']}: {e}")

    # 2. GitHub Trending（失败不阻断 HP 源入榜）
    repos = fetch_trending_via_browser()
    if not repos:
        print("[gh_collect] WARN: Playwright returned no trending repos "
              "(will rely on HP sources only)")
        repos = []

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

    # 3. cleanup 后 HP 先写、trending 后写（HP blacklist_score=9999 天然置顶）
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
