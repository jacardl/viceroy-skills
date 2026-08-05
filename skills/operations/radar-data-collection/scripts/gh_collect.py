#!/usr/bin/env python3
"""
GitHub Trending 采集 — v7（playwright 渲染版）

CRON调用:
  export TZ=Asia/Shanghai && python3 /Users/apple/.openclaw/workspace/scripts/radar/gh_collect.py [YYYY-MM-DD]
"""

import os, sys, subprocess, re, tempfile
from datetime import datetime

PYTHON_BIN = "/Users/apple/.agent-reach-venv314/bin/python3"
PLAYWRIGHT_PATH = "/Users/apple/.agent-reach-venv314/lib/python3.14/site-packages"

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
    # 直接写脚本文件，避免 -c 参数转义问题
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
        "    repo_m = re.search(r'href=\"/([a-zA-Z0-9_\\\\-\\\\.]+/[a-zA-Z0-9_\\\\-\\\.]+)\"', art)\n"
        "    if not repo_m:\n"
        "        continue\n"
        "    owner_repo = repo_m.group(1)\n"
        "    desc_m = re.search(r'<p[^>]*class=\"[^\"]*color-fg-muted[^\"]*\"[^>]*>(.*?)</p>', art, re.DOTALL)\n"
        "    desc = re.sub(r'<[^>]+>', '', (desc_m.group(1) if desc_m else '')).strip()[:300]\n"
        "    lang_m = re.search(r'programmingLanguage[\"\\\s>]+([^<]+)', art)\n"
        "    lang = lang_m.group(1).strip() if lang_m else ''\n"
        "    # stars today\n"
        "    today_m = re.search(r'([0-9,]+)\s*stars?\s*today', art, re.IGNORECASE)\n"
        "    stars_today = int(today_m.group(1).replace(',', '')) if today_m else 0\n"
        "    # total stars: 找 article 里所有含 stars 的数字节点，倒数第一个是 stars today，倒数第二个是 total\n"
        "    all_star_nodes = re.findall(r'([0-9,]+)\s*stars?(?:\s+today)?', art, re.IGNORECASE)\n"
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

# ─── 黑马分 ───────────────────────────────────────────────

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
        desc_clean = (repo.get('description') or '').strip()[:300]  # 干净中文 desc，不带 ⭐
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
    print(f"[gh_collect] Fetching GitHub Trending for {TODAY} via playwright...")

    repos = fetch_trending_via_browser()
    if not repos:
        print("[gh_collect] ERROR: Playwright returned no repos")
        return False

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

    cleanup_existing(TODAY)
    insert_to_db(top10, TODAY)

    r = DB_PSQL(f"SELECT COUNT(*) FROM news_articles WHERE article_date='{TODAY}' AND category='github';")
    count = int(r.stdout.strip()) if r.stdout.strip().isdigit() else 0

    print(f"[gh_collect] Inserted {count}/{len(top10)} repos")
    for i, repo in enumerate(top10, 1):
        new_tag = " (NEW)" if repo.get("is_new") else ""
        print(f"  {i}. {repo['owner_repo']} - "
              f"*{repo.get('stars_today', 0)}today/*{repo.get('total_stars', 0)}total "
              f"[{repo.get('language', '')}] "
              f"score={repo['black_horse_score']:.0f}{new_tag}")

    return count >= 5

if __name__ == "__main__":
    main()
    sys.exit(0)
