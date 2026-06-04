---
name: skill-github-sync
description: >
  将 Skills 同步到 GitHub 仓库（viceroy-skills 公开仓库 + 私有专属仓库），并维护符合 khazix-skills 标准的 README。当用户说"同步skills到GitHub"、"上传skill到github"、"推送skill到远程"、"更新viceroy-skills仓库"、"维护GitHub上的skill仓库"、"更新 README"时使用此技能。包含完整的 GitHub 推送流程和标准 README 生成规范。
---

# Skill GitHub Sync

将本地 Skills 同步到 GitHub 仓库的完整流程。

## 现有分类（必须使用）

| 英文分类 | 中文名 | 说明 |
|---------|--------|------|
| `ai` | AI模型 | 9router, mmx-cli |
| `assistant` | 助理 | **baoyu-url-to-markdown**, find-skills, markitdown, markdown-to-report, neat-freak, obsidian, obsidian-cli, storage-analyzer, wechat-article-to-markdown, youtube-transcript |
| `creative` | 创意 | khazix-writer, zhili-publish, zhilicomments, zhiligithub |
| `developer` | 开发 | scrapling, setup-matt-pocock-skills, skill-creator, skill-github-sync, skill-maintenance |
| `operations` | 运营 | aihot, geo系列(3个), github-daily-trending, radar系列(3个), SEO系列(25个) |
| `product` | 产品 | brand-product-audience-relevance, competitor-discovery, hv-analysis, patent-disclosure-skill, software-copyright-materials |

**铁律**：不要新增分类，只在现有分类中添加技能。

## 0. 预检（必读）—— sync 之前先看这里

> ⛔ **铁律**：执行下面"## 核心流程"之前，**必须先读完 L396 起的"⚠️ 踩坑"章节** 和 `references/sync-pitfalls.md`。这 3-5 分钟能省你 30 分钟 debug。

### 为什么需要预检（实战教训）

**2026-06-04 实战案例**：重装云端版 skill-github-sync 时，主文件已经带 5 个坑的精简版（L396-477）+ 详细版 `references/sync-pitfalls.md`（8621B）。**但实战 sync zhiligithub + zhilicomments 时没读**这俩文件，重复踩了 3 个坑：

| 坑 | 实战表现 | 已知解法（已有但被忽略） |
|----|---------|---------------------|
| **云端严重落后** | 本地 `1000-1500字` / 云端 `2000-3000字` | SKILL.md L400-417 / sync-pitfalls.md L9-50 |
| **443 偶发断连** | 第一次 push 超时，sleep 5 秒后成功 | SKILL.md L436-451 / sync-pitfalls.md L101-143 |
| **push 前需 rebase** | 远端有 cron commit，rejected | SKILL.md L453-466 / sync-pitfalls.md L147-189 |

### 3 个 yes 自检（不通过就别动）

执行 sync 之前，**这 3 个问题** 必须都有答案：

- [ ] **YES 1**：我读完了 SKILL.md L396-477 的 5 个坑章节，并知道每个坑的"症状+处理"
- [ ] **YES 2**：我读完了 `references/sync-pitfalls.md` 的 4 个坑详细复现
- [ ] **YES 3**：我刚 `git fetch origin && git log --oneline origin/main -5` 看过远端最近 5 个 commit，知道**本地 HEAD 和远端 HEAD 的关系**

**3 个全 yes** → 走"## 核心流程"。**任一是 no** → 先补读，再走流程。

### 跳过预检的代价（量化）

实战中跳过预检踩坑的成本：

| 坑 | 跳过代价 |
|----|---------|
| 云端落后 | push 完后才发现云端字数还是 `4000-8000字` 旧值，要再开一个 commit 修 |
| 443 断连 | 第一次 push 超时返回，需要 sleep + 重试，**多耗 5-10 秒** |
| rejected | push 被拒，需要 `pull --rebase --autostash` 后再 push，**多耗 30-60 秒** |
| **合计** | **5-15 分钟 debug** vs 3-5 分钟预检 |

### 行号引用铁律（改 SKILL.md 必看）

**铁律**：在 SKILL.md 里**引用 SKILL.md 自身的行号**时（"见 L396 起的踩坑章节"这种），**patch 之后必须立即 grep 实测**位置，不能按改动前的位置猜。

**反面教材（本 session 实战）**：
```
第一次 patch 后引用了 L361-442（L365-382 / L401-416 / L418-431）
实际位置：L396-477（L400-417 / L436-451 / L453-466）
原因：插入新章节后行号下移 +35，但 patch 时没实测
```

**正确流程**（写 SKILL.md 必走）：
```bash
# Step 1: patch 完引用 L 编号的章节
# Step 2: 立即 grep 实测新位置
grep -n '^## 踩坑\|^### 坑 [0-9]' /root/.hermes/skills/developer/skill-github-sync/SKILL.md
# Step 3: 把所有引用更新到实测位置
# Step 4: 再次 grep 确认引用和实际位置一致
```

**什么时候不算坑**：引用**其他文件**（如 `references/sync-pitfalls.md L9-50`）的行号可以用，因为没动那个文件；但引用**同一个文件**自己的行号必须实测。

**为什么容易踩**：patch 操作本身不返回行号变化，agent 容易"按记忆里"写 L 编号。等下一个 agent 来读这文件时引用会指向错地方。

## 核心流程

### 第一步：读取 Token

从 `~/.hermes/keys/github_token.txt` 读取 GitHub PAT。

### 第二步：读取仓库目录结构（必须）

**同步前必须先读取仓库现有结构**，确认目标分类存在：

```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://api.github.com/repos/jacardl/viceroy-skills/contents/skills" | \
  grep '"name"'
```

### 第三步：同步 Skill 文件（完整目录，非仅 SKILL.md）

**⚠️ 重要：同步的是整个技能目录，不是单个文件。**

每个 Skill 包含多个支持文件（参考资料、脚本、模板等），同步时必须复制整个目录：

```
khazix-writer/
├── SKILL.md          ← 主文件
├── references/       ← 参考资料
│   └── xxx.md
├── scripts/          ← 执行脚本
│   └── xxx.py
├── templates/        ← 模板文件
│   └── xxx.html
└── assets/           ← 静态资源
    └── xxx.png
```

错误做法：`cp SKILL.md ...`（只复制单个文件）
正确做法：`cp -r skill-name/ ...`（复制整个目录）

使用 git 原生 push 方式（比 GitHub API 更稳定）：

1. `git clone https://github.com/jacardl/viceroy-skills.git /tmp/viceroy-skills_sync`
2. 复制技能文件到对应分类目录
3. `git add → commit → GIT_ASKPASS=echo git push`

**Token 持久化方式**（直接嵌入 URL 更稳定）：

```bash
git remote set-url origin https://jacardl:$(cat ~/.hermes/keys/github_token.txt)@github.com/jacardl/viceroy-skills.git
```

### 第四步：同步后必须更新 README

每次增删技能或调整分类后，**必须同步更新 README.md 和 README.en.md**。

## README 保护条款

> ⚠️ **任何人（包括协作者）更新 viceroy-skills 的 README 时，必须严格遵循本技能的格式规范。格式不符合的 PR 将被拒绝合并。**

README 是仓库的门面，格式混乱会直接损害仓库形象。任何人提交 README 更新，都必须对照本技能的模板进行检查。

## README 标准格式（khazix-skills 风格·严格遵循）

### 必须包含的元素

| 元素 | 说明 |
|------|------|
| **LICENSE 文件** | 必须有 MIT LICENSE 文件在仓库根目录 |
| **双语 README** | 必须有 `README.md`（中文主文件）和 `README.en.md`（英文版） |
| **标题图标** | `# 🧰 viceroy-skills`（必须有 🧰 图标） |
| **描述文案** | `我自己每天在用的一些 AI 技能和 Prompt，都开源在这里。` |
| **Status Badges** | `LICENSE` · `SKILLS-N` · `AGENTSKILLS-Standard`（三个，必须） |
| **平台徽章** | Claude Code · Codex · OpenCode · OpenClaw（四个，必须） |
| **中英切换** | `**中文** · [English](./README.en.md)` 或 `[中文](./README.md) · **English**` |
| **目录表** | 所有分类一览，含中文说明 |
| **安装方式** | `npx skills add jacardl/viceroy-skills --skill <skill-name>` |
| **触发示例** | 中文自然句式（帮我安装xxx） |
| **技能表格** | 每技能：名字 + One-liner + 触发方式 |
| **关于段落** | 作者说明段落 |
| **页脚** | License + Made by @jacardl |

### ❌ 禁止出现的格式

- ❌ `# viceroy-skills`（无 🧰 图标）
- ❌ `# Skillshub` / `# viceroy`（错误标题名）
- ❌ `npx skills add jacardl/skillshub`（旧的错误的仓库名）
- ❌ `Install this skill: https://...`（旧的非标准安装格式）
- ❌ `[中文](./README.md) · **English**` 在英文 README 中（应用 `[中文](./README.md) · **English**`）
- ❌ 缺少任何一个 Badge 或平台徽章
- ❌ `skillhub` 作为仓库名出现

### README 完整模板（中文版 README.md）

```html
<div align="center">

**中文** · [English](./README.en.md)

# 🧰 viceroy-skills

我自己每天在用的一些 AI 技能和 Prompt，都开源在这里。

[![License](https://img.shields.io/badge/License-MIT-3B82F6?style=for-the-badge)](./LICENSE)
[![Skills](https://img.shields.io/badge/Skills-59-10B981?style=for-the-badge)](#-skills)
[![AgentSkills](https://img.shields.io/badge/AgentSkills-Standard-8B5CF6?style=for-the-badge)](https://agentskills.io)

![Claude Code](https://img.shields.io/badge/Claude_Code-Skill-D97706?style=flat-square&logo=anthropic&logoColor=white)
![Codex](https://img.shields.io/badge/Codex-Skill-10B981?style=flat-square&logo=openai&logoColor=white)
![OpenCode](https://img.shields.io/badge/OpenCode-Skill-3B82F6?style=flat-square)
![OpenClaw](https://img.shields.io/badge/OpenClaw-Skill-8B5CF6?style=flat-square)

</div>

---

## 📋 目录

| Category | Description |
|----------|-------------|
| [AI Models](#-ai-models) | 本地/远程 AI 网关，图片生成，终端交互 |
| [Assistant](#-assistant) | 文件处理、知识管理、Obsidian、存储分析 |
| [Creative](#-creative) | 微信公众号写作、封面图、短评、GitHub 精选 |
| [Developer](#-developer) | Skill 创建与维护、代码质量 |
| [Operations](#-operations) | SEO / GEO 策略、舆情、爬虫、自动化 |
| [Product](#-product) | 竞品分析、人群研究、专利、软著 |

---

## 📦 安装

```bash
npx skills add jacardl/viceroy-skills --skill <skill-name>
```

触发示例：
```
帮我安装 storage-analyzer
帮我安装 hv-analysis
帮我安装 khazix-writer
```

---

## ✨ Skills

<a id="-skills"></a>

---

### 🤖 AI Models

| Name | One-liner |
|------|-----------|
| [**9router**](skills/ai/9router/SKILL.md) | 本地/远程 AI 网关 — 一个 Key 调用多个 Provider，OpenAI 兼容 API |
| [**mmx-cli**](skills/ai/mmx-cli/SKILL.md) | 用 MiniMax 生成文本、图片、视频、音乐 — 含搜索功能 |

---

### 🧑‍💼 Assistant

| Name | How to trigger |
|------|----------------|
| [**find-skills**](skills/assistant/find-skills/SKILL.md) | 在 ClawHub 上找 SEO 相关 Skill |
| [**markitdown**](skills/assistant/markitdown/SKILL.md) | 把这个 PDF 转成 markdown |
| ...（其他 Assistant 技能）...

---

### 🎨 Creative

| Name | How to trigger |
|------|----------------|
| [**khazix-writer**](skills/creative/khazix-writer/SKILL.md) | 用卡兹克的风格写一篇公众号文章 |
| [**zhili-publish**](skills/creative/zhili-publish/SKILL.md) | 把这个 HTML 草稿发布到微信公众号 |
| [**zhilicomments**](skills/creative/zhilicomments/SKILL.md) | 发一条短评论到公众号 |
| [**zhiligithub**](skills/creative/zhiligithub/SKILL.md) | 把这个 GitHub 项目写成一篇公众号文章 |

---

### 🛠️ Developer

| Name | How to trigger |
|------|----------------|
| ...（Developer 技能）...

---

### 📊 Operations

| Name | How to trigger |
|------|----------------|
| ...（单个技能列示）... |
| **GEO 系列（3个）** | geo-content-strategy · geo-keyword-research · geo-strategy-report |
| **SEO 系列（25个）** | seo · seo-audit · ...（全部 25 个，用 · 分隔）... |

---

### 📊 Operations — 其他

| Name | How to trigger |
|------|----------------|
| [**github-daily-trending**](skills/operations/github-daily-trending/SKILL.md) | 今天 GitHub 有什么趋势 |
| [**radar-daily-report**](skills/operations/radar-daily-report/SKILL.md) | 给我一份 Radar 日报 |
| [**radar-data-collection**](skills/operations/radar-data-collection/SKILL.md) | 舆情数据采集标准规范 |

---

### 📦 Product

| Name | How to trigger |
|------|----------------|
| ...（Product 技能）...

---

## 🌟 关于

这是我的私人 Skill 库——每个 Skill 都在我自己项目里跑过足够久、确认真的省时间才开源的。没有噱头，只有实用。

如果你觉得有用，欢迎 ⭐。问题和建议欢迎提 Issue / Discussion。

---

<div align="center">

[MIT License](./LICENSE) · 随意使用、修改和分发

Made by [@jacardl](https://github.com/jacardl)

</div>
```

### README 完整模板（英文版 README.en.md）

```html
<div align="center">

**中文** · [English](./README.en.md)

# 🧰 viceroy-skills

我自己每天在用的一些 AI 技能和 Prompt，都开源在这里。

[![License](https://img.shields.io/badge/License-MIT-3B82F6?style=for-the-badge)](./LICENSE)
[![Skills](https://img.shields.io/badge/Skills-59-10B981?style=for-the-badge)](#-skills)
[![AgentSkills](https://img.shields.io/badge/AgentSkills-Standard-8B5CF6?style=for-the-badge)](https://agentskills.io)

![Claude Code](https://img.shields.io/badge/Claude_Code-Skill-D97706?style=flat-square&logo=anthropic&logoColor=white)
![Codex](https://img.shields.io/badge/Codex-Skill-10B981?style=flat-square&logo=openai&logoColor=white)
![OpenCode](https://img.shields.io/badge/OpenCode-Skill-3B82F6?style=flat-square)
![OpenClaw](https://img.shields.io/badge/OpenClaw-Skill-8B5CF6?style=flat-square)

</div>

---

## 📋 Index

| Category | Description |
|----------|-------------|
| [AI Models](#-ai-models) | Local/remote AI gateway, image generation, terminal interaction |
| [Assistant](#-assistant) | File processing, knowledge management, Obsidian, storage analysis |
| [Creative](#-creative) | WeChat article writing, cover images, short comments, GitHub highlights |
| [Developer](#-developer) | Skill creation & maintenance, code quality |
| [Operations](#-operations) | SEO / GEO strategy, public opinion, scraping, automation |
| [Product](#-product) | Competitor analysis, audience research, patents, copyright |

---

## 📦 Install

```bash
npx skills add jacardl/viceroy-skills --skill <skill-name>
```

Examples:
```
帮我安装 storage-analyzer
帮我安装 hv-analysis
帮我安装 khazix-writer
```

---

## ✨ Skills

<a id="-skills"></a>

---
...（各分类技能，同中文版结构，每项英文 One-liner）...
---

## 🌟 About

This is my personal skill library — everything here is what I use daily in real projects. If it's useful to you, a ⭐ is appreciated. Questions and suggestions welcome in Issues / Discussions.

---

<div align="center">

[MIT License](./LICENSE) · Free to use, modify, and redistribute

Made by [@jacardl](https://github.com/jacardl)

</div>
```

### 安装命令格式（必须用 `--skill`）

```bash
npx skills add jacardl/viceroy-skills --skill <skill-name>
```

### 表格格式要求

每个技能一行，格式：

| 名字 | 一句话 | 触发示例 |
|------|--------|----------|
| [**skill-name**](path) | 简短描述 | 触发命令 |

### 系列技能合并规则

- **SEO 系列（25个）**、**GEO 系列（3个）**：合并为一行，内部用 `·` 分隔
- 剩余单个技能正常列示
- 运营分类可拆分为 `运营（operations）` + `运营（operations）— 其他`

## 注意事项

1. **README 必须随技能同步更新**——每次 add/commit/push 后检查 README 是否需要更新
2. **使用英文分类名**：operations, product, assistant, creative, developer, ai
3. **不要新增分类**：如果仓库没有对应分类，将技能放入最接近的现有分类
4. **Token 权限**：确认 PAT 有 `repo` 写入权限
5. **git mv 优先**：同仓库内移动文件用 `git mv` 而非 `cp + git add`（保留历史）
6. **README 数字准确性**：每次更新后核实各分类技能数量和总数
7. **格式一致性**：README.md 和 README.en.md 必须同步更新，两者结构必须一致
8. **标题图标**：必须为 `# 🧰 viceroy-skills`，禁止其他变体

## ⚠️ 踩坑（2026-06-04 实战 sync 4 个 skill 沉淀）

sync 操作不顺利时按这 4 个坑对号入座。详细复现/诊断命令见 `references/sync-pitfalls.md`。

### 坑 1：云端严重落后于本地（最常踩）

**症状**：push 完后才发现云端 SKILL.md 字数还是 `4000-8000字`（旧版），本地早已是 `1500-2000字`。**会重蹈数周的旧规范。**

**原因**：你可能几周没推过，云端是上次 push 时冻结的版本。其他协作者也可能 push 过（cron 维护等）。

**预防**（sync 第一步，不是最后一步）：
```bash
# 看远端最新 commit（不是本地 HEAD）
git fetch origin
git log --oneline origin/main -5
# 对比关键字段：直接读云端 SKILL.md 的 frontmatter
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://api.github.com/repos/jacardl/viceroy-skills/contents/skills/<cat>/<skill>/SKILL.md" | \
  python3 -c "import sys,json,base64; print(base64.b64decode(json.load(sys.stdin)['content']).decode()[:300])"
```

**处理**：把云端落后部分也纳入本次 commit（不只是本地新文件）。

### 坑 2：本地路径 ≠ 云端分类路径

**症状**：本地 `~/.hermes/skills/social-media/zhilicomments/`，云端 `skills/creative/zhilicomments/`，**直接 `cp -r` 路径就错**。本地装的 skill 路径由装的位置决定（`social-media/`、`openclaw-imports/` 等），云端按 6 大分类组织。

**规则**：
- 本地：`~/.hermes/skills/<本地领域>/<skill>/`（本地领域是装的时候定的，可能五花八门）
- 云端：`skills/<6大分类>/<skill>/`（**只有这 6 个**：ai / assistant / creative / developer / operations / product）
- **映射原则**：以**云端 README 现有归类**为准，看 README.md 里这个 skill 在哪个分类下，就同步到哪个云端分类

**处理**：
```bash
# 错误：cp -r /root/.hermes/skills/social-media/zhilicomments skills/  # 路径错
# 正确：先 rm -rf 云端旧版本，再 cp 本地到云端分类
rm -rf skills/<cloud_category>/<skill>/*
cp -r /root/.hermes/skills/<local_area>/<skill>/* skills/<cloud_category>/<skill>/
```

### 坑 3：443 偶发 connection timed out

**症状**：`git pull` / `git push` 报 `Failed to connect to github.com port 443: Connection timed out`，**但 `curl https://github.com` 是通的**。

**原因**：git 协议对 443 的连接偶发被路由/防火墙 drop（curl 通常走不同路径或 keep-alive 不一样）。**不是配置问题**，重试就行。

**处理**：
```bash
# 第一次失败 → sleep 3-5 秒 → 再试
sleep 3 && GIT_TERMINAL_PROMPT=0 git push origin main
# 仍失败 → sleep 10 秒再试
sleep 10 && GIT_TERMINAL_PROMPT=0 git push origin main
# 还失败 → 切 SSH 协议（前提 ~/.ssh/id_rsa 是 GitHub key）
git remote set-url origin git@github.com:jacardl/viceroy-skills.git
git push origin main
```

### 坑 4：push 之前要先 rebase

**症状**：`git push` 报 `! [rejected] main -> main (fetch first)`。

**原因**：之前 `git pull` 超时失败了，但远端实际已经写入了新 commit（可能是 GitHub Action / cron / 其他 agent）。你本地还停留在旧 HEAD。

**处理**：
```bash
# --autostash：把 working tree 的未提交变更暂存，rebase 后自动恢复
GIT_TERMINAL_PROMPT=0 git pull --rebase --autostash origin main
GIT_TERMINAL_PROMPT=0 git push origin main
```

**注意**：如果 working tree 里有重要的本地文件（比如刚 `cp -r` 进去还没 `git add` 的），`--autostash` 会保留它们；rebase 完会自动 unstash 回来。**不要用普通的 `git stash`，会丢东西。**

### 坑 5（补充）：同步前先备份云端原版

**为什么**：万一本地的版本有 regression（比如漏了某个 reference），可以秒级回滚到云端旧版对比。

**做法**（不是 git 操作，单纯 cp 一份）：
```bash
# 备份到 /tmp
cp -r skills/<cat>/<skill> /tmp/cloud_backup_<skill>_$(date +%Y%m%d)
# 同步完后想回滚：rm -rf skills/<cat>/<skill>/* && cp -r /tmp/cloud_backup_<skill>_*/* skills/<cat>/<skill>/
```

## 推送命令示例

```bash
# 克隆
git clone https://github.com/jacardl/viceroy-skills.git /tmp/viceroy-skills_sync

# 复制技能（如 storage-analyzer 到 assistant）
mkdir -p /tmp/viceroy-skills_sync/skills/assistant/storage-analyzer
cp -r /path/to/skill/* /tmp/viceroy-skills_sync/skills/assistant/storage-analyzer/

# 提交
cd /tmp/viceroy-skills_sync
git add <files>
git commit -m "feat: add storage-analyzer skill"
GIT_ASKPASS=echo git push
```

## README 更新检查清单

每次同步后，逐项核对：

- [ ] 标题：`# 🧰 viceroy-skills`（有 🧰 图标）
- [ ] 描述：`我自己每天在用的一些 AI 技能和 Prompt，都开源在这里。`
- [ ] Status Badges：LICENSE · SKILLS（数量正确）· AgentSkills
- [ ] 平台徽章：Claude Code · Codex · OpenCode · OpenClaw（四个）
- [ ] 中英切换入口存在且格式正确
- [ ] 安装命令：`npx skills add jacardl/viceroy-skills --skill <name>`
- [ ] 触发示例：中文自然句式
- [ ] 技能数量：59 个（AI 2 + Assistant 10 + Creative 4 + Developer 5 + Operations 33 + Product 5）
- [ ] SEO/GEO 系列已合并列示
- [ ] README.md 和 README.en.md 同时更新