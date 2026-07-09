#!/usr/bin/env python3
"""Compile frontend GEO prompt JSON from prompt and source artifacts."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

DEFAULT_TASKS = [
    "接收任务与读取品牌信息",
    "搜索官网、竞品和第三方来源",
    "抓取核心页面并整理证据",
    "沉淀品牌/产品知识库",
    "生成 Prompt、参考 URL 和覆盖结论",
]


def load_json(path: str | None, default: Any) -> Any:
    if not path:
        return default
    return json.loads(Path(path).read_text(encoding="utf-8"))


def normalize_prompts(value: Any) -> list[dict[str, str]]:
    items = value.get("prompts", value) if isinstance(value, dict) else value
    if not isinstance(items, list):
        return []
    prompts: list[dict[str, str]] = []
    for index, item in enumerate(items, 1):
        if not isinstance(item, dict):
            continue
        prompt = str(item.get("prompt") or item.get("keyword") or "").strip()
        frame = str(item.get("frameType") or item.get("category") or "").strip()
        if not prompt or not frame:
            continue
        prompts.append({
            "id": str(item.get("id") or f"p{index}"),
            "prompt": prompt,
            "frameType": frame,
            "priority": str(item.get("priority") or "P2"),
            "rationale": str(item.get("rationale") or item.get("why") or "基于已选分类和公开证据生成"),
            "evidenceNeeded": str(item.get("evidenceNeeded") or item.get("evidence") or "官网、第三方评测、案例或社区讨论"),
        })
    return prompts


def normalize_sources(value: Any) -> list[dict[str, str]]:
    if isinstance(value, dict):
        items = value.get("references") or value.get("sources") or []
    else:
        items = value
    if not isinstance(items, list):
        return []
    refs: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        url = str(item.get("url") or item.get("URL") or "").strip()
        if not url or url in seen:
            continue
        seen.add(url)
        refs.append({
            "title": str(item.get("title") or item.get("页面标题") or url),
            "url": url,
            "source": str(item.get("source") or item.get("来源网站") or ""),
            "supportPoint": str(item.get("supportPoint") or item.get("支持点") or item.get("note") or ""),
        })
    return refs


def merge_prompts(existing: list[dict[str, str]], new: list[dict[str, str]]) -> list[dict[str, str]]:
    merged: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for item in [*existing, *new]:
        key = (item["frameType"], item["prompt"])
        if key in seen:
            continue
        seen.add(key)
        merged.append({**item, "id": f"p{len(merged) + 1}"})
    return merged


def write_urls_markdown(path: Path, refs: list[dict[str, str]]) -> None:
    lines = [
        "# 品牌级信源链接",
        "",
        "| # | 标题 | URL | 来源 | 支持点 |",
        "|---:|---|---|---|---|",
    ]
    for index, ref in enumerate(refs, 1):
        lines.append(f"| {index} | {ref['title']} | {ref['url']} | {ref['source']} | {ref['supportPoint']} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def sources_from_csv(path: str) -> list[dict[str, str]]:
    with Path(path).open(encoding="utf-8", newline="") as f:
        return normalize_sources(list(csv.DictReader(f)))


def coverage_summary(prompts: list[dict[str, str]], refs: list[dict[str, str]], context: dict[str, Any]) -> str:
    brand = str(context.get("brand") or context.get("product") or "目标品牌")
    categories = sorted({item["frameType"] for item in prompts})
    competitors = context.get("competitors") if isinstance(context.get("competitors"), list) else []
    competitor_text = "、".join(str(item) for item in competitors[:3]) or "主要竞品"
    return (
        f"本次围绕 {brand} 生成 {len(prompts)} 条 Prompt，覆盖 {', '.join(categories) or '未指定分类'}。"
        f"参考来源 {len(refs)} 个，用于判断品牌可见度、引用覆盖和与 {competitor_text} 的比较机会。"
        "证据不足的 Prompt 应优先进入来源补齐或顾问复核。"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompts", required=True, help="Prompt JSON/list file")
    parser.add_argument("--sources", help="Sources JSON file")
    parser.add_argument("--sources-csv", help="Sources CSV file")
    parser.add_argument("--context", help="Context JSON")
    parser.add_argument("--output", required=True, help="Output frontend result JSON")
    parser.add_argument("--artifact-dir", help="Workspace-relative directory for prompt-analysis.json and sources.json")
    args = parser.parse_args()

    prompt_data = load_json(args.prompts, [])
    prompts = normalize_prompts(prompt_data)
    source_data = sources_from_csv(args.sources_csv) if args.sources_csv else load_json(args.sources, [])
    refs = normalize_sources(source_data)
    context = load_json(args.context, {})

    artifacts = None
    if args.artifact_dir:
        artifact_dir_arg = Path(args.artifact_dir)
        if artifact_dir_arg.is_absolute() or ".." in artifact_dir_arg.parts:
            raise SystemExit("--artifact-dir must be workspace-relative")
        artifact_dir = artifact_dir_arg
        artifact_dir.mkdir(parents=True, exist_ok=True)
        prompt_path = artifact_dir / "prompt-analysis.json"
        source_path = artifact_dir / "sources.json"
        urls_path = artifact_dir / "urls.md"
        existing_prompts = normalize_prompts(load_json(str(prompt_path), {})) if prompt_path.exists() else []
        existing_refs = normalize_sources(load_json(str(source_path), {})) if source_path.exists() else []
        prompts = merge_prompts(existing_prompts, prompts)
        refs = normalize_sources({"references": [*existing_refs, *refs]})
        prompt_path.write_text(json.dumps({"prompts": prompts}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        source_path.write_text(json.dumps({"references": refs}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        write_urls_markdown(urls_path, refs)
        knowledge_base_dir = artifact_dir / "brand_knowledge"
        knowledge_base_paths = sorted(str(path) for path in knowledge_base_dir.glob("*.md")) if knowledge_base_dir.exists() else []
        artifacts = {
            "promptAnalysisPath": str(prompt_path),
            "sourcesPath": str(source_path),
            "knowledgeBaseDir": str(knowledge_base_dir),
            "knowledgeBasePaths": knowledge_base_paths,
        }

    result = {
        "tasks": DEFAULT_TASKS,
        "prompts": prompts,
        "references": refs,
        "coverageSummary": coverage_summary(prompts, refs, context),
    }
    if artifacts:
        result["artifacts"] = artifacts
    Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "prompts": len(prompts), "references": len(refs), "artifacts": artifacts}, ensure_ascii=False))


if __name__ == "__main__":
    main()
