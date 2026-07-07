---
name: geo-keyword-research2.0
description: Evidence-backed GEO keyword and Prompt Map research for Chinese AI visibility. Use when asked to generate GEO keywords, AI-search prompts, prompt/question coverage, Nanobot prompt-map JSON, or grouped questions for 品类问题、场景问题、品牌问题、竞品比较问题; also use for this GEO diagnostic page's Step 3 prompt analysis.
---

# GEO Keyword Research 2.0

## Quick start

Required input: brand or product name. Prefer: website, industry, market, competitors, campaign plans, selected question categories, material/source hints.

Default categories when absent: `品类问题`, `竞品比较问题`.

Choose one mode:

- **frontend-json mode**: fast Step 3 response. Return strict JSON for the GEO diagnostic page.
- **full-research mode**: evidence-heavy research. Use DAG search, source files, fetches, then compile JSON/report.

Use bundled resources:

- Build the search DAG: `python3 scripts/build_query_plan.py --input context.json --output query-plan.json`
- Search with configured preset: `model_preset_call(preset="search", prompt="...")`
- Fetch/read source pages with configured preset: `model_preset_call(preset="fetch", prompt="...")`
- Validate frontend JSON: `python3 scripts/validate_prompt_json.py --input result.json --context context.json --strict-count`
- Compile frontend JSON from prompt/source artifacts: `python3 scripts/compile_result.py --prompts prompts.json --sources sources.json --output result.json`
- URL table template: `templates/data-url-template.md`
- Category definitions: `references/category-taxonomy.md`
- Output formats: `references/output-schema.md`
- Evidence workflow: `references/evidence-workflow.md`

## Workflow

1. Normalize inputs.
   - Trim brand/product/competitors/campaigns.
   - Record brand aliases if provided or discovered; final prompts should use the user-facing brand name.
   - Use only current categories: `品类问题`, `场景问题`, `品牌问题`, `竞品比较问题`.
   - Never emit old categories: `品牌认知类`, `推荐决策类`, `竞品对比类`, `预算价格类`, `落地执行类`, `风险合规类`.
2. Build a query plan.
   - Use `build_query_plan.py` for any structured task.
   - In full-research mode, assign one independent dimension per search subtask and write source records.
3. Collect and persist evidence.
   - Use `model_preset_call(preset="search", prompt=...)` for query-plan searches; it reads the configured `search` model preset from `nanobot-runtime/config.json`.
   - Full mode: write sources to `{workspace}/geo-keyword-research2.0/{task_id}/{task_id}_urls.md` using `templates/data-url-template.md`.
   - Every run must collect at least 100 unique, real, traceable source URLs before prompt generation; if sources are weak, continue补搜 rather than inventing URLs.
4. Fetch and synthesize.
   - Use `model_preset_call(preset="fetch", prompt=...)` for URL/page reading and source summarization; it reads the configured `fetch` model preset from `nanobot-runtime/config.json`.
   - Full mode: fetch 8-12 high-value pages with the failure limits in `references/evidence-workflow.md`.
   - Frontend mode: do not stall on exhaustive fetch; prefer concise source-backed prompts.
5. Generate questions/keywords.
   - Frontend JSON: return strict JSON only; no Markdown fences.
   - Full report: use `references/output-schema.md` Markdown report format.
   - Default count: 10 natural-language prompts per selected category.
   - Each prompt must be one standalone question only; do not combine multiple questions in one prompt or use multiple question marks.
   - Base every prompt angle on customer inputs first: brand/company, product/service, website, positioning, audience, campaign name/date/brief, competitors, AI platforms, existing/analyzed prompts, material URLs/files, and content types.
   - For `品类问题`, ask category-choice/recommendation/selection-standard questions and never put the target brand/product name or aliases in `prompt`.
   - For `场景问题`, ask about the product/service's main use cases, audiences, timing, workflows, or campaign scenarios; never put the target brand/product name or aliases in `prompt`.
   - For `品牌问题`, include the target brand/product and focus on specific functions, specific scenarios, audience fit, trust, or public evidence.
   - For `竞品比较问题`, include target brand/product plus a named competitor, comparing around the target product's strongest functions, scenarios, audiences, benefits, rights, or differentiators.
6. Validate and compile.
   - Run or mentally apply `validate_prompt_json.py` before returning frontend JSON.
   - Use `compile_result.py` when prompt and source artifacts are separate.

## Category intent

Keep short definitions here; read `references/category-taxonomy.md` for examples and anti-patterns.

- `品类问题`: non-brand category/category-choice questions. Must omit the target brand/product name in the user-facing prompt.
- `场景问题`: brand-neutral use-case/audience/campaign/timing/workflow questions for the product/service's main usage scenarios.
- `品牌问题`: direct target-brand questions about specific functions, scenarios, audience fit, trust, evidence, or sourceability.
- `竞品比较问题`: target brand vs named competitors, comparing concrete functions, scenarios, audiences, benefits, or differentiators.

## Output contract for frontend-json mode

Save two workspace files for every run, then return exactly this shape:

- `prompt-artifacts/{taskId}/prompt-analysis.json`: categorized prompts, rationale, evidence/data support, optional `supportingSourceUrls[]`.
- `prompt-artifacts/{taskId}/sources.json`: all searched source records, at least 100 unique URLs.

```json
{
  "tasks": ["正在搜索官网与第三方来源"],
  "artifacts": {
    "promptAnalysisPath": "prompt-artifacts/{taskId}/prompt-analysis.json",
    "sourcesPath": "prompt-artifacts/{taskId}/sources.json"
  },
  "prompts": [
    {
      "id": "p1",
      "prompt": "自然语言问题或 keyword",
      "frameType": "品类问题",
      "priority": "P1",
      "rationale": "为什么值得优先验证",
      "evidenceNeeded": "需要哪些可信证据支持回答"
    }
  ],
  "references": [
    {
      "title": "来源标题",
      "url": "https://source.example.org",
      "source": "来源网站",
      "supportPoint": "该来源支持了什么判断"
    }
  ],
  "coverageSummary": "整体占有率、引用覆盖、竞品覆盖和品牌机会"
}
```

## Quality bar

- Use real, traceable sources; no placeholder URLs.
- Do not promise rankings, traffic, conversion, or final pricing.
- Budget/high-trust topics are diagnostic only; mark medical/financial/legal/education claims for consultant or compliance review.
- If evidence is weak, prefer fewer confident claims over invented confidence.
