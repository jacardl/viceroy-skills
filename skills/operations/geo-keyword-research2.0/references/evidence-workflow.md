# Evidence Workflow

Two modes share the same evidence standard.

- `frontend-json`: fast prompt-map JSON for the GEO diagnostic page.
- `full-research`: DAG search + source files + fetched pages + compiled artifacts.

## 0. Configured research models

This project provides Nanobot model presets in `nanobot-runtime/config.json`:

- `search` → search-combo, for query expansion, SERP/source discovery, and source candidate extraction.
- `fetch` → fetch-combo, for URL/page reading, extraction, and source summarization.
- `geoPrimary` → final synthesis and frontend JSON generation.

Use `model_preset_call(preset="search", prompt=...)` for every search/source-discovery phase and `model_preset_call(preset="fetch", prompt=...)` for every URL/page-reading phase. These configured presets are the联网检索/抓取执行层 for this skill.

## 1. Search DAG planning

Use `scripts/build_query_plan.py` when inputs are structured. It outputs:

- `taskId`
- `mode`
- `sourceTargets`
- `baseQueries`
- `dimensions[]`
- `fetchPolicy`
- `outputFiles`

Full-research mode must split search work by independent dimensions:

1. `brand_official` — required. Brand website or official profile.
2. `category_selection` — category choices and selection criteria.
3. `competitor_compare` — target brand vs named competitors.
4. `third_party_review` — media, reports, reviews.
5. `community_discussion` — Q&A, forum, social, user discussion.
6. `campaign_scene` — campaign brief, audience, use case, timing.

Use only dimensions relevant to the selected categories, but `brand_official` is always required.

## 2. Source targets and补搜 rules

Minimum targets:

| Mode | De-duplicated URLs | Per selected category | Fetch pages |
|---|---:|---:|---:|
| frontend-json | 100+ required | 10+ preferred | optional |
| full-research | 100+ required | 20+ preferred | 8-12 |

If any run has fewer than 100 de-duplicated URLs, perform补搜 before generating prompts.

For each dimension, call `search` separately so the result can be traced back to its category and intent. Ask the `search` preset to return only real titles/URLs/snippets and to omit unknown URLs instead of inventing them.

For each useful source, record:

- Display query
- Actual search query
- URL
- Title
- Source/site name
- Category supported
- Candidate prompt/keyword supported
- Support point in one sentence

Use `templates/data-url-template.md` for the final URL file. In frontend mode, also save the machine-readable source artifact to `prompt-artifacts/{taskId}/sources.json`; save categorized prompt/rationale/evidence output to `prompt-artifacts/{taskId}/prompt-analysis.json`. The final response must include both paths in `artifacts`.

## 3. Evidence priority

1. Official brand/product website, docs, FAQ, case pages
2. Authorities: regulators, associations, academic/industry reports
3. Trusted media, vertical media, third-party reviews
4. User discussion, Q&A, forums, social/community content

Never fabricate URLs. If evidence is missing, mark prompt as `待补来源` or make `evidenceNeeded` specific.

## 4. Fetching rules for full-research

Fetch 8-12 high-value pages through the configured `fetch` preset when tools allow.

Priority:
- at least one official source
- at least one third-party/review source
- at least one user/community source when available
- competitor sources for `竞品比较问题`
- campaign/source pages for `场景问题`

Failure controls:
- Fetch each URL at most once.
- Do not retry failed URLs.
- Stop after 3 consecutive fetch failures.
- Stop after 12 total fetch attempts.
- Continue with available content if enough source material exists.

## 5. Synthesis before prompt generation

Generate prompts after evidence synthesis, not before.

Input priority for prompt angles:
1. Brand/company name, product/service name, official website, and one-line positioning.
2. Campaign plan: name, brief, start/end date, audience, timing, channel, and key selling points.
3. Named competitors from the form.
4. Selected AI platforms and selected question categories.
5. Previously analyzed/exported prompts supplied by the user.
6. Existing content materials: selected material types, public URLs, uploaded files, and fetched/extracted page text.

These inputs must shape the prompt wording before category expansion. For example, a positioning like “面向商务和休闲旅客的国际酒店与度假住宿服务” plus a “暑期出行预订增长” campaign should produce scenario prompts around business travel, leisure travel, summer booking timing, hotel/room selection, membership rights, booking workflow, and travel audience needs — without naming the target brand in `场景问题`.

Before prompt generation, classify material evidence into a reusable brand/product knowledge-base note:
- Entity and positioning
- Main scenarios and audiences
- Functions/capabilities/benefits
- Campaign signals and timing
- Competitor/differentiation evidence
- Source URLs/files and confidence

Synthesize:
- Brand/entity understanding
- Category selection criteria
- Scenario/campaign fit
- Product usage scenarios and audience fit
- Competitor positioning
- Source gaps and confidence

## 6. Prompt generation rules

Each prompt needs:
- A real user phrasing
- A valid category (`frameType`)
- Priority (`P1` high business intent, `P2` useful, `P3` exploratory)
- Rationale tied to business value and AI visibility
- Evidence needed or existing evidence summary

Category-specific gates:
- `品类问题`: must omit target brand/product and aliases; focus on category choice.
- `场景问题`: must omit target brand/product and aliases; use product positioning plus campaign/scene/audience/workflow signals.
- `品牌问题`: must include target brand/product; ask about specific functions, scenarios, audience fit, trust, or evidence.
- `竞品比较问题`: must include target brand/product and at least one specific competitor; compare around concrete functions, scenarios, audience, or differentiators.

Reject or rewrite prompts that:
- Use obsolete categories
- Mix category intent too broadly
- Need unsupported factual claims
- Include fake URLs or vague sources
- Promise ranking/traffic/pricing outcomes

## 7. Confidence labels

Use:
- 高: multiple authoritative/official and third-party sources align
- 中高: official + one credible third-party source
- 中: one credible source plus plausible category logic
- 待补: useful prompt but insufficient source evidence; route to source repair
