"""
zhililong · markdown → zhili-publish 规范 HTML 转码器

用法：
    python3 markdown_to_html.py <input.md> <output.html>

转换规则：
- ## 章节 → <h2 style="...">章节</h2>
- **重点** → <strong style="color:#e63946;">重点</strong>
- > 引用 → <blockquote style="...">引用</blockquote>
- 普通段落 → <p style="...">段落</p>
- *脚注* → <p style="color:#888;font-size:14px;...">*脚注*</p>
- 跳过 # 主标题（传给 draft/add 的 title 字段）
- 用 ''.join() 拼接，块间无分隔符
- 所有样式 inline（微信公众平台过滤 <style> 标签）
"""
import sys
import re


def get_font_size_for_h2():
    return 18


def md_to_html(md: str) -> str:
    lines = md.split("\n")
    blocks = []
    buf = []

    for line in lines:
        s = line.strip()
        if not s:
            if buf:
                blocks.append(" ".join(buf))
                buf = []
        elif s.startswith("# "):
            # 主标题：跳过（传给 title 字段）
            if buf:
                blocks.append(" ".join(buf))
                buf = []
        elif s.startswith("## "):
            # 二级标题
            if buf:
                blocks.append(" ".join(buf))
                buf = []
            title = s[3:].strip()
            blocks.append(
                f'<h2 style="font-size:18px;font-weight:bold;margin:24px 0 12px 0;'
                f'padding-top:8px;text-align:left;color:#111;">{title}</h2>'
            )
        elif s.startswith("> "):
            # 引用块
            if buf:
                blocks.append(" ".join(buf))
                buf = []
            quote = s[2:].strip()
            blocks.append(
                f'<blockquote style="margin:16px 0;padding:12px 16px;background:#f8f6f0;'
                f'border-left:3px solid #c9b88c;font-size:15px;color:#555;line-height:1.6;'
                f'text-align:left;">{quote}</blockquote>'
            )
        elif s.startswith("*") and s.endswith("*") and len(s) > 2 and not s.startswith("**"):
            # *脚注* 单星号
            if buf:
                blocks.append(" ".join(buf))
                buf = []
            note = s.strip("* ")
            blocks.append(
                f'<p style="color:#888;font-size:14px;margin:0 0 16px 0;'
                f'text-align:left;">* {note}*</p>'
            )
        else:
            buf.append(s)

    if buf:
        blocks.append(" ".join(buf))

    # 段落 + 强调转换
    html_blocks = []
    for b in blocks:
        if b.startswith("<h2") or b.startswith("<blockquote") or b.startswith('<p style="color:#888'):
            html_blocks.append(b)
            continue
        # 转义
        b = escape_html(b)
        # **重点** → <strong>重点</strong>
        b = re.sub(r"\*\*(.+?)\*\*", r'<strong style="color:#e63946;">\1</strong>', b)
        # *单词*（行内斜体）→ 不处理（renwei 不写斜体）
        html_blocks.append(
            f'<p style="margin:0 0 16px 0;line-height:1.6;text-align:left;">{b}</p>'
        )

    return (
        '<div style="max-width:678px;margin:0 auto;padding:0 8px;'
        'font-size:16px;line-height:1.6;color:#333;text-align:left;">'
        + "".join(html_blocks)
        + "</div>"
    )


def escape_html(s: str) -> str:
    """转义非标签字符的 < > &"""
    # & 必须先转
    s = s.replace("&", "&amp;")
    # 只转不在标签内的 < 和 >
    # 这里用简化版：因为 markdown 里 < > 通常不出现
    s = s.replace("<", "&lt;").replace(">", "&gt;")
    return s


def main():
    if len(sys.argv) != 3:
        print("用法: python3 markdown_to_html.py <input.md> <output.html>")
        sys.exit(1)
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        md = f.read()
    html = md_to_html(md)
    with open(sys.argv[2], "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ HTML 转码完成: {sys.argv[2]} ({len(html)} chars)")


if __name__ == "__main__":
    main()
