<div align="center">

**中文** · English

# 🧰 Skillshub

#### 佳哥私人 Skill 库，按岗位分类，开箱即用

[![Skills](https://img.shields.io/badge/Skills-59-10B981?style=for-the-badge)](#-skills)
[![License](https://img.shields.io/badge/License-MIT-3B82F6?style=for-the-badge)](./LICENSE)

支持 Claude Code、Codex、OpenClaw 等 Agent

</div>

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

| 名字 | 一句话 |
|------|--------|
| [**find-skills**](skills/assistant/find-skills/SKILL.md) | 从 ClawHub / AgentSkills.io 搜索和安装 Skill |
| [**markitdown**](skills/assistant/markitdown/SKILL.md) | 把 PDF、Word、PPT、HTML 丢进去，出来干净 Markdown |
| [**markdown-to-report**](skills/assistant/markdown-to-report/SKILL.md) | 把 Markdown 转成排版精美的 HTML 报告（信息图风格） |
| [**neat-freak**](skills/assistant/neat-freak/SKILL.md) | 每次任务跑完，把文档、CLAUDE.md、Agent 记忆全部对齐一遍 |
| [**obsidian**](skills/assistant/obsidian/SKILL.md) | 读取、搜索、新建、编辑 Obsidian 笔记库 |
| [**obsidian-cli**](skills/assistant/obsidian-cli/SKILL.md) | Obsidian CLI 版本，支持所有主流 Obsidian 插件 |
| [**storage-analyzer**](skills/assistant/storage-analyzer/SKILL.md) | 一句话扫描 Mac / Windows 磁盘，三色分级，网页上一键清理 |
| [**wechat-article-to-markdown**](skills/assistant/wechat-article-to-markdown/SKILL.md) | 把微信公众号文章转成干净 Markdown |
| [**youtube-transcript**](skills/assistant/youtube-transcript/SKILL.md) | 拉 YouTube 字幕，按时间戳整理成结构化笔记 |

---

### 🎨 创意（creative）

| 名字 | 一句话 |
|------|--------|
| [**khazix-writer**](skills/creative/khazix-writer/SKILL.md) | 用卡兹克的写作风格写公众号长文（节奏、禁忌词、风格示例全有） |
| [**zhili-publish**](skills/creative/zhili-publish/SKILL.md) | 把 HTML 草稿发布到「直隶按察使」公众号，支持封面图、摘要、自动发布 |
| [**zhilicomments**](skills/creative/zhilicomments/SKILL.md) | 把短评发布到「独立小扎喝不醉每天都在天上飞」公众号 |
| [**zhiligithub**](skills/creative/zhiligithub/SKILL.md) | 把 GitHub 项目写成公众号文章（标题 + 介绍 + 要点） |

---

### 🛠️ 开发（developer）

| 名字 | 一句话 |
|------|--------|
| [**setup-matt-pocock-skills**](skills/developer/setup-matt-pocock-skills/SKILL.md) | 在 AGENTS.md 里一键搭建 Matt Pocock 的 Skill 规范 |
| [**skill-creator**](skills/developer/skill-creator/SKILL.md) | 从零创建一个符合规范的 Skill，包含 SKILL.md、references、scripts |
| [**skill-github-sync**](skills/developer/skill-github-sync/SKILL.md) | 把本地 Skill 同步到 GitHub 仓库，支持 README 自动生成 |
| [**skill-maintenance**](skills/developer/skill-maintenance/SKILL.md) | 整理技能库：分类、查重、清理低频技能 |

---

### 📊 运营（operations）

| 名字 | 一句话 |
|------|--------|
| [**aihot**](skills/operations/aihot/SKILL.md) | 每天 AI 圈动态：日报、精选条目、模型发布、产品动态 |
| [**baoyu-url-to-markdown**](skills/operations/baoyu-url-to-markdown/SKILL.md) | 把链接转成干净 Markdown（支持公众号、知乎、微博等） |
| [**geo-content-strategy**](skills/operations/geo-content-strategy/SKILL.md) | GEO 内容策略：覆盖度 × 权威性 × 信任度三维度 |
| [**geo-keyword-research**](skills/operations/geo-keyword-research/SKILL.md) | 从搜索和社交挖掘高频关键词，生成 10+10 GEO 关键词报告 |
| [**geo-strategy-report**](skills/operations/geo-strategy-report/SKILL.md) | GEO 策略报告：四象限矩阵、竞品分析、预算分配、执行路线图 |
| [**github-daily-trending**](skills/operations/github-daily-trending/SKILL.md) | 黑马发现引擎，多源项目选题 → 公众号文章全流程 |
| [**radar-daily-report**](skills/operations/radar-daily-report/SKILL.md) | Radar 日报：黄金价格 + AI 圈 + 国际大事件 |
| [**radar-data-collection**](skills/operations/radar-data-collection/SKILL.md) | Radar 数据采集规范：严谨、完整、有据可查 |
| [**scrapling**](skills/operations/scrapling/SKILL.md) | 自适应爬虫框架，处理 Cloudflare、反检测、动态内容 |
| **SEO 系列** | seo · seo-audit · seo-backlinks · seo-cluster · seo-competitor-pages · seo-content · seo-content-brief · seo-dataforseo · seo-drift · seo-ecommerce · seo-flow · seo-geo · seo-google · seo-hreflang · seo-image-gen · seo-images · seo-local · seo-maps · seo-page · seo-plan · seo-programmatic · seo-schema · seo-sitemap · seo-sxo · seo-technical（共 25 个） |

---

### 📦 产品（product）

| 名字 | 一句话 |
|------|--------|
| [**brand-product-audience-relevance**](skills/product/brand-product-audience-relevance/SKILL.md) | 品牌/产品 vs CID 人群数据分析：关联度、转化、Chi-Square 证据 |
| [**competitor-discovery**](skills/product/competitor-discovery/SKILL.md) | 从 AI 回答文本中高精度识别竞品，支持知识库持久化 |
| [**hv-analysis**](skills/product/hv-analysis/SKILL.md) | 横纵分析法：纵向追时间深度，横向追同期广度，万字 PDF 报告 |
| [**markdown-to-report**](skills/product/markdown-to-report/SKILL.md) | Markdown → 精美 HTML 报告（信息图风格） |
| [**patent-disclosure-skill**](skills/product/patent-disclosure-skill/SKILL.md) | 专利交底书生成：从会议纪要/架构文档提取技术方案，输出规范格式 |
| [**software-copyright-materials**](skills/product/software-copyright-materials/SKILL.md) | 软件著作权申请材料：从真实项目自动生成（操作手册 + 源码比对） |

---

共 6 个分类，59 个技能。