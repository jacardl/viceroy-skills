# Brand/Product Knowledge Base

Generate this Markdown knowledge base before frontend JSON prompt generation whenever customer materials, website, campaign brief, competitors, or public sources are provided.

Output directory:

```text
final_report/brands/{brandId}/brand_knowledge/
├── 00_品牌总览.md
├── 01_产品服务定位.md
├── 02_campaign_brief.md
├── 03_目标人群与场景.md
├── 04_核心卖点.md
├── 05_竞品对比.md
├── 06_FAQ与推荐话术.md
├── 07_事实参数与约束.md
└── 08_来源素材索引.md
```

`brandId` comes from `scripts/build_query_plan.py`. It is stable for the same brand across repeated runs.

## Rules

- Use only customer input, uploaded files, official website, material URLs, fetched pages, and real searched sources.
- Before writing, read existing pages in `final_report/brands/{brandId}/brand_knowledge/` and update the same files in place.
- Preserve verified existing claims, add new evidence/claims, and mark unresolved conflicts as `待验证`; do not silently replace existing brand knowledge.
- Every important claim must include evidence: URL, uploaded file name/path, or `待验证`.
- Keep pages reusable: concise bullets, tables, and source mapping; no long pasted raw source text.
- Do not promise rankings, traffic, final pricing, or regulated claims.
- If a section has no evidence, create it anyway and mark missing items as `待验证` / `待补素材`.

## Page templates

### 00_品牌总览.md

```markdown
# 品牌 / 产品知识库总览

## 1. 一句话定位
> 

## 2. Campaign 目标
| Campaign | 时间 | 业务目标 | 优先场景 | 证据 |
|---|---|---|---|---|
|  |  |  |  |  |

## 3. 目标用户
- 

## 4. 核心卖点
| 卖点 | 证据来源 | 优先级 | 对应 Prompt / 问题场景 |
|---|---|---|---|
|  |  | P0/P1/P2 |  |

## 5. must_say
- 

## 6. must_not_say / 风险约束
- 

## 7. 竞品差异化
| 竞品 | 竞品优势 | 本品应对话术 | 证据来源 |
|---|---|---|---|
|  |  |  |  |

## 8. 素材缺口
| 缺口 | 影响 | 建议补充内容 | 优先级 |
|---|---|---|---|
|  |  |  | P0/P1/P2 |
```

### Source index pattern

For `08_来源素材索引.md`, include one row per unique URL or uploaded file path:

```markdown
# 来源素材索引

| 编号 | 标题 / 文件名 | 类型 | URL / 文件路径 | 支持信息 | 可信度 |
|---|---|---|---|---|---|
| S001 |  | official/campaign/product_doc/press/media/social/sales/other |  |  | 官方/第三方/用户生成/待验证 |
```

## Classification tags

Source type: `official`, `campaign`, `product_doc`, `press`, `media`, `social`, `sales`, `other`.

Content themes: `品牌定位`, `产品卖点`, `目标人群`, `使用场景`, `价格权益`, `服务能力`, `竞品对比`, `FAQ`, `事实参数`, `口碑背书`.

Priority: `P0` must enter diagnosis and prompt generation; `P1` important support; `P2` background; `P3` low priority or unverified.
