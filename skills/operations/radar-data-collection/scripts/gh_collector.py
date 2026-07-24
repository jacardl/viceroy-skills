#!/usr/bin/env python3
"""
GitHub Trending 采集脚本
用法：bash --noprofile --norc -c '/Users/apple/.agent-reach-venv314/bin/python3 /tmp/gh_collector.py'
输出：/tmp/gh_repos.json
"""
import re, json, urllib.request, sys, os

# ── GitHub Token ──────────────────────────────────────────────────────────────
HERMES_KEYS = "/Users/apple/.hermes/keys"
GH_TOKEN_FILE = os.path.join(HERMES_KEYS, "github_token.txt")

def get_token():
    try:
        with open(GH_TOKEN_FILE) as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""

TOKEN = get_token()
HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "radar-bot/1.0"
}

# ── GitHub API ────────────────────────────────────────────────────────────────
def gh_api(path):
    url = f"https://api.github.com{path}"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=8) as r:
            return json.loads(r.read())
    except Exception:
        return None

# ── Trending 抓取 ─────────────────────────────────────────────────────────────
def fetch_trending(agent_reach_available=True):
    repos = []
    md = ""

    # 方式A: agent-reach WebChannel（推荐）
    if agent_reach_available:
        try:
            from agent_reach.channels.web import WebChannel
            ch = WebChannel()
            md = ch.read('https://github.com/trending')
        except Exception:
            md = ""

    # 方式B: web_fetch 兜底
    if not md:
        try:
            import urllib.request as ur
            req = ur.Request(
                "https://github.com/trending",
                headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
            )
            with ur.urlopen(req, timeout=10) as r:
                html = r.read().decode("utf-8", errors="ignore")
            # 简单 HTML→markdown 近似解析
            md = html_to_md_approx(html)
        except Exception:
            pass

    if not md:
        print("ERROR: 无法获取 GitHub Trending 页面", file=sys.stderr)
        return []

    lines = md.split('\n')
    for i, line in enumerate(lines):
        if not line.strip().startswith('## ['):
            continue
        m = re.search(r'\[([^\]]+)\]\(https://github\.com/([^\)]+)\)', line)
        if not m:
            continue
        full_name = m.group(2).strip()

        # 找页面描述（下一行非stars行）
        desc = ''
        for j in range(i+1, i+5):
            if j >= len(lines):
                break
            nl = lines[j].strip()
            if nl and not nl.startswith('[') and 'stars' not in nl.lower():
                desc = nl
                break

        # 找 stars 行
        stars_line = ''
        for j in range(i+1, i+12):
            if j >= len(lines):
                break
            if 'stars today' in lines[j].lower():
                stars_line = lines[j]
                break

        if not stars_line:
            continue

        m_lang = re.search(r'^([A-Za-z+#]+)\[([\d,]+)\]', stars_line)
        m_today = re.search(r'([\d,]+)\s+stars\s+today', stars_line, re.I)
        if not (m_lang and m_today):
            continue

        lang = m_lang.group(1)
        total = int(m_lang.group(2).replace(',', ''))
        today = int(m_today.group(1).replace(',', ''))

        bonus = 2.0 if total < 5000 else 1.5 if total < 20000 else 1.0 if total < 100000 else 0.8
        score = int(today * bonus)

        repos.append({
            'num': len(repos)+1,
            'name': full_name,
            'desc': desc[:120] if desc else '',
            'lang': lang,
            'total': total,
            'today': today,
            'score': score,
            'url': f'https://github.com/{full_name}'
        })
        if len(repos) >= 15:
            break

    return repos

def html_to_md_approx(html):
    """HTML 简单转 markdown 近似（兜底用）"""
    import re
    repos = []
    # 找 <h2 class="h3"> 或 article 里的 repo 名
    pattern = r'<h2 class="h3">.*?<a href="/([^"]+)"[^>]*>([^<]+)</a>'
    names = re.findall(pattern, html, re.DOTALL)
    return ""  # 简化：交给 agent-reach

# ── API 补全描述 ───────────────────────────────────────────────────────────────
def enrich_with_api(repos):
    for r in repos:
        owner, repo = r['name'].split('/', 1)
        data = gh_api(f"/repos/{owner}/{repo}")
        if data:
            api_desc = (data.get('description') or '').strip()
            if api_desc and not r['desc']:
                r['desc'] = api_desc[:120]
            r['topics'] = data.get('topics', [])[:3]
        else:
            r['topics'] = []
        if not r['desc']:
            r['desc'] = f"{r['lang']} project on GitHub"
    return repos

# ── DB 写入 ───────────────────────────────────────────────────────────────────
def write_to_db(repos, article_date, docker=True):
    """写入 radar 数据库 news_articles 表"""
    import subprocess

    for r in repos:
        title = r['name']
        content = (
            f"⭐ {r['total']:,} | 🍴 — | 📈 {r['today']:,} stars today — {r['desc']}"
        )
        source = r['lang']
        url = r['url']
        score = r['score']

        sql = (
            f"INSERT INTO news_articles "
            f"(article_date, category, title, content, source, url, lang, blacklist_score) "
            f"VALUES ("
            f"'{article_date}', 'github', $$ {title} $$, $$ {content.replace('$','�')} $$, "
            f"$$ {source} $$, $$ {url} $$, 'en', {score}"
            f") ON CONFLICT DO NOTHING;"
        )
        sql = sql.replace("�", "$")
        cmd = [
            "docker", "exec", "radar-db", "psql", "-U", "radar", "-d", "radar", "-c", sql
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=5)
        except Exception as e:
            print(f"WARN: failed to write {r['name']}: {e}", file=sys.stderr)

    print(f"✅ Wrote {len(repos)} repos to DB for {article_date}")

# ── 主入口 ────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    import datetime
    # 北京时间今天日期
    import subprocess
    result = subprocess.run(
        ["date", "-u", "+%Y-%m-%d"],
        capture_output=True, text=True,
        env={**os.environ, "TZ": "Asia/Shanghai"}
    )
    today_utc = result.stdout.strip()
    # 转为北京时间日期
    article_date = today_utc  # UTC date = 北京 date（差8小时但取日一致）

    repos = fetch_trending(agent_reach_available=True)
    if not repos:
        sys.exit(1)

    repos = enrich_with_api(repos)

    # 写 /tmp/gh_repos.json（供主进程读）
    out = "/tmp/gh_repos.json"
    with open(out, 'w') as f:
        json.dump(repos, f, ensure_ascii=False, indent=2)
    print(f"✅ Written {len(repos)} repos to {out}")

    # 直接写 DB
    write_to_db(repos, article_date)
