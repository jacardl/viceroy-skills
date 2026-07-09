# Output Schema

## Frontend JSON mode

Return strict JSON only. No Markdown, no comments, no trailing commas.

Required top-level shape:

```json
{
  "tasks": ["string"],
  "prompts": [
    {
      "id": "p1",
      "prompt": "string",
      "frameType": "品类问题 | 场景问题 | 品牌问题 | 竞品比较问题",
      "priority": "P1 | P2 | P3",
      "rationale": "string",
      "evidenceNeeded": "string"
    }
  ],
  "artifacts": {
    "promptAnalysisPath": "final_report/brands/{brandId}/prompt-analysis.json",
    "sourcesPath": "final_report/brands/{brandId}/sources.json",
    "knowledgeBaseDir": "final_report/brands/{brandId}/brand_knowledge",
    "knowledgeBasePaths": ["final_report/brands/{brandId}/brand_knowledge/00_品牌总览.md"]
  },
  "references": [
    {
      "title": "string",
      "url": "https://...",
      "source": "string",
      "supportPoint": "string"
    }
  ],
  "coverageSummary": "string"
}
```

Validation rules:
- Every analysis run must save and merge `final_report/brands/{brandId}/prompt-analysis.json` for categorized prompts/data support/rationale, `final_report/brands/{brandId}/sources.json` for searched sources, `final_report/brands/{brandId}/research-trace.json` for configured preset calls, and `final_report/brands/{brandId}/brand_knowledge/*.md` for the Markdown knowledge base.
- Final frontend JSON must include brand-level `artifacts.promptAnalysisPath` and `artifacts.sourcesPath` so the frontend can read those files; include `knowledgeBaseDir` and `knowledgeBasePaths` when Markdown files are generated.
- Prompt questions must be calibrated against the generated `brand_knowledge/*.md`: use its positioning, audience, scenarios, campaign timing, competitor framing, `must_say`, and `must_not_say`; facts marked `待验证` may only become validation questions, not proven claims.
- `frameType` must exactly match one selected category.
- Default count is 10 prompts per selected category.
- `priority` must be `P1`, `P2`, or `P3`.
- `prompt` must be one standalone natural user question or search-like keyword, not an internal task label; do not combine multiple questions in one prompt.
- `references[].url` must be real and traceable. Frontend mode targets 20 de-duplicated source URLs but may return fewer real sources; full-research mode must include at least 100. Omit unknown URLs instead of inventing.
- `coverageSummary` must mention brand visibility, source coverage, competitor coverage, and next opportunity.

Category-specific validation:
- `品类问题`: must omit target brand/product names and aliases in `prompt`; ask category/selection/recommendation questions.
- `场景问题`: must omit target brand/product names and aliases in `prompt`; use product positioning plus campaign brief, audience, scenario, timing, or workflow in prompt/rationale/evidence.
- `品牌问题`: include target brand/product and focus on specific functions, scenarios, audience fit, trust, or evidence.
- `竞品比较问题`: include target brand/product and at least one concrete competitor; compare around concrete functions, scenarios, audiences, benefits, or differentiators.

Use `scripts/validate_prompt_json.py --input result.json --context context.json --strict-count` before returning if a file artifact exists.

## Artifact mode

When prompts and sources are collected separately, compile the frontend JSON with:

```bash
python3 scripts/compile_result.py \
  --prompts prompts.json \
  --sources sources.json \
  --context context.json \
  --output result.json
```

Then validate `result.json`.

## Markdown report mode

Use this format when the caller asks for a research report instead of frontend JSON.

```markdown
# GEO Keyword Research 2.0 Report - {品牌/产品}

## 数据源统计
- 搜索次数：N
- 去重 URL 数：M
- 抓取正文页数：K
- 选中问题分类：品类问题、场景问题
- 数据源文件：{path or 未写入文件}

## 品牌/产品理解
- 品牌定位：...
- 核心产品/服务：...
- 目标人群：...
- Campaign 信号：...
- 信息来源：
  - 来源名｜URL｜支持点

## 原始 GEO 关键词
### 第一类关键词（行业推荐型）- 10 个
1. 关键词文本
- 为什么选择：...
- GEO 策略：...

### 第二类关键词（品牌直指型）- 10 个
1. 关键词文本
- 为什么选择：...
- GEO 策略：...

## 按优先问题分类覆盖的关键词
### 分类：品类问题 - 10 个
1. keyword 文本
- 用户意图：...
- 为什么选择：...
- GEO 策略：...
- 高可信证据：
  - 来源名｜URL｜支持点：...
  - 来源名｜URL｜支持点：...
- 证据可信度：高 / 中高 / 中 / 待补
```

Quality rules:
- If evidence is incomplete, mark `证据可信度：待补` and name the missing source type.
- Do not turn diagnostic budget or rankings into guarantees.
