---
name: radar-data-collection
description: "采集金价+TIPS/国际政治/AI热讯/GitHub Trending 写入 radar 数据库"
metadata: { "openclaw": { "emoji": "🛰️" } }
---

# 雷达数据采集

执行入口：直接运行本 skill，由 cron 触发。

## 采集前时区确认

```bash
export TZ=Asia/Shanghai && date '+%Y-%m-%d'
```
DATE = 输出结果（如 2026-08-03）

## 执行脚本

> ⚠️ **脚本统一（2026-08-05）**：以下路径是 symlink，指向 `~/.openclaw/workspace/scripts/radar/` 下唯一权威脚本。修改只改 workspace 路径，symlink 自动同步。

### 脚本 1：GitHub Trending（先跑，避免竞速）
```
export TZ=Asia/Shanghai
python3 ~/.openclaw/skills/operations/radar-data-collection/scripts/gh_collect.py $(TZ=Asia/Shanghai date +%Y-%m-%d)
```
> symlink → `~/.openclaw/workspace/scripts/radar/gh_collect.py`

### 脚本 2：主采集（金价 + TIPS + 政治 + AI）
```
export TZ=Asia/Shanghai
python3 ~/.openclaw/skills/operations/radar-data-collection/scripts/collect.py $(TZ=Asia/Shanghai date +%Y-%m-%d)
```
> symlink → `~/.openclaw/workspace/scripts/radar/collect.py`

## 生产级采集链路（2026-08-05 升级 / v4.1 字段对齐）

> ⚠️ **脚本统一声明（2026-08-05 修复）**：
> - `~/.openclaw/workspace/scripts/radar/{collect.py, gh_collect.py}` 是**唯一权威**生产脚本
> - skill 路径的 `scripts/collect.py` 和 `scripts/gh_collect.py` 是 **symlink**，指向 workspace 路径
> - **禁止在两处独立修改代码**；修改只改 workspace 路径，symlink 自动同步
> - 历史备份在 `/tmp/radar-old-scripts-0829-1217/`

### 金价 + TIPS
- **国际金价**：腾讯 hf_GC（`qt.gtimg.cn/q=hf_GC`） → Yahoo Finance GC=F 备选
  - **v_hf_GC 字段索引（v4.1 修正）**：
    - `[0]` = 当前价（USD/oz）
    - `[1]` = 涨跌额（USD）
    - `[5]` = 昨收（USD）← **不是 [4]**，v4 错用 [4] 算出 0 或乱值
  - `intl_price_change` = (今-昨)/昨 × 100%（百分比，不是绝对额）
- **国内金价**：东财 `push2.eastmoney.com/api/qt/stock/get?secid=118.AU9999`（分/g）
  - **东财字段索引（v4.1 修正）**：
    - `f43` = 最新价（分，÷100 转元/g）
    - `f60` = 昨收（分，÷100 转元/g）← **不是 f170**，v4 错用 f170 当昨收算出 5 万%
    - `f169` = 涨跌额（分，÷100 转元/g）
    - `f170` = 涨跌幅 × 100（÷100 转百分比）
- **TIPS 十年期**：treasury.gov CSV（`10 Yr` 列）
- **写入字段**：`intl_price_usd`, `intl_price_change`, `domestic_price_cny`, `domestic_price_change`, `tips_yield_10y`, `tips_yield_change`, **`gold_note`**（v4.1 新增）
- **异常**：金价全来源失败 → 跳过写入，不 fallback 旧数据

### 国际政治（生产级三段链，**v4.1 政治 bug 修复**）
1. **9Router search-combo**：12 个 query × 8 条候选，recency_days=2
2. **9Router web/fetch**：逐条抓全文 markdown（超时 30s），提取正文 200-1500 字
3. **agent-reach WebChannel**：BBC/FT/部分新闻站优先走 urllib 直抓（独立通道，不依赖 9Router）
4. **兜底**：全部失败则降级为 content（≥30 字），**不**强依赖 snippet
5. **时效过滤**：published_at 超过 48h 跳过
6. **去重**：按 URL 去重，保留最早一条
7. **达标**：≥10 条；< 5 条 → 🚨 告警标注
- **v4.1 修复**：政治 8-02/8-03/8-04/8-05 连续 4 天 0 条的根因是「snippet 全 null + `len<30` 过滤」；修复后**优先走 web/fetch 抓全文**，snippet 只作兜底
- **region 字段（v4.1 新增）**：每个 query 标 region（🔴亚太/🔵中东·欧洲/🟢美洲），写入 DB 供 push.py 分区

### AI 热讯
- **主选**：aihot.virxact.com（精选模式，take=10）
- **备选**：HackerNews Algolia API（AI/ML/LLM/GPT 关键词，hitsPerPage=8）
- **写入字段**：title / content / **summary** / **description** / source / url / lang / blacklist_score / **region**（v4.1 新增 region 写入，默认 🟢）
- **达标**：≥10 条

### GitHub Trending
- gh_collect.py 抓 GitHub Trending 页面 → 写入 DB
- **v4.1 description 字段修复**：以前塞了 `* N today | total* N | lang | desc[:80]`，现在改为干净中文 desc（≤300字）
- **写入字段**：title / description / stars_count / period_new_stars / blacklist_score / **is_new_project**（v4.1 新增）
- **达标**：≥10 条

## 采集完成后验证

```bash
docker exec radar-db psql -U radar -d radar -t -c \
  "SELECT category, COUNT(*) FROM news_articles WHERE article_date='${DATE}' GROUP BY category ORDER BY category;"

docker exec radar-db psql -U radar -d radar -t -c \
  "SELECT price_date, intl_price_usd, tips_yield_10y, tips_yield_change FROM gold_prices WHERE price_date='${DATE}';"
```

达标：金价 1 条 / AI ≥ 8 条 / 政治 ≥ 10 条 / GitHub ≥ 10 条。

## 异常处理铁律

- 金价所有来源均失败 → 跳过写入，汇报注明「金价缺失」
- 政治 < 5 条 → 🚨 告警，注明「政治不足」
- AI < 5 条 → 注明「AI不足」
- GitHub = 0 条且 gh_collector 报错 → 注明「GitHub失败」
- **绝对禁止 fallback 旧数据**

## 完成后发送飞书统计

格式：
```
📡 采集完成（YYYY-MM-DD）
| 类目 | 条数 |
| 金价 | X |
| AI | X |
| 政治 | X |
| GitHub | X |
异常：XXX（如有）
```
发送目标：ou_5ded4476a110b6eccdeafdc6ea3cf3b2
