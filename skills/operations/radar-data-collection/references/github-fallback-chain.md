# GitHub 数据源回退链（防火墙环境）

## 适用场景

GitHub 主网被防火墙阻挡时（实测 `github.com` / `api.github.com` / `objects.githubusercontent.com` TCP 443 超时无 RST），仍需从 GitHub 仓库抓数据写本地 DB。

## 回退链（按可用顺序）

1. **`ungh.cc/repos/<owner>/<repo>`** — 仓库元信息（stars / watchers / forks / defaultBranch / pushedAt / createdAt）
   - 无 auth、无速率限制
   - 返回 JSON：`{"repo": {"stars": ..., "pushedAt": "...", "description": "..."}}`
   - 实测延迟 < 500ms
2. **`raw.githubusercontent.com/<owner>/<repo>/<branch>/<path>`** — 仓库原始文件
   - 无 auth
   - 支持任意 text 文件（README / docs / *.md）
   - 实测对 ~50KB 文本稳定
3. **回退到 `web.archive.org/web/<timestamp>/https://github.com/...`** — 历史快照
   - 仅在 raw 也不可达时启用

**不可用**：
- `gh` CLI（依赖 api.github.com）
- `git clone https://github.com/...`（HTTPS 被墙）
- 直接浏览器访问 `github.com`（被墙）

## UA 标识

自定义 UA `radar-gh-collect/1.0` 在采集脚本中标注，便于远端日志识别合法流量。

## 实战模板（固定高优先级源）

`gh_collect.py` 中的 `fetch_high_priority_source()` 是该回退链的实例化：每日先抓一批固定仓库（不依赖 trending），按 `blacklist_score=9999` 置顶写入 `news_articles` 表（`category='github'`）。

适用仓库特征：
- README 列出"最新一期/最新版本/最新更新"链接到具体文件
- 文件名/路径可正则化（如 `docs/issue-NNN.md` / `CHANGELOG.md` / `releases/vX.Y.md`）
- 文件含 H1 标题 + 首段摘要

新增固定源：在 `gh_collect.py` 顶部 `HIGH_PRIORITY_SOURCES` 加一项 dict 即可（`owner_repo` / `branch` / `score` / `reason`）。

## 端点速查

```bash
# 仓库元信息
curl -s "https://ungh.cc/repos/<owner>/<repo>"

# README
curl -s "https://raw.githubusercontent.com/<owner>/<repo>/<branch>/README.md"

# 任意路径
curl -s "https://raw.githubusercontent.com/<owner>/<repo>/<branch>/<path>"
```

## 失败诊断

| 现象 | 原因 | 修复 |
|---|---|---|
| `ungh.cc` 返回 `{"error": true, "status": 404}` | 仓库不存在或私有 | 确认 `owner_repo` 拼写 + 公开性 |
| `raw.githubusercontent.com` 返回 404 | branch 或 path 错误 | `curl https://ungh.cc/repos/<owner>/<repo>` 看 `defaultBranch`，README 列 `path` 正则匹配 |
| ungh 502 / 超时 | ungh.cc 临时不可用 | 重试 1-2 次仍挂则跳过该源，不阻塞 trending |

## 已知限制

- ungh.cc 不返回 issues / pulls / commits 列表（仅仓库元信息 + README）
- raw.githubusercontent.com 不支持 git LFS / binary large files
- 仓库不存在或私有时 ungh.cc 返回 404，不会 fallback 到 archive.org
