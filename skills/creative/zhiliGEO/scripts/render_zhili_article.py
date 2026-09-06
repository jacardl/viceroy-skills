#!/usr/bin/env python3
"""
直隶按察使 · zhiligithub markdown → HTML 渲染器（样式A）

用法:
  python3 render_zhili_article.py <draft.md> <article.html>
  python3 render_zhili_article.py draft.md article.html --title "打包器哲学:5MB把网页变桌面App"

设计原则（2026-06-21 沉淀）:
  - 精简规则：body 不放 H1 / 分类标签 / 「刘生」页脚 / 「六、总结」H2 / ✅❌ 适合不适合盒
  - H2 必须带 `border-left:4px solid #00d4aa` 左边框（样式A 签名特征）
  - 段落 `<p>` 用 `line-height:1.85`，图片占位符由 publish 阶段替换为 mmbiz URL
  - 整体走 block-level `''.join()` 拼接（不要 `\\n\\n.join`），避免 WeChat JSON payload 出现空段
  - 代码块用 `<br>` 分隔（不是真实 `\\n`），否则 WeChat 渲染成多段

占位符约定（markdown 里直接写）:
  - `[GitHub 元信息卡片]` → 替换为 GitHub 元信息 div（数据由本脚本根据 markdown 头部检测）
  - `[mmbiz <图注>]` → 替换为 `<img src="PLACEHOLDER" />` + 图注 `<p>`,发布前替换为 mmbiz URL
  - `---` → 分隔线 `· · ·`
  - `**bold**` → `<strong style="color:#1B365D">`（关键词/重点）
  - `**bold**` + 行末标点 → 视上下文
  - `` `code` `` → `<code>` 内联代码块（淡红字）
"""

import argparse
import re
import sys

# 样式A 核心 CSS（与 practical-writing-workflow.md / memory 一致）
H2_STYLE = (
    "font-size:20px;font-weight:bold;color:#1B365D;"
    "border-left:4px solid #00d4aa;padding-left:12px;margin:28px 0 12px 0;"
)
P_STYLE = "font-size:16px;line-height:1.85;color:#2c2c2c;margin:0 0 14px 0;"
DIVIDER = (
    '<div style="text-align:center;color:#c9553d;margin-bottom:24px;'
    'font-size:18px;letter-spacing:6px">· · ·</div>'
)
IMG_STYLE = "width:100%;border-radius:6px;margin:16px 0;display:block;"
CAPTION_STYLE = (
    "font-size:13px;color:#7c6f64;font-style:italic;margin:0 0 20px 0;text-align:center;"
)
CODE_PRE_STYLE = (
    "background:#1e1e1e;border-radius:6px;padding:14px 16px;margin:12px 0;overflow-x:auto;"
)
CODE_STYLE = (
    "font-family:Consolas,Monaco,Courier New,monospace;"
    "color:#e8e8e8;font-size:14px;line-height:1.5;"
)


def render_p(text: str) -> str:
    """段落内联渲染：内联 `code` + **bold**。"""
    text = re.sub(
        r"`([^`]+)`",
        r'<code style="background:#f0efe8;color:#c9553d;padding:1px 6px;'
        r'border-radius:3px;font-family:Consolas,Monaco,monospace;font-size:14px;">\1</code>',
        text,
    )
    parts = re.split(r"(\*\*[^*]+\*\*)", text)
    out = []
    for p in parts:
        if p.startswith("**") and p.endswith("**"):
            out.append(f'<strong style="color:#1B365D;font-weight:bold;">{p[2:-2]}</strong>')
        else:
            out.append(p)
    return "".join(out)


def render_code(code: str) -> str:
    """代码块：escape HTML + 用 <br> 分隔多行。"""
    escaped = code.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return (
        f'<pre style="{CODE_PRE_STYLE}"><code style="{CODE_STYLE}">'
        + "<br>".join(escaped.split("\n"))
        + "</code></pre>"
    )


def render_meta_card(stars: str, forks: str, language: str, license: str, url: str) -> str:
    """GitHub 元信息卡片：⭐ stars / 🍴 forks / language / license / url"""
    return (
        '<div style="display:flex;flex-wrap:wrap;gap:8px;margin:14px 0;'
        'padding:14px 16px;background:#efeee5;border-radius:6px;border:1px solid #d4d1c5;">'
        f'<span style="background:#1B365D;color:#f5f4ed;padding:3px 10px;'
        f'font-size:13px;border-radius:3px;">⭐ <strong>{stars}</strong></span>'
        f'<span style="background:#1B365D;color:#f5f4ed;padding:3px 10px;'
        f'font-size:13px;border-radius:3px;">🍴 <strong>{forks}</strong></span>'
        f'<span style="background:#1B365D;color:#f5f4ed;padding:3px 10px;'
        f'font-size:13px;border-radius:3px;">{language}</span>'
        f'<span style="background:#1B365D;color:#f5f4ed;padding:3px 10px;'
        f'font-size:13px;border-radius:3px;">{license}</span>'
        f'<span style="color:#6b665b;font-size:13px;padding:3px 0;">{url}</span>'
        "</div>"
    )


def parse_meta_from_md(md: str) -> dict:
    """
    从 markdown 头部找形如 `**Stars**：54.9k | **Forks**：10.9k | **Language**：Rust | **License**：GPL-3.0` 的行
    （项目研究阶段已写到 markdown 头部 / 注释里）
    """
    meta = {"stars": "", "forks": "", "language": "", "license": "", "url": ""}
    for line in md.split("\n")[:30]:
        for key, label in [
            ("stars", "stars"),
            ("forks", "forks"),
            ("language", "language"),
            ("license", "license"),
            ("url", "url"),
        ]:
            m = re.search(rf"\*\*{label}\*\*[::]\s*([^\s|]+)", line, re.IGNORECASE)
            if m and not meta[key]:
                meta[key] = m.group(1).strip()
    return meta


def md_to_blocks(md: str):
    """markdown → block 列表。H1 被吞掉（精简规则：body 不放 H1）。"""
    blocks = []
    lines = md.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            i += 1
            continue
        # H1 跳过（精简规则）
        if stripped.startswith("# ") and not stripped.startswith("## "):
            i += 1
            continue
        # H2
        if stripped.startswith("## "):
            blocks.append(("h2", stripped[3:].strip()))
            i += 1
            continue
        # 代码块
        if stripped.startswith("```"):
            code = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code.append(lines[i])
                i += 1
            i += 1
            blocks.append(("code", "\n".join(code)))
            continue
        # 分隔线
        if stripped == "---":
            blocks.append(("divider", None))
            i += 1
            continue
        # 图片占位符
        m_img = re.match(r"\[mmbiz (.+?)\]", stripped)
        if m_img:
            blocks.append(("img", m_img.group(1)))
            i += 1
            continue
        # 元信息卡片占位符
        if stripped.startswith("[GitHub"):
            blocks.append(("meta", None))
            i += 1
            continue
        # 段落（合并连续非空行）
        para = [stripped]
        i += 1
        while (
            i < len(lines)
            and lines[i].strip()
            and not lines[i].strip().startswith(("#", "##", "```", "---"))
            and not re.match(r"\[mmbiz|\[GitHub", lines[i].strip())
        ):
            para.append(lines[i].strip())
            i += 1
        blocks.append(("p", " ".join(para)))
    return blocks


def extract_title_from_md(md: str) -> str:
    """从 markdown 提取标题：优先 H1，其次第一个 H2，用于 <title> 和封面 prompt。"""
    for line in md.split("\n")[:10]:
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    # 没有 H1 时用第一个 H2（降级）
    for line in md.split("\n"):
        stripped = line.strip()
        if stripped.startswith("## "):
            return stripped[3:].strip()
    return ""


def render(md: str, title: str = "") -> str:
    """主渲染函数。

    Args:
        md: markdown 内容
        title: 可选，外部传入的标题（优先使用）。不传时从 markdown 提取。
    """
    meta = parse_meta_from_md(md)
    blocks = md_to_blocks(md)

    # 标题：优先使用外部传入的 title，否则从 markdown 提取（H1 > 第一个 H2）
    article_title = title if title else extract_title_from_md(md)

    out = []
    for b in blocks:
        if b[0] == "h2":
            out.append(f'<h2 style="{H2_STYLE}">{b[1]}</h2>')
        elif b[0] == "p":
            out.append(f'<p style="{P_STYLE}">{render_p(b[1])}</p>')
        elif b[0] == "divider":
            out.append(DIVIDER)
        elif b[0] == "code":
            out.append(render_code(b[1]))
        elif b[0] == "img":
            caption = b[1]
            # ⚠️ PLACEHOLDER 必须替换为 mmbiz URL 后才能 publish_zhili.py（image gate 拦截）
            out.append(f'<img src="PLACEHOLDER" style="{IMG_STYLE}" />')
            out.append(f'<p style="{CAPTION_STYLE}">▲ {caption}</p>')
        elif b[0] == "meta":
            out.append(
                render_meta_card(
                    meta["stars"] or "—",
                    meta["forks"] or "—",
                    meta["language"] or "—",
                    meta["license"] or "—",
                    meta["url"] or "github.com/",
                )
            )

    body = "".join(out)  # block-level, no separator

    return (
        "<!DOCTYPE html>\n"
        "<html>\n"
        "<head><meta charset=\"utf-8\">"
        f"<title>{article_title}</title>"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"></head>\n"
        "<body style=\"margin:0;padding:0;background-color:#f5f4ed;"
        "font-family:Georgia,'Times New Roman',serif;\">\n"
        "<div style=\"max-width:680px;margin:0 auto;padding:24px 16px 60px\">\n"
        f"{body}\n"
        "</div>\n"
        "</body>\n"
        "</html>\n"
    )


def main():
    ap = argparse.ArgumentParser(description="直隶按察使 · zhiligithub markdown → HTML 渲染器")
    ap.add_argument("input", help="markdown 草稿文件路径")
    ap.add_argument("output", help="HTML 输出文件路径")
    ap.add_argument("--title", required=True, help="文章标题（必须传入，嵌入 <title> 并用于封面生成）")
    args = ap.parse_args()

    with open(args.input, encoding="utf-8") as f:
        md = f.read()
    html = render(md, title=args.title)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(html)
    # 简要统计
    cn = re.sub(r"<[^>]+>", "", html)
    cn = re.sub(r"[^\u4e00-\u9fff]", "", cn)
    h2 = len(re.findall(r"<h2[^>]*>", html))
    img_count = html.count("<img ")
    print(f"[OK] {args.output} | 中文字数={len(cn)} H2={h2} 图片占位={img_count}")
    print(f"     ⚠️ 发布前需将 <img src=\"PLACEHOLDER\"> 替换为 mmbiz URL，否则 publish_zhili.py 会拦截")


if __name__ == "__main__":
    main()
