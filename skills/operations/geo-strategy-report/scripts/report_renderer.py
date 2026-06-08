#!/usr/bin/env python3
"""Independent report renderer: MD → styled A4-printable HTML via LLM.

This module is intentionally standalone — it depends only on:
  - Python stdlib (codecs, http.client, json, re, ssl)
  - beautifulsoup4 + html5lib (for validation/repair)

It does NOT import anything from roleserver or nanobot internals,
making it easy to test, maintain, and reuse.
"""

import codecs
import http.client
import json
import re
import ssl
from urllib.parse import urlparse


# ── Custom exceptions ───────────────────────────────────────────────────

class HtmlRenderError(RuntimeError):
    """Raised when LLM call fails or returns empty content."""


class HtmlValidationError(RuntimeError):
    """Raised when generated HTML is fundamentally broken and cannot be repaired."""


# ── System prompt (verified version — auto-pagination via @page) ────────

SYSTEM_PROMPT = r"""# Role
你是一位精通数据可视化报告、咨询 PPT 转网页的资深前端架构师。你的任务是将用户提供的结构化文本，精准地转化为符合现代极简主义设计规范的、A4 打印级 HTML 报告代码。

# Design System Rules (设计系统规范)
你必须严格遵守以下 CSS 规范，并将其内置在输出的 `<style>` 标签中：

1. **配色方案 (Color Palette)**：
   - 主色调（品牌色）：深绿色 `#11673d`（用于页眉、表头、大数字、卡片核心标题）。
   - 背景与容器：主背景纯白 `#ffffff`；卡片或侧边栏淡背景 `#f4f7f5`；边框线 `#eef2ef`。
   - 文字颜色：正文深灰 `#333333`；辅助/次要文字浅灰 `#666666`。

2. **布局与打印分页 (Layout & Print Pagination)**：
   - **不要使用固定高度的 `.page` 容器！** 改为使用 CSS `@page` 规则来定义 A4 尺寸。
   - 在 CSS 中设置：
     ```
     @page { size: A4; margin: 15mm; }
     body { width: 210mm; margin: 0 auto; }
     ```
   - 使用 `.section` 包裹每个逻辑章节，每个 `.section` 设置 `page-break-inside: avoid;` 防止章节被截断。
   - 如果某个 `.section` 内容很长（如大表格），允许跨页，但在 `tr` 上设置 `page-break-inside: avoid;` 防止表格行被截断。
   - 使用 `page-break-before: always;` 在需要强制换页的地方（如大章节标题前）插入分页。

3. **排版层级 (Typography)**：
   - 字体族：优先使用现代系统级无衬线字体（-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif）。
   - 页眉大标题：`20px`，粗体。正文：`13px` 或 `14px`，行高 `1.6`。

4. **组件特征 (Components)**：
   - 卡片 (.card)：带 `1px solid #eef2ef` 边框，`border-radius: 6px`，`padding: 5mm`，无夸张阴影，保持极简主义。
   - 数据大数字 (.stat-number)：`font-size: 38px; font-weight: 800; color: #11673d; line-height: 1;`。

5. **组件间距 (Spacing)**：
   - 每个 `.section` 之间的 `margin-bottom` 为 `8mm`。
   - 卡片 `.card` 的 `margin-bottom` 为 `6mm`。
   - 表格 `table` 的 `margin-bottom` 为 `6mm`。
   - `h2` 标题的 `margin-top` 为 `8mm`，`margin-bottom` 为 `5mm`。

# HTML Component Structure Guide (组件构造指南)
在解析用户文本时，请自动识别以下场景并转换为对应的高级 HTML 结构：
- **场景 A：包含大数字或百分比的核心指标** -> 转换为横向并排的 `.stat-group` 卡片（使用 CSS Grid `grid-template-columns: repeat(4, 1fr)`）。
- **场景 B：包含侧边栏总结+右侧详细拆解** -> 转换为两栏布局（左侧 30% 宽带浅绿背景，右侧 70%）。
- **场景 C：多平台、多维度对比或并列概念** -> 转换为网格卡片布局。
- **场景 D：多行定量数据或命中率矩阵** -> 转换为极简 `<table>`，且表头必须为深绿底白字。

# HTML Structure (HTML 结构要求)
报告的整体结构应该是：
1. 一个 `.report-header` 区域：包含报告标题、日期、维度摘要，使用深绿色背景。
2. 多个 `.section` 区域：每个 section 包含 `h2` 标题和具体内容。section 之间由浏览器自动分页。
3. **不需要 footer 和页码**，打印时会自动处理。
4. **不要使用固定高度的 div 来模拟页面**。

# Output Requirements (输出要求)
1. 仅输出完整的、自包含的单文件 HTML 代码，包含 `<style>`，严禁包含任何外部 CSS 或 JS 库。
2. 确保开启 `-webkit-print-color-adjust: exact;` 和 `print-color-adjust: exact;` 属性。
3. 严格禁止自由发挥。不要添加任何花哨的渐变色或大圆角。
4. 不要输出任何 markdown 代码块标记或解释文字，直接输出HTML代码。"""


# ── Public API ──────────────────────────────────────────────────────────

def convert_md_to_html(md_content: str, config: dict) -> str:
    """Convert markdown report to validated A4-printable HTML via LLM streaming.

    Args:
        md_content: Markdown report content.
        config: Dict with keys ``api_key``, ``api_base``, ``model``.

    Returns:
        Validated and (if needed) repaired HTML string.

    Raises:
        HtmlRenderError: If LLM call fails or returns empty.
        HtmlValidationError: If HTML is fundamentally broken.
    """
    raw_html = _call_llm_streaming(md_content, config)
    cleaned = _clean_llm_output(raw_html)
    validated = _validate_and_repair_html(cleaned)
    return validated


# ── LLM streaming call ──────────────────────────────────────────────────

def _call_llm_streaming(md_content: str, config: dict) -> str:
    """Call OpenAI-compatible chat/completions with SSE streaming."""
    api_key = config["api_key"]
    api_base = config["api_base"]
    model = config["model"]

    parsed = urlparse(f"{api_base}/chat/completions")

    body = {
        "model": model,
        "stream": True,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"# User Data To Render (待渲染的用户原始数据)\n\n{md_content}"},
        ],
        "max_tokens": 16384,
        "temperature": 0.1,
    }

    payload = json.dumps(body, ensure_ascii=False).encode("utf-8")

    # SSL context — skip verification for corporate proxies
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    print(f"[report_renderer] Calling LLM ({model}) with streaming ...")

    conn = http.client.HTTPSConnection(
        parsed.hostname, parsed.port or 443, context=ctx, timeout=300,
    )
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "Accept": "text/event-stream",
    }

    try:
        conn.request("POST", parsed.path, body=payload, headers=headers)
        response = conn.getresponse()
    except Exception as exc:
        raise HtmlRenderError(f"LLM connection failed: {exc}") from exc

    if response.status != 200:
        err = response.read().decode("utf-8", errors="replace")[:1000]
        raise HtmlRenderError(f"LLM HTTP {response.status}: {err}")

    # Incremental UTF-8 decoder — avoids corrupting multi-byte CJK chars
    collected: list[str] = []
    char_count = 0
    decoder = codecs.getincrementaldecoder("utf-8")("replace")
    text_buffer = ""

    while True:
        chunk = response.read(4096)
        if not chunk:
            text_buffer += decoder.decode(b"", True)
            break
        text_buffer += decoder.decode(chunk, False)

        while "\n" in text_buffer:
            line, text_buffer = text_buffer.split("\n", 1)
            line = line.strip()
            if not line:
                continue
            if line.startswith("data: "):
                data_str = line[6:]
                if data_str == "[DONE]":
                    break
                try:
                    data = json.loads(data_str)
                    delta = data.get("choices", [{}])[0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        collected.append(content)
                        char_count += len(content)
                        if char_count % 5000 < len(content):
                            print(f"[report_renderer]   ... {char_count} chars", flush=True)
                except (json.JSONDecodeError, IndexError, KeyError):
                    pass

    conn.close()

    if not collected:
        raise HtmlRenderError("LLM returned empty content")

    full = "".join(collected)
    print(f"[report_renderer] LLM returned {len(full)} chars total")
    return full


# ── Output cleaning ─────────────────────────────────────────────────────

def _clean_llm_output(raw: str) -> str:
    """Strip <think> blocks, markdown fences, and find the HTML start."""
    # Remove <think>...</think> reasoning blocks
    cleaned = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL)

    # Strip markdown code fences
    cleaned = cleaned.strip()
    if cleaned.startswith("```html"):
        cleaned = cleaned[7:]
    if cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]

    # Find the real HTML start
    idx = cleaned.find("<!DOCTYPE")
    if idx == -1:
        idx = cleaned.find("<html")
    if idx > 0:
        cleaned = cleaned[idx:]

    return cleaned.strip()


# ── HTML validation & repair ────────────────────────────────────────────

def _validate_and_repair_html(html: str) -> str:
    """Validate structure and repair broken tags using html5lib.

    Checks:
      1. Must contain <html>, <body>, <style> tags.
      2. Body must have meaningful text content (>100 chars).

    Repair:
      - html5lib parses exactly like a browser, fixing unclosed/mismatched tags.
      - Original <style> blocks are preserved (html5lib can mangle them).

    Raises:
        HtmlValidationError if fundamental structure is missing.
    """
    from bs4 import BeautifulSoup

    lower = html.lower()

    # Phase 1 — structural checks
    if "<html" not in lower:
        raise HtmlValidationError("Missing <html> tag — LLM output is not HTML")
    if "<body" not in lower:
        raise HtmlValidationError("Missing <body> tag")
    if "<style" not in lower:
        raise HtmlValidationError("Missing <style> tag (no embedded CSS)")

    # Phase 2 — save original <style> blocks before html5lib rewrites them
    original_styles = re.findall(r"<style[^>]*>.*?</style>", html, re.DOTALL)

    # Phase 3 — parse & repair with html5lib (browser-grade)
    soup = BeautifulSoup(html, "html5lib")

    # Phase 4 — content check
    body = soup.find("body")
    if not body or len(body.get_text(strip=True)) < 100:
        raise HtmlValidationError("Body content too short — likely incomplete generation")

    # Phase 5 — reconstruct
    repaired = str(soup)

    # Phase 6 — re-inject original <style> blocks (html5lib may have altered them)
    repaired_styles = re.findall(r"<style[^>]*>.*?</style>", repaired, re.DOTALL)
    if original_styles and repaired_styles:
        for orig, rep in zip(original_styles, repaired_styles):
            repaired = repaired.replace(rep, orig, 1)

    print(f"[report_renderer] Validated & repaired: {len(repaired)} chars")
    return repaired
