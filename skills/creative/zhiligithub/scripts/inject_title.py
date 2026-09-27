#!/usr/bin/env python3
"""inject_title.py — inject <title> tag into rendered HTML before push.

Usage:
    python3 inject_title.py "文章标题" /path/to/article.html

The render_zhili_article.py script does NOT inject <title>.
push.py extracts <title> from HTML to use as the WeChat draft title.
If <title> is missing, push.py defaults to "GitHub 黑马项目".
"""
import re, sys

def inject_title(title: str, html_path: str) -> None:
    with open(html_path, encoding="utf-8") as f:
        html = f.read()

    if re.search(r"<title>", html):
        print(f"[inject_title] <title> already present, skipping: {html_path}")
        return

    title_tag = f"<title>{title}</title>\n"
    # Insert after <head ...> tag
    html_out = re.sub(r"(<head[^>]*>)", r"\1\n" + title_tag, html, count=1)
    if html_out == html:
        # Fallback: insert before <body
        html_out = re.sub(r"(<body[^>]*>)", title_tag + r"\1", html, count=1)

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_out)

    m = re.search(r"<title>(.*?)</title>", html_out)
    print(f"[inject_title] title='{m.group(1)}' → {html_path}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: inject_title.py <title> <html_path>")
        sys.exit(1)
    inject_title(sys.argv[1], sys.argv[2])
