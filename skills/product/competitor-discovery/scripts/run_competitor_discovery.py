#!/usr/bin/env python3
"""run_competitor_discovery.py - Orchestrator for competitor identification.

Maintained in competitor-discovery/scripts/ so any skill can call it.

Reads a source text file, uses the competitor-discovery SKILL.md as the LLM
system prompt, and asks the LLM to identify competitors with confidence scoring.

Outputs:
  1. {workspace}/competitor/{task_id}/competitor.md  — Markdown KB file
  2. {output_file}  — Structured JSON for the caller to consume

Exit 0 = success, Exit 1 = fatal error, Exit 2 = no competitors found (non-fatal).

Usage:
    python3 run_competitor_discovery.py \\
        --source-file /workspace/geo-keyword-research/tsk_xxx/tsk_xxx_report.md \\
        --brand-name "固特异" \\
        --task-id tsk_xxx \\
        --workspace /workspace \\
        --config-file /path/to/config.json \\
        --output-file /workspace/geo-keyword-research/tsk_xxx/tsk_xxx_competitors.json

Callers:
    geo-keyword-research/scripts/on_success.py
    (other skills as needed)
"""

from __future__ import annotations

import argparse
import json
import re
import ssl
import sys
import urllib.request as _req
from datetime import date
from pathlib import Path


def strip_think_tags(text: str) -> str:
    """Remove <think>...</think> blocks from LLM output."""
    if not text:
        return text
    return re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()

# ---------------------------------------------------------------------------
# Path constants
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent            # competitor-discovery/scripts/
SKILL_DIR  = SCRIPT_DIR.parent                          # competitor-discovery/
SKILLS_DIR = SKILL_DIR.parent                           # nanobot/skills/
COMPETITOR_DISCOVERY_SKILL = SKILL_DIR / "SKILL.md"     # competitor-discovery/SKILL.md


# ---------------------------------------------------------------------------
# LLM call helper
# ---------------------------------------------------------------------------

def _call_llm(
    system_prompt: str,
    user_prompt: str,
    config_file: Path,
    max_tokens: int = 4096,
) -> str:
    """Call the configured LLM and return the text content of the first choice.

    Bypasses SSL verification for corporate proxy environments.
    Raises RuntimeError on any failure.
    """
    cfg = json.loads(config_file.read_text(encoding="utf-8"))
    defaults = (cfg.get("agents") or {}).get("defaults", {})
    provider_name = defaults.get("provider", "")
    provider = (cfg.get("providers") or {}).get(provider_name, {})
    api_base = provider.get("apiBase", "").rstrip("/")
    api_key = provider.get("apiKey", "")
    model = defaults.get("model", "gpt-4o-mini")

    if not api_base or not api_key:
        raise RuntimeError("No apiBase/apiKey found in config")

    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": 0,
    }).encode("utf-8")

    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE

    req = _req.Request(
        f"{api_base}/chat/completions",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    with _req.urlopen(req, timeout=60, context=ssl_ctx) as resp:
        body = json.loads(resp.read().decode("utf-8"))

    return body["choices"][0]["message"]["content"].strip()


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------

def _build_system_prompt(skill_md_text: str) -> str:
    """Build the system prompt from the competitor-discovery SKILL.md content.

    Appends JSON output format requirements so the LLM returns parseable data.
    """
    output_schema = """
---

## 输出要求（必须严格遵守）

你的最终输出必须是一个 JSON 对象，不包含任何其他文字说明。格式如下：

```json
{
  "competitors": [
    {
      "brand": "品牌标准名",
      "brand_en": "Brand English Name",
      "sku": "具体产品型号（若无则为空字符串）",
      "nicknames": ["昵称1", "昵称2"],
      "confidence": "⭐⭐⭐",
      "score": 7,
      "evidence_count": 3,
      "evidence_quotes": [
        "原文证据片段1",
        "原文证据片段2"
      ]
    }
  ],
  "pending": [
    {
      "brand": "待验证品牌名",
      "sku": "",
      "confidence": "⭐",
      "score": 1,
      "evidence_count": 1,
      "evidence_quotes": ["原文证据片段"]
    }
  ]
}
```

规则：
- `competitors` 包含 ⭐⭐（3-4分）和 ⭐⭐⭐（≥5分）的竞品
- `pending` 包含 ⭐（1-2分）的待验证竞品
- `score` 为 L1-L5 信号累计分值
- `evidence_quotes` 最多 3 条，每条为原文中包含该竞品信号的片段（≤100字）
- 若文本中未发现任何竞品信号，输出 `{"competitors": [], "pending": []}`
- **禁止**在 JSON 之外输出任何解释文字
"""
    return skill_md_text + output_schema


def _build_user_prompt(
    brand_name: str,
    sku_name: str,
    target_type: str,
    source_text: str,
) -> str:
    """Build the user prompt containing brand name, target type, and source text."""
    # Truncate very long texts to avoid token limits (~60k chars ≈ ~15k tokens)
    max_chars = 60_000
    if len(source_text) > max_chars:
        source_text = source_text[:max_chars] + "\n\n[... 文本已截断 ...]"

    if target_type == "brand":
        return (
            f"目标品牌：{brand_name}\n"
            f"分析粒度：品牌级别（仅识别竞争品牌名称，不需要识别具体产品型号/SKU）\n\n"
            f"以下是需要分析的文本：\n\n{source_text}"
        )
    else:
        sku_info = f"（产品型号：{sku_name}）" if sku_name else ""
        return (
            f"目标品牌：{brand_name}{sku_info}\n"
            f"分析粒度：SKU级别（需要识别竞争品牌及其具体产品型号）\n\n"
            f"以下是需要分析的文本：\n\n{source_text}"
        )


# ---------------------------------------------------------------------------
# Output parsing
# ---------------------------------------------------------------------------

def _parse_llm_json(raw: str) -> dict:
    """Extract and parse JSON from LLM response.

    Handles:
    - Markdown code fences (```json ... ```)
    - MiniMax <think>...</think> chain-of-thought blocks
    - JSON embedded inside think blocks (fallback)
    """
    text = raw.strip()

    # 1. Strip <think>...</think> blocks (MiniMax chain-of-thought)
    stripped = strip_think_tags(text)

    # 2. Strip markdown code fences
    if stripped:
        stripped = re.sub(r"```[a-z]*\s*", "", stripped)
        stripped = re.sub(r"```", "", stripped).strip()

    # 3. Try to find JSON object in the stripped content
    if stripped:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(stripped[start:end + 1])
            except json.JSONDecodeError:
                pass

    # 4. Fallback: search the FULL text (including inside think blocks) for JSON
    #    MiniMax sometimes puts the final JSON inside <think> tags
    clean = re.sub(r"```[a-z]*\s*", "", text)
    clean = re.sub(r"```", "", clean)
    clean = re.sub(r"</?think>", "", clean)  # strip residual tags for fallback

    # Find all {...} JSON object candidates, try the last one
    matches = list(re.finditer(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", clean))
    if matches:
        for m in reversed(matches):
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                continue

    # 5. Last resort: try to find any JSON object in the raw text
    start = clean.find("{")
    end = clean.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(clean[start:end + 1])
        except json.JSONDecodeError:
            pass

    raise ValueError(
        f"No valid JSON object found in LLM response: {raw[:500]}"
    )


# ---------------------------------------------------------------------------
# KB file writer
# ---------------------------------------------------------------------------

def _write_kb(
    kb_file: Path,
    brand_name: str,
    task_id: str,
    competitors: list[dict],
    pending: list[dict],
) -> None:
    """Write competitor knowledge base in competitor-discovery KB format."""
    today = date.today().isoformat()
    total = len(competitors) + len(pending)

    lines = [
        f"# {brand_name} 竞品知识库\n",
        f"> 本文件由 competitor-discovery skill 自动生成\n",
        f"> 来源任务: {task_id}\n",
        "",
        "## 档案信息\n",
        f"- **目标品牌**：{brand_name}",
        f"- **首次建档**：{today}",
        f"- **最后更新**：{today}",
        f"- **累计竞品**：{total} 个（{len(competitors)} 个已确认，{len(pending)} 个待验证）",
        "",
        "---\n",
        "## 竞品列表\n",
    ]

    # Confidence groups
    high = [c for c in competitors if c.get("confidence") == "⭐⭐⭐"]
    mid = [c for c in competitors if c.get("confidence") == "⭐⭐"]

    def _entry(c: dict) -> list[str]:
        brand = c.get("brand", "")
        brand_en = c.get("brand_en", "")
        sku = c.get("sku", "")
        nicknames = c.get("nicknames", [])
        confidence = c.get("confidence", "")
        score = c.get("score", 0)
        ev_count = c.get("evidence_count", 0)
        quotes = c.get("evidence_quotes", [])

        result = [
            f"### {brand} {confidence}\n",
            f"- **标准名**：{brand}",
        ]
        if brand_en:
            result.append(f"- **英文名**：{brand_en}")
        if sku:
            result.append(f"- **产品名**：{sku}")
        if nicknames:
            result.append(f"- **别名**：{', '.join(nicknames)}")
        result.append(f"- **置信度**：{confidence}（评分 {score} 分）")
        result.append(f"- **证据来源**：{ev_count} 条")
        for q in quotes[:3]:
            result.append(f"  - \"{q.strip()}\"")
        result.append(f"- **首次发现**：{today}")
        result.append("")
        return result

    if high:
        lines.append("### ⭐⭐⭐ 高置信竞品\n")
        for c in high:
            lines.extend(_entry(c))

    if mid:
        lines.append("### ⭐⭐ 中置信竞品\n")
        for c in mid:
            lines.extend(_entry(c))

    if pending:
        lines += ["", "---\n", "## 等待验证区\n",
                  "> 置信度不足（⭐），不主动输出，需人工确认\n"]
        for c in pending:
            lines.extend(_entry(c))

    lines += [
        "",
        "---\n",
        "## 变更历史\n",
        "| 日期 | 操作 | 内容 |",
        "|------|------|------|",
        f"| {today} | 初始化 | 由 task {task_id} 自动生成，共 {total} 个竞品 |",
        "",
    ]

    kb_file.parent.mkdir(parents=True, exist_ok=True)
    kb_file.write_text("\n".join(lines), encoding="utf-8")
    print(f"[run_competitor_discovery] KB written: {kb_file}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Competitor discovery orchestrator (competitor-discovery skill)"
    )
    parser.add_argument("--source-file", required=True,
                        help="Path to the source text file to analyse (e.g. report.md)")
    parser.add_argument("--brand-name", required=True,
                        help="Target brand name (standard name)")
    parser.add_argument("--sku-name", default="",
                        help="Target SKU/model name (empty for brand-level)")
    parser.add_argument("--target-type", default="sku", choices=["brand", "sku"],
                        help="Analysis granularity: brand (brand-only) or sku (brand+SKU)")
    parser.add_argument("--task-id", required=True,
                        help="Caller task ID (used for KB path and output naming)")
    parser.add_argument("--workspace", required=True,
                        help="Workspace root directory")
    parser.add_argument("--config-file", required=True,
                        help="LLM config file (JSON with providers + agents)")
    parser.add_argument("--output-file", required=True,
                        help="Output path for {task_id}_competitors.json")
    args = parser.parse_args()

    source_file = Path(args.source_file).expanduser().resolve()
    workspace = Path(args.workspace).expanduser().resolve()
    config_file = Path(args.config_file).expanduser().resolve()
    output_file = Path(args.output_file).expanduser().resolve()
    brand_name = args.brand_name
    sku_name = args.sku_name
    target_type = args.target_type
    task_id = args.task_id

    # ── Validation ──────────────────────────────────────────────────────────
    if not source_file.exists():
        print(f"[run_competitor_discovery] FATAL: source file not found: {source_file}",
              file=sys.stderr)
        return 1

    if not config_file.exists():
        print(f"[run_competitor_discovery] FATAL: config not found: {config_file}",
              file=sys.stderr)
        return 1

    if not COMPETITOR_DISCOVERY_SKILL.exists():
        print(f"[run_competitor_discovery] FATAL: competitor-discovery SKILL.md not found: "
              f"{COMPETITOR_DISCOVERY_SKILL}", file=sys.stderr)
        return 1

    # ── Step 1: Read source text ─────────────────────────────────────────────
    source_text = source_file.read_text(encoding="utf-8")
    print(f"[run_competitor_discovery] Source loaded: {len(source_text)} chars", file=sys.stderr)

    # ── Step 2: Build system prompt from competitor-discovery SKILL.md ───────
    skill_md = COMPETITOR_DISCOVERY_SKILL.read_text(encoding="utf-8")
    system_prompt = _build_system_prompt(skill_md)

    # ── Step 3: Build user prompt ────────────────────────────────────────
    user_prompt = _build_user_prompt(brand_name, sku_name, target_type, source_text)

    # ── Step 4: Call LLM ─────────────────────────────────────────────────────
    print(f"[run_competitor_discovery] Calling LLM for brand={brand_name}...", file=sys.stderr)
    try:
        raw_response = _call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            config_file=config_file,
        )
    except Exception as exc:
        print(f"[run_competitor_discovery] FATAL: LLM call failed: {exc}", file=sys.stderr)
        return 1

    # ── Step 5: Parse LLM output ─────────────────────────────────────────────
    try:
        parsed = _parse_llm_json(raw_response)
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"[run_competitor_discovery] FATAL: Cannot parse LLM JSON: {exc}",
              file=sys.stderr)
        print(f"[run_competitor_discovery] Raw response (first 500 chars): "
              f"{raw_response[:500]}", file=sys.stderr)
        return 1

    competitors: list[dict] = parsed.get("competitors", [])
    pending: list[dict] = parsed.get("pending", [])
    today = date.today().isoformat()

    print(
        f"[run_competitor_discovery] Found {len(competitors)} confirmed, "
        f"{len(pending)} pending competitors",
        file=sys.stderr,
    )

    if not competitors and not pending:
        print("[run_competitor_discovery] No competitors found in source text.", file=sys.stderr)

    # ── Step 6: Write KB file ─────────────────────────────────────────────────
    kb_file = workspace / "competitor" / task_id / "competitor.md"
    _write_kb(kb_file, brand_name, task_id, competitors, pending)

    # ── Step 7: Write output JSON ─────────────────────────────────────────────
    result = {
        "brand_name": brand_name,
        "sku_name": sku_name,
        "target_type": target_type,
        "task_id": task_id,
        "discovered_at": today,
        "kb_file": str(kb_file),
        "competitors": competitors,
        "pending": pending,
    }
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[run_competitor_discovery] Output JSON written: {output_file}", file=sys.stderr)

    return 0 if (competitors or pending) else 2


if __name__ == "__main__":
    sys.exit(main())
