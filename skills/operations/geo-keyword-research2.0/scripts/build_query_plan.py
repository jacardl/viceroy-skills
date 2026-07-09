#!/usr/bin/env python3
"""Build deterministic GEO keyword research query/DAG plans."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

CATEGORIES = ["品类问题", "场景问题", "品牌问题", "竞品比较问题"]
DEFAULT_CATEGORIES = ["品类问题", "竞品比较问题"]
DEFAULT_WORKSPACE = "final_report"
UNSAFE_PATH_CHARS = re.compile(r"[\\/:*?\"<>|\x00-\x1f]+")


def clean_list(items: Any) -> list[str]:
    if not isinstance(items, list):
        return []
    return [str(item).strip() for item in items if str(item).strip()]


def slug(value: str) -> str:
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()[:8]
    return f"geo_{digest}"


def safe_path_segment(value: str) -> str:
    name = " ".join(value.strip().split())
    name = UNSAFE_PATH_CHARS.sub("-", name).strip(" .-")
    return name or slug(value)


def website_host(value: str) -> str:
    if not value.strip():
        return ""
    parsed = urlparse(value if "://" in value else f"https://{value}")
    return (parsed.netloc or parsed.path.split("/")[0]).strip().lower()


def normalize_identity(value: str) -> str:
    return " ".join(value.strip().casefold().split())


def canonical_brand(ctx: dict[str, Any]) -> str:
    brand = str(ctx.get("brand") or "").strip()
    product = str(ctx.get("product") or "").strip()
    host = website_host(str(ctx.get("website") or ctx.get("websiteUrl") or ""))
    return brand or product or host or "unknown-brand"


def brand_id(ctx: dict[str, Any]) -> str:
    return safe_path_segment(canonical_brand(ctx))


def campaign_text(campaigns: Any) -> str:
    if not isinstance(campaigns, list):
        return ""
    parts: list[str] = []
    for item in campaigns:
        if isinstance(item, dict):
            text = f"{item.get('name', '')} {item.get('brief', '')}".strip()
        else:
            text = str(item).strip()
        if text:
            parts.append(text)
    return "；".join(parts)


def aliases(ctx: dict[str, Any]) -> list[str]:
    values = clean_list(ctx.get("aliases"))
    brand = str(ctx.get("brand") or ctx.get("product") or "").strip()
    if brand and brand not in values:
        values.insert(0, brand)
    return values


def q(display: str, actual: str, category: str, intent: str) -> dict[str, str]:
    return {"displayQuery": display, "query": actual, "category": category, "intent": intent}


def dimension_queries(category: str, ctx: dict[str, Any]) -> list[dict[str, str]]:
    brand = str(ctx.get("brand") or ctx.get("product") or "").strip()
    product = str(ctx.get("product") or brand).strip()
    market = str(ctx.get("market") or "中国大陆中文").strip()
    competitors = clean_list(ctx.get("competitors"))
    campaign = campaign_text(ctx.get("campaigns"))
    alias_values = aliases(ctx)
    search_brand = alias_values[0] if alias_values else brand or product
    category_label = str(ctx.get("category") or ctx.get("industry") or "目标品类").strip()
    if not category_label or category_label == brand or category_label == product:
        category_label = "目标品类"

    if category == "品类问题":
        return [
            q(f"{category_label} 怎么选", f"{category_label} 怎么选 推荐 品牌 {market}", category, "category_selection"),
            q(f"{category_label} 选择标准", f"{category_label} 评测 对比 选择标准", category, "third_party_criteria"),
            q(f"{category_label} 用户讨论", f"{category_label} 哪个好 用户 讨论", category, "community_questions"),
        ]
    if category == "场景问题":
        scene = campaign or f"{category_label} 使用场景"
        return [
            q(scene, f"{scene} {search_brand} {product}".strip(), category, "campaign_scene"),
            q(f"{category_label} 场景案例", f"{category_label} 场景 解决方案 案例", category, "use_case"),
            q(f"{brand or product} 落地流程", f"{search_brand or product} 怎么使用 流程 案例".strip(), category, "implementation"),
        ]
    if category == "品牌问题":
        return [
            q(f"{brand or product} 官网", f"{search_brand or product} 官网 产品 服务".strip(), category, "official_entity"),
            q(f"{brand or product} 可信度", f"{search_brand or product} 评价 资质 案例".strip(), category, "brand_trust"),
            q(f"{brand or product} 是什么", f"{search_brand or product} 是什么 适合谁".strip(), category, "brand_faq"),
        ]

    competitor = competitors[0] if competitors else "主要竞品"
    competitor_line = " ".join(competitors[:3]) if competitors else competitor
    return [
        q(f"{brand or product} vs {competitor}", f"{search_brand or product} {competitor} 对比 哪个好".strip(), category, "direct_comparison"),
        q(f"{competitor} 替代方案", f"{competitor} 替代方案 {search_brand or product}".strip(), category, "alternatives"),
        q(f"{brand or product} 竞品评测", f"{search_brand or product} {competitor_line} 评测 对比".strip(), category, "competitor_reviews"),
    ]


def build_dimensions(categories: list[str], ctx: dict[str, Any]) -> list[dict[str, Any]]:
    brand = str(ctx.get("brand") or ctx.get("product") or "").strip()
    website = str(ctx.get("website") or ctx.get("websiteUrl") or "").strip()
    host = website_host(website)
    dims: list[dict[str, Any]] = [{
        "id": "brand_official",
        "required": True,
        "category": "品牌问题" if "品牌问题" in categories else categories[0],
        "queries": [
            q(f"{brand} 官网", f"{brand} 官网".strip(), "品牌问题", "brand_official"),
            *([q(f"{brand} site", f"site:{host} {brand}".strip(), "品牌问题", "official_site")] if host else []),
        ],
        "writeTo": "{taskId}_search_01.tmp.md",
    }]

    seen = {"brand_official"}
    for category in categories:
        for item in dimension_queries(category, ctx):
            dim_id = item["intent"]
            if dim_id in seen:
                continue
            seen.add(dim_id)
            dims.append({
                "id": dim_id,
                "required": category in {"品牌问题", "竞品比较问题"},
                "category": category,
                "queries": [item],
                "writeTo": f"{{taskId}}_search_{len(dims) + 1:02d}.tmp.md",
            })
    return dims


def build_plan(ctx: dict[str, Any], mode: str, workspace: str) -> dict[str, Any]:
    categories = [c for c in clean_list(ctx.get("categories")) if c in CATEGORIES] or DEFAULT_CATEGORIES
    brand = str(ctx.get("brand") or ctx.get("product") or "").strip()
    task_id = str(ctx.get("taskId") or slug(json.dumps(ctx, ensure_ascii=False, sort_keys=True)))
    brand_name = canonical_brand(ctx)
    brand_slug = brand_id(ctx)
    out_dir = f"{workspace}/brands/{brand_slug}"
    min_urls = 100 if mode == "full-research" else 1
    target_urls = 100 if mode == "full-research" else 20
    per_category = 20 if mode == "full-research" else 10

    return {
        "taskId": task_id,
        "brandId": brand_slug,
        "brandName": brand_name,
        "mode": mode,
        "brand": brand,
        "categories": categories,
        "aliases": aliases(ctx),
        "sourceTargets": {
            "minDedupUrls": min_urls,
            "targetDedupUrls": target_urls,
            "minUrlsPerCategory": per_category,
            "fetchPages": "8-12" if mode == "full-research" else "optional",
        },
        "executionContract": {
            "searchPreset": "search",
            "fetchPreset": "fetch",
            "searchTool": "model_preset_call",
            "fetchTool": "model_preset_call",
            "requiredTraceFile": f"{out_dir}/research-trace.json",
            "forbiddenAsPrimarySearch": ["web_search"],
            "minThirdPartySources": 1 if mode == "frontend-json" else 5,
        },
        "dimensions": build_dimensions(categories, ctx),
        "fetchPolicy": {
            "maxAttempts": 12,
            "maxConsecutiveFailures": 3,
            "retrySameUrl": False,
        },
        "outputFiles": {
            "directory": out_dir,
            "urls": f"{out_dir}/urls.md",
            "report": f"{out_dir}/report.md",
            "frontendJson": f"{out_dir}/result.json",
            "promptAnalysis": f"{out_dir}/prompt-analysis.json",
            "sourcesJson": f"{out_dir}/sources.json",
            "researchTrace": f"{out_dir}/research-trace.json",
            "knowledgeBaseDir": f"{out_dir}/brand_knowledge",
            "runScratchDir": f"{workspace}/runs/{task_id}",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Input context JSON")
    parser.add_argument("--output", help="Output query plan JSON")
    parser.add_argument("--mode", choices=["frontend-json", "full-research"], default="frontend-json")
    parser.add_argument("--workspace", default=DEFAULT_WORKSPACE, help="Relative workspace output directory")
    args = parser.parse_args()

    ctx = json.loads(Path(args.input).read_text(encoding="utf-8"))
    plan = build_plan(ctx, args.mode, args.workspace)
    payload = json.dumps(plan, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)


if __name__ == "__main__":
    main()
