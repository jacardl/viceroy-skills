#!/usr/bin/env python3
"""
Webpage Audit — Structured JSON Builder

Converts analyze_html.py raw analysis output into the AuditResultStructured
format expected by the frontend card renderer.

Input:  analyze_html.py JSON output (stdin or file path)
Output: result_structured JSON → stdout

Usage:
    python analyze_html.py page.html | python build_structured_result.py
    python build_structured_result.py analysis.json

Output schema:
    {
      "overall_score": int,           # 0-100
      "overall_description": str,     # summary text
      "cards": [
        {
          "id": str,                  # kebab-case dimension id
          "title": str,               # display title
          "score": int,               # 0-100
          "highlights": [str, ...],   # positive findings
          "recommendations": [str, ...] # improvement suggestions
        }
      ],
      "scores": {                     # flat scores for list-page preview
        "heading-hierarchy": int,
        "schema-markup": int,
        ...
        "overall": int
      }
    }
"""

from __future__ import annotations

import json
import sys
from typing import Any


# ---------------------------------------------------------------------------
# Dimension definitions (id, display title, scores_key in analyze_html output)
# ---------------------------------------------------------------------------

DIMENSIONS: list[tuple[str, str, str | None]] = [
    ("heading-hierarchy",    "Heading Hierarchy",          "heading_hierarchy"),
    ("schema-markup",        "Schema Markup",               "schema_markup"),
    ("semantic-html",        "Semantic HTML",               "semantic_html"),
    ("seo-metadata",         "SEO Metadata",                "metadata_seo"),
    ("content-balance",      "Content Balance",             "content_balance"),
    ("accessibility",        "Accessibility (WCAG)",        "accessibility"),
    ("navigation-links",     "Navigation & Links",          "navigation_links"),
    ("mobile-friendliness",  "Mobile-Friendliness",        "mobile_friendly"),
    ("performance",          "Performance",                 "performance"),
    ("image-optimization",   "Image Optimization",          "image_optimization"),
    ("security",             "Security",                    "security"),
    ("social-media",         "Social Media Integration",    "social_media"),
]


# ---------------------------------------------------------------------------
# Per-dimension highlight & recommendation builders
# These produce human-readable strings from raw analysis data — zero LLM.
# ---------------------------------------------------------------------------

def _build_heading_card(a: dict) -> tuple[list[str], list[str]]:
    h = a.get("heading_hierarchy", {})
    counts = h.get("counts", {})
    issues = h.get("issues", [])
    score = int(a["scores"]["heading_hierarchy"])

    highlights, recs = [], []

    h1 = counts.get("h1", 0)
    if h1 == 1:
        total = h.get("total", 0)
        h2 = counts.get("h2", 0)
        highlights.append(f"Perfect heading hierarchy — 1 H1, {h2} H2s, {total} total headings")
    elif h1 > 1:
        recs.append(f"Multiple H1 tags found ({h1}) — reduce to exactly one H1 per page")
    elif h1 == 0:
        recs.append("No H1 heading found — add a primary H1 to establish document structure")

    if h.get("has_proper_hierarchy"):
        highlights.append("No skipped heading levels — proper H1→H2→H3 nesting")

    for issue in issues:
        if issue.startswith("skipped_level"):
            parts = issue.split("_")
            recs.append(f"Heading level skipped from H{parts[-3]} to H{parts[-1]} — fix nesting")

    dupes = h.get("duplicates", {})
    for level, pairs in dupes.items():
        for text, count in pairs:
            recs.append(f'Duplicate {level.upper()} heading: "{text}" appears {count} times')

    if score >= 90 and not recs:
        highlights.append("Excellent heading structure — ideal for AI crawlers and screen readers")

    return highlights, recs


def _build_schema_card(a: dict) -> tuple[list[str], list[str]]:
    s = a.get("schema", {})
    score = int(a["scores"]["schema_markup"])
    highlights, recs = [], []

    if s.get("has_schemas"):
        types = s.get("schema_types", [])
        total = s.get("total_schemas", 0)
        highlights.append(f"{total} schema(s) detected: {', '.join(types[:5])}")
        if s.get("json_ld_count", 0) > 0:
            highlights.append("Clean JSON-LD implementation (preferred format)")
        if s.get("parse_errors", 0) == 0:
            highlights.append("No schema parse errors")
        if total < 3:
            recs.append("Add more schema types (Product, FAQ, BreadcrumbList) to improve AI understanding")
        recs.append("Consider adding SearchAction schema for site search functionality")
    else:
        highlights.append("(ZERO structured data detected — critical gap for AI visibility)")
        recs.append("Add JSON-LD Organization schema with name, URL, logo, and contact details")
        recs.append("Add WebPage or WebSite schema as baseline structured data")
        recs.append("Consider Product/Service schemas relevant to your content")

    return highlights, recs


def _build_semantic_card(a: dict) -> tuple[list[str], list[str]]:
    s = a.get("semantic_html", {})
    score = int(a["scores"]["semantic_html"])
    found = s.get("semantic_elements_found", {})
    missing = s.get("missing_core_semantic", [])
    highlights, recs = [], []

    if found:
        found_str = ", ".join(f"<{k}>×{v}" for k, v in found.items())
        highlights.append(f"Semantic elements found: {found_str}")
    if not missing:
        highlights.append("All core semantic regions present (header, nav, main, footer)")
    else:
        for tag in missing:
            recs.append(f"Missing <{tag}> — wrap appropriate content in semantic container")

    ratio = s.get("semantic_ratio_percent", 0)
    if ratio > 5:
        highlights.append(f"Semantic density ratio: {ratio:.1f}%")
    else:
        recs.append("Low semantic density — replace generic <div> containers with semantic HTML5 elements")

    return highlights, recs


def _build_seo_card(a: dict) -> tuple[list[str], list[str]]:
    seo = a.get("seo_basics", {})
    meta = a.get("metadata", {})
    score = int(a["scores"]["metadata_seo"])
    highlights, recs = [], []

    if seo.get("has_title"):
        tlen = seo.get("title_length", 0)
        if 30 <= tlen <= 70:
            highlights.append(f"Title tag present and well-sized ({tlen} chars — optimal 30-70)")
        else:
            recs.append(f"Title tag is {tlen} chars — aim for 30-70 characters")
    else:
        recs.append("Missing <title> tag — critical for SEO and AI understanding")

    if seo.get("has_description"):
        dlen = seo.get("description_length", 0)
        if 120 <= dlen <= 160:
            highlights.append(f"Meta description present and well-sized ({dlen} chars)")
        else:
            recs.append(f"Meta description is {dlen} chars — aim for 120-160 characters")
    else:
        recs.append("Missing meta description — add a 120-160 char description")

    if meta.get("open_graph_complete"):
        highlights.append("Complete Open Graph tags (title, description, image, url)")
    else:
        missing_og = meta.get("missing_required_og", [])
        if missing_og:
            recs.append(f"Missing Open Graph properties: {', '.join(missing_og)}")

    if meta.get("twitter_card_complete"):
        highlights.append("Complete Twitter Card configuration")
    else:
        recs.append("Add Twitter Card meta tags for better social sharing previews")

    if seo.get("has_canonical"):
        highlights.append("Canonical URL correctly specified")
    else:
        recs.append("Add <link rel='canonical'> to prevent duplicate content issues")

    return highlights, recs


def _build_content_card(a: dict) -> tuple[list[str], list[str]]:
    t = a.get("text_content", {})
    score = int(a["scores"]["content_balance"])
    highlights, recs = [], []

    ratio = t.get("text_to_code_ratio", 0)
    words = t.get("estimated_word_count", 0)

    if 25 <= ratio <= 40:
        highlights.append(f"Optimal text-to-code ratio: {ratio:.1f}% (ideal range 25-40%)")
    elif ratio < 15:
        recs.append(f"Very low text ratio ({ratio:.1f}%) — content may be too sparse for AI parsing")
    elif ratio > 50:
        recs.append(f"Very high text ratio ({ratio:.1f}%) — consider structuring content better")
    else:
        highlights.append(f"Text-to-code ratio: {ratio:.1f}%")

    if words >= 500:
        highlights.append(f"Estimated {words:,} words — sufficient content depth")
    elif words < 200:
        recs.append(f"Only ~{words} words detected — thin content may reduce AI understanding")

    return highlights, recs


def _build_a11y_card(a: dict) -> tuple[list[str], list[str]]:
    acc = a.get("accessibility", {})
    score = int(a["scores"]["accessibility"])
    highlights, recs = [], []

    if acc.get("language_specified"):
        highlights.append("Language attribute specified on <html> tag")
    else:
        recs.append("Add lang attribute to <html> — required for accessibility and AI language detection")

    missing_alt = acc.get("images_missing_alt", 0)
    if missing_alt == 0:
        highlights.append("All images have alt text — full accessibility compliance")
    else:
        recs.append(f"{missing_alt} image(s) missing alt text — add descriptive alt attributes")

    if acc.get("skip_link_present"):
        highlights.append("Skip-to-content link present — good keyboard navigation")
    else:
        recs.append("Add a skip-to-content link for keyboard and screen reader users")

    aria = acc.get("aria_attributes_found", 0)
    if aria > 0:
        highlights.append(f"ARIA attributes used ({aria} found) — enhanced accessibility")
    else:
        recs.append("Add ARIA roles and attributes to interactive elements")

    return highlights, recs


def _build_nav_card(a: dict) -> tuple[list[str], list[str]]:
    links = a.get("links", {})
    total = a.get("total_links", 0)
    score = int(a["scores"]["navigation_links"])
    highlights, recs = [], []

    internal = links.get("internal", 0)
    external = links.get("external", 0)
    generic = links.get("generic", 0)

    highlights.append(f"{internal} internal links, {external} external links, {total} total")

    if total > 0:
        gen_ratio = generic / total
        if gen_ratio < 0.1:
            highlights.append(f"Low generic/# link ratio ({generic} of {total}) — good descriptive anchors")
        else:
            recs.append(f"{generic} generic/# links found — replace with descriptive anchor text")

    if links.get("noopener", 0) > 0:
        highlights.append("External links use noopener for security")
    elif external > 0:
        recs.append("Add rel='noopener noreferrer' to external links for security")

    return highlights, recs


def _build_mobile_card(a: dict) -> tuple[list[str], list[str]]:
    mob = a.get("mobile", {})
    score = int(a["scores"]["mobile_friendly"])
    highlights, recs = [], []

    if mob.get("has_viewport"):
        highlights.append("Viewport meta tag present")
        if mob.get("viewport_width_device_width"):
            highlights.append("width=device-width correctly set for responsive layout")
        else:
            recs.append("Set viewport width=device-width for proper mobile scaling")
        if mob.get("viewport_user_scalable", True):
            highlights.append("User scalability enabled — good accessibility practice")
        else:
            recs.append("Enable user scalability (remove user-scalable=no) for accessibility")
    else:
        recs.append("Missing viewport meta tag — page will not render correctly on mobile")
        recs.append("Add: <meta name='viewport' content='width=device-width, initial-scale=1'>")

    return highlights, recs


def _build_performance_card(a: dict) -> tuple[list[str], list[str]]:
    perf = a.get("performance", {})
    score = int(a["scores"]["performance"])
    highlights, recs = [], []

    total_res = perf.get("total_external_resources", 0)
    css = perf.get("external_css", 0)
    js = perf.get("external_js", 0)

    highlights.append(f"{total_res} external resources ({css} CSS, {js} JS)")

    if total_res < 20:
        highlights.append("Low external resource count — excellent page load performance")
    elif total_res < 40:
        recs.append(f"Moderate external resources ({total_res}) — consider bundling CSS/JS")
    else:
        recs.append(f"High external resource count ({total_res}) — significantly impacts load time")
        recs.append("Audit and eliminate unused CSS/JS dependencies")

    if perf.get("inline_css", 0) > 5:
        recs.append("Excessive inline CSS detected — move to external stylesheet")

    return highlights, recs


def _build_image_card(a: dict) -> tuple[list[str], list[str]]:
    imgs = a.get("images", {})
    score = int(a["scores"]["image_optimization"])
    highlights, recs = [], []

    total = imgs.get("total", 0)
    if total == 0:
        highlights.append("No images found on page")
        return highlights, recs

    missing_alt = imgs.get("missing_alt", 0)
    lazy = imgs.get("lazy_loaded", 0)
    srcset = imgs.get("with_srcset", 0)
    width = imgs.get("with_width", 0)

    highlights.append(f"{total} images found")

    if missing_alt == 0:
        highlights.append("All images have alt text")
    else:
        recs.append(f"{missing_alt} image(s) missing alt text — required for accessibility and AI")

    if lazy > 0:
        highlights.append(f"{lazy} image(s) use native lazy loading — good performance practice")
    else:
        recs.append("Enable loading='lazy' on below-the-fold images for faster page load")

    if srcset > 0:
        highlights.append(f"{srcset} image(s) use srcset for responsive delivery")
    else:
        recs.append("Add srcset and sizes attributes for responsive image loading")

    no_dim = total - width
    if no_dim > 0:
        recs.append(f"{no_dim} image(s) missing width/height — specify dimensions to prevent CLS")

    return highlights, recs


def _build_security_card(a: dict) -> tuple[list[str], list[str]]:
    sec = a.get("security", {})
    highlights, recs = [], []

    mixed = sec.get("external_resource_without_https", 0)
    if mixed == 0:
        highlights.append("No mixed content — all resources served over HTTPS")
    else:
        recs.append(f"{mixed} resource(s) loaded over HTTP — switch all to HTTPS to prevent mixed content")

    if sec.get("has_http_equiv_csp"):
        highlights.append("Content-Security-Policy meta tag present")
    else:
        recs.append("Consider adding Content-Security-Policy header or meta tag")

    if sec.get("has_x_ua_compatible"):
        highlights.append("X-UA-Compatible header present")

    return highlights, recs


def _build_social_card(a: dict) -> tuple[list[str], list[str]]:
    social = a.get("social", {})
    meta = a.get("metadata", {})
    highlights, recs = [], []

    if social.get("og_complete"):
        highlights.append("Complete Open Graph configuration — ready for social sharing")
    else:
        missing = meta.get("missing_required_og", [])
        if missing:
            recs.append(f"Missing OG properties: {', '.join(missing)}")
        else:
            recs.append("Add Open Graph tags for better social media previews")

    if social.get("twitter_complete"):
        highlights.append("Complete Twitter Card configuration")
    else:
        recs.append("Add Twitter Card meta tags (twitter:card, twitter:title, twitter:image)")

    slinks = social.get("social_links_found", 0)
    if slinks > 0:
        highlights.append(f"{slinks} social media profile link(s) found")
    else:
        recs.append("Add links to your social media profiles for discoverability")

    return highlights, recs


# Map dimension id → builder function
_CARD_BUILDERS = {
    "heading-hierarchy":   _build_heading_card,
    "schema-markup":       _build_schema_card,
    "semantic-html":       _build_semantic_card,
    "seo-metadata":        _build_seo_card,
    "content-balance":     _build_content_card,
    "accessibility":       _build_a11y_card,
    "navigation-links":    _build_nav_card,
    "mobile-friendliness": _build_mobile_card,
    "performance":         _build_performance_card,
    "image-optimization":  _build_image_card,
    "security":            _build_security_card,
    "social-media":        _build_social_card,
}


# ---------------------------------------------------------------------------
# Score derivation for dimensions without a direct numeric score
# ---------------------------------------------------------------------------

def _security_score(a: dict) -> int:
    sec = a.get("security", {})
    score = 100
    if sec.get("external_resource_without_https", 0) > 0:
        score -= 40
    if not sec.get("has_http_equiv_csp", False):
        score -= 20
    return max(0, score)


def _social_score(a: dict) -> int:
    social = a.get("social", {})
    score = 0
    if social.get("og_complete"):
        score += 50
    if social.get("twitter_complete"):
        score += 30
    if social.get("social_links_found", 0) > 0:
        score += 20
    return min(100, score)


# ---------------------------------------------------------------------------
# Overall description builder
# ---------------------------------------------------------------------------

def _build_overall_description(overall: int, cards: list[dict], url: str = "") -> str:
    domain = url.replace("https://", "").replace("http://", "").split("/")[0] or "This page"

    if overall >= 85:
        quality = "excellent"
        outlook = "minor refinements could push it to near-perfect"
    elif overall >= 70:
        quality = "strong"
        outlook = "targeted improvements can significantly boost AI visibility"
    elif overall >= 55:
        quality = "moderate"
        outlook = "several important areas need attention to improve AI readability"
    else:
        quality = "below average"
        outlook = "fundamental issues need to be addressed for proper AI visibility"

    # find top 2 strengths and weaknesses
    sorted_cards = sorted(cards, key=lambda c: c["score"], reverse=True)
    strengths = [c["title"] for c in sorted_cards[:2] if c["score"] >= 70]
    weaknesses = [c["title"] for c in sorted_cards[-2:] if c["score"] < 60]

    parts = [f"{domain} shows {quality} AI optimization ({overall}/100)."]
    if strengths:
        parts.append(f"Key strengths: {' and '.join(strengths)}.")
    if weaknesses:
        parts.append(f"Priority improvements needed in: {' and '.join(weaknesses)}.")
    parts.append(f"With {outlook}.")

    return " ".join(parts)


# ---------------------------------------------------------------------------
# Main builder
# ---------------------------------------------------------------------------

# Weights for all 12 dimensions — must sum to 1.0
_DIMENSION_WEIGHTS: dict[str, float] = {
    "heading-hierarchy":   0.08,
    "schema-markup":       0.12,
    "semantic-html":       0.08,
    "seo-metadata":        0.12,
    "content-balance":     0.12,
    "accessibility":       0.10,
    "navigation-links":    0.08,
    "mobile-friendliness": 0.06,
    "performance":         0.06,
    "image-optimization":  0.06,
    "security":            0.06,
    "social-media":        0.06,
}


def build_structured(analysis: dict, url: str = "") -> dict:
    """Build AuditResultStructured from analyze_html output."""
    raw_scores = analysis.get("scores", {})

    cards = []
    flat_scores: dict[str, int] = {}

    for dim_id, dim_title, scores_key in DIMENSIONS:
        # Get score — prefer raw scores from analyze_html, fallback to derived
        if scores_key and scores_key in raw_scores:
            score = int(raw_scores[scores_key])
        elif dim_id == "security":
            score = _security_score(analysis)
        else:
            score = _social_score(analysis)

        flat_scores[dim_id] = score

        # Build highlights and recommendations
        builder = _CARD_BUILDERS.get(dim_id)
        if builder:
            highlights, recommendations = builder(analysis)
        else:
            highlights, recommendations = [], []

        cards.append({
            "id":              dim_id,
            "title":           dim_title,
            "score":           score,
            "highlights":      highlights,
            "recommendations": recommendations,
        })

    # Compute overall from all 12 dimensions with weights
    overall = int(round(sum(
        flat_scores.get(dim_id, 0) * _DIMENSION_WEIGHTS.get(dim_id, 0)
        for dim_id, _, _ in DIMENSIONS
    )))
    flat_scores["overall"] = overall
    overall_description = _build_overall_description(overall, cards, url)

    return {
        "overall_score":       overall,
        "overall_description": overall_description,
        "cards":               cards,
        "scores":              flat_scores,
    }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    if len(sys.argv) == 1:
        # Read from stdin
        raw = sys.stdin.read()
    elif len(sys.argv) == 2:
        with open(sys.argv[1], encoding="utf-8") as f:
            raw = f.read()
    else:
        print(
            f"Usage: {sys.argv[0]} [analysis.json]\n"
            "       Or pipe: python analyze_html.py page.html | python build_structured_result.py",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        analysis = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"Error: invalid JSON input — {e}", file=sys.stderr)
        sys.exit(1)

    result = build_structured(analysis)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
