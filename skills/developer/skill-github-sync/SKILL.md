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

### 第三步：同步 Skill 文件

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