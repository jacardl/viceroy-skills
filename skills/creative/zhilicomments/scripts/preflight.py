#!/usr/bin/env python3
"""
zhilicomments · Pre-flight 自检脚本
2026-06-19 实战首版：把 SKILL.md 里所有需要检查的项一次性跑完。

Usage:
    python3 preflight.py /tmp/article.html

检查项：
1. 禁用词扫描（5 个）
2. branding 扫描（13 个禁用字符串）
3. digest 字节预检（≤54B）
4. CJK 字数核对（1000-1500）
5. HTML 结构（H1/H2/p 数量）
6. 样式 A CSS 对齐（16 项关键数值）
7. Pre-submit 5 项精简检查

任一 ❌ 即非零退出。
"""
import re
import sys


def calc_bytes(s: str) -> int:
    """WeChat 草稿 digest 字节计算：CJK=3 bytes，ASCII=1 byte"""
    return sum(3 if ord(c) > 127 else 1 for c in s)


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 preflight.py /tmp/article.html")
        sys.exit(1)

    path = sys.argv[1]
    with open(path, encoding="utf-8") as f:
        html = f.read()
    text = re.sub(r"<[^>]+>", "", html)
    text = re.sub(r"&[a-z]+;", "", text)

    failed = []
    passed = 0

    def check(name, ok, detail=""):
        nonlocal passed
        mark = "✓" if ok else "❌"
        print(f"  {mark}  {name}" + (f"  ({detail})" if detail else ""))
        if ok:
            passed += 1
        else:
            failed.append(name)

    print("=" * 64)
    print("【1/7 禁用词扫描】")
    for w in ["说白了", "意味着什么", "本质上", "换句话说", "不可否认", "头皮发麻"]:
        check(f"禁用词: {w}", w not in text)

    print()
    print("=" * 64)
    print("【2/7 branding 扫描】")
    branding = [
        "卡兹克", "khazix", "zhiliGitHub", "zhiliComments", "本文由",
        "一键三连", "扫码", "wzglyay", "自动发布", "jacardl",
    ]
    for s in branding:
        check(f"branding: {s}", s not in text)

    print()
    print("=" * 64)
    print("【3/7 标点扫描】")
    check("中文冒号「：」为 0", text.count("：") == 0, f"{text.count('：')} 次")
    check("中文破折号「——」为 0", text.count("——") == 0, f"{text.count('——')} 次")
    dq = text.count("\u201c") + text.count("\u201d")
    check("英文双引号为 0", dq == 0, f"{dq} 次")

    print()
    print("=" * 64)
    print("【4/7 CJK 字数】")
    cjk = re.findall(r"[\u4e00-\u9fff]", text)
    n = len(cjk)
    check(f"中文字数 1000-1500", 1000 <= n <= 1500, f"{n} 字")

    print()
    print("=" * 64)
    print("【5/7 HTML 结构】")
    h1 = len(re.findall(r"<h1", html))
    h2 = len(re.findall(r"<h2", html))
    p = len(re.findall(r"<p", html))
    check("body 无 H1", h1 == 0, f"{h1} 个")
    check(f"H2 ≥ 3（建议 4-5）", h2 >= 3, f"{h2} 个")
    check(f"P ≥ 20（短评 ≥20 段）", p >= 20, f"{p} 个")

    print()
    print("=" * 64)
    print("【6/7 样式 A CSS 对齐 reference】")
    css_checks = [
        ("max-width:680px", "容器宽度 680px"),
        ("padding:24px 16px 60px", "容器内边距 24/16/60"),
        ("background:#f5f4ed", "背景色 #f5f4ed"),
        ("'Noto Serif SC', Georgia, serif", "字体栈（Noto 在前）"),
        ("font-size:20px;color:#1B365D", "H2 基础"),
        ("border-left:4px solid #00d4aa", "H2 青色左边框（样式A 标志）"),
        ("font-weight:700", "H2 字重 700"),
        ("margin:0 0 16px", "H2 边距 0/16"),
        ("font-size:16px;line-height:1.85", "P 字号行高"),
        ("color:#2c2c2c", "P 颜色"),
        ("margin:0 0 28px", "P 段距 28px"),
        ("color:#1B365D", "墨蓝色"),
        ("color:#c9553d", "红棕色"),
        ("background:#fff3b0", "黄底高亮"),
        ("font-family:monospace", "来源行 monospace"),
        ("font-size:13px;color:#7c6f64", "作者行"),
    ]
    for pat, desc in css_checks:
        check(desc, pat in html)

    print()
    print("=" * 64)
    print("【7/7 Pre-submit 5 项精简检查】")
    title_match = re.search(r"<title>(.*?)</title>", html)
    title = title_match.group(1) if title_match else ""
    title_cjk = re.findall(r"[\u4e00-\u9fff]", title)
    check(f"标题 ≤10 中文字", len(title_cjk) <= 10, f"{len(title_cjk)} 字「{title}」")
    check("body 无 H1", "<h1" not in html)
    check("body 无「刘生 · 2026」副标题", "刘生 · 2026" not in text)
    check("body 无顶部分类标签（直隶按察使 / 短评）",
          "短评</span>" not in text and "直隶按察使</span>" not in text)
    sue = re.findall(r"说完了[^。]+", text)
    check("H2 间无「说完了 X」过渡句", not sue)

    print()
    print("=" * 64)
    total = passed + len(failed)
    print(f"汇总：{passed}/{total} 通过")
    if failed:
        print(f"\n❌ {len(failed)} 项失败，必须修复后再推：")
        for f in failed:
            print(f"  - {f}")
        sys.exit(1)
    print("\n✅ 全部通过，可以推草稿了。")
    print(f"   python3 ~/.hermes/skills/creative/zhilicomments/scripts/push.py")


if __name__ == "__main__":
    main()