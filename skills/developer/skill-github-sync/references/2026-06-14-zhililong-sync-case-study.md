# Case Study: zhililong 全套 sync（2026-06-14）

> **适用场景**：当你要 sync 一个**完整 skill 目录**（含 agents/ + references/ + scripts/ 多个子目录）到 viceroy-skills 时，对照本案例走一遍。
> **不适用**：单文件 patch / SKILL.md-only 改动（走 `## 核心流程` 即可）。

## 实战输入

| 项目 | 值 |
|------|-----|
| Skill 名 | `zhililong` |
| 本地路径 | `~/.hermes/skills/zhililong/`（zhililong 与 zhili-publish/khazix-writer 是兄弟） |
| 云端目标 | `skills/creative/zhililong/` |
| 本地大小 | 49496 bytes（9 文件 / 4 子目录） |
| 云端初态 | **不存在**（HTTP 404）—— 首次 push |

## 实战命令（按坑 1-5 顺序）

### Step 0：预检（5 项 yes 自检）

- [x] YES 1：读完 SKILL.md L420+ 的 8 坑章节（坑 1-8）+ references/sync-pitfalls.md
- [x] YES 2：知道本地路径 ≠ 云端分类路径（zhili-publish 本地是 `social-media/.agents/skills/`，云端是 `creative/`）
- [x] YES 3：`git fetch origin && git log --oneline origin/main -5` 看过远端 5 commit
- [x] YES 4：本任务涉及**新增 skill**（不是覆盖/重装），走首次 push 流程
- [x] YES 5：确认 token 有 `repo` 写入权限

### Step 1：云端存在性 + 字节数核对

```bash
curl -sLo /dev/null -w "HTTP %{http_code}\n" \
  "https://raw.githubusercontent.com/jacardl/viceroy-skills/main/skills/creative/zhililong/SKILL.md"
# → 404（首次 push，正常）
```

### Step 2：备份 README（坑 5）

```bash
cp /tmp/viceroy-skills/README.md /tmp/cloud_backup_README.md_$(date +%Y%m%d)
cp /tmp/viceroy-skills/README.en.md /tmp/cloud_backup_README.en.md_$(date +%Y%m%d)
```

### Step 3：先 rm 后 cp（坑 2 防嵌套）

```bash
TARGET=/tmp/viceroy-skills/skills/creative/zhililong
rm -rf "$TARGET" 2>/dev/null   # ← 关键：先删后建
mkdir -p "$TARGET"
cp -r /Users/apple/.hermes/skills/zhililong/* "$TARGET/"
# 明确 * 通配：避免 cp -r zhililong → $TARGET/zhililong/ 嵌套
```

### Step 4：字节数核对（坑 9 — 2026-06-14 沉淀）

```bash
LOCAL=/Users/apple/.hermes/skills/zhililong
for f in $(find "$LOCAL" -type f | sed "s|$LOCAL/||"); do
  L=$(wc -c < "$LOCAL/$f")
  C=$(wc -c < "$TARGET/$f" 2>/dev/null || echo "MISSING")
  if [ "$L" = "$C" ]; then
    echo "✅ $f  $L bytes"
  else
    echo "⚠️  $f  local=$L cloud=$C"
  fi
done
```

**实战结果**：

| 文件 | 本地 | 云端 |
|------|------|------|
| SKILL.md | 14585 | 14585 ✅ |
| agents/openai.yaml | 608 | 608 ✅ |
| references/html-gotchas.md | 3999 | 3999 ✅ |
| references/post-edit-checklist.md | 4091 | 4091 ✅ |
| references/zhililong-examples.md | 4045 | 4045 ✅ |
| scripts/markdown_to_html.py | 4001 | 4001 ✅ |
| scripts/post_edit_check.py | 4827 | 4827 ✅ |
| scripts/cover_pil.py | 5759 | 5759 ✅ |
| scripts/publish_lanlong.py | 7581 | 7581 ✅ |
| **总计** | **49496** | **49496** ✅ |

差值 0 = 可以 commit。

### Step 5：README 更新（中文 + 英文）

```bash
# 中文 README（坑 8 列出当前真实分类数）
sed -i 's|Skills-66|Skills-68|' /tmp/viceroy-skills/README.md
# 在 Creative 分类下新增 zhililong 行
```

**英文 README 落后**（坑 7 实证）：本实战发现英文 README 只有 4 个 Creative（缺 guizang-ppt-skill），但**保守策略**：只同步本次涉及的 zhili 行，不动无关兄弟（避免引入额外差异掩盖本任务）。

### Step 6：commit + push（一次过）

```bash
cd /tmp/viceroy-skills
git add -A
git commit -m "feat(creative): add zhililong skill — 4000-5500 char WeChat long-form with auto-draft push"
GIT_TERMINAL_PROMPT=0 git push origin main
# → a327517..b5cb063  main -> main
```

**没踩坑 3（443）和坑 4（rejected）**：因为是首次 push + 远端 6 小时内无新 commit。

### Step 7：验证（4 项必查）

```bash
# 1. 远端最新 commit 是你的
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://api.github.com/repos/jacardl/viceroy-skills/commits?per_page=3" | \
  python3 -c "import sys,json; [print(c['sha'][:7], c['commit']['message'].split(chr(10))[0]) for c in json.load(sys.stdin)[:3]]"

# 2. 远端 SKILL.md 字节数 == 本地
REMOTE_SIZE=$(curl -sIL "https://raw.githubusercontent.com/jacardl/viceroy-skills/main/skills/creative/zhililong/SKILL.md" | grep -i content-length | awk '{print $2}' | tr -d '\r')

# 3. 远端文件结构 == 本地（4 子目录 + 9 文件）
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://api.github.com/repos/jacardl/viceroy-skills/contents/skills/creative/zhililong" | \
  python3 -c "import sys,json; [print(x['type'][:4], x['size'], x['name']) for x in json.load(sys.stdin)]"

# 4. README 徽章数 = 实际 skill 数
curl -s "https://raw.githubusercontent.com/jacardl/viceroy-skills/main/README.md" | grep -oE 'Skills-[0-9]+' | head -1
```

## 实战产出

| 项 | 值 |
|----|-----|
| Commit SHA | `b5cb063` |
| Commit 父 | `a327517`（docs: update patent-disclosure-skill in README） |
| 新增文件 | 9（SKILL.md + agents/ + 3 references/ + 4 scripts/） |
| 修改文件 | 2（README.md + README.en.md） |
| 总行数 | +1276 / -2 |
| 推 push 次数 | 1（一次过，无重试） |

## 关键经验

1. **字节数核对是 sync 的最后保险**——`git diff --stat` 只能告诉你"有变更"，不能告诉你"全到位"
2. **`rm -rf $TARGET + cp -r source/* $TARGET/`** 是防嵌套的硬公式，**永远**用这套
3. **首次 push vs 覆盖式 sync** 走不同分支——首次只看路径 + 字节数，覆盖式还要对比 frontmatter
4. **跨 skill 路径统一**——把 zhililong 放在 `~/.hermes/skills/zhililong/`（不带 `social-media/` 前缀），未来 sync 直接对得上
5. **skill-github-sync 自身不在本次 push 范围**——坑 9 是本地沉淀，下次 sync skill-github-sync 时再带上去

## 不在本案例范围

- zhili-publish 本地 50KB vs 云端 71KB（35% 落后）——属于另一个 sync 任务
- README 英文版 Creative 缺 guizang-ppt-skill——属于 README 校对任务
- 未来 zhili-publish / zhilicomments / zhiligithub 同步——下次再说
