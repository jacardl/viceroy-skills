# 2026-06-14 凭证安全 + rebase 决策 实战沉淀

> 📌 本文档是 2026-06-14 zhililong + zhiligithub + zhilicomments 三 skill renwei 集成同步的实战记录。**主 SKILL.md 已有坑 1-9**；本文件专讲**坑 10（凭证安全）** 和 **坑 11（rebase 决策）**——这是本次差点把真实 APPSECRET 推到云端的惊险案例。

---

## 坑 10：本地 credentials 文件含明文真实凭证，必须双向 diff 后才能 push

### 症状

`cp -r` 本地 skill 目录到云端 working directory 时，**本地 `references/config.md` 里有真实 APPSECRET**（如 `APPSECRET: 07b4dc2d64ddbe6f53707977dbabdbbe`），**云端是脱敏版**（`APPSECRET: ***REDACTED***`）。如果直接 `git add + commit + push`，**真实凭证明文上云**——GitHub 即使是 private repo，泄露面也扩大到所有协作者 + GitHub backup + 任何被举报的可疑活动触发的扫描。

### 背景

- 凭证管理常态：**本地**为了脚本能跑会写真实值，**云端**为了安全用 `***REDACTED***` 占位
- 这种"本地真值、云端占位"的差异**不是 bug**——是设计
- 但 `cp -r` 不区分两者，**机械复制会把真值带上云**
- 我的前序代码已经把 `references/config.md` 当作"普通文件" 一起 `cp -r`，没意识到这是个凭证文件

### 识别信号（同步前必须 grep）

```bash
# Step 1: 列本地 skills 目录里所有可能含凭证的文件
find ~/.hermes/skills -path "*/references/config.md" -o -path "*/references/credentials*" 2>/dev/null

# Step 2: 全文搜敏感词（APPSECRET / APPID / SECRET / API_KEY / TOKEN / PASSWORD / WX_ / PRIVATE_KEY）
for f in $(find ~/.hermes/skills -path "*/references/config.md" 2>/dev/null); do
  echo "=== $f ==="
  grep -inE "appsecret|api_key|secret|password|token|wx_|private_key" "$f" | head -5
done

# Step 3: 检查每个被命中的文件，对比云端 HEAD 的版本
for f in $(... 上一步命中的文件 ...); do
  rel=${f#~/.hermes/skills/}
  cloud="https://raw.githubusercontent.com/jacardl/viceroy-skills/main/skills/${rel#*/}"
  # 或者自己用 git tree API
  cloud_content=$(git -C /tmp/viceroy-skills2 show HEAD:"${rel#skills/}" 2>/dev/null)
  if echo "$cloud_content" | grep -q "REDACTED\|\\*\\*\\*\\*\\*"; then
    echo "✅ $f 云端脱敏" 
  else
    echo "⚠️ $f 云端可能也是明文——先确认"
  fi
done
```

### 处理流程

```bash
# 1. 一旦发现"本地真值、云端占位"差异：
#    绝对不要把本地版本推到云端

# 2. 拉云端 HEAD 版本（脱敏版）覆盖本地 working directory
git -C /tmp/viceroy-skills2 checkout HEAD -- skills/<cat>/<skill>/references/config.md

# 3. 验证覆盖成功
diff /tmp/viceroy-skills2/skills/<cat>/<skill>/references/config.md \
     /Users/apple/.hermes/skills/<local-area>/<skill>/references/config.md
# 输出为空 = 两边一致；非空 = 还需重做

# 4. git diff 这个文件应该是 0 变化
git diff skills/<cat>/<skill>/references/config.md
```

### 实战案例（2026-06-14）

- 本地 `zhilicomments/references/config.md` 348 字节 + **明文 APPSECRET** `07b4dc2d64ddbe6f53707977dbabdbbe`
- 云端 HEAD `references/config.md` 536 字节 + `APPSECRET: ***REDACTED***`
- 我 `cp -r` 时没意识到，working directory 是本地明文版
- 走 `git status` 时 `references/config.md` 显示 modified
- **走 `git diff` 时才看到真实 APPSECRET 明文出现在 diff 里**——这是最后拦截机会
- 立即 `git checkout HEAD -- .../config.md` 还原到脱敏版
- **用户 10 分钟内未拍板"是否上云"**——按最安全默认（**只推核心改动，整个 zhilicomments 跳过**），commit 里不包含 zhilicomments 的任何文件

### 失败兜底（如果已 push 到云端）

```bash
# 1. 立即从 GitHub history 删文件（包含所有 commit 里的版本）
#    用 BFG Repo-Cleaner 或 git filter-branch
bfg-repo-cleaner --delete-files config.md viceroy-skills.git
# 或
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch skills/creative/zhilicomments/references/config.md" \
  --prune-empty --tag-name-filter cat -- --all
git push origin --force --all

# 2. 立即轮换 APPSECRET（去微信公众平台后台重置）
# 3. 通知所有协作者
```

### 预防清单（写入 SKILL.md 必走）

每次 `cp -r` 之后、`git add` 之前：

- [ ] **逐个 `git diff` 检查改动的文件**——不是只看 `git status --stat`
- [ ] **凭证文件专属 grep**：所有 `config.md` / `credentials*` / `*_token.txt` 必须确认是脱敏版
- [ ] **diff 含 APPSECRET/API_KEY/TOKEN/PASSWORD 字面量 → 立即 `git checkout HEAD`**

---

## 坑 11：rebase vs 跳过决策（"本地 vs 云端 SKILL.md 字节差"）

### 症状

sync 之前发现：**本地 SKILL.md 字节数 < 云端 SKILL.md 字节数**（如 zhiligithub 本地 71088 / 云端 78211，差 7123 bytes = 10%）。这意味着**云端比本地多了一些"踩坑修复 12 处""技能边界"等条款**，本地严重过时。

### 决策树

```
本地 N bytes / 云端 M bytes（N < M，差 >5%）
  │
  ├─ 任务 = "重装整个 skill"（用户明确说"重装 X"）
  │    → 默认 A 方案：先 rebase 本地到云端，再加新内容
  │
  ├─ 任务 = "给 X 集成新特性"（如 renwei），但用户没要求重装
  │    → 必须先问用户。3 个选项：
  │       A. 全面 rebase：先 rebase 本地到云端 → 加新内容 → 整份上云
  │       B. 保守：本地头部加新段，云端不动（不引入未授权修改）
  │       C. 跳过：留待下次完整重装
  │
  └─ 任务 = "推全新 skill 到云端"（云端 404）
       → 不需要 rebase（云端没这个 skill）
```

### 实战案例（2026-06-14 zhiligithub 集成 renwei）

- 任务：给 zhiligithub 集成 renwei
- 预检发现：本地 71088 bytes < 云端 78211 bytes（差 7123 bytes，云端有"踩坑修复 12 处""技能边界"等）
- 用户拍了"选 A"——**先 rebase 本地到云端**（拉云端 78KB 覆盖本地），再在本地加 renwei 集成段，最后整份上云
- **实际执行**：
  1. `cp -r /Users/apple/.hermes/skills/.../zhiligithub /tmp/local_backup_zhiligithub_$(date)`（备份本地 71KB）
  2. `curl -sL cloud/SKILL.md -o local/SKILL.md`（拉云端 78KB 覆盖本地）
  3. `python3 diff` 核对所有 27 个文件字节数（云端 vs 本地）——全部 ✅
  4. 在本地 SKILL.md 加 renwei 集成段（用 `patch` 在「精简规则」之后插入）
  5. 重新比对：本地 82269 bytes > 云端 78211 bytes（合理——本地加了 4058 bytes renwei 段）
  6. `cp -r` 到云端 working directory → `git add` → `git commit` → `git push`
- 验证：远端 zhiligithub SKILL.md 82269 bytes ✅，云端本次 commit 包含全部本地修改

### 反例（2026-06-14 zhilicomments 没做 rebase）

- 任务：给 zhilicomments 集成 renwei
- 预检发现：本地 30209 bytes > 云端 27306 bytes（**本地领先 2903 bytes** = 10%）
- **我没意识到这是个潜在风险**——`cp -r` 后直接 `git diff` 才发现**本地 references/config.md 是明文真实凭证**（坑 10 浮现）
- 用户 10 分钟内未拍板如何处理 zhilicomments
- **最安全默认**：本次跳过整个 zhilicomments 同步，留待下次用户明确决定

### 教训

**预检时**：

- 不要只看"本地领先/落后"的字节数
- 要看 **diff 内容**——本地领先 10% 未必是好事，可能包含"本应上云但用户没意识到"的内容（明文凭证、过时规范、调试脚本）
- 本地领先云端时，**`git diff` 必须逐文件过一遍**——不只是看 stat 数字

**rebase 决策**：

- 用户给的是"集成新特性"任务，但发现本地过时 → **必须问用户**（不是默认选 A 也不是默认选 C）
- 给用户 3 个选项（rebase / 保守 / 跳过）+ 各自的代价——让用户拍板

### 简化版"sync 前 3 必做"清单

不管任务是什么，sync 之前这 3 步必走：

1. **字节数对比**：本地 vs 云端 SKILL.md 字节数 + 差值%
2. **逐文件 diff**（如 `git -C /tmp/viceroy-skills2 fetch && diff`）：本地领先/落后内容是啥
3. **凭证文件扫描**：`find ... -name "config.md" -o -name "credentials*"` + grep 敏感词

3 步全过且无异常 → 走 sync。任一异常 → 先问用户。

---

## 完整实战时间线（2026-06-14）

| 时刻 | 事件 | 决策点 |
|------|------|-------|
| 13:21 | zhiligithub 本地 71KB < 云端 78KB 发现 | 问用户选 A（rebase）/B（保守）/C（跳过） |
| 13:21-13:24 | 用户选 A：rebase | 备份本地 → 拉云端 78KB 覆盖 → 加 renwei 段 |
| 13:24 | zhiligithub renwei 段集成完（SKILL.md 82269 bytes） | 准备 push |
| 13:25 | zhililong 强化 renwei Step 3（16647 bytes） | 准备 push |
| 13:26 | zhilicomments 集成 renwei（34448 bytes） | 准备 push |
| 13:28 | `cp -r` 三个 skill 到云端 working directory | 字节数核对全 ✅ |
| 13:29 | `git status` 发现 zhilicomments/references/config.md 显示 modified | 警觉 |
| 13:29 | `git diff` 看到 config.md 含明文 APPSECRET | **坑 10 触发** |
| 13:30 | 用户 10 分钟内未拍板 zhilicomments 凭证风险 | 默认最安全：跳过整个 zhilicomments |
| 13:32 | `git checkout HEAD -- zhilicomments/` 还原 + `rm -rf scripts/` | zhilicomments 完全不动 |
| 13:38 | commit `d3396ae`：5 个改动（zhililong + zhiligithub + lanlong-quickstart + README×2） | 推送 |
| 13:39 | push 一次成功 | 验证 5 项全过 |

## 留待下次

zhilicomments 4 个待办（**2026-06-14 zhilicomments 凭证问题待解决**）：

1. `references/config.md` 本地明文真实 APPSECRET vs 云端脱敏版——必须先在本地把云端脱敏版拉下来覆盖、避免脚本里直接读 config.md 拿到真值出日志
2. `references/wechat-pitfalls.md` 本地 2026-06-11 主动改写（含"凭证来源 2026-06-11 修正"段）——需用户手动审阅
3. `scripts/preflight.py`（5019 字节）——云端无，可单独 push
4. `SKILL.md` 的 renwei 集成段（短评版）——本次云端没拿，下次任务时一起处理
