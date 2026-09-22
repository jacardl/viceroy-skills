# 固定高优先级源（high-priority sources）

`gh_collect.py` 顶部维护 `HIGH_PRIORITY_SOURCES` 列表，每天**先于 trending** 抓取，cleanup 后写入，强制 `blacklist_score` 高分置顶。这套机制让"必读源"绕开 trending 不确定性 + GitHub 主网被墙 + gh CLI 不可用三个限制。

## 触发场景

当用户想加一个**每日必入榜**的仓库/源（不是 trending 一次性热度，而是反复出现的高价值内容）：

1. 不是 GitHub Trending 当日爆款，但有长期价值（如阮一峰周刊、技术资讯汇总、Awesome 系列）
2. 仓库 README 本身就是内容索引（按期/按分类列出文章）
3. 需要绕过 GitHub 主网/API 的回退链（防火墙环境）

## 采集链路（不依赖 gh CLI / GitHub API）

```
1. https://ungh.cc/repos/<owner>/<repo>
   → JSON: { repo: { stars, pushedAt, description, ... } }
   → 拿到仓库元信息（无需 GitHub API token）

2. https://raw.githubusercontent.com/<owner>/<repo>/<branch>/README.md
   → 正则匹配最新一期链接（例: `\(docs/(issue-\d+)\.md\)`）
   → 第一条匹配即视为「最新一期」

3. https://raw.githubusercontent.com/<owner>/<repo>/<branch>/docs/<slug>.md
   → 拿 H1 标题（`^#\s+(.+?)$`）
   → 拿首段非空非列表非引用的段落做摘要
```

**防火墙环境实测**：ungh.cc + raw.githubusercontent.com 在 GitHub 主网被墙时仍可直连（hermes-agent 项目根目录的 `references/network-restricted-environments.md` 已确认）。

## DB 字段写入（与 trending repo 同 schema）

| 字段 | 值 |
|------|-----|
| `category` | `'github'` |
| `article_date` | 当日（CST） |
| `source` | `'Markdown'`（固定） |
| `lang` | `'zh'` |
| `is_new_project` | `false` |
| `blacklist_score` | `spec["score"]`（默认 `9999.0`，确保置顶） |
| `stars_count` | `<repo>.stars` |
| `period_new_stars` | `0`（不是 trending，无今日新增） |
| `url` | `https://github.com/<owner_repo>` |
| `title` | `<owner/repo> — <desc[:80]>` |
| `description` | `第 N 期《主题》— 首段摘要（前 200 字）` |
| `content` | 多行 metadata + 完整 markdown 前 3000 字 |

`push.py` v4.5 的 `build_msg3()` 自动按 `blacklist_score DESC` 排序，HP 源天然排在 trending top10 之上。

## HIGH_PRIORITY_SOURCES 配置项

```python
HIGH_PRIORITY_SOURCES = [
    {
        "owner_repo": "ruanyf/weekly",       # 必填
        "branch": "master",                    # 默认 master
        "score": 9999.0,                       # 默认 9999.0（足够高即可）
        "reason": "...",                       # 日志/调试用，不入库
    },
]
```

**添加新源**：dict 加一项即可。如果 README 索引路径不是 `docs/issue-NNN.md`，需要扩 `fetch_high_priority_source()` 的正则。

## 当前在用源（2026-09-21）

- `ruanyf/weekly` — 阮一峰科技爱好者周刊，每周五发布，中文科技资讯高优

## 添加源时的检查清单

1. README 有可机读的最新一期链接（不能是手工维护的目录树）
2. 单期 markdown 在 raw.githubusercontent.com 可直连
3. `ungh.cc/repos/<owner>/<repo>` 返回 200 且含 `repo.stars` 字段
4. `blacklist_score` 设多少？默认 9999.0，多个 HP 源并存时按加入顺序排

## 已知坑

- **gh_collect.py 主流程改动**：HP 源先于 trending 抓取，写入时**先 cleanup 再 insert HP + insert top10**，确保 HP 不被覆盖。
- **trending 全挂时**：main() 改为 `repos = []`（不再 `return False`），HP 源仍能独立完成日报。2026-09-21 实测 trending 只出 6 条，HP 源正常入榜。
- **digest 字节控制**（push.py 内）：description `第 N 期《主题》— 首段摘要` 这种格式约 30-40 字节，安全。

## 参考

- `gh_collect.py` 顶部 `HIGH_PRIORITY_SOURCES` 定义
- `fetch_high_priority_source()` 实现细节
- 父 SKILL.md「固定高优先级源（2026-09-21 新增）」段落
