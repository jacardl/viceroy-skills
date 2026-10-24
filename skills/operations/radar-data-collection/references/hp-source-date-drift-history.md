# HP 源日期漂移 Bug — 完整复现时间线

> 本文件整合 4 份会话日志（2026-09-24 / 25 / 27 / 28），按时间顺序记录 HP 源日期漂移 bug 的发现、复现、自愈流程与最终修复路径。
> 同一 bug 每天新增一份「日期版」日志累积过快——本文件作为单一权威参考，新一轮 bug 复现直接追加在 `## 后续复现` 节，不要再拆出独立 dated 文件。

## Bug 总览

**症状**：gh_collect.py 显式传入 `TODAY=YYYY-MM-DD`，但写入的 HP 源（ruanyf/weekly）`article_date = TODAY-1`（昨日），而 trending repos 写入 `article_date = TODAY`（正确）。两条数据日期不一致，HP 源错位。

**根因（推测，未直接读代码）**：`gh_collect.py` 内 HP 写入路径未把 `article_date` 参数透传到底层 INSERT；trending 路径正确。

**状态（2026-09-28）**：代码层未修复。每日靠人工自愈流程兜底。2026-09-28 首次观察 HP 写入正确日期——可能 v9 改动顺带修了 HP 路径的透传问题，但未确认根因消除，需继续每次采集后核验。

**长期修法建议**：在 `fetch_high_priority_source()` 末尾 INSERT 调用处显式补 `article_date=TODAY`，并加 unit test 断言 HP 写入 article_date 等于入参。

---

## 复现时间线

### 2026-09-23

| 维度 | 值 |
|------|-----|
| 传入参数 | `2026-09-23` |
| HP 实际写入 | `2026-09-22`（漂移） |
| trending 实际写入 | `2026-09-23`（正确） |
| 自愈结果 | 手动 DELETE + 重跑 |

### 2026-09-24（首份正式日志）

**完整复现命令**：
```bash
TODAY="2026-09-24"
python3 /Users/apple/.shared-agent-skills/operations/radar-data-collection/scripts/gh_collect.py "$TODAY"

# 验证
docker exec radar-db psql -U radar -d radar -t -c "
SELECT article_date, COUNT(*) FROM news_articles
WHERE category = 'github' AND article_date >= '2026-09-23'
GROUP BY article_date ORDER BY article_date DESC LIMIT 2"

# 错误输出（bug 存在时）：
#  2026-09-23   |     5   ← HP 源错误日期
#  2026-09-24   |     0   ← trending 未写入
```

**自愈步骤**：
1. 删错误日期数据
2. 重跑 `gh_collect.py "$TODAY"` 传今日日期
3. 验证 article_date 统一为今日（HP(1) + trending(7~9) 应共 ~8）

### 2026-09-25（第三次复现）

**重要确认**：代码层未修复（与 9-24 同 bug）。修复策略不变：DELETE 错误日期 + 重跑。

### 2026-09-27（第五天）

**新增异常**：HP 源 ruanyf/weekly 今日返回 `HTTP 403 Forbidden`：
```
[gh_collect] HP FAIL: ruanyf/weekly: HTTP Error 403: Forbidden
```

- HP 源完全失败（403），非日期漂移问题
- trending repos 正常写入 10 条，article_date=2026-09-27
- gh_collect.py 仍返回成功（trending 覆盖 HP 缺口）
- 可能原因：GitHub 仓库权限变更 / ungh.cc 对该仓库代理失效
- **日报整体不受影响**，HP 失败不阻塞推送

### 2026-09-28（第六天）

**首次无漂移**：
```
2026-09-28 | 7   ← HP(1) + trending(6)，日期全部正确
2026-09-27 | 10  ← 昨日旧数据（已清理）
```

**两种可能性**：
1. 代码修复已生效（HP 路径 now passes TODAY correctly）
2. 间歇性 bug（特定边界条件触发）

**结论**：继续每次采集后核验 `article_date`，漂移仍需自愈流程兜底。

---

## 自愈 SOP（每次采集后必跑）

```bash
# 1. gh_collect.py 跑完后立刻核验
TODAY=$(TZ=Asia/Shanghai date '+%Y-%m-%d')
docker exec radar-db psql -U radar -d radar -t -c "
SELECT article_date, COUNT(*) FROM news_articles
WHERE category = 'github' AND article_date >= '$TODAY' - interval '1 day'
GROUP BY article_date ORDER BY article_date DESC LIMIT 2"

# 2. 三种状态判断：
#    (a) 今日 count ≥ 1 + 昨日 count = 0  → 成功 ✅
#    (b) 昨日 count > 0 + 今日 count = 0  → HP 源日期漂移（本文 bug）
#    (c) 仅昨日日期                          → trending 全失败，需重试

# 3. 漂移修复
docker exec radar-db psql -U radar -d radar -t -c "
DELETE FROM news_articles WHERE category='github' AND article_date='<错误日期>';"
python3 "$SCRIPT_DIR/gh_collect.py" "$TODAY"

# 4. 再核验
docker exec radar-db psql -U radar -d radar -t -c "
SELECT article_date, COUNT(*) FROM news_articles
WHERE category = 'github' AND article_date = '$TODAY'"
```

**验收标准**：修复后只有今日日期，count ≥ 1。

---

## 区分：日期漂移 vs 正常 HP backdating

**不是所有「HP 写入日期 ≠ TODAY」都是 bug**：

- 2026-10-02 实测（见 `references/gh-collect-macos-grep-p-fix.md`）：ruanyf/weekly issue-413 周五 CST 早上发布，gh_collect.py 写 `article_date=2026-10-01`（周四 UTC）。这是 GitHub Trending UTC~00:00 重置导致（UTC 日历日切换 = CST 08:00），CST 08:00 前发布的内容属前一日 UTC 日历日。**不是 bug，正常行为**。

**接受条件**：`article_date = TODAY - 1`（差 1 天）= 正常。仅当差 ≥ 2 天，或 trending 也错位时，才触发自愈流程。

---

## 关联 SKILL.md 节

- `### gh_collect.py 初采后 article_date 可能不匹配（2026-08-29 发现）` — 父 SKILL.md「关键陷阱」节
- `### gh_collect.py 日期偏移陷阱（2026-08-27 发现）` — 父 SKILL.md「关键陷阱」节
- `references/gh-collect-macos-grep-p-fix.md` — 相关但不同：macOS BSD grep -P 重试循环坑
