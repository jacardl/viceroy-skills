# sync 踩坑详细复现配方

SKILL.md 里只列了 4-5 个坑的症状和处理。**这份是详细版**，含：复现命令、典型输出、恢复动作。

> **适用时机**：sync 过程中遇到任何不顺（push 失败、文件没上去、远端版本不对、路径错等），先来这里对号入座。

---

## 坑 1：云端严重落后于本地

### 复现命令

```bash
# Step 1: 看远端最近 5 个 commit
git -C /tmp/viceroy-skills fetch origin
git -C /tmp/viceroy-skills log --oneline origin/main -5

# 期望看到自己的 commit 在顶端。如果不是，说明：
# - 其他人/GitHub Action 推过
# - 你之前有未提交的本地变更
# - 你之前 push 失败但没意识到

# Step 2: 对比本地 vs 远端 frontmatter
LOCAL_HASH=$(grep -A2 '^description:' /root/.hermes/skills/<cat>/<skill>/SKILL.md | head -3)
REMOTE_CONTENT=$(curl -s -H "Authorization: Bearer $(cat ~/.hermes/keys/github_token.txt)" \
  "https://api.github.com/repos/jacardl/viceroy-skills/contents/skills/<cat>/<skill>/SKILL.md" | \
  python3 -c "import sys,json,base64; print(base64.b64decode(json.load(sys.stdin)['content']).decode())")
REMOTE_HASH=$(echo "$REMOTE_CONTENT" | grep -A2 '^description:' | head -3)
[ "$LOCAL_HASH" = "$REMOTE_HASH" ] && echo "✅ 一致" || echo "⚠️ 不一致"
```

### 典型症状

- **2026-06-04 实战**：本地 zhilicomments 字数 `1000-1500字`，远端还是 `2000-3000字`
- **2026-06-04 实战**：本地 zhiligithub 字数 `1500-2000字`，远端还是 `4000-8000字`
- 共同原因：上次 push 是 2026-06-02 06-04 之间隔了几天

### 恢复动作

把云端落后部分也纳入本次 commit。**不要**只 commit 本地新文件——否则云端规范会跟本地永远脱节。

```bash
# 把本地整个目录覆盖到云端（不是只 add 新文件）
rm -rf /tmp/viceroy-skills/skills/<cat>/<skill>/*
cp -r /root/.hermes/skills/<local_area>/<skill>/* /tmp/viceroy-skills/skills/<cat>/<skill>/
cd /tmp/viceroy-skills
git add -A
git status  # 应该看到 SKILL.md 改动 + 新增的 references/scripts/templates
git diff --cached --stat  # 看 stat 确认
```

---

## 坑 2：本地路径 ≠ 云端分类路径

### 路径映射表（2026-06-04 现状）

| Skill | 本地路径 | 云端分类 | 同步目标 |
|-------|----------|----------|----------|
| zhiligithub | `~/.hermes/skills/creative/zhiligithub/` | `creative/` | `skills/creative/zhiligithub/` ✅ 一致 |
| zhilicomments | `~/.hermes/skills/social-media/zhilicomments/` | `creative/` | `skills/creative/zhilicomments/` ⚠️ **路径不同** |
| khazix-writer | `~/.hermes/skills/creative/khazix-writer/` | `creative/` | `skills/creative/khazix-writer/` ✅ 一致 |
| zhili-publish | `~/.hermes/skills/openclaw-imports/zhili-publish/` | `creative/` | `skills/creative/zhili-publish/` ⚠️ 路径不同 |

### 怎么查云端分类

```bash
# 看 README 里这个 skill 归在哪个分类下
grep "<skill-name>" /tmp/viceroy-skills/README.md
# 找路径前缀：skills/ai/、skills/assistant/、skills/creative/、skills/developer/、skills/operations/、skills/product/
```

**铁律**：以**云端 README 现有归类**为准，**不要**按本地路径推。

### 复现命令

```bash
# 错误示范：按本地路径推
cp -r /root/.hermes/skills/social-media/zhilicomments /tmp/viceroy-skills/skills/social-media/
# 后果：新建了一个云端没有的 social-media/ 分类，违反"不要新增分类"铁律

# 正确做法：按云端分类推
rm -rf /tmp/viceroy-skills/skills/creative/zhilicomments/*
cp -r /root/.hermes/skills/social-media/zhilicomments/* /tmp/viceroy-skills/skills/creative/zhilicomments/
```

### 典型错误

```bash
# 错误 1：直接 cp -r 不 rm 旧的
cp -r /root/.hermes/skills/<skill> /tmp/viceroy-skills/skills/<cat>/
# 后果：<cat>/<skill>/<skill>/ 嵌套，路径变成 skills/<cat>/<skill>/<skill>/SKILL.md

# 错误 2：cp -r 后忘记 cd
cp -r /root/.hermes/skills/<skill> /tmp/viceroy-skills/skills/<cat>/
git push  # 什么也没推上去，因为 git add -A 没执行
```

---

## 坑 3：443 connection timed out

### 复现命令

```bash
# 触发条件
GIT_TERMINAL_PROMPT=0 git push origin main
# 报错：fatal: unable to access 'https://github.com/jacardl/viceroy-skills.git/': Failed to connect to github.com port 443: Connection timed out

# 验证不是 github 挂了
curl -v --max-time 8 -o /dev/null -s https://github.com 2>&1 | head -3
# 期望：Connected to github.com (...) port 443 (#0)
# 如果 curl 都连不上 → 真的是网络问题，重试+换代理
# 如果 curl 通了但 git 不通 → git 协议特定问题，按下面处理
```

### 恢复动作（按推荐顺序）

```bash
# 步骤 1：短间隔重试（80% 概率解决）
sleep 3
GIT_TERMINAL_PROMPT=0 git push origin main

# 步骤 2：长间隔重试（10% 概率）
sleep 10
GIT_TERMINAL_PROMPT=0 git push origin main

# 步骤 3：切 SSH 协议（前提 SSH key 已配）
ssh -T git@github.com  # 先验证 SSH 通
git remote set-url origin git@github.com:jacardl/viceroy-skills.git
git push origin main

# 步骤 4：换 proxy（如果有的话）
git config --global http.proxy http://<proxy>:<port>
git push origin main
git config --global --unset http.proxy  # 推完恢复
```

### 不要做的事

- ❌ 多次并行 git push（会加重网络拥堵）
- ❌ 改 DNS / hosts（治标不治本）
- ❌ 删 .git 重新 clone（会丢所有 working tree 的修改）

---

## 坑 4：push rejected (fetch first)

### 复现命令

```bash
# 触发：之前 git pull 超时失败（或者从来没 pull 过）
GIT_TERMINAL_PROMPT=0 git push origin main
# 报错：! [rejected] main -> main (fetch first)
```

### 复现链条

```
1. (几天前) git pull 超时 → 失败
2. (几天里) 远端有新 commit (cron 维护 / GitHub Action)
3. (今天) git push → rejected
4. git pull → 成功（因为网络刚好恢复了）
5. git push → 成功
```

### 恢复动作

```bash
# 标准流程
GIT_TERMINAL_PROMPT=0 git pull --rebase --autostash origin main
GIT_TERMINAL_PROMPT=0 git push origin main

# --autostash 的作用：
# - rebase 之前：自动 stash working tree 的未提交变更
# - rebase 之后：自动 unstash 回来
# - 适用于：刚才 cp -r 进去的文件还没 git add（这种情况下普通 git pull 会冲突）
```

### 冲突处理

```bash
# 如果 rebase 出现冲突
git status  # 看冲突文件
# 解决冲突
git add <冲突文件>
git rebase --continue
git push origin main
```

---

## 验证：push 真的成功了吗

### 必须验证项

```bash
# 验证 1: 远端 commit 列表顶端是你刚 commit 的
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://api.github.com/repos/jacardl/viceroy-skills/commits?per_page=3" | \
  python3 -c "import sys,json; [print(c['sha'][:7], c['commit']['message'].split(chr(10))[0]) for c in json.load(sys.stdin)[:3]]"

# 验证 2: 远端文件内容确实更新了
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://api.github.com/repos/jacardl/viceroy-skills/contents/skills/<cat>/<skill>/SKILL.md" | \
  python3 -c "import sys,json,base64; print(base64.b64decode(json.load(sys.stdin)['content']).decode()[:500])"
```

### 典型反例

- `git push` 显示 `bf2465b..abc1234  main -> main` → **成功** ✅
- `git push` 立即退出无输出 → **可能根本没推上去**，重新执行
- `git push` 报 `rejected` → 按坑 4 处理

---

## 一键诊断脚本

如果 sync 全程不顺，把这段粘到 terminal 一次跑完：

```bash
CLOUD=/tmp/viceroy-skills
TOKEN=$(cat ~/.hermes/keys/github_token.txt)

echo "=== 1. 云端 commit 状态 ==="
git -C $CLOUD log --oneline -3
echo ""

echo "=== 2. working tree 状态 ==="
git -C $CLOUD status --short
echo ""

echo "=== 3. 网络连通性 ==="
curl -s -o /dev/null -w "HTTPS 443: %{http_code} (耗时 %{time_total}s)\n" --max-time 8 https://github.com
echo ""

echo "=== 4. 远端 commit 列表 ==="
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://api.github.com/repos/jacardl/viceroy-skills/commits?per_page=3" | \
  python3 -c "import sys,json; [print(c['sha'][:7], c['commit']['message'].split(chr(10))[0]) for c in json.load(sys.stdin)[:3]]"
echo ""

echo "=== 5. 诊断结论 ==="
LOCAL=$(git -C $CLOUD rev-parse HEAD)
REMOTE=$(git -C $CLOUD rev-parse origin/main)
if [ "$LOCAL" = "$REMOTE" ]; then
  echo "✅ 本地 == 远端，状态健康"
else
  echo "⚠️ 本地 ($LOCAL) != 远端 ($REMOTE)"
  echo "   → 本地领先：git push 即可"
  echo "   → 远端领先：git pull --rebase --autostash origin main"
fi
```

把输出贴给后续 debug 用。
