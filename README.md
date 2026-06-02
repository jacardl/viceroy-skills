<div align="center">

**中文** · [English](./README.en.md)

# 🧰 Skillshub

#### 佳哥私人 Skill 库，按岗位分类，开箱即用

[![License](https://img.shields.io/badge/License-MIT-3B82F6?style=for-the-badge)](./LICENSE)
[![Skills](https://img.shields.io/badge/Skills-59-10B981?style=for-the-badge)](#-skills)
[![AgentSkills](https://img.shields.io/badge/AgentSkills-Standard-8B5CF6?style=for-the-badge)](https://agentskills.io)

![Claude Code](https://img.shields.io/badge/Claude_Code-Skill-D97706?style=flat-square&logo=anthropic&logoColor=white)
![Codex](https://img.shields.io/badge/Codex-Skill-10B981?style=flat-square&logo=openai&logoColor=white)
![OpenCode](https://img.shields.io/badge/OpenCode-Skill-3B82F6?style=flat-square)
![OpenClaw](https://img.shields.io/badge/OpenClaw-Skill-8B5CF6?style=flat-square)

</div>

---

都是自己在项目里跑通了一段时间、确实省事才开源的东西。没什么花活，就是几个挺实用的技能。

- **Skills** — Agent 能直接加载的结构化指令集，遵循 [Agent Skills](https://agentskills.io) 开放标准。Claude Code、Codex、OpenCode、OpenClaw 都能装
- 支持 Claude Code、Codex、OpenClaw 等主流 Agent

---

## 📋 目录

| 分类 | 说明 |
|------|------|
| [AI模型](#-ai模型) | 本地/远程 AI 网关、图片生成、终端交互 |
| [助理](#-助理) | 文件处理、知识管理、Obsidian、存储分析 |
| [创意](#-创意) | 公众号写作、封面图、短评、GitHub 热点 |
| [开发](#-开发) | Skill 创作与维护、代码质量 |
| [运营](#-运营) | SEO / GEO 策略、舆情、爬虫、自动化 |
| [产品](#-产品) | 竞品分析、人群研究、专利、版权 |

---

## 📦 安装方式

在支持 Skill 的 Agent 里直接说：

```
帮我安装这个 skill：https://github.com/jacardl/skillshub/tree/main/<skill-name>
```

示例：
```
帮我安装 storage-analyzer
帮我安装 hv-analysis
帮我安装 khazix-writer
```

---

## ✨ Skills

<a id="-skills"></a>

---

### 🤖 AI模型（ai）

| 名字 | 一句话 |
|------|--------|
| [**9router**](skills/ai/9router/SKILL.md) | 本地/远程 AI 网关，一个 Key 调用多个 Provider，OpenAI 兼容接口 |
| [**mmx-cli**](skills/ai/mmx-cli/SKILL.md) | 用 MiniMax 模型生成文本、图片、视频、音乐，支持联网搜索 |

---

### 🧑‍💼 助理（assistant）

| 名字 | 触发示例 |
|------|----------|
| [**find-skills**](skills/assistant/find-skills/SKILL.md) | 帮我找一下 ClawHub 上有关 SEO 的 skill |
| [**markitdown**](skills/assistant/markitdown/SKILL.md) | 这个 PDF 转成 markdown |
| [**markdown-to-report**](skills/assistant/markdown-to-report/SKILL.md) | 把这份报告转成信息图风格 HTML |
| [**neat-freak**](skills/assistant/neat-freak/SKILL.md) | /neat（任务结束后整理文档和记忆） |
| [**obsidian**](skills/assistant/obsidian/SKILL.md) | 搜一下我的 Obsidian 笔记库 |
| [**obsidian-cli**](skills/assistant/obsidian-cli/SKILL.md) | 新建一条 Obsidian 笔记 |
| [**storage-analyzer**](skills/assistant/storage-analyzer/SKILL.md) | 帮我看看存储 / C盘满了 / 清理磁盘 |
| [**wechat-article-to-markdown**](skills/assistant/wechat-article-to-markdown/SKILL.md) | 这篇公众号文章转成 markdown |
| [**youtube-transcript**](skills/assistant/youtube-transcript/SKILL.md) | 这个 YouTube 视频的字幕拉下来 |

---

### 🎨 创意（creative）

| 名字 | 触发示例 |
|------|----------|
| [**khazix-writer**](skills/creative/khazix-writer/SKILL.md) | 用卡兹克的风格写篇公众号文章 |
| [**zhili-publish**](skills/creative/zhili-publish/SKILL.md) | 把这个 HTML 草稿发布到公众号 |
| [**zhilicomments**](skills/creative/zhilicomments/SKILL.md) | 发一条短评到公众号 |
| [**zhiligithub**](skills/creative/zhiligithub/SKILL.md) | 把这个 GitHub 项目写成公众号文章 |

---

### 🛠️ 开发（developer）

| 名字 | 触发示例 |
|------|----------|
| [**setup-matt-pocock-skills**](skills/developer/setup-matt-pocock-skills/SKILL.md) | 帮我装 Matt Pocock 的 Skill 规范 |
| [**skill-creator**](skills/developer/skill-creator/SKILL.md) | 帮我从零创建一个 skill |
| [**skill-github-sync**](skills/developer/skill-github-sync/SKILL.md) | 同步本地 skill 到 GitHub 仓库 |
| [**skill-maintenance**](skills/developer/skill-maintenance/SKILL.md) | 整理一下技能库 / 查重 |

---

### 📊 运营（operations）

| 名字 | 触发示例 |
|------|----------|
| [**aihot**](skills/operations/aihot/SKILL.md) | 今天 AI 圈有什么新东西 / 最近一周 AI 论文 |
| [**baoyu-url-to-markdown**](skills/operations/baoyu-url-to-markdown/SKILL.md) | 这个链接转成 markdown |
| [**geo-content-strategy**](skills/operations/geo-content-strategy/SKILL.md) | 做一下 GEO 内容策略 |
| [**geo-keyword-research**](skills/operations/geo-keyword-research/SKILL.md) | 帮我研究一下关键词 |
| [**geo-strategy-report**](skills/operations/geo-strategy-report/SKILL.md) | 生成一份 GEO 策略报告 |
| [**github-daily-trending**](skills/operations/github-daily-trending/SKILL.md) | 今天 GitHub 有什么黑马项目 |
| [**radar-daily-report**](skills/operations/radar-daily-report/SKILL.md) | 给我一份 Radar 日报 |
| [**radar-data-collection**](skills/operations/radar-data-collection/SKILL.md) | 舆情数据采集规范 |
| [**scrapling**](skills/operations/scrapling/SKILL.md) | 帮我爬这个网站 |
| **SEO 系列（25个）** | seo · seo-audit · seo-backlinks · seo-cluster · seo-competitor-pages · seo-content · seo-content-brief · seo-dataforseo · seo-drift · seo-ecommerce · seo-flow · seo-geo · seo-google · seo-hreflang · seo-image-gen · seo-images · seo-local · seo-maps · seo-page · seo-plan · seo-programmatic · seo-schema · seo-sitemap · seo-sxo · seo-technical |

---

### 📦 产品（product）

| 名字 | 触发示例 |
|------|----------|
| [**brand-product-audience-relevance**](skills/product/brand-product-audience-relevance/SKILL.md) | 分析这个品牌和 CID 人群的关联度 |
| [**competitor-discovery**](skills/product/competitor-discovery/SKILL.md) | 从这段 AI 回答里识别竞品 |
| [**hv-analysis**](skills/product/hv-analysis/SKILL.md) | 帮我研究一下这个公司 / 产品 |
| [**patent-disclosure-skill**](skills/product/patent-disclosure-skill/SKILL.md) | 生成一份专利交底书 |
| [**software-copyright-materials**](skills/product/software-copyright-materials/SKILL.md) | 生成软件著作权申请材料 |

---

## 🌟 关于

我是佳哥，这个 Skill 库里的技能都是我自己每天在项目里用的。如果对你有帮助，给个 ⭐ 就好。有问题或建议，欢迎在 Issues / Discussions 里说一声。

---

## ⭐ 支持这个项目

如果这个项目对你有用，可以通过以下方式支持：

- **给个 ⭐** — 在 GitHub 上 star 这个仓库
- **提 Issue** — 有问题或功能建议
- **贡献 Skill** — 一起完善这个技能库

---

<div align="center">

[MIT License](./LICENSE) · 自由使用 / 修改 / 再分发

Made by [@jacardl](https://github.com/jacardl)

</div>