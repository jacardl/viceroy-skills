---
name: webpage-audit
description: "The world's most comprehensive AI-powered webpage audit tool. Analyzes 15+ key dimensions including AI readability, structured data, SEO, accessibility, mobile-friendliness, performance, security, image optimization, and social media integration. Delivers actionable recommendations with scored assessments."
---

# Ultimate Webpage Audit - The Most Comprehensive Web Analysis Tool

## Overview

This is the **world's most comprehensive** AI-powered webpage audit tool that analyzes every critical aspect of a webpage for optimization. It goes far beyond basic checks to deliver deep insights across **15+ scoring dimensions** with actionable recommendations for improvement.

Whether you're auditing for AI readability, SEO, accessibility, performance, or modern web best practices — this tool gives you professional-grade analysis with concrete, prioritized recommendations.

## Core Capabilities (15+ Scoring Dimensions)

When given a webpage URL (or HTML content), the skill produces a structured audit report with the following scoring dimensions (0-100 each):

---

### 🎯 **1. AI Optimization Score (AIO) - Overall**
The **first-ever composite score** that measures how well your webpage is optimized for AI systems, search engines, and modern web crawlers. Combines all 15 dimensions into a single actionable score.

> **What it measures:** Overall AI-readability, structured data completeness, content structure, and machine understanding.

---

### 📊 **2. Heading Hierarchy Score**
Deep analysis of document outline, proper heading nesting, duplicate detection, and semantic structure.

**Checks for:**
- Proper H1-H6 nesting (prevents level skipping)
- Single vs multiple H1 detection
- Duplicate heading text identification
- Document outline completeness
- Zero heading detection

---

### 🏷️ **3. Schema Markup & Structured Data Score**
Comprehensive analysis of all schema.org implementations including JSON-LD, microdata, and RDFa.

**Checks for:**
- JSON-LD parsing and validation
- Schema type detection and counting
- Proper @context and @type validation
- Parse error detection
- Multiple schema format support
- Recommended extension schemas

---

### 🌐 **4. Semantic HTML Score**
Evaluates proper usage of modern semantic HTML5 elements.

**Checks for:**
- Core semantic elements (<main>, <nav>, <header>, <footer>)
- Advanced semantics (<section>, <article>, <figure>, <figcaption>, <details>)
- Semantic density ratio (vs div/spam)
- Missing core semantic regions

---

### 🏴 **5. SEO Metadata Score**
Complete metadata analysis covering basic SEO, Open Graph, and Twitter Cards.

**Checks for:**
- Title tag presence and length
- Meta description presence and length
- Canonical URL detection
- Robots directives
- Hreflang annotations
- Complete Open Graph (all 4 required properties)
- Complete Twitter Card configuration
- Charset declaration

---

### 📝 **6. Content Balance Score**
Text-to-HTML ratio analysis and content density measurement.

**Checks for:**
- Optimal 25-40% text-to-code ratio
- Estimated word count
- Content density evaluation
- Thin content detection
- Code-bloat detection

---

 ♿ **7. Accessibility (WCAG) Score**
Web accessibility evaluation based on WCAG principles.

**Checks for:**
- Image alt text completeness (missing alt detection)
- Language attribute specification
- Skip link detection for keyboard navigation
- ARIA attribute usage
- Form labeling best practices
- Minimum accessibility requirements

---

### 🧭 **8. Navigation & Link Structure Score**
Internal/external link analysis and navigability assessment.

**Checks for:**
- Internal vs external link counting
- Generic/# empty link detection
- Nofollow attribute usage
- Noopener security attribute usage
- Social media link detection
- Descriptive anchor text best practices

---

### 📱 **9. Mobile-Friendliness Score**
Mobile optimization checks based on Google best practices.

**Checks for:**
- Viewport meta tag presence
- `device-width` configuration
- User scalability enabled/disabled
- Responsive design indicators

---

### ⚡ **10. Performance Indicators Score**
Client-side performance optimization assessment.

**Checks for:**
- External CSS/JS resource counting
- Inline CSS/JS detection
- Total external resource estimation
- Performance bloat indicators

---

### 🖼️ **11. Image Optimization Score**
Image optimization and accessibility analysis.

**Checks for:**
- Missing alt text detection
- Lazy loading adoption
- Width/height dimension specification
- srcset responsive image support
- sizes attribute usage

---

### 🔒 **12. Security Best Practices**
Security header and HTTPS detection.

**Checks for:**
- Content-Security-Policy meta detection
- X-UA-Compatible compatibility header
- Mixed content detection (HTTP resources on HTTPS)
- Mixed content warnings

---

### 🌍 **13. Social Media Integration Score**
Open Graph and Twitter Card completeness for social sharing.

**Checks for:**
- Required OG properties (title, description, image, url)
- Twitter Card requirements
- Social media link presence
- Social sharing readiness

---

### 🚀 **14. Modern Web Features**
Detection of modern web capabilities.

**Checks for:**
- AMP detection
- PWA manifest detection
- Service Worker detection
- Schema.org presence in any format

---

## Workflow

> **⚠️ CRITICAL: You MUST follow these steps EXACTLY. Do NOT skip any step. Do NOT generate your own JSON output. The downstream system reads `result_structured.json` and will FAIL if the file is missing or has a non-standard schema.**

### Step 1 — Fetch Content
Use `web_crawl` to retrieve the full webpage HTML content from the provided URL.

### Step 2 — Save HTML to Disk (MANDATORY)
Save the fetched HTML content to the session directory:
```
write_file {session_dir}/page.html
```

### Step 3 — Run analyze_html.py (MANDATORY)
Execute the Python analyzer script. This produces scores and raw analysis data:
```
exec python3 {script_dir}/analyze_html.py {session_dir}/page.html > {session_dir}/analysis.json
```
**Do NOT attempt to calculate scores yourself.** The script handles all 12 scoring dimensions.

### Step 4 — Run build_structured_result.py (MANDATORY)
Execute the structured result builder. This converts analysis data into the card-format JSON required by the frontend:
```
exec python3 {script_dir}/build_structured_result.py {session_dir}/analysis.json > {session_dir}/result_structured.json
```
**Do NOT skip this step. Do NOT generate the structured result yourself.**

### Step 5 — Confirm Completion
Reply with a **single-line confirmation only**, e.g.:
```
"Audit complete for example.com. Overall score: 79/100."
```

> **🚫 FORBIDDEN ACTIONS:**
> - Do NOT generate your own JSON result — always use the Python scripts above
> - Do NOT output a lengthy markdown report
> - Do NOT create `result_structured.json` by writing JSON directly — it MUST be produced by `build_structured_result.py`
> - Do NOT invent your own schema (e.g. `critical_issues`, `important_issues`, `opportunities`) — the ONLY valid schema contains a `cards` array produced by the script


## Scoring Standards

| Dimension | Good (≥80) | Needs Improvement (50-79) | Poor (<50) |
|-----------|------------|---------------------------|------------|
| **AI Optimization (AIO)** | Excellent AI-readability, very few issues | Some issues, good foundation | Major problems need addressing |
| **Heading Hierarchy** | Proper nesting, no duplicates, single H1 | Minor issues, mostly good | Multiple duplicates, major level skipping |
| **Schema Markup** | Multiple schemas, correct JSON-LD | Primary schema present | No schemas or invalid markup |
| **Semantic HTML** | All core regions use semantics | Some semantic elements | All divs/spans, no semantics |
| **SEO Metadata** | Complete OG + Twitter + basics | Basic SEO complete | Missing title/description |
| **Content Balance** | 25-40% text ratio | 15-24% or 41-50% | <15% or >50% |
| **Accessibility** | All images have alt, language set | Minor issues missing | Multiple accessibility problems |
| **Navigation** | <10% generic links, clear structure | 10-25% generic links | >25% generic links |
| **Mobile-Friendly** | Viewport properly configured | Viewport present but incomplete | No viewport tag |
| **Performance** | <20 external resources | 20-40 external resources | >40 external resources |
| **Image Optimization** | <10% missing alts, dimensions set | 10-30% missing alts | >30% missing alts |

## Scoring Methodology

The overall **AI Optimization Score (AIO)** uses a weighted composite across all 12 scoring dimensions (weights sum to 100%):

| Dimension | Weight | Rationale |
|-----------|--------|-----------|
| Heading Hierarchy | 8% | Fundamental document structure |
| Schema Markup | 12% | Critical for AI understanding |
| Semantic HTML | 8% | Semantic structure for machines |
| SEO Metadata | 12% | Critical for search & social |
| Content Balance | 12% | Content density for AI readability |
| Accessibility | 10% | Accessibility benefits all users |
| Navigation/Links | 8% | Site structure understanding |
| Mobile-Friendly | 6% | Modern web requirement |
| Performance | 6% | User experience & crawling |
| Image Optimization | 6% | Accessibility & performance |
| Security | 6% | HTTPS & CSP best practices |
| Social Media | 6% | Social sharing & discoverability |

## Priority Recommendation System

After analysis, the tool automatically prioritizes recommendations:

1. **Critical** - Fix immediately (missing H1, no schema, all images missing alt)
2. **Important** - Should fix soon (poor heading hierarchy, incomplete metadata)
3. **Opportunity** - Improvement opportunities (add more schemas, enable lazy loading)

## Example Complete Report

See `references/full-example-report.md` for a complete real-world audit example.

## Usage

Simply provide a URL and ask for an audit:

> "Audit https://example.com and give me a complete report"

The tool handles everything automatically: fetching, analysis, scoring, and report generation.

## Key Differentiators

Why this is the most comprehensive webpage audit skill available:

- ✅ **15 scoring dimensions** (vs 5-7 in other tools)
- ✅ **All schema formats supported** (JSON-LD, microdata, RDFa)
- ✅ **Accessibility (WCAG) analysis** built-in
- ✅ **Mobile-friendliness checking**
- ✅ **Image optimization audit**
- ✅ **Performance indicators**
- ✅ **Security best practices**
- ✅ **Social media integration**
- ✅ **Python-powered deep parsing** (not superficial checks)
- ✅ **Actionable recommendations** not just scores
- ✅ **Prioritized improvement roadmap**
- ✅ **AI-readability focus** for modern AI crawlers and LLMs
