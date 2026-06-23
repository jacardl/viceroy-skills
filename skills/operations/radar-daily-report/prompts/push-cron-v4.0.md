# 雷达每日报告推送 Cron v4.0

## 核心变更（2026-06-23 佳哥自查发现）

**🔥 根因**：老 prompt 里写了大量 `GOLD_COUNT=$(docker exec psql ... | tr -d ' \n')` 这种 bash 语法，
但 LLM 并不会真的执行 shell，而是在"假装运行"，猜了一个 COUNT=0 出来 → 触发补采分支 → 用户收到旧数据。

**🔥 修复方案**：**每步先 exec 抓真实结果，再基于结果组装，禁止用 bash `$()` 伪执行**。

## 规则（强制）

1. **先 exec 取证，后组装**：先跑 `docker exec radar-db psql ...` 拿到真实输出，再基于输出做组装。不要"猜"数据库里是什么。
2. ❌ **禁止**在 prompt 文本里写 `GOLD_COUNT=$(docker exec ... | tr -d ' \n')` 这种 bash 赋值——LLM 会假想一个值。
3. ✅ **必须**实际调用 exec tool 跑命令，并读回结果 stdout。
4. 所有日期/星期判断必须 `export TZ=Asia/Shanghai` 后取。
5. 数据不存在（金价0条/各类目0条）→ 用最近一日数据兜底，标题标注「使用 YYYY-MM-DD 数据」。
6. 每条 message send 后检查返回是否 ok，失败重试 1 次。
7. 最后必发✅完成回报。

## 第一步：时区同步

```bash
export TZ=Asia/Shanghai && date '+%Y-%m-%d %u'
```
记录：ARTICLE_DATE、DAY_OF_WEEK（1=周一...7=周日）

## 第二步：查询今日 DB 数据量（真正 exec，不是猜）

exec 以下命令并**读取 stdout**：

```bash
export TZ=Asia/Shanghai
ARTICLE_DATE=$(date '+%Y-%m-%d')

echo "=== GOLD ==="
docker exec radar-db psql -U radar -d radar -t -c "SELECT COUNT(*) FROM gold_prices WHERE price_date='${ARTICLE_DATE}';" | tr -d ' \n'

echo "=== AI ==="
docker exec radar-db psql -U radar -d radar -t -c "SELECT COUNT(*) FROM news_articles WHERE category='ai' AND article_date='${ARTICLE_DATE}';" | tr -d ' \n'

echo "=== POLITICS ==="
docker exec radar-db psql -U radar -d radar -t -c "SELECT COUNT(*) FROM news_articles WHERE category='politics' AND article_date='${ARTICLE_DATE}';" | tr -d ' \n'

echo "=== GITHUB ==="
docker exec radar-db psql -U radar -d radar -t -c "SELECT COUNT(*) FROM news_articles WHERE category='github' AND article_date='${ARTICLE_DATE}';" | tr -d ' \n'
```

**接收 stdout 后**，判断：
- 如果 GOLD_COUNT=0，需要去查最近一日有数据的日期
- AI < 8 或 POLITICS < 8 或 GITHUB < 5 说明数据不全

## 第三步：判断是否需要兜底

如果今日数据为空（GOLD_COUNT=0 且 AI_COUNT=0 且 POLITICS_COUNT=0 且 GITHUB_COUNT=0）：

```bash
export TZ=Asia/Shanghai
# 找最近一日有数据的日期
docker exec radar-db psql -U radar -d radar -t -c "SELECT MAX(article_date) FROM news_articles WHERE article_date < CURRENT_DATE;"
```

用该日数据替代，**所有标题标注「使用 YYYY-MM-DD 数据」**。

## 第四步：读取金价数据

exec 并读取 stdout：

```bash
export TZ=Asia/Shanghai
ARTICLE_DATE="2026-06-23"  # 用上一步决定的实际日期

docker exec radar-db psql -U radar -d radar -t -c "SELECT intl_price_usd, intl_price_change, domestic_price_cny, domestic_price_change FROM gold_prices WHERE price_date='${ARTICLE_DATE}';"
```

输出示例：`4172.90 | -155.10 | 935.00 | +9.07`

## 第五步：发送消息一·金价

用 Markdown 表格（**不要代码块包装**）：

```
💰 雷达每日报告 · 金价速览（YYYY-MM-DD · 黑马日报/周报/月报）

| 指标 | 价格 | 涨跌 |
|---|---|---|
| 国际金价（USD/盎司） | $INTL | ±CHANGE |
| 国内金价（CNY/克） | ¥DOMESTIC | ±CHANGE |

📊 简评
💡 建议
```

用 message tool 发送：
`message action=send channel=feishu target=user:ou_5ded4476a110b6eccdeafdc6ea3cf3b2 message="<内容>"`

检查返回 ok=true，失败重试 1 次。

## 第六步：发送消息二·AI热讯 + 国际政治

先 exec 读真实数据：

```bash
export TZ=Asia/Shanghai
ARTICLE_DATE="YYYY-MM-DD"  # 实际日期

echo "=== AI ==="
docker exec radar-db psql -U radar -d radar -t -c "SELECT title, source, url, content FROM news_articles WHERE article_date='${ARTICLE_DATE}' AND category='ai' ORDER BY blacklist_score DESC NULLS LAST LIMIT 10;"

echo "=== POLITICS ==="
docker exec radar-db psql -U radar -d radar -t -c "SELECT title, source, url, content FROM news_articles WHERE article_date='${ARTICLE_DATE}' AND category='politics' ORDER BY blacklist_score DESC NULLS LAST LIMIT 12;"
```

基于 stdout 里的真实内容组装：

**AI 热讯**：bullet list，每条：`N. **标题** | 来源：xxx`

**国际政治**：按区域分类（🔴亚太 / 🔵中东·欧洲 / 🟢美洲），每条：
- **标题**
  - 事件：（1~2 句事实）
  - 背景：（1~2 句）
  - 影响：（1~2 句）

**版式铁律（佳哥 2026-06-17 拍板）**：
- ❌ 不要代码块包装
- ❌ 不要中英对照（中文优先）
- ✅ 每条必须「事件 / 背景 / 影响」三段
- ✅ 按区域分类

如果总字符 > 8000，拆 msg2a + msg2b 两条发送。

用 message tool 发送，检查返回，失败重试 1 次。

## 第七步：发送消息三·GitHub 黑马

```bash
~/.agent-reach-venv314/bin/python3 /Users/apple/.openclaw/scripts/gh_trending.py "https://github.com/trending"
```

或根据报告类型加参数：
- 周六：`?since=weekly`
- 月末周一：`?since=monthly`

读取 stdout，解析 `## [owner/repo](url)` 格式，按黑马分排序取前 10。

每条格式：
```
N. **owner/repo** — 语言 · ⭐总stars (+今日)
   一句简介
   https://github.com/owner/repo
```

用 message tool 发送，检查返回，失败重试 1 次。

## 第八步：完成回报

```bash
mkdir -p /Users/apple/.openclaw/workspace/daily-reports

cat > /Users/apple/.openclaw/workspace/daily-reports/${ARTICLE_DATE}.md << 'EOF'
（组装三条消息存入）
EOF
```

然后 send 状态消息：
```
✅ 雷达日报推送完成（YYYY-MM-DD · 黑马日报/周报/月报）
- 消息一 / 金价：${OK/FAIL}（使用 YYYY-MM-DD 数据）
- 消息二 / AI+政治：${OK/FAIL}
- 消息三 / GitHub：${OK/FAIL}
- 补采：无/正在后台补采
```

即使 3 turn 中有失败，也要 send 这一条并在对应项标❌原因。

## 第九步：数据库清理警示

⚠️ 2026-06-23 发现：news_articles.article_date 列**缺少索引**，COUNT 查询没有走索引。
长期大量数据后性能会下降，建议加索引，但不是本 cron 的任务。

## 附录：佳哥版式参考

详见 `~/.openclaw/workspace/.agents/skills/radar-daily-report/templates/approved-template-2026-06-17.md`
