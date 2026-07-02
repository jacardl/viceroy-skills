#!/usr/bin/env python3
"""
zhilicomments Pre-flight 自检脚本（2026-06-11 补写）
推送前最后一道关：禁用词 / branding / digest 字节 / CJK 字数 / HTML 结构。
用法: python3 preflight.py <html_path>
退出码: 0=通过, 1=失败
"""
import re
import sys
from pathlib import Path


# 禁用词清单（branding + 内容）
BANNED_WORDS = [
    "说白了", "意味着什么", "本质上", "换句话说", "不可否认",
    # 中文标点
    "：", "——", "\u201C", "\u201D", "  ",
]
BANNED_STRINGS = [
    "卡兹克", "khazix", "zhiliGitHub", "zhiliComments", "本文由",
    "一键三连", "扫码", "wzglyay", "自动发布", "jacardl",
]

# 虚词黑名单（5.5 铁律）
FILLER_WORDS = ["这种", "这回", "已经", "那种", "那一种", "给我说", "我给你"]


def calc_bytes(s: str) -> int:
    """WeChat 草稿 digest 字节计算：CJK = 3 bytes, ASCII = 1 byte"""
    return sum(3 if ord(c) > 127 else 1 for c in s)


def strip_html(html: str) -> str:
    """去掉 HTML 标签，保留正文文本"""
    return re.sub(r"<[^>]+>", " ", html)


def cjk_count(text: str) -> int:
    return sum(1 for c in text if '\u4e00' <= c <= '\u9fff')


def extract_digest(html: str) -> str:
    """从 <meta name="description"> 提取 digest（如果有），否则尝试找第一个 blockquote"""
    m = re.search(r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']*)["\']', html)
    if m:
        return m.group(1)
    m = re.search(r'<blockquote[^>]*>(.*?)</blockquote>', html, re.DOTALL)
    if m:
        return strip_html(m.group(1))[:80]
    return ""


def check(html: str) -> list:
    """返回 [(severity, category, message, line_no), ...]"""
    issues = []
    text = strip_html(html)
    text_lower = text  # 中文不分大小写

    # 1. 禁用词扫描
    for w in BANNED_WORDS:
        # BANNED_WORDS 里的中文标点要去掉空白再匹配
        w_clean = w.strip()
        if not w_clean:
            continue
        # 在原文 + 标签文本里都查
        for hay in (text, html):
            idx = hay.find(w_clean)
            if idx != -1:
                line_no = hay[:idx].count('\n') + 1
                issues.append(("ERROR", "禁用词", f"'{w_clean}'", line_no))
                break  # 同一词只报一次

    # 2. branding 扫描
    for s in BANNED_STRINGS:
        if s in text or s in html:
            line_no = html[:html.find(s)].count('\n') + 1 if s in html else 0
            issues.append(("ERROR", "branding", f"'{s}'", line_no))

    # 3. digest 字节预检
    digest = extract_digest(html)
    if digest:
        b = calc_bytes(digest)
        if b > 54:
            issues.append(("WARN", "digest字节", f"{b} 字节 (>{54} 上限)，可能触发 45004", 0))
        else:
            issues.append(("INFO", "digest字节", f"{b}/{54} 字节 ✓", 0))

    # 4. CJK 字数核对
    cjk = cjk_count(text)
    if not (1000 <= cjk <= 1500):
        issues.append(("ERROR", "CJK字数", f"{cjk} 字（要求 1000-1500）", 0))
    else:
        issues.append(("INFO", "CJK字数", f"{cjk} 字 ✓", 0))

    # 5. HTML 结构
    h1_count = len(re.findall(r"<h1[\s>]", html))
    h2_count = len(re.findall(r"<h2[\s>]", html))
    p_count = len(re.findall(r"<p[\s>]", html))
    if h1_count > 0:
        issues.append(("WARN", "HTML结构", f"<h1> 出现 {h1_count} 次（应放在草稿 title 字段，不应在 body）", 0))
    if h2_count < 2:
        issues.append(("WARN", "HTML结构", f"<h2> 数量 {h2_count}（建议 3-5 个）", 0))
    issues.append(("INFO", "HTML结构", f"h1={h1_count}, h2={h2_count}, p={p_count}", 0))

    # 6. 5.5 虚词精简扫描
    filler_hits = [w for w in FILLER_WORDS if w in text]
    if filler_hits:
        issues.append(("WARN", "虚词", f"命中: {', '.join(filler_hits)}（5.5 铁律）", 0))

    return issues


def main():
    if len(sys.argv) < 2:
        print("用法: python3 preflight.py <html_path>")
        sys.exit(2)

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"❌ 文件不存在: {path}")
        sys.exit(2)

    html = path.read_text(encoding="utf-8")
    issues = check(html)

    print(f"\n{'='*60}")
    print(f"🔍 zhilicomments Pre-flight: {path.name}")
    print(f"{'='*60}\n")

    errors = [i for i in issues if i[0] == "ERROR"]
    warns = [i for i in issues if i[0] == "WARN"]
    infos = [i for i in issues if i[0] == "INFO"]

    for sev, cat, msg, line in issues:
        icon = {"ERROR": "❌", "WARN": "⚠️ ", "INFO": "ℹ️ "}[sev]
        line_str = f" (line ~{line})" if line else ""
        print(f"  {icon} [{cat}]{line_str} {msg}")

    print(f"\n{'='*60}")
    print(f"  ERROR: {len(errors)} | WARN: {len(warns)} | INFO: {len(infos)}")
    print(f"{'='*60}")

    if errors:
        print("\n🚫 预检未通过，请修复后重跑。")
        sys.exit(1)
    else:
        print("\n✅ 预检通过，可以推 draft/add。")
        sys.exit(0)


if __name__ == "__main__":
    main()
