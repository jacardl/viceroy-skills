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

> ⛔ **铁律**：执行下面"## 核心流程"之前，**必须先读完末尾的"⚠️ 踩坑"章节**（坑 1-11）和 `references/sync-pitfalls.md`、`references/2026-06-14-credential-safety.md`。这 3-5 分钟能省你 30 分钟 debug。

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
- [ ] **YES 4（凭证红线）**：我跑过凭证扫描，**确认本次要同步的所有 skill 的 `references/config.md` / `credentials*` 都是脱敏版**（命中 `sk-you...here` 等占位符 = 安全；命中 `sk-0d68d...` 等真实值 = 立即停下，参考坑 10）。
- [ ] **YES 5（新 skill 还是更新？）**：`curl .../skills/<cat>/<skill>/SKILL.md` 返回 **HTTP 404** → 全新推送，不需要 rebase，参考 `references/push-new-skill.md`。返回 **HTTP 200** → 走坑 11 决策树（rebase / 保守 / 跳过）。

**3 个全 yes（实际是 5 项全 yes）** → 走"## 核心流程"。**任一是 no** → 先补读，再走流程。

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

## ⚠️ 踩坑（2026-06-04 + 2026-06-11 + 2026-06-14 实战 sync 沉淀）

sync 操作不顺利时按这 11 个坑对号入座。详细复现/诊断命令见 `references/sync-pitfalls.md` 和 `references/2026-06-14-credential-safety.md`。

| 📌 **2026-06-11 重装 zhilicomments v2 实战参考**：`references/zhilicomments-v2-reinstall.md`（完整流程 + 字节数对比 + 同分类兄弟检查模板）。
| 📌 **2026-06-14 zhililong 首次全套 sync 实战**：`references/2026-06-14-zhililong-sync-case-study.md`（9 文件 49496 字节，字节数一一核对表 + 4 项验证清单 + 跨 skill 路径统一经验）。
| 📌 **2026-06-14 凭证安全 + rebase 决策（P0 必读）**：`references/2026-06-14-credential-safety.md`（差点把 zhilicomments 真实 APPSECRET 推到云端的实战复盘 + 还原命令 + 失败兜底）。 |
| 📌 **2026-07-03 heredoc 写 Python 脚本失败**：`references/heredoc-python-token-fail.md`（TOKEN=*** 字符串被外层 bash wrapper 吞掉，5 次 SyntaxError 后改用 write_file → terminal python3 一次成功）。|
| 📌 **2026-07-04 shallow clone 复用导致 .git 不完整**：`references/shallow-clone-reuse-failure.md`（`--depth=1` 克隆后跨 session 复用，`git status` 报 `fatal: not a git repository`，实际是 shallow 对象缺失；解法：每次 sync 重新全量克隆或用检测脚本）。|

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

### 坑 6：本地路径 ≠ 用户给的 GitHub 路径（重装时最常踩）

**症状**：用户给一个 GitHub URL（比如 `https://github.com/jacardl/viceroy-skills/tree/main/skills/creative/zhilicomments`），但本地装在 `~/.hermes/skills/social-media/.agents/skills/zhilicomments/`。你以为这是同一回事，**直接覆盖就完了**——其实差两个层级。

**正确做法**：先**确认云端的真实路径**（`/skills/<cat>/<skill>`）和**本地的真实路径**（五花八门，依赖安装历史），再去覆盖。

**验证脚本**（重装前必跑）：
```bash
# Step 1: 列云端 skills/<cat>/ 下的所有 skill（确认 cat 和 skill 名都对）
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://api.github.com/repos/jacardl/viceroy-skills/contents/skills/creative" | \
  python3 -c "import sys,json; [print(x['name']) for x in json.load(sys.stdin)]"

# Step 2: 列本地 ~/.hermes/skills/ 下的所有 skill（找全路径，**别只看 .agents/，要看所有子目录**）
find ~/.hermes/skills -name "SKILL.md" -path "*zhilicomments*" -o -name "SKILL.md" -path "*zhiligithub*" 2>/dev/null

# Step 3: 比较两边字节数——字节差 >30% 几乎一定有遗漏
LOCAL_SIZE=$(wc -c < ~/.hermes/skills/social-media/.agents/skills/zhilicomments/SKILL.md)
REMOTE_SIZE=$(curl -sIL "https://raw.githubusercontent.com/jacardl/viceroy-skills/main/skills/creative/zhilicomments/SKILL.md" | grep -i content-length | awk '{print $2}' | tr -d '\r')
echo "本地: $LOCAL_SIZE bytes, 云端: $REMOTE_SIZE bytes"
# 差>30% 或本地>云端 → 重装；本地<云端 → 本地严重过时，必须重装
```

**实战案例**（2026-06-11）：
- 本地 `zhilicomments` 10534字节 vs 云端 27306字节 → **本地严重过时**，必须重装
- 5 条精简规则（5.1-5.7）、禁词清单、`scripts/preflight.py` 引用、streambert-reference.html 都在云端，本地全缺
- 重装后还需 patch SKILL.md 的 `description` 让字数/作者/公众号对齐（避免 agent 拿到的是旧版触发词）

### 坑 7：同分类兄弟 skill 同步落后（重装时易漏）

**症状**：重装 `zhilicomments` 时只覆盖了它一个，结果 `zhiliGitHub` 还是本地版（云端可能更新了几次）。下次推 GitHub 长文时，又踩同样的"云端落后"坑。

**正确做法**：用户说"重装 X"时，**主动列出同类 skill 并对比**：

```bash
# Step 1: 找出云端 creative/ 下所有 zhili-* 技能（同一作者、可能同批次落后）
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://api.github.com/repos/jacardl/viceroy-skills/contents/skills/creative" | \
  python3 -c "import sys,json; [print(x['name']) for x in json.load(sys.stdin) if 'zhili' in x['name']]"
# 输出: zhili-publish, zhilicomments, zhiligithub

# Step 2: 每个都跑"坑 6"里的字节数对比
for skill in zhili-publish zhilicomments zhiligithub; do
  LOCAL=$(wc -c < ~/.hermes/skills/social-media/.agents/skills/$skill/SKILL.md 2>/dev/null || echo "MISSING")
  REMOTE=$(curl -sIL "https://raw.githubusercontent.com/jacardl/viceroy-skills/main/skills/creative/$skill/SKILL.md" | grep -i content-length | awk '{print $2}' | tr -d '\r')
  echo "$skill: 本地=$LOCAL 云端=$REMOTE"
done

# Step 3: 列出所有差>30% 的，逐个询问用户是否要一起重装
```

**判断标准**：
- 字节差 >30% 或本地<云端 → **强烈建议一起重装**
- 字节差 ≤10% 或本地>云端 → 本地可能领先，**不要动**，提示用户确认

**实战案例**（2026-06-11）：重装 zhilicomments 后立刻建议同步重装 zhiliGitHub / zhili-publish。

### 坑 8：先试 `npx skills add` 失败后才查云端路径（流程倒置）

**症状**：用户给一个 GitHub URL（如 `https://github.com/jacardl/viceroy-skills/tree/main/skills/creative/zhilicomments`），我**第一反应**是直接试 `npx skills add jacardl/viceroy-skills --skill zhilicomments`。失败了再退而求其次用 curl 拉 SKILL.md 比对——**但此时我已经报告"云端不存在"或路径错**。

**问题**：报告错了。用户实际意思是"按这个 URL 重装"，不是"用 npx 装"。我应该**第一时间就验证 URL 路径是否存在**，而不是猜 npx 路径后倒推。

**正确顺序**（任何"按 URL 重装"任务的第一步）：

```bash
# Step 1: 验证云端路径（用户给的 URL 段）真实存在
USER_PATH="skills/creative/zhilicomments"   # 从 URL 提取
curl -sLo /dev/null -w "%{http_code}\n" \
  "https://raw.githubusercontent.com/jacardl/viceroy-skills/main/${USER_PATH}/SKILL.md"
# 200 = 云端路径对；404 = 云端真没这个路径或拼写错

# Step 2: 列云端 SKILL.md 字节数 + 本地字节数（直接看出谁新）
REMOTE_SIZE=$(curl -sIL "https://raw.githubusercontent.com/jacardl/viceroy-skills/main/${USER_PATH}/SKILL.md" | grep -i content-length | awk '{print $2}' | tr -d '\r')

# Step 3: find 本地真实路径（**不要假设路径！** search 全树）
LOCAL_PATH=$(find ~/.hermes/skills ~/.agents/skills ~/.openclaw/skills -name "SKILL.md" -path "*$(basename $USER_PATH)*" 2>/dev/null | head -1)
LOCAL_SIZE=$(wc -c < "$LOCAL_PATH" 2>/dev/null || echo "MISSING")

echo "云端 $REMOTE_SIZE bytes / 本地 $LOCAL_SIZE bytes / 本地路径 $LOCAL_PATH"
```

**关键规则**：
- ✅ **永远先 grep 云端实存**——URL 里的 `skills/<cat>/<skill>` 是 ground truth，不靠 npx 反推
- ✅ **永远先 find 本地真实路径**——本地的 `social-media/.agents/skills/`、`~/.agents/skills/`、`~/.openclaw/skills/` 都是合法安装位置，别预设
- ❌ **不要先试 npx skills add**——失败后的报错容易误导（"路径不存在"实际是 npx 内部解析问题，不是云端真没）

**`npx skills add` 的真实路径规则**（2026-06-11 实战确认）：
- 默认落地：`~/.agents/skills/<name>/`（**根目录散落**，不带分类前缀）
- 如果之前用别的方式装过：可能落在 `~/.hermes/skills/<cat>/<name>/` 或 `~/.openclaw/skills/<cat>/<name>/`
- **三种合法路径都可能存在**，跨工具/跨 session 装的历史会让一个 skill 出现 2-3 份副本——这是混乱但不是 bug
- 重装时**优先覆盖用户当前 session 实际生效的那份**（看 `hermes skills list` 或 `~/.hermes/skills/` 目录）

**实战案例**（2026-06-11）：
- 用户说"按这个 URL 重装 zhilicomments: `https://github.com/jacardl/viceroy-skills/tree/main/skills/creative/zhilicomments`"
- 我第一反应：`npx skills add jacardl/viceroy-skills --skill zhilicomments` → 假设本地就是 `social-media/zhilicomments`
- **真实情况**：云端是 `skills/creative/zhilicomments`，本地是 `~/.hermes/skills/social-media/.agents/skills/zhilicomments/`（中间多个 `.agents/skills/` 嵌套层）
- 用户必须纠正我"重新安装"——浪费一轮
- **修复**：坑 6 已经提到"重装前先验证云端路径"，坑 8 补充"重装任务的**第一步就是验证**用户给的 URL，不要绕道 npx"

### 坑 9：sync 全套 skill 时拆目录的字节数核对（2026-06-14 zhililong 实战沉淀）

**症状**：本地 skill 目录有 9 个文件（SKILL.md + agents/ + references/ + scripts/），云端不存在/或旧版。`cp -r` 完只看了 `git diff --stat` 没看字节数，结果**漏拷了一个嵌套子目录**或者**覆盖了非空子目录产生嵌套**（`skill/skill/SKILL.md`），push 上去云端乱套。

**简短流程**（详细版见 `references/2026-06-14-zhililong-sync-case-study.md`）：

1. **备份云端 README**（坑 5）
2. **`rm -rf $TARGET` + `cp -r source/* $TARGET/`** —— 关键：先删后建 + 明确 `*` 通配
3. **字节数核对**：对每个文件 `wc -c` 对比，差值 0 才能 commit
4. **commit + push** 一次过（无重试）
5. **5 项验证**：远端 commit、字节数、文件结构、徽章数、**凭证文件脱敏核查**（独立走坑 10 流程，**不能合并到字节数核对里**——字节对不代表没明文）

**实战数据（zhililong 9 文件 49496 字节，差值 0）**：见 `references/2026-06-14-zhililong-sync-case-study.md` 的完整字节数表。

**为什么要先 rm 再 cp**：本地路径五花八门（`~/.hermes/skills/`, `~/.agents/skills/`, `~/.openclaw/skills/`），直接 `cp -r` 到云端会产生 `skills/creative/zhililong/agents/openai.yaml` **或** `skills/creative/zhililong/zhililong/agents/openai.yaml`（嵌套），取决于 cp 源是否带尾斜杠。**`rm -rf $TARGET` + `cp -r source/* $TARGET/`**（明确 `*` 通配）能保证**扁平化**。

**踩坑信号**：
- `git diff --cached --stat` 显示 `skills/creative/zhililong/zhililong/...` → 嵌套了
- `git push` 后 `curl raw.githubusercontent.com` 返回的文件路径里多了 `zhililong/` → 同上
- 修复：amend commit 或 revert 后重新 sync

**README 数字核实（必走）**：
- 实际 `find skills -name SKILL.md | wc -l` = 真实总数
- README 徽章 `Skills-N` 的 N 必须 = 真实总数
- 中英文版本都改（本实战：中文 66→68，英文 64→66；英文版 6 个 Creative 缺 1 个 `guizang-ppt-skill`，保守策略只同步本次涉及的 zhili 行，不动无关兄弟）

### 坑 10（P0 安全红线）：本地 credentials 文件含明文真实凭证，必须双向 diff 后才能 push

**症状**：`cp -r` 本地 skill 到云端 working dir 时，**本地 `references/config.md` 里有真实 APPSECRET/API_KEY/TOKEN**，**云端是脱敏版**（`***REDACTED***`）。**直接 `git add + commit + push` → 真实凭证明文上云**——GitHub private repo 也算泄露（协作者 + GitHub backup + 自动扫描）。

**实战案例（2026-06-14 zhilicomments）**：
- 本地 `zhilicomments/references/config.md` 348 字节 + 明文 `APPSECRET: 07b4dc2d64ddbe6f53707977dbabdbbe`
- 云端 HEAD `references/config.md` 536 字节 + `APPSECRET: ***REDACTED***`
- `cp -r` 时没意识到这是凭证文件，working dir 被本地明文覆盖
- `git status` 显示 modified，但**真正拦截点是 `git diff`**——明文 APPSECRET 出现在 diff 里
- 立即 `git checkout HEAD -- .../config.md` 还原到脱敏版
- 用户 10 分钟内未拍板 → **本次跳过整个 zhilicomments**（commit 里不包含它的任何文件）

**识别信号**（同步前必跑，3 步全过才能 push）：

```bash
# Step 1: 列本地所有可能的凭证文件
find ~/.hermes/skills -path "*/references/config.md" -o -path "*/references/credentials*" -o -name "*_token.txt" 2>/dev/null

# Step 2: 全文搜敏感词（APPSECRET / API_KEY / SECRET / PASSWORD / PRIVATE_KEY / WX_）
for f in $(find ~/.hermes/skills -path "*/references/config.md" 2>/dev/null); do
  echo "=== $f ==="
  grep -inE "appsecret|api_key|secret|password|token|wx_|private_key" "$f" | head -5
done

# Step 3: 对每个命中文件，对比云端 HEAD
for f in $(... 命中文件 ...); do
  rel=${f#~/.hermes/skills/}
  cloud_content=$(git -C /tmp/viceroy-skills2 show HEAD:"${rel#skills/}" 2>/dev/null)
  if echo "$cloud_content" | grep -qE "REDACTED|\\*\\*\\*\\*\\*"; then
    echo "✅ $f 云端脱敏" 
  else
    echo "⚠️ $f 云端可能也是明文——先确认"
  fi
done
```

**处理流程**（发现"本地真值、云端占位"差异时）：

```bash
# 1. 绝对不要把本地版本推到云端

# 2. 拉云端 HEAD 版本（脱敏版）覆盖本地 working dir
git -C /tmp/viceroy-skills2 checkout HEAD -- skills/<cat>/<skill>/references/config.md

# 3. 验证覆盖成功
diff /tmp/viceroy-skills2/skills/<cat>/<skill>/references/config.md \
     /Users/apple/.hermes/skills/<local-area>/<skill>/references/config.md
# 输出为空 = 两边一致；非空 = 还需重做

# 4. git diff 这个文件应该是 0 变化
git diff skills/<cat>/<skill>/references/config.md
```

**预防清单**（`cp -r` 之后、`git add` 之前）：

- [ ] **逐个 `git diff` 检查改动的文件**——不是只看 `git status --stat`
- [ ] **凭证文件专属 grep**：所有 `config.md` / `credentials*` / `*_token.txt` 必须确认是脱敏版
- [ ] **diff 含 APPSECRET/API_KEY/TOKEN/PASSWORD 字面量 → 立即 `git checkout HEAD`**
- [ ] **整个 skill 含凭证文件 → 默认跳过该 skill**，留给用户手动决定

**失败兜底**（如果已经 push 到云端）：

```bash
# 1. 立即从 GitHub history 删文件（含所有 commit 里的版本）
#    BFG Repo-Cleaner（推荐）
bfg-repo-cleaner --delete-files config.md viceroy-skills.git
# 或 git filter-branch
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch skills/<cat>/<skill>/references/config.md" \
  --prune-empty --tag-name-filter cat -- --all
git push origin --force --all

# 2. 立即轮换 APPSECRET/API_KEY（去对应平台后台重置）
# 3. 通知所有协作者
# 4. 检查 GitHub Secret Scanning 告警
```

**详细复现 + 实战时间线**：`references/2026-06-14-credential-safety.md`（6465 字节，含 13:21→13:39 完整决策路径）。

### 坑 11：冲突解决策略（本地 vs 云端内容冲突）

**核心原则（2026-07-04 更新）**：

当本地和云端对**同一内容**有不同描述时，采用以下优先级策略：

| 优先级 | 规则 | 说明 |
|--------|------|------|
| 1 | **最新内容优先** | 以最后修改的版本为准，不比较来源（本地 vs 云端） |
| 2 | **删除旧内容** | 旧版中与新版重复的描述、引用、代码块，**直接删除**，不做合并 |
| 3 | **云端只是备份** | 云端 ≠ 权威，本地才是工作区；云端落后就以本地为准 |
| 4 | **不保留双重版本** | 不同时保留新旧两份内容，必须二选一 |

**具体处理规则**：

#### 1. 描述冲突
- 如果云端有一段描述，本地有同一主题的另一段描述
- **以本地为准**，删除云端旧描述中的重复部分
- 如果本地描述更完整，**直接用本地全文替换云端**

#### 2. 引用/参考样式冲突
- 如果同一引用（URL、文件名、API 端点）在新旧版本中有不同的描述方式
- **以最新版本的描述为准**，删除旧版本中的重复引用
- 如果旧版本有多余的示例/模板代码，**直接删除**

#### 3. 代码/脚本冲突
- 如果同一功能在新旧版本中有不同的实现
- **以最新版本为准**，删除旧版本中的旧实现
- 注释中的重复说明也需清理

#### 4. 不要 git merge-file
**绝对不要用 `git merge-file` 做三方合并**——它的合并逻辑会保留两边的共同祖先内容，导致重复代码累积。

**正确做法**：
```
# Step 1: 判断哪个版本更新
# 规则：mtime 更新的那个 = 新版；或者用户明确指定的 = 新版

# Step 2: 以新版为准，清理旧版内容
# 如果本地是新版 → 直接用本地覆盖云端（rm + cp）
# 如果云端是新版 → 拉取云端覆盖本地，再加本地新内容

# Step 3: 在新版基础上追加/修改，不保留旧版的任何内容
```

#### 5. 决策树

```
sync 时发现本地 vs 云端有内容差异
  │
  ├─ 本地是用户刚更新的（mtime 最近）
  │    → 以本地为准，直接覆盖云端
  │    → 不做三方合并，不用 git merge-file
  │    → 推送前确认：本地版本确实是最新的
  │
  ├─ 云端比本地新（云端 mtime 更近，或用户明确说"以云端为准"）
  │    → 以云端为准，拉取云端到本地
  │    → 在云端基础上加本地新内容
  │    → 推送云端
  │
  └─ 用户给了特定版本要求（如"用本地版本"）
       → 按用户要求执行
       → 用户说哪个版本，哪个就是新版
```

**实战案例（2026-07-04 skill-maintenance v2.7）**：
- 任务：更新 skill-maintenance 到云端
- 预检：本地 52110 chars > 云端 20404 chars（本地领先 155%）
- 判断：本地是新版（mtime 最近，且 mtime 差距 >30 天）
- 操作：**以本地为准**，云端旧版直接丢弃（20404 chars 的旧内容不合并）
- 结果：云端更新为 52110 chars 新版，差值 0

**关键原则**：
- **不要做三方合并**——merge-file 会保留两边的共同内容，导致文件越来越臃肿
- **删除旧内容**——重复的描述、引用、代码块直接删，不保留两份
- **以最新为准**——版本新旧由 mtime 和用户指定决定，不看本地 vs 云端标签
- **云端是备份，不是权威**——云端落后就丢弃云端版本，以本地为准

---

**冲突解决核心检查（每次 sync 前必做）**：

1. **判断版本新旧**：比较本地 vs 云端 SKILL.md 的 mtime 或内容更新时间
2. **凭证文件扫描**（坑 10）：`find ... -name "config.md" -o -name "credentials*" | xargs grep -iE "sk-[0-9a-z]{32}|wx[0-9a-f]{16}"`
3. **确认：无真实密钥** → 以最新版本为准，直接覆盖旧版本

**三步全过且无异常 → 走 sync。任一异常 → 先问用户。**

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
- [ ] **凭证文件核查（2026-06-14 新增）**：`grep -lE "appsecret|api_key|password|token" skills/<cat>/<skill>/references/` 输出为空，或命中行都是 `***REDACTED***` 占位符