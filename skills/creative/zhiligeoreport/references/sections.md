# 板块定义（v1.17 决策）

> v1.17 把行业从 8 个细分简化到 2 个互斥板块。代码改造（classify.py / weekly.html.j2）待跟进。

## 2 个板块

### 1. GEO 技术科普（`geo_tech_science`）
- GEO 概念 / 方法论 / 原理
- GEO 工具评测
- AI 搜索算法 / LLM 工作流
- Schema 标记 / 结构化数据
- Prompt 工程
- GEO 白皮书 / 行业研究报告

### 2. GEO 行业动态（`geo_industry_dynamics`）
- GEO 服务商动态
- 客户实战案例
- GEO 行业新闻
- GEO 大会 / 行业活动
- GEO 融资 / 投资
- 行业政策

## 不再细分行业的理由

- 8 行业细分（医药 / 金融 / 家电 / 汽车 / 餐饮 / 水果 / B2B SaaS / 电商）分类准确率 ~70%，人工调整成本高
- 边界案例多：
  - 「医药 GEO 五大底层原因」→ 归 GEO 技术科普还是处方药？
  - 「AI 推荐水果店」→ 归 GEO 技术科普还是本地服务？
- 2 板块互斥准确率接近 100%，避免 ai_tool / cross_industry 那种边界混淆

## 数据可追溯性

- `items.industry` 字段仍保留细分值（`geo_tech_science` / `geo_industry_dynamics`）用于数据回溯
- 但周报渲染只展示 2 板块标签
- 个别 item 仍可在标题前显示【细分】做上下文提示（如「【GEO 工具评测】」「【GEO 实战案例】」）

## 分类逻辑（`classify.py` 待实现）

```
classify_industry(title, body, source_industry):
  1. 信源 industry（已配置）
  2. 信源名硬映射
  3. GEO_TECH_SCIENCE_KEYWORDS 命中 → 'geo_tech_science'
  4. GEO_SERVICE_PROVIDER_KEYWORDS 命中 → 'geo_industry_dynamics'
  5. 兜底 'geo_industry_dynamics'
```

## v1.17 待办

- [ ] `classify.classify_industry` 改造：板块从 9 行业简化到 2 个
- [ ] `weekly.html.j2` 改造：模板只渲染 2 板块，移除 8 行业 IND_ORDER
- [ ] `classify.GEO_TECH_SCIENCE_KEYWORDS` + `GEO_SERVICE_PROVIDER_KEYWORDS` 重新整理
- [ ] `SPEC_ITEM_PIPELINE.md` §1.11 更新：板块分类规则文档化
- [ ] `SPEC_REPORT_TEMPLATE.md` 更新：模板结构文档化