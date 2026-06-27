<div align="center">

**中文** · [English](./README.en.md)

# 🧰 viceroy-skills

我自己每天在用的一些 AI 技能和 Prompt，都开源在这里。

[![License](https://img.shields.io/badge/License-MIT-3B82F6?style=for-the-badge)](./LICENSE)
[![Skills](https://img.shields.io/badge/Skills-108-10B981?style=for-the-badge)](#-skills)
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
| [**Legal** ⚖️](#-legal) | 法律推理能力库 — 检索→推理→论证→文书，清华智能法治研究院 |

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
| [**deductive-reasoning**](skills/ai/deductive-reasoning/SKILL.md) | 三段论 P-F-C 推理链 + 中项识别 + 谬误检测 |
| [**inductive-reasoning**](skills/ai/inductive-reasoning/SKILL.md) | 从具体案例提炼一般规则 |
| [**analogical-reasoning**](skills/ai/analogical-reasoning/SKILL.md) | 类比推理（法律漏洞填补） |
| [**legal-abductive-reasoning**](skills/ai/legal-abductive-reasoning/SKILL.md) | 溯因推理：证据不完整时的最佳解释 |
| [**counterfactual-reasoning**](skills/ai/counterfactual-reasoning/SKILL.md) | 反事实推理：因果认定/责任比例 |
| [**formal-legal-consequence**](skills/ai/formal-legal-consequence/SKILL.md) | 推理链终端：推导具体法律后果 |

---
### 🧑‍💼 Assistant

| Name | How to trigger |
|------|----------------|
| [**diary-write**](skills/assistant/diary-write/SKILL.md) | 写日记 / 向 Obsidian 写日记 / 我发给你位置 |
| [**find-skills**](skills/assistant/find-skills/SKILL.md) | 在 ClawHub 上找 SEO 相关 Skill |
| [**markitdown**](skills/assistant/markitdown/SKILL.md) | 把这个 PDF 转成 markdown |
| [**markdown-to-report**](skills/assistant/markdown-to-report/SKILL.md) | 把这个 markdown 转成带样式的 HTML 报告 |
| [**neat-freak**](skills/assistant/neat-freak/SKILL.md) | /neat — 整理本次会话的文档和记忆 |
| [**obsidian**](skills/assistant/obsidian/SKILL.md) | 搜索我的 Obsidian 笔记库 |
| [**obsidian-cli**](skills/assistant/obsidian-cli/SKILL.md) | 创建一条新 Obsidian 笔记 |
| [**storage-analyzer**](skills/assistant/storage-analyzer/SKILL.md) | 看看我的硬盘 / C 盘满了 / 清理一下 |
| [**wechat-article-to-markdown**](skills/assistant/wechat-article-to-markdown/SKILL.md) | 把这篇微信文章转成 markdown |
| [**youtube-transcript**](skills/assistant/youtube-transcript/SKILL.md) | 抓取这个 YouTube 视频的字幕 |
| [**legal-element-extraction**](skills/assistant/legal-element-extraction/SKILL.md) | 从非结构化文本提取法律事实（生活语言→法律语言） |
| [**structured-element-extraction**](skills/assistant/structured-element-extraction/SKILL.md) | 结构化要素清单，下游推理的质量闸门 |
| [**dispute-issue-identification**](skills/assistant/dispute-issue-identification/SKILL.md) | 争议焦点识别，排除无争议事项 |
| [**legal-concept-comprehension**](skills/assistant/legal-concept-comprehension/SKILL.md) | 法律概念解析、构成要件拆解 |
| [**legal-terminology**](skills/assistant/legal-terminology/SKILL.md) | 法律术语规范，贯穿所有输出 |
| [**evidence-evaluation**](skills/assistant/evidence-evaluation/SKILL.md) | 证据三性评估 + 证明力判断 |
| [**evidence-argument-chain**](skills/assistant/evidence-argument-chain/SKILL.md) | 主张→要件→证据→证明力完整映射 |
| [**argument-chain-construction**](skills/assistant/argument-chain-construction/SKILL.md) | 将推理组织为完整论证结构 |
| [**argument-strength-evaluation**](skills/assistant/argument-strength-evaluation/SKILL.md) | 论证强度/置信度评级 + 薄弱环节标注 |
| [**legal-document-formatting**](skills/assistant/legal-document-formatting/SKILL.md) | 裁判文书格式规范 |
| [**legal-document-summarization**](skills/assistant/legal-document-summarization/SKILL.md) | 判决/裁定结构化摘要 |
| [**multi-document-summarization**](skills/assistant/multi-document-summarization/SKILL.md) | 跨文档综合分析 |
| [**judgment-document-generation**](skills/assistant/judgment-document-generation/SKILL.md) | 复合能力：8步流水线生成完整判决书 |

---
### 🎨 Creative

| Name | How to trigger |
|------|----------------|
| [**khazix-writer**](skills/creative/khazix-writer/SKILL.md) | 用卡兹克的风格写一篇公众号文章 |
| [**renwei-writing**](skills/creative/renwei-writing/SKILL.md) | 打磨、润色、改写文案时保住人的存在感——位置+代价+手迹三件套，去 AI 味儿 |
| [**zhili-publish**](skills/creative/zhili-publish/SKILL.md) | 把这个 HTML 草稿发布到微信公众号 |
| [**zhilicomments**](skills/creative/zhilicomments/SKILL.md) | 发一条短评论到公众号 |
| [**zhiligithub**](skills/creative/zhiligithub/SKILL.md) | 把这个 GitHub 项目写成一篇公众号文章 |
| [**zhililong**](skills/creative/zhililong/SKILL.md) | 写 4000-5500 字公众号长文，自动对接 zhili-publish 推送到草稿箱 |
| [**guizang-ppt-skill**](skills/creative/guizang-ppt-skill/SKILL.md) | 生成横向翻页网页 PPT；触发：杂志风 PPT / 瑞士风 PPT / Swiss Style / horizontal swipe deck |
| [**xiaohu-ip-studio**](skills/creative/xiaohu-ip-studio/SKILL.md) | 给文章配图/正文配图/IP配图；自带31个原创IP角色生成正文解释图 |
| [**zhili-illustration**](skills/creative/zhili-illustration/SKILL.md) | 写作技能统一配图：读取HTML→shot list→IP配图→注入HTML→上传微信素材 |

---
### 🛠️ Developer

| Name | How to trigger |
|------|----------------|
| [**setup-matt-pocock-skills**](skills/developer/setup-matt-pocock-skills/SKILL.md) | 在 AGENTS.md 里配置 Matt Pocock 的 Skill 规范 |
| [**skill-creator**](skills/developer/skill-creator/SKILL.md) | 从零创建一个新 Skill |
| [**skill-github-sync**](skills/developer/skill-github-sync/SKILL.md) | 把本地 Skills 同步到 GitHub |
| [**skill-maintenance**](skills/developer/skill-maintenance/SKILL.md) | 整理 Skill 库 / 查重 / **安装前安全审计**（v2.1+ skillspector） |
| [**legal-interpretation-argument**](skills/developer/legal-interpretation-argument/SKILL.md) | 综合文义/体系/目的解释 |
| [**systematic-interpretation**](skills/developer/systematic-interpretation/SKILL.md) | 体系解释：规范在体系中的位置 |
| [**teleological-interpretation**](skills/developer/teleological-interpretation/SKILL.md) | 目的解释：条文目的论证 |
| [**normative-meaning-argumentation**](skills/developer/normative-meaning-argumentation/SKILL.md) | 规范目的与价值导向分析 |
| [**conflict-resolution**](skills/developer/conflict-resolution/SKILL.md) | 法条竞合/证据矛盾/法源冲突 |

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
| [**case-retrieval**](skills/operations/case-retrieval/SKILL.md) | 类案检索，查找相似判决与裁判规则 |
| [**legal-article-retrieval**](skills/operations/legal-article-retrieval/SKILL.md) | 法条检索，生成标准化检索报告 |
| [**other-legal-retrieval**](skills/operations/other-legal-retrieval/SKILL.md) | 立法背景、监管案例、行业标准、学术通说检索 |
| [**legal-norm-validity-check**](skills/operations/legal-norm-validity-check/SKILL.md) | 法条效力验证：现行有效、层级正确、无冲突 |

---


---
### 📦 Product

| Name | How to trigger |
|------|----------------|
| [**brand-product-audience-relevance**](skills/product/brand-product-audience-relevance/SKILL.md) | 分析这个品牌和 CID 人群数据的相关性 |
| [**competitor-discovery**](skills/product/competitor-discovery/SKILL.md) | 从这段 AI 回复里识别竞品 |
| [**hv-analysis**](skills/product/hv-analysis/SKILL.md) | 研究这个公司 / 产品 |
| [**research-synth**](skills/product/research-synth/SKILL.md) | 综合用户访谈 / Survey 开放题 / Synthetic User Q&A，生成产品洞察、机会 backlog、研究计划和知识图谱 |
| [**patent-disclosure-skill**](skills/product/patent-disclosure-skill/SKILL.md) | 通用中国专利挖掘、查新、技术交底书生成与自检；触发：专利挖掘 / 技术交底书 / patent-disclosure。 |
| [**software-copyright-materials**](skills/product/software-copyright-materials/SKILL.md) | 生成软件著作权申请材料 |
| [**legal-risk-assessment**](skills/product/legal-risk-assessment/SKILL.md) | 综合法律风险评估 |
| [**dispute-and-performance-risk**](skills/product/dispute-and-performance-risk/SKILL.md) | 合同争议与履约风险评估 |
| [**internal-compliance-risk-identification**](skills/product/internal-compliance-risk-identification/SKILL.md) | 内部合规风险识别 |
| [**case-lifecycle-planning**](skills/product/case-lifecycle-planning/SKILL.md) | 案件时间线与路线图 |
| [**billing-and-litigation-budget**](skills/product/billing-and-litigation-budget/SKILL.md) | 工时/费用/预算管理 |
| [**trial-scheduling-and-deadline-monitoring**](skills/product/trial-scheduling-and-deadline-monitoring/SKILL.md) | 开庭/举证/上诉期限跟踪 |
| [**strategic-risk-prioritization**](skills/product/strategic-risk-prioritization/SKILL.md) | 风险排序 + 资源战略性取舍 |
| [**administrative-value-judgment**](skills/product/administrative-value-judgment/SKILL.md) | 行政价值判断 |
| [**judicial-value-judgment**](skills/product/judicial-value-judgment/SKILL.md) | 司法价值判断 |
| [**legal-judgment-prediction**](skills/product/legal-judgment-prediction/SKILL.md) | 复合能力：调度多原子能力做裁决预测 |
---

## 🌟 关于

这是我的私人 Skill 库——每个 Skill 都在我自己项目里跑过足够久、确认真的省时间才开源的。没有噱头，只有实用。

如果你觉得有用，欢迎 ⭐。问题和建议欢迎提 Issue / Discussion。

---

<div align="center">

[MIT License](./LICENSE) · 随意使用、修改和分发

Made by [@jacardl](https://github.com/jacardl)

</div>
