#!/usr/bin/env python3
"""on_success callback for geo_keyword_research DAG tasks.

Called by the nanobot framework after the geo_keyword_research DAG completes
successfully.  Parses the LLM-generated report.md, then:
  1. Runs product-image/extract.py  (if official_site.txt exists)
  2. Runs user-image/extract.py     (one per persona found in report)
  3. Writes a unified {task_id}_result.json

Auto-recovery: if report.md is missing (e.g. due to agent context-compaction
bug), on_success.py will attempt to regenerate the report from existing
page_*.txt files by calling the LLM directly before failing.

Exit 0 = success (all critical steps OK, non-critical warnings logged).
Exit 1 = fatal error (report.md missing AND auto-recovery failed).

Usage (standalone test):
    python3 on_success.py \\
        --task-id tsk_abc123 \\
        --workspace /workspace/users/{uid} \\
        --config-file /nanobot/task.json
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import uuid
from pathlib import Path

# ---------------------------------------------------------------------------
# Script path constants
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
SKILLS_DIR = SCRIPT_DIR.parent.parent          # nanobot/skills/
PRODUCT_IMAGE_SCRIPT = SKILLS_DIR / "product-image" / "scripts" / "extract.py"
USER_IMAGE_SCRIPT = SKILLS_DIR / "user-image" / "scripts" / "extract.py"
COMPETITOR_DISCOVERY_SCRIPT = SKILLS_DIR / "competitor-discovery" / "scripts" / "run_competitor_discovery.py"
GEO_SKILL_MD = SCRIPT_DIR.parent / "SKILL.md"   # geo-keyword-research/SKILL.md


# ---------------------------------------------------------------------------
# Auto-recovery: regenerate report.md from page_*.txt when agent forgot to write it
# ---------------------------------------------------------------------------

def _recover_report_with_llm(
    geo_dir: Path,
    task_id: str,
    brand_name_raw: str,
    config_file: Path,
    report_file: Path,
) -> bool:
    """Attempt to regenerate {task_id}_report.md from existing page_*.txt files.

    Called when the agent successfully collected data but context-compaction
    caused it to skip the report-writing step.

    Returns True if recovery succeeded (report_file now exists and is valid).
    Returns False on any error (caller should treat as fatal).
    """
    import glob
    import ssl
    import urllib.request as _req

    # ── Collect available source material ────────────────────────────────────
    page_files = sorted(geo_dir.glob("page_*.txt"))
    urls_file = geo_dir / f"{task_id}_urls.md"
    official_site_file = geo_dir / f"{task_id}_official_site.txt"

    if not page_files and not urls_file.exists():
        print("[on_success][recover] No page_*.txt or urls.md found — cannot recover",
              file=sys.stderr)
        return False

    # Build source text from all available page files (cap at ~80k chars)
    source_parts: list[str] = []
    total_chars = 0
    MAX_CHARS = 80_000

    if urls_file.exists():
        try:
            urls_text = urls_file.read_text(encoding="utf-8")[:5000]
            source_parts.append(f"## 数据源URL列表（摘要）\n\n{urls_text}")
        except Exception:
            pass

    for pf in page_files:
        if total_chars >= MAX_CHARS:
            break
        try:
            content = pf.read_text(encoding="utf-8")
            snippet = content[:min(len(content), MAX_CHARS - total_chars)]
            source_parts.append(f"## 页面内容：{pf.name}\n\n{snippet}")
            total_chars += len(snippet)
        except Exception:
            continue

    if not source_parts:
        print("[on_success][recover] All page files unreadable — cannot recover",
              file=sys.stderr)
        return False

    source_text = "\n\n---\n\n".join(source_parts)
    brand_display = brand_name_raw or "目标品牌"

    # ── Read SKILL.md output format spec ─────────────────────────────────────
    skill_format_hint = ""
    if GEO_SKILL_MD.exists():
        try:
            skill_text = GEO_SKILL_MD.read_text(encoding="utf-8")
            # Extract just the output format section to keep prompt focused
            marker = "## 输出格式"
            idx = skill_text.find(marker)
            if idx >= 0:
                skill_format_hint = skill_text[idx:idx + 4000]
        except Exception:
            pass

    # ── Build recovery prompt ─────────────────────────────────────────────────
    system_prompt = (
        "你是一位专业的 GEO 关键词研究分析师。你的任务是基于已收集的网页内容，"
        "为目标品牌生成一份完整的 GEO 关键词研究报告。\n\n"
        "报告必须严格遵守以下格式规范：\n\n"
        + (skill_format_hint or (
            "报告包含四个部分：\n"
            "1. 品牌/产品理解（含信息来源URL）\n"
            "2. 目标人群理解（末尾必须有人群分类列表）\n"
            "3. 关键词列表（第一类行业推荐型10个 + 第二类品牌直指型10个，每个含为什么选择和GEO策略）\n"
            "4. 总结与研究洞察（末尾必须有研究洞察区块，每条含XX%内容支持）"
        ))
        + "\n\n直接输出报告内容，不要有任何前言或说明。"
    )

    user_prompt = (
        f"目标品牌：{brand_display}\n\n"
        f"以下是已收集的网页内容，请基于这些内容生成完整的 GEO 关键词研究报告：\n\n"
        f"{source_text}"
    )

    # ── Call LLM ─────────────────────────────────────────────────────────────
    try:
        cfg = json.loads(config_file.read_text(encoding="utf-8"))
        defaults = (cfg.get("agents") or {}).get("defaults", {})
        provider_name = defaults.get("provider", "")
        provider = (cfg.get("providers") or {}).get(provider_name, {})
        api_base = provider.get("apiBase", "").rstrip("/")
        api_key = provider.get("apiKey", "")
        model = defaults.get("model", "gpt-4o-mini")

        if not api_base or not api_key:
            raise ValueError("no apiBase/apiKey in config")

        payload = json.dumps({
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": 8192,
            "temperature": 0.3,
        }).encode("utf-8")

        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE

        req = _req.Request(
            f"{api_base}/chat/completions",
            data=payload,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
            method="POST",
        )
        print(f"[on_success][recover] Calling LLM to regenerate report "
              f"({len(source_text)} chars of source material)...", file=sys.stderr)
        with _req.urlopen(req, timeout=120, context=ssl_ctx) as resp:
            body = json.loads(resp.read().decode("utf-8"))

        report_text = body["choices"][0]["message"]["content"].strip()

    except Exception as exc:
        print(f"[on_success][recover] LLM call failed: {exc}", file=sys.stderr)
        return False

    # ── Validate and write ────────────────────────────────────────────────────
    if len(report_text) < 1000:
        print(f"[on_success][recover] LLM response too short ({len(report_text)} chars) — ignoring",
              file=sys.stderr)
        return False

    geo_dir.mkdir(parents=True, exist_ok=True)
    report_file.write_text(report_text, encoding="utf-8")
    line_count = len(report_text.splitlines())
    print(f"[on_success][recover] Report recovered: {line_count} lines, "
          f"{len(report_text)} chars → {report_file}", file=sys.stderr)
    return line_count >= 20  # minimal sanity check


# ---------------------------------------------------------------------------
# LLM brand / sku_name parser
# ---------------------------------------------------------------------------

def _parse_brand_sku_with_llm(raw_brand_name: str, config_file: Path) -> tuple[str, str]:
    """Split a raw brand string into (brand_name, sku_name).

    Strategy:
    1. Rule-based regex first (fast, no network) — handles most Chinese phone/product names.
    2. LLM fallback for ambiguous cases (SSL errors are bypassed with unverified context).

    Example inputs -> outputs:
      "肯德基 吵指原味鸡" -> ("肯德基", "吵指原味鸡")
      "BMW X1"           -> ("BMW", "X1")
      "红米k90"          -> ("红米", "K90")
      "华为Mate60"        -> ("华为", "Mate60")
      "固特异轮胎"        -> ("固特异轮胎", "")

    Returns (raw_brand_name, "") on any error so the caller is never blocked.
    """
    if not raw_brand_name:
        return raw_brand_name, ""

    s = raw_brand_name.strip()

    # ── Strategy 1: LLM (primary) ────────────────────────────────────────────
    try:
        import ssl
        import urllib.request as _req

        cfg = json.loads(config_file.read_text(encoding="utf-8"))
        defaults = (cfg.get("agents") or {}).get("defaults", {})
        provider_name = defaults.get("provider", "")
        provider = (cfg.get("providers") or {}).get(provider_name, {})
        api_base = provider.get("apiBase", "").rstrip("/")
        api_key  = provider.get("apiKey", "")
        model    = defaults.get("model", "gpt-4o-mini")

        if not api_base or not api_key:
            raise ValueError("no apiBase/apiKey in config")

        prompt = (
            "You are a brand data parser. Given a raw brand name string that may contain "
            "both a brand name and a product model/SKU, split them into two parts.\n"
            "Rules:\n"
            "- brand_name: the company or master brand (e.g. KFC, BMW, 肯德基, 宝马, 红米/REDMI, 小米, 华为)\n"
            "- sku_name: the specific product line, series name, or model number "
            "(e.g. X1, 吮指原味鸡, K90, Mate60, GT8, Ace6, Assurance MaxGuard). "
            "Empty string ONLY if the entire input is purely a brand with no product model.\n"
            "- For phone brands like 红米/REDMI/Xiaomi/vivo/OPPO/荣耀/一加, "
            "the alphanumeric part (K90, GT8, X300, Mate60 Pro, etc.) is the SKU.\n"
            "- Chinese product names often combine brand + model without space: "
            "'红米k90' -> brand='红米', sku='K90'; '华为Mate60' -> brand='华为', sku='Mate60'\n"
            "Return ONLY a JSON object: {\"brand_name\": \"...\", \"sku_name\": \"...\"}\n\n"
            f"Input: {raw_brand_name}"
        )

        payload = json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 200,
            "temperature": 0,
        }).encode("utf-8")

        # Bypass SSL verification for corporate proxy / self-signed cert environments
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE

        req = _req.Request(
            f"{api_base}/chat/completions",
            data=payload,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
            method="POST",
        )
        with _req.urlopen(req, timeout=15, context=ssl_ctx) as resp:
            body = json.loads(resp.read().decode("utf-8"))

        content = body["choices"][0]["message"]["content"].strip()
        content = re.sub(r"^```[a-z]*\n?", "", content)
        content = re.sub(r"```$", "", content).strip()
        parsed_llm = json.loads(content)
        brand = str(parsed_llm.get("brand_name") or raw_brand_name).strip()
        sku   = str(parsed_llm.get("sku_name") or "").strip()
        print(f"[on_success] _parse_brand_sku LLM: '{raw_brand_name}' -> brand='{brand}' sku='{sku}'",
              file=sys.stderr)
        return brand, sku

    except Exception as exc:
        print(f"[on_success] _parse_brand_sku LLM failed ({exc}), falling back to regex",
              file=sys.stderr)

    # ── Strategy 2: rule-based regex fallback ────────────────────────────────
    # Pattern A: pure Chinese brand + alphanumeric model (no space)
    # e.g. "红米k90" "华为Mate60" "真我GT8" "一加Ace6T"
    m = re.match(r"^([\u4e00-\u9fff]+)([A-Za-z0-9].*)$", s)
    if m:
        brand_part = m.group(1).strip()
        sku_part   = m.group(2).strip()
        if brand_part and sku_part and (
            any(c.isdigit() for c in sku_part)
            or (sku_part[0].isupper() and len(sku_part) >= 2)
        ):
            sku_norm = sku_part[0].upper() + sku_part[1:]
            print(f"[on_success] _parse_brand_sku regexA: '{raw_brand_name}' -> brand='{brand_part}' sku='{sku_norm}'",
                  file=sys.stderr)
            return brand_part, sku_norm

    # Pattern B: brand + space + model  e.g. "BMW X1" "REDMI K90" "肯德基 吮指原味鸡"
    m2 = re.match(r"^([A-Za-z\u4e00-\u9fff]{2,12})\s+(.{1,30})$", s)
    if m2:
        brand_part = m2.group(1).strip()
        sku_part   = m2.group(2).strip()
        if brand_part and sku_part:
            print(f"[on_success] _parse_brand_sku regexB: '{raw_brand_name}' -> brand='{brand_part}' sku='{sku_part}'",
                  file=sys.stderr)
            return brand_part, sku_part

    print(f"[on_success] _parse_brand_sku: no match for '{raw_brand_name}', sku_name set to empty",
          file=sys.stderr)
    return raw_brand_name, ""



# ---------------------------------------------------------------------------
# report.md parsing
# ---------------------------------------------------------------------------

def _extract_section(text: str, *heading_patterns: str) -> str:
    """Extract the body of a markdown section matching any of the heading patterns.

    Searches for the first H2/H3 heading that contains any of the given
    substrings (case-insensitive), then returns all text until the next
    heading of the same or higher level.

    Supports Chinese numeral prefixes: 一、二、三、四 etc.
    """
    lines = text.splitlines()
    start = -1
    heading_level = 2

    for i, line in enumerate(lines):
        stripped = line.lstrip("#").strip()
        if line.startswith("#") and any(p.lower() in stripped.lower() for p in heading_patterns):
            heading_level = len(line) - len(line.lstrip("#"))
            start = i + 1
            break

    if start < 0:
        return ""

    body_lines: list[str] = []
    for line in lines[start:]:
        if line.startswith("#"):
            cur_level = len(line) - len(line.lstrip("#"))
            if cur_level <= heading_level:
                break
        body_lines.append(line)

    return "\n".join(body_lines).strip()


def _strip_markdown(text: str) -> str:
    """Convert markdown text to plain-text paragraphs.

    Removes headings, bold/italic, bullets, tables, links, and images.
    Collapses multiple blank lines into paragraph breaks.
    """
    lines = text.splitlines()
    out: list[str] = []
    for line in lines:
        s = line.strip()
        # Skip heading lines
        if s.startswith("#"):
            continue
        # Skip table separator rows
        if re.match(r"^\|[-|\s]+\|$", s):
            continue
        # Strip table pipes — convert |a|b|c| to "a b c"
        if s.startswith("|") and s.endswith("|"):
            cells = [c.strip() for c in s.split("|") if c.strip()]
            s = "  ".join(cells)
        # Strip bold/italic markers
        s = re.sub(r"\*{1,3}", "", s)
        # Strip bullet list prefix
        s = re.sub(r"^[-*+]\s+", "", s)
        # Strip numbered list prefix
        s = re.sub(r"^\d+[.。]\s+", "", s)
        # Strip image syntax ![alt](url)
        s = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", s)
        # Strip link syntax [text](url) → text
        s = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", s)
        # Collapse multiple spaces
        s = re.sub(r"\s{2,}", " ", s).strip()
        out.append(s)
    # Collapse blank lines into single paragraph breaks
    result = re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip()
    return result


def _run_competitor_discovery(
    workspace: Path,
    task_id: str,
    brand_name: str,
    sku_name: str,
    target_type: str,
    config_file: Path,
    geo_dir: Path,
    report_file: Path,
) -> list[dict]:
    """Run run_competitor_discovery.py and return brand_mentions list.

    Calls the competitor-discovery orchestration script which uses the
    competitor-discovery SKILL.md as an LLM system prompt to identify
    competitors from the report text.

    Returns a list of {brand: str, sku: str} dicts (only ⭐⭐/⭐⭐⭐ confidence).
    Returns [] on any failure (non-fatal, logged as WARNING).
    """
    if not COMPETITOR_DISCOVERY_SCRIPT.exists():
        print(
            f"[on_success] WARNING: run_competitor_discovery.py not found: "
            f"{COMPETITOR_DISCOVERY_SCRIPT}",
            file=sys.stderr,
        )
        return []

    output_file = geo_dir / f"{task_id}_competitors.json"
    cmd = [
        sys.executable, str(COMPETITOR_DISCOVERY_SCRIPT),
        "--source-file", str(report_file),
        "--brand-name", brand_name,
        "--sku-name", sku_name,
        "--target-type", target_type,
        "--task-id", task_id,
        "--workspace", str(workspace),
        "--config-file", str(config_file),
        "--output-file", str(output_file),
    ]

    rc, stdout, stderr_out = _run(cmd)
    if stderr_out:
        for line in stderr_out.splitlines()[:15]:
            print(f"[on_success][competitor-discovery] {line}", file=sys.stderr)

    if rc not in (0, 2):
        print(
            f"[on_success] WARNING: run_competitor_discovery.py failed (rc={rc}), "
            "brand_mentions will be empty",
            file=sys.stderr,
        )
        return []

    # Read and convert to brand_mentions format: [{brand, sku}]
    if not output_file.exists():
        print("[on_success] WARNING: _competitors.json not created, brand_mentions empty",
              file=sys.stderr)
        return []

    try:
        comp_data = json.loads(output_file.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"[on_success] WARNING: Cannot read _competitors.json: {exc}", file=sys.stderr)
        return []

    confirmed = comp_data.get("competitors", [])  # ⭐⭐ and ⭐⭐⭐ only
    if target_type == "brand":
        # Brand mode: strip SKU from all competitor entries
        brand_mentions = [
            {"brand": c["brand"], "sku": ""}
            for c in confirmed if c.get("brand")
        ]
    else:
        brand_mentions = [
            {"brand": c.get("brand", ""), "sku": c.get("sku", "")}
            for c in confirmed if c.get("brand")
        ]
    print(
        f"[on_success] competitor-discovery done: {len(brand_mentions)} brand_mentions "
        f"({len(comp_data.get('pending', []))} pending)",
        file=sys.stderr,
    )
    return brand_mentions



def _parse_coverage_summary(report_text: str) -> list[dict]:
    """Parse the '\u7814\u7a76\u6d1e\u5bdf\uff1a' bullet block from the summary section.

    Expects bullets in the format::

        **\u7814\u7a76\u6d1e\u5bdf\uff1a**
        - \u56fa\u7279\u5f02\u5728\u8f6e\u80ce\u8010\u4e45\u6027\u9886\u57df\u5177\u6709\u663e\u8457\u8ba4\u77e5\u4f18\u52bf\uff0880%\u5185\u5bb9\u652f\u6301\uff09
        - \u7528\u6237\u5bf9\u4ef7\u683c/\u6027\u4ef7\u6bd4\u7684\u5173\u6ce8\u5ea6\u9ad8\u4e8e\u6280\u672f\u53c2\u6570\uff0865%\u5185\u5bb9\u652f\u6301\uff09

    Returns list of {"insight": str, "coverage_perc": int}.
    coverage_perc is parsed from a trailing "(N%\u5185\u5bb9\u652f\u6301)" pattern;
    defaults to 0 if not found.
    """
    def _extract_insights(text: str) -> list[dict]:
        """Extract insight bullets from text containing '\u7814\u7a76\u6d1e\u5bdf'."""
        insights: list[dict] = []
        in_block = False
        for line in text.splitlines():
            stripped = line.strip()
            if "\u7814\u7a76\u6d1e\u5bdf" in stripped:
                in_block = True
                continue
            if not in_block:
                continue
            if stripped.startswith("##") or (
                stripped.startswith("**") and stripped.endswith("**")
                and "\u6d1e\u5bdf" not in stripped
            ):
                break
            if not (stripped.startswith("- ") or stripped.startswith("* ")):
                continue
            text_line = stripped[2:].strip()
            if not text_line:
                continue
            perc = 0
            m = re.search(r"[\uff08(](\d{1,3})%[^\uff09)]{0,15}[\uff09)]", text_line)
            if m:
                perc = int(m.group(1))
                text_line = (text_line[:m.start()] + text_line[m.end():]).strip()
            insights.append({"insight": text_line, "coverage_perc": perc})
        return insights

    # Strategy 1: find section, then look for block inside
    summary_section = _extract_section(report_text, "\u603b\u7ed3", "summary", "\u7b2c\u56db\u6bb5")
    if summary_section:
        insights = _extract_insights(summary_section)
        if insights:
            return insights

    # Strategy 2: fallback - search the entire report for the block.
    # Handles cases where heading contains the keyword itself.
    return _extract_insights(report_text)



def _extract_brand_url(section_text: str, official_site_file: Path) -> str:
    """Extract the first https URL from the '信息来源' block of a section.

    Falls back to scanning official_site_file for the first line starting
    with 'http' if the markdown extraction fails.
    """
    # Try markdown: look for lines under "信息来源" containing a URL
    in_sources = False
    for line in section_text.splitlines():
        stripped = line.strip()
        if "信息来源" in stripped:
            in_sources = True
            continue
        if in_sources:
            # Stop at next bold heading or empty line followed by heading
            if stripped.startswith("**") and stripped.endswith("**") and "来源" not in stripped:
                break
            urls = re.findall(r"https?://[^\s\)\"']+", stripped)
            if urls:
                return urls[0].rstrip(".")

    # Fallback: first URL anywhere in the section
    urls = re.findall(r"https?://[^\s\)\"']+", section_text)
    if urls:
        return urls[0].rstrip(".")

    # Fallback: read official_site_file first non-empty line
    if official_site_file.is_file():
        for raw_line in official_site_file.read_text(encoding="utf-8").splitlines():
            stripped = raw_line.strip()
            if stripped.startswith("http"):
                return stripped.split()[0].rstrip(".")

    return ""


def _parse_personas(user_section: str) -> list[dict]:
    """Parse the structured persona list from the user-image section.

    Priority 1 (structured block):
        **人群分类：**
        - 人群名：brief description

    Priority 2 (numbered bold headings, old report format):
        **1. 年轻家庭用户（25-40岁）**
        - 注重用餐体验...

    Returns list of {"persona_name": str, "brief": str}.
    """
    personas: list[dict] = []
    in_block = False
    for line in user_section.splitlines():
        stripped = line.strip()
        if "人群分类" in stripped:
            in_block = True
            continue
        if in_block:
            if stripped.startswith("- ") or stripped.startswith("* "):
                content = stripped[2:].strip()
                sep = "：" if "：" in content else ":"
                parts = content.split(sep, 1)
                if len(parts) == 2:
                    name = parts[0].strip()
                    brief = parts[1].strip()
                    if name:
                        personas.append({"persona_name": name, "brief": brief})
            elif stripped.startswith("#") or (stripped and not stripped.startswith("-") and not stripped.startswith("*")):
                if stripped.startswith("#"):
                    break

    if personas:
        return personas

    # ── Fallback: parse **N. 人群名（年龄段）** numbered bold heading format ──
    current_name = ""
    current_bullets: list[str] = []

    for line in user_section.splitlines():
        stripped = line.strip()
        m = re.match(r"^\*{1,2}\d+[.。]\s*(.+?)\*{1,2}$", stripped)
        if m:
            if current_name and current_bullets:
                personas.append({
                    "persona_name": current_name,
                    "brief": "；".join(current_bullets[:3]),
                })
            raw_name = m.group(1).strip()
            current_name = re.sub(r"[（(][^）)]*[）)]", "", raw_name).strip()
            current_bullets = []
        elif current_name and (stripped.startswith("- ") or stripped.startswith("* ")):
            bullet = stripped[2:].strip()
            if bullet and "主要场景" not in bullet:
                current_bullets.append(bullet)
        elif current_name and stripped.startswith("#"):
            if current_bullets:
                personas.append({
                    "persona_name": current_name,
                    "brief": "；".join(current_bullets[:3]),
                })
            current_name = ""
            current_bullets = []

    if current_name and current_bullets:
        personas.append({
            "persona_name": current_name,
            "brief": "；".join(current_bullets[:3]),
        })

    return personas


def _parse_keyword_block(block_text: str, is_industry: bool) -> list[dict]:
    """Parse a keyword list from a markdown block.

    Supports three formats:

    Format A (numbered headings):
        ### 1. 轮胎品牌推荐（✅ 已验证）
        - **原因**：...
        - **GEO 策略**：...

    Format B (markdown table):
        |#|关键词|为什么选择|GEO 策略|
        |-|-|-|-|
        |1|**轮胎品牌推荐**|原因文本|策略文本|

    Format C (bullet list):
        - **轮胎品牌推荐**（✅ 已验证）：描述
    """
    keywords: list[dict] = []
    lines = block_text.splitlines()
    i = 0

    # Detect table format first
    has_table = any("|" in line and not line.strip().startswith("#") for line in lines)

    if has_table:
        verified_by_section = is_industry and "已验证" in block_text[:400]
        header_skipped = False
        for line in lines:
            stripped = line.strip()
            if not stripped.startswith("|"):
                continue
            # Skip separator rows (|-|-|-|)
            if re.match(r"^\|[-|\s]+\|$", stripped):
                continue
            # Skip the FIRST non-separator pipe row if all cells are short (header row)
            if not header_skipped:
                cells = [c.strip() for c in stripped.split("|") if c.strip()]
                if cells and all(len(c) <= 10 for c in cells):
                    header_skipped = True
                    continue
            # Parse data row: |#|keyword|reason|strategy|
            parts = [p.strip() for p in stripped.split("|")]
            parts = [p for p in parts if p != ""]
            if len(parts) >= 2:
                kw = re.sub(r"\*{1,2}", "", parts[1]).strip()
                reason = parts[2].strip() if len(parts) > 2 else ""
                geo_strategy = parts[3].strip() if len(parts) > 3 else ""
                if kw and not re.match(r"^[-|\d]+$", kw):
                    keywords.append({
                        "keyword": kw,
                        "reason": reason,
                        "geo_strategy": geo_strategy,
                        "verified": verified_by_section,
                    })
        return keywords

    while i < len(lines):
        line = lines[i].strip()

        # --- Format A: numbered heading ---
        # Supports:  ### 1. keyword       (heading style)
        #            1. keyword            (plain numbered)
        #            **1. keyword**        (bold numbered)
        #            **1. keyword**：desc  (bold with trailing desc)
        m = re.match(
            r"^(?:#{1,4}\s+)?"           # optional ### heading prefix
            r"\*{0,2}"                    # optional ** bold open
            r"(\d+)[.。]\s+"             # number + dot
            r"(.+?)"                      # keyword text (non-greedy)
            r"\*{0,2}"                    # optional ** bold close
            r"(?:\s*$|[：:])",            # end of line or : separator
            line,
        )
        if m:
            raw_title = m.group(2).strip()
            verified_match = re.search(r"[（(][✅❌✓✗][^）)]*[）)]", raw_title)
            verified = bool(verified_match and ("✅" in verified_match.group() or "✓" in verified_match.group()))
            keyword_text = re.sub(r"[（(][✅❌✓✗][^）)]*[）)]", "", raw_title).strip().rstrip("（(").strip()
            # Strip trailing bold markers
            keyword_text = keyword_text.strip("*").strip()
            reason = ""
            geo_strategy = ""
            i += 1
            while i < len(lines):
                sub = lines[i].strip()
                # Stop at next numbered keyword
                if re.match(r"^(?:#{1,4}\s+)?\*{0,2}\d+[.。]\s+", sub):
                    break
                if sub.startswith("#"):
                    break
                # Match reason: supports 原因/reason/为什么选择/选择原因
                reason_m = re.match(
                    r"^[-*]\s*\*{0,2}(?:原因|reason|为什么选择|选择原因)\*{0,2}[：:]\s*(.+)$",
                    sub, re.I,
                )
                # Match GEO strategy: supports 'GEO 策略'/'GEO策略'/'geo strategy'
                geo_m = re.match(
                    r"^[-*]\s*\*{0,2}(?:GEO\s*策略|geo\s*strategy)\*{0,2}[：:]\s*(.+)$",
                    sub, re.I,
                )
                if reason_m:
                    reason = reason_m.group(1).strip()
                elif geo_m:
                    geo_strategy = geo_m.group(1).strip()
                i += 1
            if keyword_text:
                keywords.append({
                    "keyword": keyword_text,
                    "reason": reason,
                    "geo_strategy": geo_strategy,
                    "verified": verified if is_industry else False,
                })
            continue

        # --- Format C: bullet list keyword ---
        m2 = re.match(r"^[-*]\s+\*{0,2}(.+?)\*{0,2}\s*(?:[（(][✅❌✓✗]([^）)]*)[）)])?[：:：]?\s*(.*)$", line)
        if m2 and not line.startswith("  "):
            kw_text = m2.group(1).strip()
            verified = "✅" in line[:len(kw_text) + 20] or "✓" in line[:len(kw_text) + 20]
            desc = m2.group(3).strip() if m2.group(3) else ""
            if kw_text and not kw_text.startswith("**") and len(kw_text) > 1:
                keywords.append({
                    "keyword": kw_text,
                    "reason": desc,
                    "geo_strategy": "",
                    "verified": verified if is_industry else False,
                })

        i += 1

    return keywords


def parse_report(report_text: str, brand_name_fallback: str = "", official_site_file: Path = Path()) -> dict:
    """Parse report.md and extract all structured fields.

    Returns:
        {
            brand_name:         str,
            brand_url:          str,
            brand_summary:      str   (full text, no truncation),
            user_image_summary: str   (full text, no truncation),
            keywords_data:      { industry: {...}, brand: {...} },
            personas:           [ {persona_name, brief} ],
        }
    """
    # ── brand_name ──────────────────────────────────────────────────────────
    brand_name = brand_name_fallback
    for line in report_text.splitlines():
        m = re.match(r"^#\s+(.+)$", line.strip())
        if m:
            # Usually "固特异 GEO 关键词研究报告" — grab first word/phrase
            title_text = m.group(1).strip()
            # Strip trailing "GEO..." or "关键词" boilerplate
            title_text = re.sub(r"\s+(GEO|geo|关键词|keyword).+$", "", title_text, flags=re.I).strip()
            if title_text:
                brand_name = brand_name or title_text
            break

    # ── brand section (第一段) ───────────────────────────────────────────────
    brand_section = _extract_section(
        report_text, "品牌", "brand", "产品理解", "第一段",
    )

    brand_url = _extract_brand_url(brand_section, official_site_file)

    # Remove "信息来源" sub-block from summary
    summary_text = re.split(r"\*{0,2}信息来源\*{0,2}", brand_section)[0].strip()
    brand_summary = _strip_markdown(summary_text)

    # ── user section (第二段) ────────────────────────────────────────────────
    user_section = _extract_section(
        report_text, "人群", "用户", "target", "第二段",
    )
    # Remove persona list block from summary
    user_summary_text = re.split(r"\*{0,2}人群分类\*{0,2}", user_section)[0].strip()
    user_image_summary = _strip_markdown(user_summary_text)

    personas = _parse_personas(user_section)

    # ── keywords ───────────────────────────────────────────────────
    # Strategy: find the H2 sections that specifically match第一类/第二类.
    # _extract_section returns BODY only; we prepend the heading text so
    # table parsers can detect '已验证' etc. from the section title.
    def _section_with_heading(text: str, *patterns: str) -> str:
        """Like _extract_section but prepends the matched heading line."""
        for i, line in enumerate(text.splitlines()):
            stripped = line.lstrip("#").strip()
            if line.startswith("#") and any(p.lower() in stripped.lower() for p in patterns):
                heading_level = len(line) - len(line.lstrip("#"))
                body_lines = [line]  # include heading
                for sub in text.splitlines()[i + 1:]:
                    if sub.startswith("#"):
                        cur_level = len(sub) - len(sub.lstrip("#"))
                        if cur_level <= heading_level:
                            break
                    body_lines.append(sub)
                return "\n".join(body_lines).strip()
        return ""

    industry_text = _section_with_heading(report_text, "第一类", "行业推荐", "industry")
    brand_text    = _section_with_heading(report_text, "第二类", "品牌直指", "brand direct")

    # Fallback: look for a single keywords section and split it
    if not industry_text and not brand_text:
        kw_section = _extract_section(report_text, "关键词", "keyword", "第三段")
        industry_match = re.search(
            r"(?:第一类|行业推荐型|industry)[^\n]*\n(.*?)(?=(?:第二类|品牌直指型|brand)[^\n]*\n|$)",
            kw_section, re.S | re.I,
        )
        brand_match = re.search(
            r"(?:第二类|品牌直指型|brand)[^\n]*\n(.*?)$",
            kw_section, re.S | re.I,
        )
        if industry_match:
            industry_text = industry_match.group(1)
        if brand_match:
            brand_text = brand_match.group(1)
        # Last resort: split in half
        if not industry_text and not brand_text and kw_section:
            kw_lines = kw_section.splitlines()
            mid = len(kw_lines) // 2
            industry_text = "\n".join(kw_lines[:mid])
            brand_text = "\n".join(kw_lines[mid:])

    industry_keywords = _parse_keyword_block(industry_text, is_industry=True)
    brand_keywords = _parse_keyword_block(brand_text, is_industry=False)

    keywords_data = {
        "industry": {
            "category": "行业推荐型",
            "description": "用户提问不包含目标品牌名，AI 在回答时会自然列举多个品牌",
            "count": len(industry_keywords),
            "keywords": industry_keywords,
        },
        "brand": {
            "category": "品牌直指型",
            "description": "用户提问中明确包含目标品牌/产品名称",
            "count": len(brand_keywords),
            "keywords": brand_keywords,
        },
    }

    return {
        "brand_name": brand_name,
        "brand_url": brand_url,
        "brand_summary": brand_summary,
        "user_image_summary": user_image_summary,
        "keywords_data": keywords_data,
        "personas": personas,
        # brand_mentions is now populated by run_competitor_discovery.py (via on_success)
        "brand_mentions": [],
        "coverage_summary": _parse_coverage_summary(report_text),
    }


# ---------------------------------------------------------------------------
# Subprocess helpers
# ---------------------------------------------------------------------------

def _run(cmd: list[str]) -> tuple[int, str, str]:
    """Run cmd as subprocess (no shell), return (returncode, stdout, stderr)."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def _create_sub_task_session(
    workspace: Path,
    sub_task_id: str,
    task_type: str,
    title: str,
    parent_task_id: str,
    metadata: dict | None = None,
) -> None:
    """Create a minimal task session so the sub-task is queryable via API.

    Writes a ``_task.json`` file in the standard session directory
    (``{workspace}/.tasks/sessions/{sub_task_id}/``).  The session is marked
    as ``status=success`` immediately because the sub-script already completed
    by the time this is called.
    """
    from datetime import datetime

    now = datetime.now().isoformat()
    session_dir = workspace / ".tasks" / "sessions" / sub_task_id
    session_dir.mkdir(parents=True, exist_ok=True)

    session_data = {
        "task_id": sub_task_id,
        "task_type": task_type,
        "title": title,
        "description": title,
        "status": "success",
        "metadata": metadata or {},
        "is_long_task": False,
        "need_review": False,
        "sync_memory": False,
        "subtasks": [],
        "usage": {},
        "final_result": "",
        "completed_at": now,
        "review_retries": 0,
        "profile": None,
        "coordinator_id": None,
        "replan_count": 0,
        "max_replans": 0,
        "temp_profiles": [],
        "created_at": now,
        "updated_at": now,
        "_parent_task_id": parent_task_id,
    }

    (session_dir / "_task.json").write_text(
        json.dumps(session_data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[on_success] Created session for {task_type}: {sub_task_id}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="on_success callback for geo_keyword_research")
    parser.add_argument("--task-id", required=True, help="Main task ID")
    parser.add_argument("--workspace", required=True, help="User workspace path")
    parser.add_argument("--config-file", required=True, help="Path to task.json (passed to sub-scripts)")
    args = parser.parse_args()

    task_id = args.task_id
    workspace = Path(args.workspace).expanduser().resolve()
    task_json_file = Path(args.config_file).expanduser().resolve()

    # Resolve the LLM provider config.json from task.json location or parent dirs.
    # Sub-scripts (product-image/extract.py, user-image/extract.py) need config.json,
    # not task.json, because they read agents.defaults.provider and providers.*.apiBase.
    config_file = task_json_file  # fallback
    for candidate_dir in [task_json_file.parent, task_json_file.parent.parent, Path.cwd()]:
        candidate = candidate_dir / "config.json"
        if candidate.exists():
            try:
                import json as _json
                _cfg = _json.loads(candidate.read_text("utf-8"))
                if "providers" in _cfg or "agents" in _cfg:
                    config_file = candidate
                    break
            except Exception:
                pass

    print(f"[on_success] Using config: {config_file}", file=sys.stderr)

    # ── Locate artifacts ────────────────────────────────────────────────────
    geo_dir = workspace / "geo-keyword-research" / task_id
    report_file = geo_dir / f"{task_id}_report.md"
    official_site = geo_dir / f"{task_id}_official_site.txt"
    result_file = geo_dir / f"{task_id}_result.json"

    # Read task metadata for brand_name (raw, as entered by user)
    # Note: must be read before the auto-recovery block so the brand name
    # is available as context for the LLM recovery prompt.
    brand_name_raw = ""
    task_session_file = workspace / ".tasks" / "sessions" / task_id / "_task.json"
    if task_session_file.exists():
        try:
            session_data = json.loads(task_session_file.read_text(encoding="utf-8"))
            meta = session_data.get("metadata") or {}
            # Prefer brand_name_raw (new key set by frontend), fall back to brand_name (legacy key)
            brand_name_raw = meta.get("brand_name_raw") or meta.get("brand_name", "")
        except Exception:
            pass

    # ── Report file check + auto-recovery ───────────────────────────────────
    if not report_file.exists():
        print(f"[on_success] WARNING: report.md not found: {report_file}", file=sys.stderr)
        print(f"[on_success] Attempting auto-recovery from page_*.txt files...", file=sys.stderr)
        recovered = _recover_report_with_llm(
            geo_dir=geo_dir,
            task_id=task_id,
            brand_name_raw=brand_name_raw,
            config_file=config_file,
            report_file=report_file,
        )
        if not recovered:
            print(f"[on_success] FATAL: report.md missing and auto-recovery failed: {report_file}",
                  file=sys.stderr)
            return 1
        print(f"[on_success] Auto-recovery succeeded — continuing with recovered report",
              file=sys.stderr)

    # Use LLM to split raw brand_name into brand_name + sku_name
    brand_name_fallback, sku_name_from_meta = _parse_brand_sku_with_llm(brand_name_raw, config_file)

    # Derive target_type: LLM found SKU → "sku", otherwise → "brand"
    target_type = "sku" if sku_name_from_meta else "brand"
    print(f"[on_success] target_type={target_type} (brand='{brand_name_fallback}' sku='{sku_name_from_meta}')",
          file=sys.stderr)

    # ── Parse report.md ─────────────────────────────────────────────────────
    report_text = report_file.read_text(encoding="utf-8")
    parsed = parse_report(report_text, brand_name_fallback=brand_name_fallback,
                          official_site_file=official_site)

    print(f"[on_success] Parsed report: brand={parsed['brand_name']}, "
          f"brand_url={parsed['brand_url']}, personas={[p['persona_name'] for p in parsed['personas']]}, "
          f"keywords industry={parsed['keywords_data']['industry']['count']} "
          f"brand={parsed['keywords_data']['brand']['count']}, "
          f"coverage_summary={len(parsed['coverage_summary'])}", file=sys.stderr)

    # ── Step 1.5: competitor discovery ──────────────────────────────────────
    brand_mentions = _run_competitor_discovery(
        workspace=workspace,
        task_id=task_id,
        brand_name=parsed["brand_name"],
        sku_name=sku_name_from_meta,
        target_type=target_type,
        config_file=config_file,
        geo_dir=geo_dir,
        report_file=report_file,
    )

    # ── Build initial result ─────────────────────────────────────────────────
    result: dict = {
        "brand_name": parsed["brand_name"],
        "sku_name": sku_name_from_meta,          # product SKU, e.g. "X1" / "吮指原味鸡"; empty string if N/A
        "brand_name_raw": brand_name_raw,             # raw user input before brand/SKU parsing, e.g. "红米k90"
        "target_type": target_type,                   # "brand" (no SKU) or "sku" (brand+SKU)
        "brand_url": parsed["brand_url"],
        "brand_summary": parsed["brand_summary"],
        "user_image_summary": parsed["user_image_summary"],
        "keywords_data": parsed["keywords_data"],
        "product_image_task_id": "",
        "user_image": [],
        # brand_mentions: populated by run_competitor_discovery.py (competitor-discovery skill)
        "brand_mentions": brand_mentions,             # [{brand, sku}] — identified competitors
        "coverage_summary": parsed["coverage_summary"], # [{insight, coverage_perc}] — research conclusion insights
    }

    # ── Step 2: product-image ────────────────────────────────────────────────
    # Primary path: use official_site.txt + brand_url (best quality input).
    # Fallback path: when official_site.txt is missing or brand_url is empty,
    #   write brand_summary to a temp file and use it as the web-content input
    #   so that product_image_task_id is always generated when brand_summary
    #   is available.
    if not PRODUCT_IMAGE_SCRIPT.exists():
        print(f"[on_success] WARNING: product-image script not found: {PRODUCT_IMAGE_SCRIPT}", file=sys.stderr)
    else:
        use_official_site = official_site.exists() and bool(parsed["brand_url"])
        brand_summary_text = parsed.get("brand_summary", "").strip()

        if use_official_site:
            web_content_path = str(official_site)
            product_url = parsed["brand_url"]
            print(
                f"[on_success] Running product-image extract for {parsed['brand_name']} "
                f"via official_site (sub_task_id pending)...", file=sys.stderr,
            )
        elif brand_summary_text:
            # Write brand_summary to a temp file as fallback input
            import tempfile as _tempfile
            _tmp = _tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", suffix=".txt", delete=False,
            )
            _tmp.write(f"{parsed['brand_name']}\n\n{brand_summary_text}")
            _tmp.close()
            web_content_path = _tmp.name
            product_url = parsed.get("brand_url", "")
            missing_reason = (
                "official_site.txt not found" if not official_site.exists()
                else "brand_url is empty"
            )
            print(
                f"[on_success] {missing_reason} — falling back to brand_summary "
                f"for product-image extract (brand={parsed['brand_name']})", file=sys.stderr,
            )
        else:
            web_content_path = ""
            product_url = ""
            print("[on_success] WARNING: brand_summary is also empty, skipping product-image", file=sys.stderr)

        if web_content_path:
            pi_task_id = f"tsk_{uuid.uuid4().hex[:8]}"
            cmd = [
                sys.executable, str(PRODUCT_IMAGE_SCRIPT),
                "--web-content-path", web_content_path,
                "--task-id", pi_task_id,
                "--output-dir", str(workspace / "product-image"),
                "--config-file", str(config_file),
            ]
            if product_url:
                cmd += ["--product-url", product_url]
            rc, stdout, stderr_out = _run(cmd)
            # Clean up temp file if we created one
            if not use_official_site and web_content_path:
                try:
                    Path(web_content_path).unlink(missing_ok=True)
                except Exception:
                    pass
            if stderr_out:
                for line in stderr_out.splitlines()[:10]:
                    print(f"[on_success][product-image] {line}", file=sys.stderr)
            if rc == 0:
                result["product_image_task_id"] = pi_task_id
                _create_sub_task_session(
                    workspace, pi_task_id, "product_image",
                    f"Product image for {parsed['brand_name']}",
                    parent_task_id=task_id,
                    metadata={"brand_name": parsed["brand_name"], "_parent_task_id": task_id},
                )
                print(f"[on_success] product-image OK, task_id={pi_task_id}", file=sys.stderr)
            elif rc == 2:
                print("[on_success] WARNING: product-image: no product detected (rc=2), skipping", file=sys.stderr)
            else:
                print(f"[on_success] WARNING: product-image failed (rc={rc}), skipping", file=sys.stderr)

    # ── Step 3: user-image (one per persona) ─────────────────────────────────
    if not USER_IMAGE_SCRIPT.exists():
        print(f"[on_success] WARNING: user-image script not found: {USER_IMAGE_SCRIPT}", file=sys.stderr)
    elif not parsed["personas"]:
        print("[on_success] WARNING: no personas found in report, skipping user-image", file=sys.stderr)
    else:
        for persona in parsed["personas"]:
            persona_name = persona["persona_name"]
            brief = persona["brief"]
            ui_task_id = f"tsk_{uuid.uuid4().hex[:8]}"
            print(f"[on_success] Running user-image extract for persona: {persona_name} (sub_task_id={ui_task_id})", file=sys.stderr)
            cmd = [
                sys.executable, str(USER_IMAGE_SCRIPT),
                "--brief", brief,           # list args — no shell injection risk
                "--task-id", ui_task_id,
                "--output-dir", str(workspace / "user-image"),
                "--config-file", str(config_file),
            ]
            rc, stdout, stderr = _run(cmd)
            if stderr:
                for line in stderr.splitlines()[:10]:
                    print(f"[on_success][user-image][{persona_name}] {line}", file=sys.stderr)
            if rc == 0:
                result["user_image"].append({
                    "persona": persona_name,
                    "task_id": ui_task_id,
                    "desc": brief,
                })
                _create_sub_task_session(
                    workspace, ui_task_id, "user_image",
                    f"User image: {persona_name}",
                    parent_task_id=task_id,
                    metadata={"persona_name": persona_name, "_parent_task_id": task_id},
                )
                print(f"[on_success] user-image OK: {persona_name} (task_id={ui_task_id})", file=sys.stderr)
            else:
                print(f"[on_success] WARNING: user-image for '{persona_name}' failed (rc={rc})", file=sys.stderr)

    # ── Step 4: write result.json ────────────────────────────────────────────
    geo_dir.mkdir(parents=True, exist_ok=True)
    result_file.write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[on_success] result.json written: {result_file}", file=sys.stderr)

    # ── Step 5: cleanup intermediate files ──────────────────────────────────
    # Keep: {task_id}_report.md, {task_id}_urls.md, {task_id}_result.json
    # Delete: *.tmp.md, page_*.txt, *_cate.txt, *_official_site.txt
    KEEP_SUFFIXES = {
        f"{task_id}_report.md",
        f"{task_id}_urls.md",
        f"{task_id}_result.json",
    }
    TEMP_PATTERNS = [
        f"{task_id}_search_*.tmp.md",   # search temp files
        "page_*.txt",                    # fetched web pages
        f"{task_id}_cate.txt",           # category temp file
        f"{task_id}_official_site.txt",  # official site (no longer needed after extract)
        f"{task_id}_competitors.json",   # competitor discovery intermediate file
    ]
    removed, failed = 0, 0
    for pattern in TEMP_PATTERNS:
        for f in geo_dir.glob(pattern):
            if f.name in KEEP_SUFFIXES:
                continue
            try:
                f.unlink()
                removed += 1
            except Exception as exc:
                print(f"[on_success] WARNING: could not delete {f.name}: {exc}", file=sys.stderr)
                failed += 1
    print(f"[on_success] Cleanup done: removed {removed} temp files"
          + (f", {failed} failed" if failed else ""), file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())

