"""
zhililong · 事后清单自检脚本

用法：
    python3 post_edit_check.py <article.md>

输出：11 项硬约束检查结果（每项 ✅/❌ + 命中位置）
"""
import sys
import re


def check_no_x_but_y(text: str) -> list:
    """检查 '不是 X 而是 Y' 句式"""
    return [m.start() for m in re.finditer(r"不是[^，。]*?而是", text)]


def check_parallel_three(text: str) -> list:
    """检查排比三连（连续 3 个顿号）"""
    results = []
    for m in re.finditer(r"([^，。、]*?)、([^，。、]*?)、([^，。、]*?)、", text):
        results.append(m.start())
    return results


def check_dash(text: str) -> list:
    """检查破折号 ——"""
    return [m.start() for m in re.finditer(r"——", text)]


def check_paragraph_bold(text: str) -> int:
    """检查段落级加粗（粗略计数 ** 出现次数）"""
    return len(re.findall(r"\*\*[^*]+\*\*", text))


def check_ai_cliches(text: str) -> dict:
    """AI 套话检查"""
    patterns = {
        "在这个快节奏的时代": r"在这个[^，。]*?时代",
        "赋能": r"赋能",
        "让我们一起": r"让我们一起",
        "不忘初心": r"不忘初心",
        "砥砺前行": r"砥砺前行",
    }
    results = {}
    for name, pat in patterns.items():
        hits = [m.start() for m in re.finditer(pat, text)]
        if hits:
            results[name] = hits
    return results


def check_grand_standing(text: str) -> list:
    """意义拔高：'这不仅是 X，更是 Y'"""
    return [m.start() for m in re.finditer(r"这不仅[^，。]*?更是", text)]


def check_universal_ending(text: str) -> list:
    """万能展望结尾：'未来属于' / '终将'"""
    results = []
    for pat in [r"未来属于", r"终将"]:
        results.extend([m.start() for m in re.finditer(pat, text)])
    return results


def check_flattery(text: str) -> list:
    """谄媚/夸赞"""
    patterns = [r"你真棒", r"怎能不", r"太[棒强]了", r"太厉害了"]
    results = []
    for pat in patterns:
        results.extend([m.start() for m in re.finditer(pat, text)])
    return results


def check_emoji(text: str) -> list:
    """emoji（基础范围）"""
    emoji_pat = re.compile(
        "["
        "\U0001F300-\U0001F5FF"
        "\U0001F600-\U0001F64F"
        "\U0001F680-\U0001F6FF"
        "\U0001F700-\U0001F77F"
        "\U0001F900-\U0001F9FF"
        "\u2600-\u26FF"
        "]+",
        flags=re.UNICODE,
    )
    return [m.start() for m in emoji_pat.finditer(text)]


def check_hedge(text: str) -> list:
    """填充对冲"""
    patterns = [
        r"当然也不排除",
        r"可能因人而异",
        r"每个人的情况不同",
        r"具体情况具体分析",
    ]
    results = []
    for pat in patterns:
        results.extend([m.start() for m in re.finditer(pat, text)])
    return results


def count_chinese_chars(text: str) -> int:
    """统计中文字符数（含 CJK 标点和全角符号，zhililong 标准计数法）"""
    return len(re.findall(r"[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]", text))


def main():
    if len(sys.argv) != 2:
        print("用法: python3 post_edit_check.py <article.md>")
        sys.exit(1)
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        text = f.read()

    print("=" * 60)
    print("zhililong 事后清单（11 项）")
    print("=" * 60)
    print(f"文件: {sys.argv[1]}")
    print(f"中文字符数: {count_chinese_chars(text)}")
    print()

    checks = [
        ("1. '不是 X 而是 Y' 句式", check_no_x_but_y(text)),
        ("2. 排比三连", check_parallel_three(text)),
        ("3. —— 破折号", check_dash(text)),
        ("4. 段落级加粗数", check_paragraph_bold(text)),
        ("5. AI 套话", check_ai_cliches(text)),
        ("6. 意义拔高", check_grand_standing(text)),
        ("7. 万能展望结尾", check_universal_ending(text)),
        ("8. 谄媚/夸赞", check_flattery(text)),
        ("9. emoji", check_emoji(text)),
        ("10. 填充对冲", check_hedge(text)),
    ]

    for name, hits in checks:
        if isinstance(hits, dict):
            if not hits:
                print(f"✅ {name}: 0 处")
            else:
                print(f"❌ {name}: {hits}")
        elif isinstance(hits, int):
            # 段落级加粗数：给出数量，>章节数+1 视为不合规
            print(f"{'✅' if hits <= 6 else '❌'} {name}: {hits} 处（每节最多 1 处）")
        else:
            if not hits:
                print(f"✅ {name}: 0 处")
            else:
                print(f"❌ {name}: {len(hits)} 处（位置: {hits[:5]}...）")

    # 字数
    n = count_chinese_chars(text)
    if 4000 <= n <= 5500:
        print(f"✅ 11. 字数: {n} (在 4000-5500 区间)")
    else:
        print(f"❌ 11. 字数: {n} (超出 4000-5500 区间)")


if __name__ == "__main__":
    main()
