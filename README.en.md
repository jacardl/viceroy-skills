<div align="center">

**中文** · [English](./README.en.md)

# 🧰 viceroy-skills

My personal AI skills and prompts — everything I use daily in real projects, open sourced here.

[![License](https://img.shields.io/badge/License-MIT-3B82F6?style=for-the-badge)](./LICENSE)
[![Skills](https://img.shields.io/badge/Skills-111-10B981?style=for-the-badge)](#-skills)
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
| [Assistant](#-assistant) | Legal reasoning, document processing, knowledge management, storage |
| [Creative](#-creative) | WeChat article writing, cover images, short comments, GitHub highlights |
| [Developer](#-developer) | Skill creation & maintenance, code quality |
| [Operations](#-operations) | SEO / GEO strategy, public opinion, scraping, automation |
| [Product](#-product) | Competitor analysis, audience research, patents, copyright |
| [Productivity](#-productivity) | Productivity tools |

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

### 🤖 AI Models

| Name | One-liner |
|------|-----------|
| [**9router**](skills/ai/9router/SKILL.md) | Local/remote AI gateway — one API key, multiple providers, OpenAI-compatible |
| [**local-model-orchestrator**](skills/ai/local-model-orchestrator/SKILL.md) | Local model orchestrator |
| [**mmx-cli**](skills/ai/mmx-cli/SKILL.md) | Generate text, images, video, music with MiniMax — includes search |

---

### 🧑‍💼 Assistant（50）

**Legal Reasoning Series（31）**：analogical-reasoning · argument-chain-construction · argument-strength-evaluation · counterfactual-reasoning · deductive-reasoning · evidence-argument-chain · evidence-evaluation · formal-legal-consequence · inductive-reasoning · judicial-value-judgment · legal-abductive-reasoning · legal-article-retrieval · legal-concept-comprehension · legal-document-formatting · legal-document-summarization · legal-element-extraction · legal-interpretation-argument · legal-judgment-prediction · legal-norm-validity-check · legal-risk-assessment · legal-terminology · normative-meaning-argumentation · structured-element-extraction · systematic-interpretation · teleological-interpretation

**Legal Business Series（15）**：administrative-value-judgment · billing-and-litigation-budget · case-lifecycle-planning · case-retrieval · conflict-resolution · diary-write · dispute-and-performance-risk · dispute-issue-identification · internal-compliance-risk-identification · judgment-document-generation · other-legal-retrieval · patent-disclosure-skill · strategic-risk-prioritization · trial-scheduling-and-deadline-monitoring

**General Tools（4）**：

| Name | How to trigger |
|------|----------------|
| [**baoyu-url-to-markdown**](skills/assistant/baoyu-url-to-markdown/SKILL.md) | URL to Markdown |
| [**find-skills**](skills/assistant/find-skills/SKILL.md) | Find Skills on ClawHub |
| [**markdown-to-report**](skills/assistant/markdown-to-report/SKILL.md) | Markdown to report |
| [**markitdown**](skills/assistant/markitdown/SKILL.md) | Convert this PDF to markdown |
| [**multi-document-summarization**](skills/assistant/multi-document-summarization/SKILL.md) | Multi-document summarization |
| [**neat-freak**](skills/assistant/neat-freak/SKILL.md) | Clean up session noise, keep knowledge points |
| [**obsidian**](skills/assistant/obsidian/SKILL.md) | Operate Obsidian vault |
| [**obsidian-cli**](skills/assistant/obsidian-cli/SKILL.md) | Obsidian CLI tool |
| [**storage-analyzer**](skills/assistant/storage-analyzer/SKILL.md) | Analyze local storage, clean up large files |
| [**wechat-article-to-markdown**](skills/assistant/wechat-article-to-markdown/SKILL.md) | Convert WeChat article to Markdown |
| [**youtube-transcript**](skills/assistant/youtube-transcript/SKILL.md) | Extract and translate YouTube subtitles |

---

### 🎨 Creative（11）

| Name | How to trigger |
|------|----------------|
| [**9router-image**](skills/creative/9router-image/SKILL.md) | 9Router image generation |
| [**guizang-ppt-skill**](skills/creative/guizang-ppt-skill/SKILL.md) | PPT generation |
| [**khazix-writer**](skills/creative/khazix-writer/SKILL.md) | Write a WeChat article in 卡兹克's style |
| [**renwei-writing**](skills/creative/renwei-writing/SKILL.md) | Renwei writing |
| [**xiaohu-ip-studio**](skills/creative/xiaohu-ip-studio/SKILL.md) | XiaoHu IP Studio |
| [**zhili-illustration**](skills/creative/zhili-illustration/SKILL.md) | WeChat cover image generation |
| [**zhili-publish**](skills/creative/zhili-publish/SKILL.md) | Publish this HTML draft to WeChat |
| [**zhiliGEO**](skills/creative/zhiliGEO/SKILL.md) | GEO vertical series |
| [**zhilicomments**](skills/creative/zhilicomments/SKILL.md) | Post a short comment to WeChat |
| [**zhiligithub**](skills/creative/zhiligithub/SKILL.md) | Turn this GitHub project into a WeChat article |
| [**zhililong**](skills/creative/zhililong/SKILL.md) | Long-form WeChat article writing |

---

### 🛠️ Developer（5）

| Name | How to trigger |
|------|----------------|
| [**scrapling**](skills/developer/scrapling/SKILL.md) | Adaptive web scraper |
| [**setup-matt-pocock-skills**](skills/developer/setup-matt-pocock-skills/SKILL.md) | Install matt-pocock Skills |
| [**skill-creator**](skills/developer/skill-creator/SKILL.md) | Create a new Skill |
| [**skill-github-sync**](skills/developer/skill-github-sync/SKILL.md) | Sync Skills to GitHub |
| [**skill-maintenance**](skills/developer/skill-maintenance/SKILL.md) | Keep the skill library clean |

---

### 📊 Operations（35）

**GEO Series（3）**：geo-content-strategy · geo-keyword-research · geo-strategy-report

**SEO Series（30）**：seo · seo-audit · seo-backlinks · seo-cluster · seo-competitor-pages · seo-content · seo-content-brief · seo-dataforseo · seo-drift · seo-ecommerce · seo-flow · seo-geo · seo-google · seo-hreflang · seo-image-gen · seo-images · seo-local · seo-maps · seo-page · seo-plan · seo-programmatic · seo-schema · seo-sitemap · seo-sxo · seo-technical

**Operations Tools（2）**：

| Name | How to trigger |
|------|----------------|
| [**aihot**](skills/operations/aihot/SKILL.md) | AI hot news query |
| [**github-daily-trending**](skills/operations/github-daily-trending/SKILL.md) | What's trending on GitHub today |
| [**radar-daily-report**](skills/operations/radar-daily-report/SKILL.md) | Radar daily report |
| [**radar-data-collection**](skills/operations/radar-data-collection/SKILL.md) | Public opinion data collection |
| [**tender-response-maker**](skills/operations/tender-response-maker/SKILL.md) | Tender response generation |
| [**webpage-audit**](skills/operations/webpage-audit/SKILL.md) | Webpage audit |
| [**zhiligithub**](skills/operations/zhiligithub/SKILL.md) | GitHub project operations |

---

### 📦 Product（6）

| Name | How to trigger |
|------|----------------|
| [**brand-product-audience-relevance**](skills/product/brand-product-audience-relevance/SKILL.md) | Audience-product-brand match analysis |
| [**competitor-discovery**](skills/product/competitor-discovery/SKILL.md) | Competitor discovery and analysis |
| [**hv-analysis**](skills/product/hv-analysis/SKILL.md) | High-value audience analysis |
| [**radar-data-collection**](skills/product/radar-data-collection/SKILL.md) | Public opinion data collection |
| [**research-synth**](skills/product/research-synth/SKILL.md) | Research synthesis |
| [**software-copyright-materials**](skills/product/software-copyright-materials/SKILL.md) | Software copyright materials |

---

### ⚡ Productivity（1）

| Name | How to trigger |
|------|----------------|
| [**skill-creator**](skills/productivity/skill-creator/SKILL.md) | Create a new Skill |

---

## 🌟 About

This is my personal skill library — everything here is what I use daily in real projects. If it's useful to you, a ⭐ is appreciated. Questions and suggestions welcome in Issues / Discussions.

---

<div align="center">

[MIT License](./LICENSE) · Free to use, modify, and redistribute

Made by [@jacardl](https://github.com/jacardl)

</div>
