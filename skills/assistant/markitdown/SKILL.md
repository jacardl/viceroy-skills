---
name: markitdown
description: Microsoft MarkItDown document-to-Markdown workflow for PDFs, Office files, HTML pages, text, CSV/JSON/XML/ZIP, images/OCR, and batch corpus preparation. Use when converting local or downloaded files to Markdown, building RAG-ready corpora, cleaning HTML-to-Markdown boilerplate, pruning low-content outputs, or extracting text from documents for LLM analysis.
---

# MarkItDown

Microsoft MarkItDown converts files into Markdown for LLM analysis and knowledge-base preparation. Use it for PDF, Word, Excel, PowerPoint, images/OCR, audio transcription, HTML, CSV, JSON, XML, ZIP, EPUB, Outlook messages, YouTube transcripts, and batch document corpora.

## Core Workflow

1. Confirm the source directory, output directory, file types, and whether the user wants the Markdown folder flattened.
2. Use a local or bundled Python runtime when system Python is unavailable.
3. Install only needed extras, preferably into a project-local dependency directory for repeatable batch work.
4. Convert files with `MarkItDown().convert()` or `convert_local()`; copy plain text sources directly when conversion would add no value.
5. Write a status CSV with source path, output path, status, errors, byte counts, and any cleanup/pruning decisions.
6. Keep original downloaded files unless the user explicitly asks to remove them.

## Installation Patterns

```bash
pip install "markitdown[all]"
pip install "markitdown[pdf,docx,pptx,xlsx]"
```

For project-local installs:

```powershell
& "C:\Users\jacar\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m pip install --target .vendor/python "markitdown[pdf]"
```

In scripts, add the local dependency directory before import when needed:

```python
import sys
from pathlib import Path

vendor = Path(".vendor/python").resolve()
if vendor.exists():
    sys.path.insert(0, str(vendor))

from markitdown import MarkItDown
```

## CLI Usage

```bash
markitdown path-to-file.pdf -o document.md
markitdown file.docx > document.md
markitdown --list-plugins
```

Cloud extraction options such as Azure Document Intelligence can improve layout extraction, but only use them when the user accepts external processing.

## Python API

```python
from markitdown import MarkItDown

md = MarkItDown()
result = md.convert_local("report.pdf")
markdown = getattr(result, "markdown", None) or getattr(result, "text_content", "")
```

Use `convert_local()` for local files when possible. Use `convert_response()` only for trusted HTTP responses that you intentionally downloaded.

## Batch Conversion Rules

- Preserve source provenance in output names, for example `pdf_`, `html_`, or `text_` prefixes.
- If the user asks to remove second-level directories, flatten outputs into one Markdown directory and avoid filename collisions.
- For downloaded PDFs, verify the file is a real PDF before conversion. If a supposed PDF is actually HTML, login, or an error page, move or treat it as HTML rather than converting it as a PDF.
- Generate a `conversion_status.csv` after every batch conversion.
- Include a short `README.md` in the output folder that explains naming, counts, cleanup reports, and pruning reports.

## HTML-to-Markdown Cleanup

HTML pages often convert into Markdown with large amounts of boilerplate. Before counting, indexing, or using the content, clean the converted Markdown.

Remove or ignore:

- Navigation bars, menus, breadcrumbs, table-of-contents jump links, pagination, and repeated header links.
- Footer content such as legal notices, privacy links, copyright, site maps, contact blocks, and newsletter signups.
- Share/social blocks, related-article cards, recommendation lists, tag clouds, author widgets, cookie banners, and advertising.
- Pure link rows, link-dense list rows, and lines where visible text is mostly anchor text.
- Login, guest login, CAPTCHA, gated download, form-only, or access-denied pages; treat these as non-content even when they exceed the raw character threshold.

Use content anchors when available:

- Start at the article title, report title, first substantial heading, or `<main>/<article>` equivalent in the converted text.
- Stop at stable footer markers such as `Archive`, `Contact`, `Legal`, `Privacy`, `Subscribe`, `Related`, `Share`, `More from`, or language/site navigation blocks.
- For known vendors or publishers, add file-specific start/stop heuristics only when they are easy to verify from the converted text.

## Effective Text Counting

When the user gives a threshold such as “effective text must be at least 5000 characters”, do not count raw Markdown bytes.

Count effective text after removing:

- Markdown syntax, headings markers, bullets, tables separators, code fences, and HTML tags.
- URLs, image links, plain links, empty links, and link-heavy lines.
- Navigation/menu/footer/share/login boilerplate.
- Repeated punctuation, whitespace, and decorative separators.

CJK characters, letters, and digits can count as effective text after cleanup. If a file is under the threshold, delete only the converted Markdown output unless the user explicitly asks to delete originals. Always write a prune report with file, status, effective count, raw bytes, and reason.

Recommended prune statuses:

- `kept`: effective text meets threshold.
- `deleted`: below threshold or known non-content page.
- `excluded`: status/README/report files that are not content documents.

## Safety Rules

- Resolve absolute paths before deleting; ensure every deletion target stays inside the intended Markdown output directory.
- Never delete original downloads while pruning converted Markdown unless the user explicitly requests it.
- Avoid processing untrusted ZIPs or remote URLs without user intent; ZIP traversal and remote fetching can expose files or make network requests.
- Do not send credentials, cookies, tokens, or private documents to cloud OCR/layout services without explicit approval.

## Project Command Pattern

The East China Airlines agent research project used this sequence:

```powershell
# Convert downloaded PDF/HTML/text files to Markdown
& "C:\Users\jacar\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" "whitepaper-resources\convert_downloads_to_markdown.py"

# Flatten Markdown outputs into one directory
& "C:\Users\jacar\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" "whitepaper-resources\flatten_markdown_outputs.py"

# Remove HTML navigation, footer, share, link-heavy, and gated-page boilerplate
& "C:\Users\jacar\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" "whitepaper-resources\clean_html_markdown_boilerplate.py"

# Delete converted Markdown with effective text below the requested threshold
& "C:\Users\jacar\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" "whitepaper-resources\prune_short_markdown.py"
```

## Fit and Limits

MarkItDown is for analysis-oriented Markdown extraction, not high-fidelity layout reproduction. For scanned PDFs and image-heavy documents, use OCR or a document intelligence service only after checking privacy and cost constraints. For final publishing, run an additional human-readable cleanup pass after conversion.
