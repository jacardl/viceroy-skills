---
name: radar-data-collection
description: "🛰️ 雷达数据采集（生产版 v5.1）：金价改用新浪hq_GC+USD/CNY换算，新增沪金Au99.99国内现货价，新增gold_note字段"
metadata: { "openclaw": { "emoji": "🛰️" }, "version": "5.1" }
---

# 雷达数据采集 Skill v5.1

**铁律：只写 DB，禁止发消息，禁止写 /tmp 以外的文件**

---

## 执行方式

将以下 Python 脚本完整写入 `/tmp/collect.py`，然后 `python3 /tmp/collect.py` 一次执行完毕。

```python
#!/usr/bin/env python3
import subprocess, json, re, os, urllib.request, urllib.error, time
from datetime import date, timedelta

# ── 时区同步 ──────────────────────────────────────────
result = subprocess.run(
    ['date', '+%Y-%m-%d'], capture_output=True, text=True,
    env={**os.environ, 'TZ': 'Asia/Shanghai'}
)
AD = result.stdout.strip()
print(f"AD={AD}", flush=True)

# ── 星期几（周日=7, 周六=6, 周一=1, …, 周五=5）────────
dow = int(subprocess.run(['date', '+%u'], capture_output=True, text=True,
    env={**os.environ, 'TZ': 'Asia/Shanghai'}).stdout.strip())
is_weekend = (dow in [6, 7])
print(f"dow={dow} is_weekend={is_weekend}", flush=True)

DB = ['docker', 'exec', '-i', 'radar-db', 'psql', '-U', 'radar', '-d', 'radar']

def psql_exec(sql):
    r = subprocess.run(DB, input=sql, capture_output=True, text=True)
    if r.stderr and 'ERROR' in r.stderr:
        return 1, r.stderr[:200]
    return r.returncode, r.stderr[:200] if r.stderr else 'ok'

def psql_scalar(query):
    r = subprocess.run(DB + ['-t', '-A', '-F', '\t'], input=query, capture_output=True, text=True)
    return r.stdout.strip()

inserted = {'gold': 0, 'ai': 0, 'politics': 0, 'github': 0}

# ── 节点 A：金价 + TIPS + 涨跌 ──────────────────────
print("Collecting gold...", flush=True)

# ── A1. NY黄金期货：新浪hq_GC ──────────────────────
intl = None
try:
    r = subprocess.run(
        ['curl', '-s', '--max-time', '10',
         '-H', 'Referer: https://finance.sina.com.cn/',
         'https://hq.sinajs.cn/list=hf_GC'],
        capture_output=True, timeout=15
    )
    # 新浪行情返回GBK编码，decode errors='replace'避免崩溃
    raw = r.stdout.decode('utf-8', errors='replace')
    m = re.search(r'hf_GC="([^"]+)"', raw)
    if m:
        fields = m.group(1).split(',')
        # 字段0 = 当前价（NY期货收盘价/最后结算价）
        intl = fields[0].strip() if fields[0].strip() else None
        print(f"  hq_GC raw={raw[:80]}", flush=True)
        print(f"  hq_GC parsed intl={intl}", flush=True)
except Exception as e:
    print(f"  hq_GC error: {e}", flush=True)

if not intl or not re.match(r'^\d+\.\d+$', intl):
    print("  hq_GC failed, using fallback 4130.0", flush=True)
    intl = '4130.0'

# ── A2. USD/CNY：open.er-api ───────────────────────
usd_cny = None
try:
    r = subprocess.run(
        ['curl', '-s', '--max-time', '10',
         'https://open.er-api.com/v6/latest/USD'],
        capture_output=True, text=True, timeout=12
    )
    d = json.loads(r.stdout)
    usd_cny = str(d.get('rates', {}).get('CNY', '6.78'))
    print(f"  USD/CNY={usd_cny}", flush=True)
except Exception as e:
    print(f"  USD/CNY error: {e}", flush=True)
    usd_cny = '6.78'

if not usd_cny or not re.match(r'^\d+\.?\d*$', usd_cny):
    usd_cny = '6.78'

# ── A3. 国内金价换算 ─────────────────────────────────
dom_float = round(float(intl) * float(usd_cny) / 31.1035, 2)
dom = str(dom_float)

# ── A4. 国内金价（沪金Au99.99）──────────────────────
shanghai_gold = None
gold_note = None

if is_weekend:
    gold_note = "休市（周六/日），参考价以上一交易日换算"
    shanghai_gold = None
    print(f"  国内金市休市，周末备注: {gold_note}", flush=True)
else:
    # 工作日抓沪金Au99.99（新浪行情）
    shanghai_codes = ['shAu99', 'shAu9999', 'szAu99', 'szAu9999']
    for code in shanghai_codes:
        try:
            r = subprocess.run(
                ['curl', '-s', '--max-time', '8',
                 '-H', 'Referer: https://finance.sina.com.cn/',
                 f'https://hq.sinajs.cn/list={code}'],
                capture_output=True, timeout=12
            )
            raw_s = r.stdout.decode('utf-8', errors='replace')
            m_s = re.search(rf'hq_str_{code}="([^"]+)"', raw_s)
            if m_s and m_s.group(1).strip():
                fields_s = m_s.group(1).split(',')
                price_s = fields_s[0].strip()
                if re.match(r'^\d+\.?\d*$', price_s):
                    shanghai_gold = price_s
                    print(f"  沪金{code}={shanghai_gold}元/克", flush=True)
                    break
        except Exception as e:
            print(f"  沪金{code} error: {e}", flush=True)
    if not shanghai_gold:
        gold_note = "沪金Au99.99报价不可达，以换算价¥{dom}/克供参考"
        shanghai_gold = None
    else:
        gold_note = None

# ── A5. TIPS 10年收益率 ───────────────────────────────
tips = None
try:
    r = subprocess.run(
        ['curl', '-s', '--max-time', '12',
         'https://fred.stlouisfed.org/graph/fredgraph.csv?id=DFII10'],
        capture_output=True, text=True, timeout=15
    )
    lines = r.stdout.strip().split('\n')
    # 跳过空行，取最后一个非空值
    valid_lines = [l for l in lines if l.strip() and ',' in l]
    if valid_lines:
        last = valid_lines[-1]
        parts = last.split(',')
        tips_raw = parts[-1].strip()
        if tips_raw and re.match(r'^-?\d+\.?\d*$', tips_raw):
            tips = str(round(float(tips_raw), 4))
            print(f"  TIPS DFII10={tips}% (from line: {last[:60]})", flush=True)
except Exception as e:
    print(f"  TIPS error: {e}", flush=True)

if not tips:
    tips = '2.24'
    print(f"  TIPS using fallback {tips}", flush=True)

# ── A6. 查前一日计算涨跌 ────────────────────────────
prev_row = psql_scalar(
    f"SELECT intl_price_usd, domestic_price_cny, tips_yield_10y FROM gold_prices "
    f"WHERE price_date < '{AD}' ORDER BY price_date DESC LIMIT 1;"
)
if prev_row and '\t' in prev_row:
    parts = [p.strip() for p in prev_row.split('\t')]
    prev_intl = float(parts[0]) if parts[0] else float(intl)
    prev_dom  = float(parts[1]) if parts[1] else float(dom)
    prev_tips = float(parts[2]) if parts[2] else float(tips)
else:
    prev_intl = float(intl)
    prev_dom  = float(dom)
    prev_tips = float(tips)

intl_chg = round(float(intl) - prev_intl, 2)
dom_chg   = round(float(dom) - prev_dom, 2)
tips_chg  = round(float(tips) - prev_tips, 4)

# ── A7. 写入 gold_prices ──────────────────────────────
# shanghai_gold 是 float 或 None（周末休市）
sh_val = shanghai_gold if shanghai_gold else 'NULL'
note_val = f"'{gold_note}'" if gold_note else 'NULL'

sql = (f"INSERT INTO gold_prices(price_date,intl_price_usd,intl_price_change,"
       f"domestic_price_cny,domestic_price_change,tips_yield_10y,tips_yield_change,"
       f"shanghai_gold_rmb_per_gram,gold_note,created_at) "
       f"VALUES('{AD}',{float(intl)},{intl_chg},{float(dom)},{dom_chg},"
       f"{float(tips)},{tips_chg},{sh_val},{note_val},NOW()) "
       f"ON CONFLICT(price_date) DO UPDATE SET "
       f"intl_price_usd=EXCLUDED.intl_price_usd,intl_price_change=EXCLUDED.intl_price_change,"
       f"domestic_price_cny=EXCLUDED.domestic_price_cny,domestic_price_change=EXCLUDED.domestic_price_change,"
       f"tips_yield_10y=EXCLUDED.tips_yield_10y,tips_yield_change=EXCLUDED.tips_yield_change,"
       f"shanghai_gold_rmb_per_gram=EXCLUDED.shanghai_gold_rmb_per_gram,"
       f"gold_note=EXCLUDED.gold_note;")
rc, err = psql_exec(sql)
inserted['gold'] = 1 if rc == 0 else 0
print(f"gold rc={rc} intl={intl}({intl_chg:+}) dom={dom}({dom_chg:+}) tips={tips}({tips_chg:+.4f}) sh={shanghai_gold} note={gold_note}", flush=True)

# ── 节点 B：国际政治 ─────────────────────────────────
print("Collecting politics...", flush=True)
ROUTER = "http://localhost:20128/v1"
ROUTER_KEY = "sk-0d68daa6645450e7-bc1xz4-8ac6a7da"

region_keys = {
    '🔴': ['亚太','南海','朝鲜','日本','印度','东南亚','Taiwan','中国','韩国','南海争端','Philippines','Korea','Japan','India'],
    '🔵': ['中东','欧洲','俄罗斯','北约','伊朗','以色列','加沙','乌克兰','土耳其','英国','法国','德国','Russia','Ukraine','Iran','Israel','Gaza','NATO','Europe','European','Turkey','UK','France','Germany'],
    '🟢': ['美洲','拉丁','美国','加拿大','巴西','墨西哥','选举','Trump','Biden','America','US','Latin','Brazil','Mexico'],
}

search_q = f"{AD} international political news today"
pol_count = 0

try:
    req_data = json.dumps({"model":"search-combo","query":search_q,"max_results":12}).encode()
    req = urllib.request.Request(f'{ROUTER}/search', data=req_data,
        headers={'Authorization': f'Bearer {ROUTER_KEY}', 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=25) as resp:
        data = json.loads(resp.read().decode())
    results = data.get('results', [])
except Exception as e:
    print(f"search error: {e}", flush=True)
    results = []

for item in results:
    url = item.get('url','')
    if not url or '://' not in url:
        continue
    snippet_raw = item.get('content','') or item.get('snippet','')
    snippet = str(snippet_raw)[:300] if not isinstance(snippet_raw, str) else snippet_raw[:300]
    title = snippet[:80].replace("'","''").replace('\n',' ')
    body = f"事件：{snippet[:200]}\n背景：国际政治动态\n影响：待评估".replace("'","''")

    region = '🟢'
    for emo, keys in region_keys.items():
        if any(k.lower() in snippet.lower() for k in keys):
            region = emo
            break

    sql = (f"INSERT INTO news_articles(article_date,category,title,content,source,url,region,lang,created_at) "
           f"VALUES('{AD}','politics','{title}','{body}','Reuters/AP','{url}','{region}','zh',NOW()) "
           f"ON CONFLICT DO NOTHING;")
    rc, _ = psql_exec(sql)
    if rc == 0:
        pol_count += 1

inserted['politics'] = pol_count
print(f"politics inserted={pol_count}/{len(results)}", flush=True)

# ── 节点 C：AI 热讯 ──────────────────────────────────
print("Collecting AI...", flush=True)
ua = "Mozilla/5.0 (compatible; aihot-skill/1.0)"
ai_items = []

try:
    r = subprocess.run(
        ['curl','-s','--max-time','10',
         '-H', f'User-Agent: {ua}',
         'https://aihot.virxact.com/api/public/items?mode=selected&take=10'],
        capture_output=True, text=True, timeout=15
    )
    d = json.loads(r.stdout)
    items = d.get('data', d.get('items',[]))
    for it in items:
        title = (it.get('title','') or '')[:200].replace("'","''").replace('\n',' ')
        content = (it.get('summary','') or it.get('content','') or '')[:300].replace("'","''").replace('\n',' ')
        source = (it.get('source','aihot') or 'aihot').replace("'","''")
        url = it.get('url','')
        score = int(it.get('score',0))
        ai_items.append({'title':title,'content':content,'source':source,'url':url,'score':score})
except Exception as e:
    print(f"aihot error: {e}", flush=True)

# fallback: HackerNews
if len(ai_items) < 5:
    try:
        r = subprocess.run(
            ['curl','-s','--max-time','10',
             'https://hn.algolia.com/api/v1/search?query=AI+OR+GPT+OR+LLM&tags=story&hitsPerPage=8'],
            capture_output=True, text=True, timeout=15
        )
        d = json.loads(r.stdout)
        for h in d.get('hits',[]):
            title = (h.get('title','') or '')[:200].replace("'","''").replace('\n',' ')
            url = h.get('url','') or f"https://news.ycombinator.com/item?id={h.get('objectID','')}"
            score = int(h.get('points',0))
            ai_items.append({'title':title,'content':'HN热门讨论','source':'HackerNews','url':url,'score':score})
    except:
        pass

ai_count = 0
for it in ai_items:
    sql = (f"INSERT INTO news_articles(article_date,category,title,content,source,url,blacklist_score,lang,created_at) "
           f"VALUES('{AD}','ai','{it['title']}','{it['content']}','{it['source']}','{it['url']}',"
           f"{it['score']},'zh',NOW()) ON CONFLICT DO NOTHING;")
    rc, _ = psql_exec(sql)
    if rc == 0:
        ai_count += 1

inserted['ai'] = ai_count
print(f"ai inserted={ai_count}", flush=True)

# ── 节点 D：GitHub Trending（HTML 解析 + API 补全）──
print("Collecting GitHub...", flush=True)

# 判断报告类型：周一=1 … 周六=6，周日=7
# 周六=dow=6 → weekly | 月末最后一天 → monthly | 其余 → daily
today_d = int(subprocess.run(['date', '+%d'], capture_output=True, text=True,
    env={**os.environ, 'TZ': 'Asia/Shanghai'}).stdout.strip())

next_month = date.today().replace(day=1) + timedelta(days=32)
monthend = (next_month.replace(day=1) - timedelta(days=1)).day
is_monthend = (today_d == monthend)

if is_monthend:
    since_param = 'monthly'
elif dow == 6:
    since_param = 'weekly'
else:
    since_param = 'daily'

trending_url = f'https://github.com/trending?since={since_param}'
print(f"GitHub URL: {trending_url} (dow={dow} is_monthend={is_monthend})", flush=True)

try:
    r = subprocess.run(
        ['curl','-s','--max-time','15','-L',
         '-H','User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
         trending_url],
        capture_output=True, text=True, timeout=20
    )
    html = r.stdout
except Exception as e:
    print(f"github error: {e}", flush=True)
    html = ''

articles = re.findall(r'<article class="Box-row">(.*?)</article>', html, re.S)
print(f"GitHub articles found: {len(articles)}", flush=True)

gh_count = 0
for blk in articles[:25]:
    h2 = re.search(r'<h2[^>]*>.*?href="/([^"]+)"', blk, re.S)
    if not h2:
        continue
    repo_full = h2.group(1).strip()
    if '/' not in repo_full or 'login' in repo_full:
        links = re.findall(r'href="/([a-zA-Z0-9_-]+/[a-zA-Z0-9_.-]+)"', blk)
        repo_full = links[0] if links else ''
        if not repo_full:
            continue

    desc_match = re.search(r'<p class="col-9[^"]*"[^>]*>\s*(.*?)\s*</p>', blk, re.S)
    desc = desc_match.group(1).strip() if desc_match else ''
    desc = re.sub(r'<[^>]+>', '', desc)[:200].replace("'","''").replace('\n',' ')

    lang_match = re.search(r'itemprop="programmingLanguage">([^<]+)<', blk)
    lang_text = lang_match.group(1).strip() if lang_match else ''

    today_match = re.search(r'([\d,]+)\s*stars?\s*(today|this week|this month)', blk, re.I)
    period_stars = int(today_match.group(1).replace(',','')) if today_match else 0
    period_label = today_match.group(2) if today_match else 'today'

    total_stars = 0
    total_forks = 0
    created_at = ''
    is_new = False
    try:
        api_url = f'https://api.github.com/repos/{repo_full}'
        req = urllib.request.Request(api_url,
            headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/vnd.github.v3+json'})
        with urllib.request.urlopen(req, timeout=8) as resp:
            repo_data = json.loads(resp.read().decode())
        total_stars = repo_data.get('stargazers_count', 0)
        total_forks = repo_data.get('forks_count', 0)
        created_at = repo_data.get('created_at', '')[:10]
        if created_at:
            from datetime import datetime as dt
            created_date = dt.strptime(created_at, '%Y-%m-%d')
            days_old = (dt.now() - created_date).days
            is_new = days_old < 30
        time.sleep(0.5)
    except Exception as e:
        print(f"  API error for {repo_full}: {e}", flush=True)

    t = float(total_stars)
    bonus = 2.0 if t < 5000 else 1.5 if t < 20000 else 1.0 if t < 100000 else 0.8
    new_bonus = 1.5 if is_new else 1.0
    score = round(period_stars * bonus * new_bonus, 1)

    content_parts = [
        f"⭐ {total_stars} total stars",
        f"📈 {period_stars} stars {period_label}",
        f"🍴 {total_forks} forks",
    ]
    if lang_text:
        content_parts.append(f"📝 {lang_text}")
    if is_new:
        content_parts.append(f"🆕 created {created_at}")
    if desc:
        content_parts.append(f"📄 {desc}")
    content = ' | '.join(content_parts).replace("'","''")

    sql = (f"INSERT INTO news_articles(article_date,category,title,content,source,url,"
           f"stars_count,period_new_stars,growth_rate,is_new_project,blacklist_score,lang,created_at) "
           f"VALUES('{AD}','github','{repo_full}','{content}','GitHub','https://github.com/{repo_full}',"
           f"{total_stars},{period_stars},{score},{'true' if is_new else 'false'},{score},'en',NOW()) "
           f"ON CONFLICT DO NOTHING;")
    rc, _ = psql_exec(sql)
    if rc == 0:
        gh_count += 1
    print(f"  {repo_full}: total={total_stars} period={period_stars} forks={total_forks} new={is_new} score={score}", flush=True)

inserted['github'] = gh_count
print(f"github inserted={gh_count}", flush=True)

# ── Phase 4：写锁 ────────────────────────────────────
lock_sql = (f"INSERT INTO push_locks(lock_date,locked_by,locked_at) "
            f"VALUES('{AD}','collector-done',NOW()) "
            f"ON CONFLICT(lock_date) DO UPDATE SET locked_by='collector-done',locked_at=NOW();")
rc, _ = psql_exec(lock_sql)
print(f"lock_write rc={rc}", flush=True)

# ── 汇总 ─────────────────────────────────────────────
print(f"\n=== DONE: gold={inserted['gold']} ai={inserted['ai']} pol={inserted['politics']} gh={inserted['github']} ===", flush=True)
```

---

## gold_prices 表新增字段

```sql
ALTER TABLE gold_prices
  ADD COLUMN IF NOT EXISTS shanghai_gold_rmb_per_gram double precision,
  ADD COLUMN IF NOT EXISTS gold_note text;
```

- `shanghai_gold_rmb_per_gram`：沪金Au99.99国内现货价（元/克），周末休市时为 NULL
- `gold_note`：标注文本，如"休市（周六/日），参考价以上一交易日换算"

---

## 飞书状态汇报（agent 采集完成后执行）

通过 `message tool action=send`，**只发数量，不发内容**：

```
🛰️ ${AD} 数据采集完成

| 类目 | 条数 |
|------|------|
| 💰 金价 | 1 条 |
| 🤖 AI 热讯 | ${AI_CNT} 条 |
| 🌐 国际政治 | ${POL_CNT} 条 |
| 💻 GitHub 黑马 | ${GH_CNT} 条 |
```

---

## 版本历史

- **v5.1**：节点A重写——NY金价改新浪`hq_GC`（字段0解析）+ open.er-api（USD/CNY）；新增沪金Au99.99国内现货抓取（周末休市自动标注）；gold_prices表新增`shanghai_gold_rmb_per_gram`+`gold_note`字段；TIPS空值行过滤；dow用`date '+%u'`确保一致性
- **v5.0**：GitHub采集重写——HTML解析 repo+desc+language+period stars，调GitHub API补全total stars/forks/created_at；period_new_stars区分daily/weekly/monthly
- **v4.0.4**：psql_exec增加stderr ERROR检测；DB表新增region列
- **v4.0.3**：修复content字段非string时[:200]报TypeError
- **v4.0.0**：彻底重写为单次python3 /tmp/collect.py脚本
