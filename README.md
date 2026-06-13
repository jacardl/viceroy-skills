<div align="center">

**中文** · [English](./README.en.md)

# 🧰 viceroy-skills

我自己每天在用的一些 AI 技能和 Prompt，都开源在这里。

[![License](https://img.shields.io/badge/License-MIT-3B82F6?style=for-the-badge)](./LICENSE)
[![Skills](https://img.shields.io/badge/Skills-66-10B981?style=for-the-badge)](#-skills)
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
| [**local-model-orchestrator**](skills/ai/local-model-orchestrator/SKILL.md) | 扫描、解释、选择并调用本地 AI 模型，优先推荐 Mac 芯片优化方案 |
| [**mmx-cli**](skills/ai/mmx-cli/SKILL.md) | 用 MiniMax 生成文本、图片、视频、音乐 — 含搜索功能 |

---

### 🧑‍💼 Assistant

| Name | How to trigger |
|------|----------------|
| [**find-skills**](skills/assistant/find-skills/SKILL.md) | 在 ClawHub 上找 SEO 相关 Skill |
| [**markitdown**](skills/assistant/markitdown/SKILL.md) | 把这个 PDF 转成 markdown |
| [**markdown-to-report**](skills/assistant/markdown-to-report/SKILL.md) | 把这个 markdown 转成带样式的 HTML 报告 |
| [**neat-freak**](skills/assistant/neat-freak/SKILL.md) | /neat — 整理本次会话的文档和记忆 |
| [**obsidian**](skills/assistant/obsidian/SKILL.md) | 搜索我的 Obsidian 笔记库 |
| [**obsidian-cli**](skills/assistant/obsidian-cli/SKILL.md) | 创建一条新 Obsidian 笔记 |
| [**storage-analyzer**](skills/assistant/storage-analyzer/SKILL.md) | 看看我的硬盘 / C 盘满了 / 清理一下 |
| [**wechat-article-to-markdown**](skills/assistant/wechat-article-to-markdown/SKILL.md) | 把这篇微信文章转成 markdown |
| [**youtube-transcript**](skills/assistant/youtube-transcript/SKILL.md) | 抓取这个 YouTube 视频的字幕 |

---

### 🎨 Creative

| Name | How to trigger |
|------|----------------|
| [**khazix-writer**](skills/creative/khazix-writer/SKILL.md) | 用卡兹克的风格写一篇公众号文章 |
| [**zhili-publish**](skills/creative/zhili-publish/SKILL.md) | 把这个 HTML 草稿发布到微信公众号 |
| [**zhilicomments**](skills/creative/zhilicomments/SKILL.md) | 发一条短评论到公众号 |
| [**zhiligithub**](skills/creative/zhiligithub/SKILL.md) | 把这个 GitHub 项目写成一篇公众号文章 |
| [**guizang-ppt-skill**](skills/creative/guizang-ppt-skill/SKILL.md) | 生成横向翻页网页 PPT；触发：杂志风 PPT / 瑞士风 PPT / Swiss Style / horizontal swipe deck |

---
### 🛠️ Developer

| Name | How to trigger |
|------|----------------|
| [**setup-matt-pocock-skills**](skills/developer/setup-matt-pocock-skills/SKILL.md) | 在 AGENTS.md 里配置 Matt Pocock 的 Skill 规范 |
| [**skill-creator**](skills/developer/skill-creator/SKILL.md) | 从零创建一个新 Skill |
| [**skill-github-sync**](skills/developer/skill-github-sync/SKILL.md) | 把本地 Skills 同步到 GitHub |
| [**skill-maintenance**](skills/developer/skill-maintenance/SKILL.md) | 整理 Skill 库 / 查重 |

---

### 📊 Operations

| Name | How to trigger |
|------|----------------|
| [**aihot**](skills/operations/aihot/SKILL.md) | 今天 AI 有什么新 / 这周 AI 论文有哪些 |
| [**baoyu-url-to-markdown**](skills/operations/baoyu-url-to-markdown/SKILL.md) | 把这个链接转成 markdown |
| [**geo-content-strategy**](skills/operations/geo-content-strategy/SKILL.md) | 构建一套 GEO 内容策略 |
| [**geo-keyword-research**](skills/operations/geo-keyword-research/SKILL.md) | 研究 GEO 关键词 |
| [**geo-strategy-report**](skills/operations/geo-strategy-report/SKILL.md) | 生成一份 GEO 策略报告 |
| [**scrapling**](skills/operations/scrapling/SKILL.md) | 爬这个网站 |
| [**tender-response-maker**](skills/operations/tender-response-maker/SKILL.md) | 分析标书 / 输出应标材料清单 |
| **GEO 系列（3个）** | geo-content-strategy · geo-keyword-research · geo-strategy-report |
| **SEO 系列（25个）** | seo · seo-audit · seo-backlinks · seo-cluster · seo-competitor-pages · seo-content · seo-content-brief · seo-dataforseo · seo-drift · seo-ecommerce · seo-flow · seo-geo · seo-google · seo-hreflang · seo-image-gen · seo-images · seo-local · seo-maps · seo-page · seo-plan · seo-programmatic · seo-schema · seo-sitemap · seo-sxo · seo-technical |
| [**github-daily-trending**](skills/operations/github-daily-trending/SKILL.md) | 今天 GitHub 有什么趋势 |
| [**radar-daily-report**](skills/operations/radar-daily-report/SKILL.md) | 给我一份 Radar 日报 |
| [**radar-data-collection**](skills/operations/radar-data-collection/SKILL.md) | 舆情数据采集标准规范 |

---


### 📦 Product

| Name | How to trigger |
|------|----------------|
| [**brand-product-audience-relevance**](skills/product/brand-product-audience-relevance/SKILL.md) | 分析这个品牌和 CID 人群数据的相关性 |
| [**competitor-discovery**](skills/product/competitor-discovery/SKILL.md) | 从这段 AI 回复里识别竞品 |
| [**hv-analysis**](skills/product/hv-analysis/SKILL.md) | 研究这个公司 / 产品 |
| [**research-synth**](skills/product/research-synth/SKILL.md) | 综合用户访谈 / Survey 开放题 / Synthetic User Q&A，生成产品洞察、机会 backlog、研究计划和知识图谱 |
| [**patent-disclosure-skill**](skills/product/patent-disclosure-skill/SKILL.md) | 生成一份专利披露文档 |
| [**software-copyright-materials**](skills/product/software-copyright-materials/SKILL.md) | 生成软件著作权申请材料 |

---

## 🌟 关于

这是我的私人 Skill 库——每个 Skill 都在我自己项目里跑过足够久、确认真的省时间才开源的。没有噱头，只有实用。

如果你觉得有用，欢迎 ⭐。问题和建议欢迎提 Issue / Discussion。

---

<div align="center">

[MIT License](./LICENSE) · 随意使用、修改和分发

Made by [@jacardl](https://github.com/jacardl)

</div>
