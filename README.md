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
| [**neat-freak**](skills/assistant/neat-freak/SKILL.md) | 清理会话里的无用内容，保留知识点 |
| [**obsidian**](skills/assistant/obsidian/SKILL.md) | 操作 Obsidian 笔记库 |
| [**obsidian-cli**](skills/assistant/obsidian-cli/SKILL.md) | Obsidian 命令行工具 |
| [**storage-analyzer**](skills/assistant/storage-analyzer/SKILL.md) | 分析本地存储占用，清理大文件 |
| [**wechat-article-to-markdown**](skills/assistant/wechat-article-to-markdown/SKILL.md) | 微信公众号文章转 Markdown |
| [**youtube-transcript**](skills/assistant/youtube-transcript/SKILL.md) | 提取 YouTube 字幕并翻译 |

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
| [**scrapling**](skills/developer/scrapling/SKILL.md) | 自适应网页爬虫 |
| [**skill-creator**](skills/developer/skill-creator/SKILL.md) | 创建新的 Skill |
| [**skill-github-sync**](skills/developer/skill-github-sync/SKILL.md) | 将 Skills 同步到 GitHub |
| [**skill-maintenance**](skills/developer/skill-maintenance/SKILL.md) | 维护 Skill 库整洁 |

---

### 📊 Operations

| Name | How to trigger |
|------|----------------|
| [**aihot**](skills/operations/aihot/SKILL.md) | AI 热点资讯查询 |
| [**github-daily-trending**](skills/operations/github-daily-trending/SKILL.md) | 今天 GitHub 有什么趋势 |
| **GEO 系列（3个）** | geo-content-strategy · geo-keyword-research · geo-strategy-report |
| **SEO 系列（25个）** | seo · seo-audit · seo-backlinks · seo-clust · seo-competitor-pages · seo-content · seo-data-forum · seo-drip · seo-ecomm · seo-flow · seo-geo · seo-google · seo-hreflang · seo-images · seo-local · seo-maps · seo-page · seo-plan · seo-programmatic · seo-schema · seo-sitemap · seo-technical · seo-translate · seo-x |

---

### 📦 Product

| Name | How to trigger |
|------|----------------|
| [**brand-product-audience-relevance**](skills/product/brand-product-audience-relevance/SKILL.md) | 人群-产品-品牌匹配分析 |
| [**competitor-discovery**](skills/product/competitor-discovery/SKILL.md) | 竞品发现与分析 |
| [**hv-analysis**](skills/product/hv-analysis/SKILL.md) | 人群价值分析 |
| [**patent-disclosure-skill**](skills/product/patent-disclosure-skill/SKILL.md) | 专利披露分析 |
| [**software-copyright-materials**](skills/product/software-copyright-materials/SKILL.md) | 软著材料生成 |

---

## 🌟 关于

这是我的私人 Skill 库——每个 Skill 都在我自己项目里跑过足够久、确认真的省时间才开源的。没有噱头，只有实用。

如果你觉得有用，欢迎 ⭐。问题和建议欢迎提 Issue / Discussion。

---

<div align="center">

[MIT License](./LICENSE) · 随意使用、修改和分发

Made by [@jacardl](https://github.com/jacardl)

</div>
