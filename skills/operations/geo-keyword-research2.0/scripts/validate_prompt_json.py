#!/usr/bin/env python3
"""Validate GEO diagnostic frontend prompt JSON."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

VALID_CATEGORIES = {"品类问题", "场景问题", "品牌问题", "竞品比较问题"}
VALID_PRIORITIES = {"P1", "P2", "P3"}
OBSOLETE_CATEGORIES = {"品牌认知类", "推荐决策类", "竞品对比类", "预算价格类", "落地执行类", "风险合规类"}
VAGUE_COMPETITORS = {"头部厂商", "同类产品", "竞品", "其他", "主要竞品"}
MIN_REFERENCES = 100


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def load_context(path: str | None) -> dict[str, Any]:
    if not path:
        return {}
    return json.loads(Path(path).read_text(encoding="utf-8"))


def clean_list(items: Any) -> list[str]:
    if not isinstance(items, list):
        return []
    return [str(item).strip() for item in items if str(item).strip()]


def campaign_terms(campaigns: Any) -> list[str]:
    terms: list[str] = []
    if isinstance(campaigns, list):
        for item in campaigns:
            if isinstance(item, dict):
                terms.extend([str(item.get("name", "")).strip(), str(item.get("brief", "")).strip()])
            else:
                terms.append(str(item).strip())
    return [term for term in terms if term]


def contains_any(text: str, terms: list[str]) -> bool:
    return any(term and term in text for term in terms)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="JSON result file")
    parser.add_argument("--context", help="Context JSON with brand/product/competitors/campaigns/categories")
    parser.add_argument("--categories", help="Comma-separated selected categories")
    parser.add_argument("--strict-count", action="store_true", help="Require exactly 10 prompts per selected category")
    args = parser.parse_args()

    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    ctx = load_context(args.context)
    if not isinstance(data, dict):
        fail("top-level value must be an object")

    prompts = data.get("prompts")
    if not isinstance(prompts, list) or not prompts:
        fail("prompts must be a non-empty array")

    context_categories = clean_list(ctx.get("categories"))
    selected = [item.strip() for item in (args.categories or "").split(",") if item.strip()] or context_categories
    if not selected:
        selected = sorted({p.get("frameType") for p in prompts if isinstance(p, dict) and p.get("frameType")})
    invalid_selected = [item for item in selected if item not in VALID_CATEGORIES]
    if invalid_selected:
        fail(f"invalid selected categories: {', '.join(invalid_selected)}")

    brand = str(ctx.get("brand") or ctx.get("product") or "").strip()
    product = str(ctx.get("product") or brand).strip()
    brand_terms = [term for term in {brand, product, *clean_list(ctx.get("aliases"))} if term]
    competitors = [item for item in clean_list(ctx.get("competitors")) if item not in VAGUE_COMPETITORS]
    scene_terms = campaign_terms(ctx.get("campaigns"))

    counts: Counter[str] = Counter()
    seen_ids: set[str] = set()
    seen_prompts: set[str] = set()
    for index, prompt in enumerate(prompts, 1):
        if not isinstance(prompt, dict):
            fail(f"prompt #{index} must be an object")
        for field in ["id", "prompt", "frameType", "priority", "rationale", "evidenceNeeded"]:
            if not str(prompt.get(field, "")).strip():
                fail(f"prompt #{index} missing {field}")
        prompt_text = str(prompt["prompt"]).strip()
        frame = str(prompt["frameType"]).strip()
        if prompt["id"] in seen_ids:
            fail(f"duplicate prompt id: {prompt['id']}")
        if prompt_text in seen_prompts:
            fail(f"duplicate prompt text: {prompt_text}")
        seen_ids.add(prompt["id"])
        seen_prompts.add(prompt_text)
        if frame in OBSOLETE_CATEGORIES:
            fail(f"prompt #{index} uses obsolete category: {frame}")
        if frame not in selected:
            fail(f"prompt #{index} frameType not selected: {frame}")
        if prompt["priority"] not in VALID_PRIORITIES:
            fail(f"prompt #{index} invalid priority: {prompt['priority']}")
        if prompt_text.count("？") + prompt_text.count("?") > 1:
            fail(f"prompt #{index} must be a single question")

        if frame == "品牌问题" and brand_terms and not contains_any(prompt_text, brand_terms):
            fail(f"prompt #{index} 品牌问题 must include brand/product")
        if frame == "竞品比较问题":
            if brand_terms and not contains_any(prompt_text, brand_terms):
                fail(f"prompt #{index} 竞品比较问题 must include brand/product")
            if competitors and not contains_any(prompt_text, competitors):
                fail(f"prompt #{index} 竞品比较问题 must include a real competitor")
        if frame == "品类问题" and brand_terms and contains_any(prompt_text, brand_terms):
            fail(f"prompt #{index} 品类问题 must omit target brand/product")
        if frame == "场景问题":
            if brand_terms and contains_any(prompt_text, brand_terms):
                fail(f"prompt #{index} 场景问题 must omit target brand/product")
            if scene_terms and not contains_any(prompt_text + str(prompt.get("rationale", "")) + str(prompt.get("evidenceNeeded", "")), scene_terms):
                fail(f"prompt #{index} 场景问题 should use campaign/scene terms")

        counts[frame] += 1

    if args.strict_count:
        for category in selected:
            if counts[category] != 10:
                fail(f"{category} must have exactly 10 prompts, got {counts[category]}")

    artifacts = data.get("artifacts", {})
    if artifacts:
        if not isinstance(artifacts, dict):
            fail("artifacts must be an object")
        for field in ["promptAnalysisPath", "sourcesPath"]:
            path = str(artifacts.get(field, "")).strip()
            if not path:
                fail(f"artifacts missing {field}")
            if Path(path).is_absolute() or ".." in Path(path).parts:
                fail(f"artifacts.{field} must be workspace-relative")

    refs = data.get("references", [])
    if refs is not None and not isinstance(refs, list):
        fail("references must be an array")
    urls: set[str] = set()
    for index, ref in enumerate(refs or [], 1):
        if not isinstance(ref, dict):
            fail(f"reference #{index} must be an object")
        url = str(ref.get("url", "")).strip()
        if url and not url.startswith(("http://", "https://")):
            fail(f"reference #{index} url must be http(s): {url}")
        if url and "example.com" in url:
            fail(f"reference #{index} uses placeholder URL: {url}")
        if url:
            urls.add(url)
    if len(urls) < MIN_REFERENCES:
        fail(f"references must include at least {MIN_REFERENCES} unique URLs, got {len(urls)}")

    print(json.dumps({"ok": True, "counts": dict(counts), "references": len(urls)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
