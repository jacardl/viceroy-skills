# 章节划分（v1.19 决策）

> v1.19 决策：按 GEO 生态角色划分 5 个互斥章节；内参板块上限 25，非内参 12；宁缺毋滥。

## 5 个章节

### 1. GEO 服务商动态（`geo_service_provider`）
- 只保留中性 GEO 服务公司新闻（融资 / 合作 / 收购 / 上市 / 财报）
- 保留 GEO 服务商市场份额 / 行业格局（非软广榜单）
- 剔除榜单、推荐、排名、哪家好、怎么选、选择指南、选型、报价、费用、服务方案、获客、厂商自夸、GEO 公司/优化服务落地页等营销稿

### 2. 品牌方实战（`brand_practice`）
- 具体品牌应用 GEO 的案例（金融 / 医疗 / 法律 / 教育 / 零售 等行业落地）
- 品牌方投放 GEO 服务的决策 / 效果 / ROI
- E-E-A-T 信任链在品牌侧的实践

### 3. 工具平台更新（`tool_platform`）
- AI 搜索产品功能更新（ChatGPT / Claude / Gemini / Perplexity / 豆包 / DeepSeek / 元宝 / Kimi / 文心）
- Schema 标记工具 / 结构化数据产品
- SEO/GEO 工具厂商动态（Ahrefs / Semrush / Shopify GEO / Botify 等）

### 4. 行业研究与数据（`industry_research`）
- 行业白皮书 / 研究报告（艾瑞咨询 / Gartner / McKinsey / IDC / 麦肯锡）
- GEO 行业市场规模 / 增长率数据
- 学界 / 学术研究论文
- 行业政策 / 监管动态

### 5. 国际市场（`international_market`）
- 海外 GEO 实战案例（北美 / 欧洲 / 东南亚 / 日韩）
- 跨境电商 GEO 优化（Shopify / DTC 品牌 / TikTok Shop）
- 海外 GEO 服务商动态（非中文市场）

## 为什么按角色分

- B2B 受众（品牌方 / 服务商 / 工具方 / 行业研究者）最容易按生态角色理解内容
- 章节数量稳定（5 个），读者可预期
- 每个角色章节对应一类商业决策，便于做 newsletter 的"角色化推荐"
- 比 v1.17 的"内容类型"分法更精准：v1.17 行业动态太杂，按角色划分后密度均匀

## 数据可追溯性

- `items.industry` 字段保留章节 ID（`geo_service_provider` / `brand_practice` / `tool_platform` / `industry_research` / `international_market`）
- 单条 item 只属于一个章节（互斥分配）
- 标题前 label 从标题动态抽取品牌/行业词（如「阿里·搜索」），失败才回退章节名。

## 分类逻辑（`classify.py` 已实现）

```
classify_industry(title, body, source_industry):
  1. 信源 industry（已配置，如 shopify → ecommerce）
  2. 信源名硬映射
  3. 关键词命中表：
     - 'geo_service_provider' ← 中性服务商动态 / 融资 / 合作 / 收购 / 上市 / 市场份额（营销稿剔除）
     - 'brand_practice' ← 实战 / 案例 / 客户 / ROI / 落地
     - 'tool_platform' ← 工具 / 平台 / 功能更新 / App / 插件 / 上线
     - 'industry_research' ← 白皮书 / 报告 / 研究 / 论文 / 政策 / 监管
     - 'international_market' ← 海外 / 跨境 / 出海 / 东南亚 / 北美
  4. 兜底 'industry_research'
```

## v1.18.1 状态

- [x] `classify.classify_industry` 已改成 5 角色（替换 v1.17 旧章节链）
- [x] `weekly.html.j2` 已按 section 渲染 5 章节并过滤空章节
- [x] `classify.SECTION_KEYWORDS` 已维护 5 个章节关键词表
- [x] `SPEC_ITEM_PIPELINE.md` §1.22 / §1.61 已记录总结失败不得截原文
- [x] `SPEC_REPORT_TEMPLATE.md` 已记录模板章节结构

## v1.19 状态

- [x] `obsidian_vault.SUBDIRS["raw/wechat"]` 标记 `internal_brief=True`
- [x] `scripts/13_render_only.py` 按 `source_weight` 加权排序（内参 × 3.0）
- [x] 内参板块上限 25，非内参 12
- [x] 生产级质量门槛：标题 ≥ 10 字、正文 ≥ 300 字、中文占比 ≥ 30%
- [x] obsidian 转载首行裸 URL 自动跳过，向下取 `# ` 标题
- [x] `SPEC_ITEM_PIPELINE.md` §1.64 / §1.65 已记录

## v1.22 状态

- [x] 章节选择仍为 5 角色，标题前 label 不直接使用章节名
- [x] obsidian 入选项必须最近 7 天创建，`mtime` 不作依据
- [x] 外部搜索入选项必须有最近 7 天原文发布时间
