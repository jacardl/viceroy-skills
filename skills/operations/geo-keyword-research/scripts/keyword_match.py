#!/usr/bin/env python3
"""Keyword–persona question generation script.

For each user persona (with its profiles), generates questions for ALL
given keywords (industry, brand, custom) in batches. Then trims the
result to a configurable budget (default 150) while guaranteeing that
every keyword is covered by at least one question.

Flow:
  For each persona:
    1. Batch all keywords into groups of QUESTION_GEN_BATCH_SIZE.
    2. Per batch: one LLM call → {keyword, confidence, profile_questions[]} for each kw.
  After all personas:
    3. Flatten all (keyword, persona, profile_id, question) items.
    4. Sort by confidence descending.
    5. Reserve 1 item per keyword (highest confidence) to guarantee coverage.
    6. Fill remaining budget from sorted list.
    7. Rebuild persona-centric output structure.
  (Paraphrase pass): for each persona in final output, generate variants.

Usage:
    python3 keyword_match.py \
        --config-file config.json \
        --task-id tsk_xxx \
        --output-dir /workspace/geo-keyword-research/ \
        --metadata-file /workspace/.tasks/sessions/tsk_xxx/_task.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

try:
    import httpx
except ImportError:
    httpx = None  # type: ignore


def strip_think_tags(text: str) -> str:
    """Remove <think>...</think> blocks from LLM output."""
    if not text:
        return text
    return re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()


# ---------------------------------------------------------------------------
# LLM config & call (same pattern as user-image/extract.py)
# ---------------------------------------------------------------------------

def load_config(config_path: str) -> dict:
    """Load LLM configuration from config.json."""
    cfg = json.loads(Path(config_path).read_text("utf-8"))
    defaults = cfg.get("agents", {}).get("defaults", {})
    provider_name = defaults.get("provider", "openai")
    provider_cfg = cfg.get("providers", {}).get(provider_name, {})
    return {
        "api_key": provider_cfg.get("apiKey", ""),
        "api_base": provider_cfg.get("apiBase", ""),
        "model": defaults.get("model", "gpt-4"),
        "temperature": defaults.get("temperature", 0.3),
        "max_tokens": min(defaults.get("maxTokens", 4096), 8192),
        "rate_limit": provider_cfg.get("rateLimit", 0),
    }


_last_call_time: float = 0.0
_min_interval: float = 0.0


def _init_rate_limiter(rpm: int) -> None:
    global _min_interval
    if rpm > 0:
        _min_interval = 60.0 / rpm


def llm_call(
    http_client: "httpx.Client",
    model: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.3,
    max_tokens: int = 4096,
) -> tuple[str, dict]:
    """Make a single LLM call via streaming SSE, printing tokens to stderr in real time."""
    global _last_call_time

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": True,
    }

    max_retries = 5
    for attempt in range(max_retries + 1):
        if _min_interval > 0:
            elapsed = time.time() - _last_call_time
            if elapsed < _min_interval:
                time.sleep(_min_interval - elapsed)
            _last_call_time = time.time()

        try:
            content = ""
            call_usage: dict = {}
            with http_client.stream("POST", "/chat/completions", json=payload) as resp:
                resp.raise_for_status()
                for line in resp.iter_lines():
                    if not line.startswith("data: ") or line == "data: [DONE]":
                        continue
                    try:
                        d = json.loads(line[6:])
                        delta = (d.get("choices", [{}])[0]
                                   .get("delta", {}).get("content", ""))
                        if delta:
                            content += delta
                            # ── 实时流式输出到 stderr ──────────────────────
                            sys.stderr.write(delta)
                            sys.stderr.flush()
                        if "usage" in d and isinstance(d["usage"], dict):
                            call_usage = d["usage"]
                    except (json.JSONDecodeError, IndexError, KeyError):
                        pass
            # 流结束后换行，保持日志整洁
            sys.stderr.write("\n")
            sys.stderr.flush()
            return content.strip(), call_usage
        except Exception as e:
            err_str = str(e).lower()
            is_retryable = any(kw in err_str for kw in [
                "rate", "limit", "429", "too many", "500", "502", "503",
                "timeout", "disconnect", "connection",
            ])
            if is_retryable and attempt < max_retries:
                wait = min(2 ** attempt * 2, 60)
                print(f"  LLM call failed (attempt {attempt+1}/{max_retries}): {e}",
                      file=sys.stderr)
                time.sleep(wait)
            else:
                raise
    return "", {}



def _accumulate_usage(total: dict, call_usage: dict) -> None:
    for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
        total[key] = total.get(key, 0) + call_usage.get(key, 0)
    total["llm_calls"] = total.get("llm_calls", 0) + 1


def _write_usage_to_session(metadata_path: Path, usage: dict) -> None:
    try:
        task_data = json.loads(metadata_path.read_text("utf-8"))
        existing = task_data.get("usage", {})
        existing["total_prompt_tokens"] = existing.get("total_prompt_tokens", 0) + usage.get("prompt_tokens", 0)
        existing["total_completion_tokens"] = existing.get("total_completion_tokens", 0) + usage.get("completion_tokens", 0)
        existing["total_tokens"] = existing.get("total_tokens", 0) + usage.get("total_tokens", 0)
        existing["total_llm_calls"] = existing.get("total_llm_calls", 0) + usage.get("llm_calls", 0)
        task_data["usage"] = existing
        metadata_path.write_text(json.dumps(task_data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        print(f"[keyword_match] WARNING: failed to write usage to _task.json: {e}", file=sys.stderr)


def _parse_json(text: str) -> dict | list | None:
    cleaned = strip_think_tags(text)
    if cleaned.startswith("```"):
        first_nl = cleaned.index("\n") if "\n" in cleaned else 3
        cleaned = cleaned[first_nl + 1:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        try:
            from json_repair import repair_json
            repaired = repair_json(cleaned, return_objects=True)
            if isinstance(repaired, (dict, list)):
                return repaired
        except Exception:
            pass
    return None


def _load_paraphrase_skill() -> str:
    candidates = []
    try:
        from nanobot.agent.skills import BUILTIN_SKILLS_DIR
        candidates.append(BUILTIN_SKILLS_DIR / "geo-keyword-research/example/semantic-paraphrase-synonyms-SKILL.md")
    except ImportError:
        pass
    candidates.append(Path(__file__).parent.parent / "example/semantic-paraphrase-synonyms-SKILL.md")
    for p in candidates:
        if p.exists():
            return p.read_text("utf-8")
    return "你是语义改写专家。规则：1.保持意图，2.保留核心词，3.只输出JSON。"


PARAPHRASE_USER_PROMPT = """\
## 当前任务
严格按照上述 Skill 规则，为下列每个问题生成 {variants_count} 个语义等价变体。
## 原始问题列表
{questions_json}
## 输出格式（严格 JSON，禁止 markdown 代码块）
{{
  "results": [
    {{
      "profile_id": "...",
      "keyword": "...",
      "original": "...",
      "variants": ["变体1", "变体2"]
    }}
  ]
}}
要求：
- results 数组长度与输入条数完全一致，顺序对应
- 每个 variants 数组恰好 {variants_count} 个字符串
- 变体简短自然（≤20字），保留核心关键词，不同变体提问模式不同
"""


def paraphrase_persona(
    http_client: "httpx.Client",
    model: str,
    cfg: dict,
    matched_keywords: list[dict],
    variants_count: int,
    skill_content: str,
) -> tuple[list[dict], dict]:
    if not matched_keywords or variants_count <= 0:
        return matched_keywords, {}

    flat_input = []
    for mk in matched_keywords:
        kw = mk.get("keyword", "")
        for pq in mk.get("profile_questions", []):
            flat_input.append({
                "profile_id": pq["profile_id"],
                "keyword": kw,
                "original": pq["question"],
            })

    if not flat_input:
        return matched_keywords, {}

    questions_json = json.dumps(flat_input, ensure_ascii=False, indent=2)
    user_prompt = PARAPHRASE_USER_PROMPT.format(variants_count=variants_count, questions_json=questions_json)
    total_usage: dict = {}
    
    raw, call_usage = llm_call(http_client, model, skill_content, user_prompt, temperature=0.7, max_tokens=min(cfg["max_tokens"], 4096))
    _accumulate_usage(total_usage, call_usage)
    parsed = _parse_json(raw)

    if parsed and isinstance(parsed, dict):
        results = parsed.get("results", [])
        variants_map = {}
        for item in results:
            key = (item.get("profile_id", ""), item.get("keyword", ""))
            variants_map[key] = item.get("variants", [])
        updated_mks = []
        for mk in matched_keywords:
            kw = mk.get("keyword", "")
            updated_pqs = [{**pq, "variants": variants_map.get((pq["profile_id"], kw), [])} for pq in mk.get("profile_questions", [])]
            updated_mks.append({**mk, "profile_questions": updated_pqs})
        return updated_mks, total_usage

    return matched_keywords, total_usage


QUESTION_GEN_SYSTEM_PROMPT = (
    "你是品牌营销专家和用户行为分析师。"
    "你的任务是为指定用户画像下的每个 profile，"
    "针对所有给定关键词生成自然问题。"
    "问题必须简短（中文≤20字，英文≤15词）、像真人在聊天框里随手打的一句话。"
    "禁止加入身份描述、场景铺垫、冗余前缀。"
    "\n⚠️ 关键词类型约束："
    "industry=问题严禁具体品牌/产品名词；"
    "brand=问题必含品牌名；"
    "custom=问题必直接体现关键词核心词。"
    "同关键词不同 profile 的问题不得雷同。只输出 JSON，禁止 markdown。"
)

QUESTION_GEN_BATCH_TEMPLATE = """\
## 任务
为用户画像 [{persona}] 下的每个 profile，
针对下列 {count} 个关键词分别生成一个自然问题。
必须覆盖每一个关键词，不得遗漏。{location_lang_hint}

### 画像信息
- 画像名称：{persona}
- 画像描述：{persona_desc}

### Profiles（虚拟用户角色）
{profiles_text}

### 关键词列表（必须全部覆盖）
{keywords_list}

### 问题生成要求
- 问题长度：中文≤20字，英文≤15词
- 直接提问，禁止身份描述或场景铺垫
- 同关键词下不同 profile 的问题不得雷同，提问模式必须不同
- 小括号内是 keyword_type 约束：
  (industry) 问题严禁出现任何品牌/产品专有名词
  (brand) 问题必须包含关键词中的品牌名
  (custom) 问题必须直接体现关键词的核心词

### 输出格式（严格 JSON，禁止 markdown 代码块）
{{
  "results": [
    {{
      "keyword": "关键词文本",
      "keyword_type": "industry | brand | custom",
      "confidence": 85,
      "reason": "该画像对此关键词的兴趣度和相关性一句话",
      "profile_questions": [
        {{
          "profile_id": "profile-id-xxx",
          "question": "该 profile 会问的问题"
        }}
      ]
    }}
  ]
}}
要求：
- results 数组长度必须等于 {count}，顺序与关键词列表一致
- 每个 profile_questions 覆盖所有 profile
- confidence 范围 0-100
"""

QUESTION_GEN_BATCH_SIZE = 10


def gen_questions_batch(
    http_client, model, cfg,
    persona, persona_desc, keyword_batch, profiles, location, lang,
) -> tuple[list[dict], dict]:
    """One LLM call: generate questions for ONE persona × ONE batch of keywords."""
    location_lang_hint = ""
    if location.strip() or lang.strip():
        parts = []
        if location.strip():
            parts.append(f"目标地区：{location}")
        if lang.strip():
            parts.append(f"目标语言：{lang}")
        location_lang_hint = f"\n({', '.join(parts)})。问题必须符合当地语言表达习惯。"

    user_prompt = QUESTION_GEN_BATCH_TEMPLATE.format(
        persona=persona,
        persona_desc=persona_desc,
        location_lang_hint=location_lang_hint,
        count=len(keyword_batch),
        keywords_list=_format_keywords_list(keyword_batch),
        profiles_text=_format_profiles(profiles),
    )

    total_usage: dict = {}
    max_retries = 2
    for attempt in range(max_retries + 1):
        raw, call_usage = llm_call(
            http_client, model, QUESTION_GEN_SYSTEM_PROMPT, user_prompt,
            temperature=cfg["temperature"], max_tokens=cfg["max_tokens"],
        )
        _accumulate_usage(total_usage, call_usage)
        parsed = _parse_json(raw)

        results = parsed.get("results", []) if isinstance(parsed, dict) else []
        if isinstance(results, list) and len(results) == len(keyword_batch):
            validated = []
            for kw_entry, res in zip(keyword_batch, results):
                if not isinstance(res, dict):
                    res = {}
                validated.append({
                    "keyword":           kw_entry["keyword"],
                    "keyword_type":      kw_entry["keyword_type"],
                    "confidence":        int(res.get("confidence", 50)),
                    "reason":            res.get("reason", ""),
                    "profile_questions": res.get("profile_questions", []),
                })
            return validated, total_usage

        if attempt < max_retries:
            print(
                f"  [gen_batch] Retry {attempt+1}/{max_retries}: "
                f"expected {len(keyword_batch)} results, got "
                f"{len(results) if isinstance(results, list) else 'parse-fail'}",
                file=sys.stderr,
            )

    # Graceful degradation on all retries exhausted
    print(
        f"  [gen_batch] ⚠️ Giving up for persona '{persona}', "
        f"batch size={len(keyword_batch)}",
        file=sys.stderr,
    )
    return [
        {"keyword": kw["keyword"], "keyword_type": kw["keyword_type"],
         "confidence": 0, "reason": "生成失败", "profile_questions": []}
        for kw in keyword_batch
    ], total_usage



def _format_profiles(profiles):
    return "\n".join([f"- **{p.get('name')}** (ID: `{p.get('profile_id')}`): {p.get('brief')}" for p in profiles])


def _format_keywords_list(keywords):
    return "\n".join([f"{i}. [{kw.get('keyword_type')}] {kw.get('keyword')}" for i, kw in enumerate(keywords, 1)])


def gen_questions_for_persona(http_client, model, cfg, persona, persona_desc, all_keywords, profiles, location, lang) -> tuple[list[dict], dict]:
    total_usage: dict = {}
    matched_keywords = []
    batches = [all_keywords[i: i + QUESTION_GEN_BATCH_SIZE] for i in range(0, len(all_keywords), QUESTION_GEN_BATCH_SIZE)]
    for batch in batches:
        res, usage = gen_questions_batch(http_client, model, cfg, persona, persona_desc, batch, profiles, location, lang)
        _accumulate_usage(total_usage, usage)
        matched_keywords.extend(res)
    return matched_keywords, total_usage


def _flatten_all(persona_results):
    items = []
    for persona, matched_keywords in persona_results:
        for mk in matched_keywords:
            for pq in mk.get("profile_questions", []):
                items.append({**mk, "persona": persona, "profile_id": pq["profile_id"], "question": pq["question"]})
    return items


def _trim_to_budget(flat_items, max_questions):
    sorted_items = sorted(flat_items, key=lambda x: x["confidence"], reverse=True)
    selected, selected_ids, keyword_covered = [], set(), set()
    for item in sorted_items:
        if item["keyword"] not in keyword_covered:
            selected.append(item)
            selected_ids.add(id(item))
            keyword_covered.add(item["keyword"])
    for item in sorted_items:
        if id(item) not in selected_ids and len(selected) < max_questions:
            selected.append(item)
            selected_ids.add(id(item))
    return selected


def _rebuild_matches(selected_items, persona_order):
    from collections import OrderedDict
    mapping = OrderedDict((p, OrderedDict()) for p in persona_order)
    for item in selected_items:
        persona, kw = item["persona"], item["keyword"]
        if kw not in mapping[persona]:
            mapping[persona][kw] = {**{k: item[k] for k in ["keyword", "keyword_type", "confidence", "reason"]}, "profile_questions": []}
        mapping[persona][kw]["profile_questions"].append({"profile_id": item["profile_id"], "question": item["question"]})
    return [{"persona": p, "matched_keywords": list(kw_map.values())} for p, kw_map in mapping.items() if kw_map]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Keyword–persona question generation (all keywords × all personas)"
    )
    parser.add_argument("--config-file", required=True, help="Path to config.json")
    parser.add_argument("--task-id", required=True, help="Task ID")
    parser.add_argument("--output-dir", required=True, help="Output directory")
    parser.add_argument("--metadata-file", required=True, help="Path to _task.json with metadata")
    args = parser.parse_args()

    if httpx is None:
        print("ERROR: httpx not installed. Run: pip install httpx", file=sys.stderr)
        return 1

    # ── Read metadata ────────────────────────────────────────────────────────
    metadata_path = Path(args.metadata_file)
    if not metadata_path.exists():
        print(f"ERROR: metadata file not found: {metadata_path}", file=sys.stderr)
        return 1

    try:
        task_data = json.loads(metadata_path.read_text("utf-8"))
        metadata = task_data.get("metadata", {})
    except Exception as e:
        print(f"ERROR: failed to read metadata: {e}", file=sys.stderr)
        return 1

    keywords_data = metadata.get("keywords", {})
    user_images   = metadata.get("user_images", [])
    location      = metadata.get("location", "")
    lang          = metadata.get("lang", "")

    if not keywords_data:
        print("ERROR: metadata.keywords is empty", file=sys.stderr)
        return 1
    if not user_images:
        print("ERROR: metadata.user_images is empty", file=sys.stderr)
        return 1

    industry_keywords = keywords_data.get("industry", [])
    brand_keywords    = keywords_data.get("brand", [])
    raw_custom        = keywords_data.get("custom", [])

    # Normalize custom keywords: support plain strings or {keyword} dicts
    custom_keywords: list[dict] = []
    for ck in raw_custom:
        if isinstance(ck, str):
            custom_keywords.append({"keyword": ck, "reason": "用户自定义关键词"})
        elif isinstance(ck, dict):
            if not ck.get("keyword"):
                ck = {**ck, "keyword": ck.get("text", ck.get("name", ""))}
            custom_keywords.append(ck)

    # Build unified keyword list with type labels
    all_keywords: list[dict] = (
        [{**kw, "keyword_type": "industry"} for kw in industry_keywords]
        + [{**kw, "keyword_type": "brand"}    for kw in brand_keywords]
        + [{**kw, "keyword_type": "custom"}   for kw in custom_keywords]
    )

    print(
        f"[keyword_match] Input: {len(all_keywords)} keywords "
        f"(industry={len(industry_keywords)} brand={len(brand_keywords)} custom={len(custom_keywords)}), "
        f"{len(user_images)} personas, location={location}, lang={lang}",
        file=sys.stderr,
    )
    if custom_keywords:
        print(
            "[keyword_match] Custom keywords: "
            + ", ".join(repr(c.get("keyword", "")) for c in custom_keywords),
            file=sys.stderr,
        )

    # ── Load LLM config ──────────────────────────────────────────────────────
    cfg = load_config(args.config_file)
    _init_rate_limiter(cfg.get("rate_limit", 0))

    # ── Paraphrase config ─────────────────────────────────────────────────────
    variants_count = int(metadata.get("variants_count", 2))
    variants_count = max(0, min(10, variants_count))   # 0 = disabled
    paraphrase_skill = _load_paraphrase_skill() if variants_count > 0 else ""
    print(f"[keyword_match] paraphrase variants_count={variants_count}", file=sys.stderr)

    # ── Max questions budget ──────────────────────────────────────────────────
    max_questions = int(metadata.get("max_questions", 150))
    max_questions = max(len(all_keywords), max_questions)  # never below keyword count
    print(f"[keyword_match] max_questions budget={max_questions}", file=sys.stderr)

    client = httpx.Client(
        verify=False,
        timeout=httpx.Timeout(180.0, connect=30.0),
        headers={
            "Authorization": f"Bearer {cfg['api_key']}",
            "Content-Type": "application/json",
        },
        base_url=cfg["api_base"],
    )

    # ── Process each persona: generate questions for ALL keywords ─────────────
    persona_results: list[tuple[str, list[dict]]] = []
    total_usage: dict = {}
    persona_order: list[str] = []

    for ui in user_images:
        persona      = ui.get("persona", "")
        persona_desc = ui.get("desc", "")
        profiles     = ui.get("profiles", [])

        if not persona:
            print("[keyword_match] WARNING: skipping user_image with empty persona",
                  file=sys.stderr)
            continue

        persona_order.append(persona)
        print(
            f"[keyword_match] Processing persona: {persona} "
            f"({len(profiles)} profiles, {len(all_keywords)} keywords)",
            file=sys.stderr,
        )

        matched_keywords, persona_usage = gen_questions_for_persona(
            http_client=client,
            model=cfg["model"],
            cfg=cfg,
            persona=persona,
            persona_desc=persona_desc,
            all_keywords=all_keywords,
            profiles=profiles,
            location=location,
            lang=lang,
        )
        _accumulate_usage(total_usage, persona_usage)
        persona_results.append((persona, matched_keywords))
        kw_with_q = sum(1 for mk in matched_keywords if mk.get("profile_questions"))
        print(
            f"[keyword_match] ✅ {persona}: {kw_with_q}/{len(all_keywords)} keywords have questions",
            file=sys.stderr,
        )

    # ── Write usage back to _task.json ────────────────────────────────────────
    _write_usage_to_session(metadata_path, total_usage)

    # ── Flatten → trim → rebuild ──────────────────────────────────────────────
    flat_items = _flatten_all(persona_results)
    print(f"[keyword_match] Raw flat items: {len(flat_items)} (before trim)", file=sys.stderr)

    selected_items = _trim_to_budget(flat_items, max_questions)
    print(f"[keyword_match] Selected items after trim: {len(selected_items)}", file=sys.stderr)

    # ── Paraphrase pass (only on selected items) ──────────────────────────────
    if variants_count > 0 and paraphrase_skill:
        from collections import OrderedDict as _OD
        # Group selected items by persona → keyword for paraphrase batching
        _persona_mks: dict = _OD()
        for item in selected_items:
            p  = item["persona"]
            kw = item["keyword"]
            if p not in _persona_mks:
                _persona_mks[p] = _OD()
            if kw not in _persona_mks[p]:
                _persona_mks[p][kw] = {
                    "keyword":          kw,
                    "keyword_type":     item["keyword_type"],
                    "confidence":       item["confidence"],
                    "reason":           item.get("reason", ""),
                    "profile_questions": [],
                }
            _persona_mks[p][kw]["profile_questions"].append({
                "profile_id": item["profile_id"],
                "question":   item["question"],
            })

        _variants_lookup: dict = {}
        for persona, kw_od in _persona_mks.items():
            mks = list(kw_od.values())
            updated_mks, para_usage = paraphrase_persona(
                http_client=client,
                model=cfg["model"],
                cfg=cfg,
                matched_keywords=mks,
                variants_count=variants_count,
                skill_content=paraphrase_skill,
            )
            _accumulate_usage(total_usage, para_usage)
            for mk in updated_mks:
                kw = mk["keyword"]
                for pq in mk.get("profile_questions", []):
                    _variants_lookup[(persona, kw, pq["profile_id"])] = pq.get("variants", [])
            print(f"[keyword_match] ✅ {persona}: paraphrase done", file=sys.stderr)

        # Attach variants back onto selected_items
        for item in selected_items:
            key = (item["persona"], item["keyword"], item["profile_id"])
            item["variants"] = _variants_lookup.get(key, [])

    # ── Rebuild persona-centric matches from selected items ───────────────────
    matches = _rebuild_matches(selected_items, persona_order)

    # ── Coverage verification log ─────────────────────────────────────────────
    covered = {item["keyword"] for item in selected_items}
    missing = [kw["keyword"] for kw in all_keywords if kw["keyword"] not in covered]
    if missing:
        print(f"[keyword_match] ⚠️ {len(missing)} keyword(s) still uncovered: {missing}",
              file=sys.stderr)
    else:
        print(f"[keyword_match] ✅ All {len(all_keywords)} keywords covered in final output.",
              file=sys.stderr)

    # ── Write output ──────────────────────────────────────────────────────────
    output_dir  = Path(args.output_dir) / args.task_id
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{args.task_id}_keyword_match.json"

    output_data = {
        "location": location,
        "lang":     lang,
        "matches":  matches,
    }

    output_file.write_text(
        json.dumps(output_data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[keyword_match] Result written: {output_file}", file=sys.stderr)

    # ── Print summary to stdout (for task agent) ──────────────────────────────
    summary = {
        "status":           "success",
        "total_questions":  len(selected_items),
        "keywords_covered": len(covered),
        "keywords_total":   len(all_keywords),
        "personas_total":   len(user_images),
        "output":           str(output_file),
    }
    print(json.dumps(summary, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    sys.exit(main())

