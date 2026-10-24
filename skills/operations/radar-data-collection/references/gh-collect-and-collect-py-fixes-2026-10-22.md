# 2026-10-22 采集链路修复记录（gh_collect.py / collect.py）

本轮 cron 采集（2026-10-22，TZ=Asia/Shanghai）踩到并修复 4 个问题，全部落在
`~/.shared-agent-skills/operations/radar-data-collection/scripts/` 下。

## 1. collect.py 的 GitHub 子脚本路径失效 → 当日 GitHub 数据被清空

**现象**
```
Attempt 1/3 FAILED: /Users/apple/.openclaw/workspace/scripts/radar/gh_collect.py
Attempt 2/3 FAILED: ...
Attempt 3/3 FAILED: ...
```
自检 `❌ github 0/10`。

**根因**：`collect.py` 两处写死了已不存在的路径：
- `GH_SCRIPT = "/Users/apple/.openclaw/workspace/scripts/radar/gh_collect.py"`
- subprocess 里 `cd /Users/apple/.openclaw/workspace && python3 scripts/radar/gh_collect.py`

**危害放大点**：`step_github()` 第一行是 `clean_news("github")`，即**先删当日 GitHub 行再调子脚本**。
子脚本不存在 → 3 次重试全失败 → 当日 GitHub 数据被删光且不会写回。
所以「self-check 假阴性」在旧代码下其实是**数据丢失**，不是无害误报。

**修复**
```python
GH_SCRIPT = "/Users/apple/.shared-agent-skills/operations/radar-data-collection/scripts/gh_collect.py"
# subprocess
f'export TZ=Asia/Shanghai && cd /Users/apple/.shared-agent-skills/operations/radar-data-collection && '
f'python3 scripts/gh_collect.py "{TODAY}"'
```
**验证**：`python3 -m py_compile collect.py gh_collect.py` → COMPILE_OK。

## 2. gh_collect.py 嵌入脚本里的 repo 正则过度转义

**现象**：Playwright 抓到的页面有 12 个 `<article>`，但正则只匹配到 5 个 repo。
连字符项目（如 `cloudflare/security-audit-skill`）全部消失。

**根因**：生成 `script_body` 时正则里的字符类被写成
`([a-zA-Z0-9_\\-\\.]+/[a-zA-Z0-9_\\-\\.]+)`，在字符类里 `\\-` 是「字面反斜杠 + 字面连字符」，
连字符不再作为范围/字面量匹配生效。

**修复**：源文件改为 `([a-zA-Z0-9_\-\.]+/[a-zA-Z0-9_\-\.]+)`。
解析数从 5 → 12。

**排查手法**：把生成的 `script_body` dump 出来看正则源码，比对着手改临时脚本快得多。

## 3. get_recently_pushed_repos 同日自去重 → 重跑结果塌缩

**现象**：连续跑 gh_collect.py，第一次 7 条，第二次只剩 2 条，且每次不同。

**根因**：`get_recently_pushed_repos(DEDUP_WINDOW_DAYS=2)` 的 SQL 查「近 2 天已推过的 owner_repo」，
但去重发生在 `cleanup_existing(TODAY)` **之前**，所以**当天已经写入的行也进了过滤池**，
重跑时把自己的行过滤掉。

**修复**：SQL 增加当日排除
```sql
AND article_date < DATE '{TODAY}'
```
**修复后**：连续重跑稳定 8 条（1 高优源 `ruanyf/weekly` + 7 trending）。

**通用教训**：任何「先查 DB 做去重、后写 DB」的流程，必须显式排除当天，
否则重跑必然自伤。

## 4. 改写模型输出带 `<think>` 块污染 description

**现象**：description 出现整段英文推理，且部分描述极短。

**处理**：
1. 剥 `<think>...</think>`；
2. 只保留最后一行/最后一句作为中文摘要；
3. 落库前校验：含中文、无 `<think>`、长度 ≥20 字；
4. 对未通过的行逐条重跑（fallback 链上换模型）。

**模型可用性（2026-10-22 实测本地 9Router `http://127.0.0.1:20128/v1/chat/completions`）**
- `cx/gpt-5.6-sol` → 经常 HTTP 503，作为首选时**不要**当成链路故障，链上继续。
- `minimax-cn/MiniMax-M3` → 多数情况成功。
- `minimax-cn/MiniMax-M2.7` → 前者失败时的兜底，成功。
- `src[:200]` → 原文截断，最终兜底（会落英文/原文，必须在统计里标注）。

**GitHub 类改写**复用
`~/.hermes/skills/operations/radar-daily-report/scripts/fill_ai_zh.py --days=1 --category=github`
（`updated=12 failed=0`）。

## 本轮最终结果

| 类别 | 条数 | 阈值 | 状态 |
|---|---|---|---|
| ai | 10 | ≥8 | ✅ |
| github | 8 | ≥10（源不足，接受） | ⚠️ 源数据仅 8 条 |
| gold_prices | 1 | 1 | ✅ |

金价：国际 GC=$4153.61/oz (+0.76%)、国内 AU9999=¥891.00/g (+0.39%)、美 10Y TIPS=5.130% (+0.010pp)。

GitHub 8 条构成：页面 12 → sponsors/* 过滤 4 → 跨日去重 1 → 剩 7 trending + 1 高优源 = 8。
这是源侧稳定产出，不是采集失败，按 SKILL.md「1-9 不告警」处理。
