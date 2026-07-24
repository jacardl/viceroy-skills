# 中文字符计数方法（zhililong 字数判断）

## 问题

zhililong 要求 4000-5500 字，但"字"的定义从未明确。

- `len(text)` — 把英文/数字/空格/标点全算进去，英文稿会虚高
- `len(chars_only)` — 只算汉字，漏掉中文标点（。、，）等 CJK 字符

## 正确方法

```python
import re

def count_chinese_chars(text: str) -> int:
    """统计中文字符（含 CJK 标点），不含英文字母/数字/空格"""
    return len(re.findall(r'[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]', text))

chinese = count_chinese_chars(article)
print(f"中文字符: {chinese}")  # 这是 zhililong 的"字数"
```

| 正则范围 | 包含内容 |
|---------|---------|
| `\u4e00-\u9fff` | 汉字 |
| `\u3000-\u303f` | 中文标点（。、，、《》） |
| `\uff00-\uffef` | 全角符号（全角括号等） |

## 阈值参考

| 场景 | 下限 | 上限 |
|------|------|------|
| zhililong 正文 | 4000 | 5500 |
| zhilicomments | 1000 | 1500 |
| zhiligithub | 1500 | 2000 |

## 实测记录

| 日期 | 文章 | 统计字数 | 判定 |
|------|------|---------|------|
| 2026-07-08 | 小红书IPO举报信 | 4039 | ✅ 达标 |
| （历史案例可继续追加） | | | |

## 与其他计数方式的差异

```python
len(text)                    # 总字符（含英文/数字/空格）——数字偏大
len(chars_only)              # 仅汉字 ——数字偏小
len(re.findall(r'[\u4e00-\u9fff]', text))  # 汉字+部分标点 ——常用但漏全角
# 推荐：re.findall(r'[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]', text)
```

## 用户粘贴原文的场景

用户直接粘贴公众号文章正文时，中文内容通常完整，但可能有：
- 英文字母（人名如 Chen Hao、IPO）
- 数字（85万元、300亿美元）
- 英文标点（全角转半角残留）

这些**不计入** zhililong 的"字数"。以中文 CJK 字符为准。
