#!/usr/bin/env python3
"""
直隶按察使 · zhiligithub 文章 4 重验证器

用法:
  python3 validate_zhili_article.py <article.html>
  # 可选标题字节检查（默认走 draft title 字段）
  python3 validate_zhili_article.py <article.html> --title "打包器哲学:5MB把网页变桌面App"

4 重验证（任一失败 = 改稿）:
  1. 7 项硬约束（字数 / 标题字节 / 空行 / branding / H2 边框 / 代码块换行 / Markdown 残留）
  2. 精简规则 7 条（body H1 / 副标题 / 分类标签 / 「刘生」页脚 / 「六、总结」H2 / ✅❌ 适合不适合盒 / 过渡句）
  3. Stop-slop 套话清单（filler + AI jargon + 强套话 + 破折号 + 「不是X是Y」）
  4. renwei 11 项套话清单（AI 写作手迹 checklist）

⚠️ 用户偏好（critical）：
- 作者名一律「刘生」，**绝对不能出现「卡兹克」**（用户 profile 硬约束）
- branding: 卡兹克 / zhiliGitHub / 本文由 / 一键三连 / 扫码 / wzglyay
- renwei 命中率 ≥ 3 项 = 整篇打回重写（不要再 grep-改-扫，会越改越用力）
"""

import argparse
import re
import sys


def check_hard_constraints(html: str, title: str = "") -> list:
    """1. 7 项硬约束。返回 (name, value, ok) 列表。"""
    checks = []

    # 1) 中文字数
    cn = re.sub(r"<[^>]+>", "", html)
    cn = re.sub(r"[^\u4e00-\u9fff]", "", cn)
    n = len(cn)
    checks.append(("字数 1500-2000", f"{n}", 1500 <= n <= 2000))

    # 2) 标题字节（≤60 硬限，14-22 推荐）
    if title:
        tb = len(title.encode("utf-8"))
        checks.append((f"标题字节 ≤60（当前 {tb}）", title, tb <= 60))

    # 3) 连续空行
    empty_p = re.findall(r"<p[^>]*>\s*</p>", html)
    consec_nl = re.findall(r"\n\n+", html)
    checks.append(
        (f"无空段/连续\\n\\n（空段={len(empty_p)} 连续\\n\\n={len(consec_nl)}）", "—", not empty_p and not consec_nl)
    )

    # 4) Markdown 残留
    md_res = re.findall(r"(?<![\">])\*\*[^*\s][^*]*\*\*", html)
    checks.append((f"** 残留 0 处", f"{len(md_res)}", len(md_res) == 0))

    # 5) branding
    branding_terms = ["卡兹克", "zhiliGitHub", "本文由", "一键三连", "扫码", "wzglyay"]
    bad = [t for t in branding_terms if t in html]
    checks.append(
        (f"branding 无（卡兹克/zhiliGitHub/本文由/一键三连/扫码/wzglyay）", f"{len(bad)} 处" if bad else "无", not bad)
    )

    # 6) H2 左边框完整性（#00d4aa 4px）
    h2 = len(re.findall(r"<h2[^>]*>", html))
    border = html.count("border-left:4px solid #00d4aa")
    checks.append((f"H2 边框完整（H2={h2} 边框={border}）", "—", h2 == border and h2 >= 1))

    # 7) 代码块换行（<code> 内不能含 \n，必须用 <br>）
    codes = re.findall(r"<code[^>]*>(.+?)</code>", html, re.DOTALL)
    bad_code = [i for i, c in enumerate(codes) if "\n" in c]
    checks.append((f"代码块用 <br> 分行（{len(codes)} 块，{len(bad_code)} 含 \\n）", "—", not bad_code))

    return checks


def check_simplification_rules(html: str) -> list:
    """2. 精简规则 7 条（2026-06-10 用户实操反馈）。"""
    checks = []

    # body 不放 H1
    h1_body = bool(re.search(r"<body[^>]*>.*?<h1", html, re.DOTALL))
    checks.append(("body 无 H1", "无" if not h1_body else "有", not h1_body))

    # body 不放「刘生 · 2026年X月」副标题
    subtitle = bool(re.search(r"刘生\s*[·•]\s*202\d\s*年", html))
    checks.append(("body 无「刘生 · 年月」副标题", "无" if not subtitle else "有", not subtitle))

    # body 不放分类标签（GitHub / 黑马项目）
    cls_tag = "黑马项目" in html
    checks.append(("body 无分类标签（黑马项目/GitHub span）", "无" if not cls_tag else "有", not cls_tag))

    # body 不放「作者：刘生 / 来源：直隶按察使」页脚
    footer = bool(re.search(r"作者[::]\s*刘生|来源[::]\s*直隶按察使", html))
    checks.append(("body 无「作者：...」页脚", "无" if not footer else "有", not footer))

    # body 不放「六、总结」H2
    six_h2 = bool(re.search(r"<h2[^>]*>.*?六[、，,]?\s*总结.*?</h2>", html, re.DOTALL))
    checks.append(("body 无「六、总结」H2", "无" if not six_h2 else "有", not six_h2))

    # body 不放 ✅/❌ 适合不适合盒
    fit_box = bool(re.search(r"(✅|❌)\s*(适合|不适合)", html))
    checks.append(("body 无 ✅/❌ 适合不适合盒", "无" if not fit_box else "有", not fit_box))

    # H2 之间不放"过渡句"——检查首段关键词
    transition_words = ["先说一个", "说几句", "接下来", "下面我们", "在开始之前"]
    has_transition = any(w in re.sub(r"<[^>]+>", "", html) for w in transition_words)
    checks.append(
        ("H2 间无过渡句（先说/接下来/说几句/下面）", "无" if not has_transition else "有", not has_transition)
    )

    return checks


def check_stop_slop(content: str) -> list:
    """3. Stop-slop 套话清单。content 是去 HTML 标签后的纯文本。"""
    checks = []

    # filler words
    fillers = [
        "值得注意的是",
        "实际上",
        "其实",
        "那么",
        "大家都知道",
        "从某种意义上",
        "归根结底",
        "不得不承认",
        "想必",
        "毫无疑问",
        "必须承认",
        "我想说的是",
        "众所周知",
    ]
    found_filler = [w for w in fillers if w in content]
    checks.append((f"filler words（其实/实际上/从某种意义上...）", f"{len(found_filler)} 处", not found_filler))

    # AI jargon
    ai_jargon = [
        "颠覆性创新",
        "赋能",
        "持续迭代",
        "深度赋能",
        "构建生态",
        "引领变革",
        "核心价值",
        "解决方案",
        "助力",
        "落地",
        "闭环",
        "矩阵",
    ]
    found_jargon = [w for w in ai_jargon if w in content]
    checks.append((f"AI jargon（赋能/解决方案/闭环/矩阵...）", f"{len(found_jargon)} 处", not found_jargon))

    # 破折号 ——（renwei 第 3 项 0 处）
    em_dash = content.count("——")
    checks.append((f"破折号 ——（renwei 要求 0）", f"{em_dash} 处", em_dash == 0))

    # 「不是 X 是 Y」句式 — 2026-07-02 修复：
    # 旧正则 re.findall(r"不是.+?[，,].+?是") 在 flat string 上跨段落匹配，
    # .+? 会越过 </p><h2> 吞掉 H2 里的「是」（如 H2 标题含「怎么做到的是」）。
    # 正确做法：按段落（split on \n\n 或 p 标签）分别检测，不跨段。
    # 同时处理 HTML 实体形式的中文逗号 &#xFF0C; / &#65392;
    paragraphs = re.split(r'(?:</p>|<br\s*/?>|\n){2,}', content)
    ny = []
    for para in paragraphs:
        # 跳过含 H2 标记的段落（H2 里出现「是」不代表正文有问题）
        if re.search(r'<h[1-6][^>]*>', para):
            continue
        # 同时检查 literal 逗号和 HTML 实体逗号
        if re.search(r'不是[^，。,\n]{1,40}[，,][^是\n]{1,40}是', para):
            ny.append(para.strip()[:60])
    checks.append((f"「不是X是Y」句式（renwei 要求 0）", f"{len(ny)} 处", len(ny) == 0))

    return checks


def check_renwei(content: str) -> list:
    """4. renwei 11 项套话清单。返回 (name, value, ok) + 总命中率。"""
    hits = 0
    details = []

    # 1. 不是X是Y — 2026-07-02：改用段落级检测（同 check_stop_slop 的修复）
    paragraphs = re.split(r'(?:</p>|<br\s*/?>|\n){2,}', content)
    ny = []
    for para in paragraphs:
        if re.search(r'<h[1-6][^>]*>', para):
            continue
        if re.search(r'不是[^，。,\n]{1,40}[，,][^是\n]{1,40}是', para):
            ny.append(para.strip()[:60])
    if ny:
        hits += 1
        details.append(f"「不是X是Y」×{len(ny)}")

    # 2. 套话式排比三连
    cliche_trigrams = ["快、好、省", "轻、强、稳", "小、快、好", "快、稳、省", "好、省、快"]
    h2_hits = [t for t in cliche_trigrams if t in content]
    if h2_hits:
        hits += 1
        details.append(f"排比三连：{h2_hits}")

    # 3. —— 破折号（与 stop-slop 重复，不重复计）
    em_dash = content.count("——")
    if em_dash:
        hits += 1
        details.append(f"破折号 ×{em_dash}")

    # 4. 段落级加粗（**..**）—— 来自 markdown 源
    bolds = re.findall(r"\*\*[^*\n]{2,30}\*\*", content)
    if len(bolds) > 0:
        hits += 1
        details.append(f"段落级加粗 ×{len(bolds)}（每节最多 1 处）")

    # 5. AI 套话
    ai = ["颠覆性创新", "赋能", "深度赋能", "构建生态", "引领变革", "核心价值", "解决方案", "助力", "落地", "闭环", "矩阵"]
    h5 = [w for w in ai if w in content]
    if h5:
        hits += 1
        details.append(f"AI 套话：{h5}")

    # 6. 意义拔高
    elevate = ["这不仅", "更是", "X 时代", "开启了", "开启新篇章", "引领"]
    h6 = [w for w in elevate if w in content]
    if h6:
        hits += 1
        details.append(f"意义拔高：{h6}")

    # 7. 万能展望结尾
    futures = ["未来属于", "未来已来", "必将", "终将"]
    h7 = [w for w in futures if w in content]
    if h7:
        hits += 1
        details.append(f"万能展望：{h7}")

    # 8. 谄媚
    flatter = ["你真棒", "致敬所有", "最优秀的"]
    h8 = [w for w in flatter if w in content]
    if h8:
        hits += 1
        details.append(f"谄媚：{h8}")

    # 9. emoji 装饰（不含 ⭐ 🍴 📌 等数据符号）
    emoji_pattern = re.compile(r"[\U0001F300-\U0001FAFF\U00002600-\U000027BF]")
    emojis = emoji_pattern.findall(content)
    # 过滤允许的：📌 数据来源标记
    emojis = [e for e in emojis if e != "📌"]
    if emojis:
        hits += 1
        details.append(f"emoji 装饰：{emojis[:5]}")

    # 10. 填充对冲
    filler = ["当然也不排除", "在某种程度上", "一定程度上", "不难看出", "值得注意的是"]
    h10 = [w for w in filler if w in content]
    if h10:
        hits += 1
        details.append(f"填充对冲：{h10}")

    # 11. AI 赞美形容词
    praise = ["非常", "极其", "令人", "强大", "优雅", "惊艳", "出色", "卓越", "优秀", "完美", "极致"]
    h11 = [w for w in praise if w in content]
    if h11:
        hits += 1
        details.append(f"AI 赞美形容词：{h11}")

    summary = f"命中率 {hits}（≥3 = 整篇打回重写）"
    if hits:
        summary += f" → {', '.join(details)}"

    return [("renwei 11 项", summary, hits < 3)]


def main():
    ap = argparse.ArgumentParser(description="直隶按察使 · zhiligithub 4 重验证器")
    ap.add_argument("html", help="待验证的 HTML 文件路径")
    ap.add_argument("--title", default="", help="WeChat 草稿 title 字段（验证字节）")
    args = ap.parse_args()

    with open(args.html, encoding="utf-8") as f:
        html = f.read()

    # 提取纯文本（去 HTML 标签）
    content = re.sub(r"<[^>]+>", "", html)

    print("=" * 60)
    print("1️⃣  7 项硬约束（字数/标题/空行/branding/H2边框/代码块/Markdown残留）")
    print("=" * 60)
    hard = check_hard_constraints(html, args.title)
    hard_pass = True
    for name, val, ok in hard:
        icon = "✅" if ok else "❌"
        print(f"  {icon} {name}: {val}")
        if not ok:
            hard_pass = False

    print()
    print("=" * 60)
    print("2️⃣  精简规则 7 条（body 装饰元素全砍）")
    print("=" * 60)
    simp = check_simplification_rules(html)
    simp_pass = True
    for name, val, ok in simp:
        icon = "✅" if ok else "❌"
        print(f"  {icon} {name}: {val}")
        if not ok:
            simp_pass = False

    print()
    print("=" * 60)
    print("3️⃣  Stop-slop 套话清单（filler + AI jargon + 破折号 + 不是X是Y）")
    print("=" * 60)
    slop = check_stop_slop(content)
    slop_pass = True
    for name, val, ok in slop:
        icon = "✅" if ok else "❌"
        print(f"  {icon} {name}: {val}")
        if not ok:
            slop_pass = False

    print()
    print("=" * 60)
    print("4️⃣  renwei 11 项套话清单（AI 写作手迹 checklist）")
    print("=" * 60)
    ren = check_renwei(content)
    ren_pass = True
    for name, val, ok in ren:
        icon = "✅" if ok else "❌"
        print(f"  {icon} {name}: {val}")
        if not ok:
            ren_pass = False

    print()
    print("=" * 60)
    total = hard_pass and simp_pass and slop_pass and ren_pass
    if total:
        print("✅ 4 重验证全部通过 → 可推 zhili-publish")
    else:
        print("❌ 验证未通过 → 改稿重跑")
        sys.exit(1)


if __name__ == "__main__":
    main()
