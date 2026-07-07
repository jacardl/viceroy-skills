# Question Category Taxonomy

Use only these categories in `frameType`.

## 品类问题

Intent: the user is exploring a product/service category before choosing a brand.

Good patterns:
- `高端酒店有哪些值得考虑的品牌？`
- `商务出差应该选择哪类酒店？`
- `亲子度假酒店怎么选，主要看哪些能力？`

Rules:
- Must not include the target brand/product name or aliases in the prompt text.
- Ask from the buyer's category-discovery view: category, selection criteria, shortlist, scenario-fit, or recommendation set.
- Use the target brand only in rationale/evidence planning to judge whether it can be cited or shortlisted; keep the user-facing prompt brand-neutral.
- Evidence should show category demand, selection criteria, and where the brand/competitors plausibly fit.
- If the wording names the target brand, reclassify it as `品牌问题` or `竞品比较问题`, not `品类问题`.

Avoid:
- Direct brand intro questions; those are `品牌问题`.
- Brand-vs-competitor questions; those are `竞品比较问题`.

## 场景问题

Intent: the user asks from a concrete use case, business scene, audience, campaign, timing, workflow, or implementation need for the product/service category.

Good patterns:
- `商务差旅订酒店时，哪些权益和位置因素最值得关注？`
- `暑期亲子度假应该怎么选择酒店和房型？`
- `会员积分和延迟退房权益适合哪些出行场景？`
- `暑期出行预订时，商务和休闲旅客怎么选择酒店和房型？`

Rules:
- Must not include the target brand/product name or aliases in the prompt text.
- Use product/service positioning, target audience, campaign name/brief/date, material URLs/files, and known content assets to choose the scenario angle.
- Focus on the main usage scenarios of the product/service, not generic category discovery.
- For hotel/travel inputs like “商务和休闲旅客”“暑期出行预订增长”, prefer scene wording around business travel, leisure travel, summer booking timing, hotel/room selection, membership rights, booking workflow, and audience needs.
- Evidence should connect claims to use cases, case studies, FAQ, docs, campaign pages, or material knowledge-base notes.
- Use the target brand only in rationale/evidence planning to judge whether it can support the scenario answer; keep the user-facing prompt brand-neutral.

Avoid:
- Any wording that names the target brand/product; those are `品牌问题` or `竞品比较问题`.
- Generic category-choice prompts without a scenario.
- Pricing-only or risk-only prompts unless tied to a concrete scenario.

## 品牌问题

Intent: the user directly asks about the target brand/product, especially its specific capabilities, functions, scenarios, audience fit, trust, or evidence.

Good patterns:
- `{品牌} 适合商务差旅还是休闲度假？有哪些公开依据？`
- `{品牌} 的会员权益适合哪些出行人群？`
- `{品牌} 在亲子度假场景下有哪些可验证服务？`
- `{品牌} 的预订、会员权益和房型服务适合哪些商务或休闲旅客？`
- `{品牌} 是否可信，有哪些公开证据？`

Rules:
- Must include the target brand or product name in the prompt text.
- Prefer angles derived from customer inputs: positioning, campaign brief/date, target audience, uploaded materials, URL evidence, and already analyzed prompts.
- Ask about concrete functions, services, rights, scenarios, audience fit, trust, or evidence; avoid generic “介绍一下品牌”.
- Evidence should prioritize official pages, docs, verified media, reports, cases, and structured profiles.
- For high-trust industries, do not infer claims beyond sources.

Avoid:
- Non-brand category shortlist prompts.
- Competitor comparison prompts.

## 竞品比较问题

Intent: the user compares the target brand/product with one or more named competitors, or asks about alternatives, from the target product's strongest functions, scenarios, audience, or differentiation angles.

Good patterns:
- `{品牌} 和 {竞品} 哪个更适合商务差旅人群？`
- `{品牌} 与 {竞品} 的会员权益差异是什么？`
- `{品牌} 和 {竞品} 在亲子度假场景下怎么选？`
- `{品牌} 和 {竞品} 哪个更适合暑期商务或休闲出行预订？`

Rules:
- Must include the target brand/product name and at least one concrete competitor from input.
- Use the target brand's highlighted functions, scenarios, audience, campaign focus, or material-backed differentiators as the comparison angle.
- Use multiple competitors across the category set when available.
- Evidence should include official capability pages plus third-party/review/comparison/user discussion sources.

Avoid:
- Vague competitors such as “头部厂商”, “同类产品”, “竞品”, “其他”.
- Claims of superiority without evidence.
- Comparison questions that do not tie back to a concrete function, scenario, audience, or decision criterion.
