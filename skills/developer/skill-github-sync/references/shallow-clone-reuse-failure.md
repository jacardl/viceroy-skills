# Pitfall 12: Shallow Clone Reuse — .git 目录对象不完整

## 症状

```bash
cd /tmp/viceroy-skills
git status
# fatal: not a git repository (or any of the parent directories): .git

# 但 ls -la .git/ 显示目录存在
# total 0
# -rw-r--r--  ... HEAD
# drwxr-xr-x-- ... hooks/  info/  logs/  objects/  refs/
```

## 根因

上一次 sync 时用 `--depth=1` shallow clone 克隆了仓库：

```bash
git clone --depth=1 https://github.com/.../viceroy-skills.git /tmp/viceroy-skills_sync
```

Shallow clone 的 `.git/objects/` 只有最近 commit 的对象，缺少完整历史。  
当**下一次 session 复用同一个目录**时：

1. Git 认为这是有效仓库（`.git/` 存在）
2. 但执行任何 git 命令（`status`、`add`、`commit`、`push`）都失败
3. 报错 `fatal: not a git repository` —— 误导性强，看起来像"根本没有 .git"
4. `git remote -v` / `git branch` 等能跑（只读操作碰巧有足够对象）
5. `git status` / `git add` / `git push` 全部失败（需要完整对象图）

## 触发条件

- 用 `--depth=1` shallow clone 到固定路径（如 `/tmp/viceroy-skills_sync`）
- 跨 session 复用同一路径（常见于 cron 自动化或固定工作目录的任务）
- 仓库后续有新的 commit（即使只有 1 个新 commit，shallow clone 缺少其祖先对象）

## 正确做法

### 方案 A（推荐）：每次 sync 重新全量克隆

```bash
rm -rf /tmp/viceroy-skills_sync
GIT_TERMINAL_PROMPT=0 git clone https://jacardl:$(cat ~/.hermes/keys/github_token.txt)@github.com/jacardl/viceroy-skills.git /tmp/viceroy-skills_sync
```

优点：永远是最干净的起点，无历史污染。  
缺点：每次多花 ~20s 克隆。

### 方案 B：复用但检测不完整

```bash
REPO=/tmp/viceroy-skills_sync

# 检测 .git 是否完整（执行一个需要完整对象的命令）
if git -C "$REPO" log -1 --oneline HEAD >/dev/null 2>&1; then
    echo "✅ .git 完整，可复用"
else
    echo "❌ .git 不完整，重新克隆"
    rm -rf "$REPO"
    git clone ... "$REPO"
fi
```

### 方案 C：不用 shallow clone，改用完整克隆但用 `.git/info/shallow` 控制深度

```bash
git clone --filter=blob:none --no-checkout \
  https://jacardl:$(cat ~/.hermes/keys/github_token.txt)@github.com/jacardl/viceroy-skills.git \
  /tmp/vicky-full
```

## 2026-07-04 实战记录

```
目标: 推送 skill-maintenance v2.7 到 viceroy-skills
路径: /tmp/viceroy-skills_sync (上一次 sync 2026-06-14 用 --depth=1 克隆)

症状:
  git status → fatal: not a git repository
  ls -la .git/ → 目录存在但 total 0

处理:
  rm -rf /tmp/viceroy-skills_sync2
  git clone (无 --depth) → 完整 .git/ 全部对象
  cp -r skill-maintenance/*
  git add → commit → push → 成功
  推送: 500a04a..7e7bf8a  main -> main
```

## 教训

- ❌ `git clone --depth=1` + 固定路径 = 迟早踩坑
- ❌ `rm -rf $DIR && mkdir $DIR` 不够 —— 还要删 `.git` 中的 partial objects
- ✅ 每次 sync 用全新目录名（如 `viceroy-skills_sync_$(date +%Y%m%d)`）或直接覆盖
- ✅ 最简单可靠：**固定路径 + 每次 `rm -rf`** —— 反正 .git 每次都要重新 fetch
