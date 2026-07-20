# preflight 高频失败模式（2026-07-07 更新）

每次写 zhilicomments 文章，以下错误都会重复出现。写完正文后，先过一遍这些项再跑 preflight，少走弯路。

## 中文标点类

### 中文冒号 `：` → 零容忍
- 写作时「说得直接：」「最重要的一条：」这种句式极顺手，preflight 会直接报错
- 高危场景：每个段落的「：」都容易漏网
- **解法**：正文写完后，执行 `grep "：" /tmp/article.html`，发现即替换为「，」

### 中文破折号 `——` → 零容忍（preflight 检查的是两个连续 em-dash U+2014）
- 高危场景：解释性语句「YOLO 模式——就是那个危险地跳过权限确认的选项」
- **解法**：用逗号断句，或拆成两句。「就是」后面直接接解释
- 实证有效：把 `——` 整体替换为 `，`（中文逗号）可通过 preflight。逗号比顿号更不影响阅读节奏。

## CSS 格式类

### 字体栈逗号后缺空格
- preflight 检查精确字符串 `'Noto Serif SC', Georgia, serif`
- 错误写法：`'Noto Serif SC',Georgia,serif`（缺空格）
- 正确写法：`'Noto Serif SC', Georgia, serif`

### 作者行 font-size 错误
- preflight 检查 `font-size:13px;color:#7c6f64`
- 错误写成 14px 会报错

## 标题类

### H2 标题过长
- 每篇 H2 标题都要 ≤10 个中文字
- 长的 H2 读者读起来累，也会触发 preflight 检查

## 中文标点二进制替换法（终极方案）

正则替换法和 grep 都可能失效，因为中文冒号有两个 Unicode 码点，视觉完全相同：

| 名称 | 码点 | UTF-8 字节 |
|------|------|-----------|
| CJK 全角冒号 | U+FF1A `：` | `ef bc 9a` |
| CJK 冒号 | U+65306 `：` | `e5 a4 b9` |

preflight 检测的是 U+FF1A。正则法替换的是 U+65306，留下 U+FF1A 不动。

**无论哪种情况都用二进制替换，一次解决所有码点：**

```python
with open('article.html', 'rb') as f:
    content = f.read()

# 替换所有形式的中文冒号 → 英文冒号
content = content.replace(b'\xef\xbc\x9a', b':')  # U+FF1A（preflight 检测的码点）
content = content.replace(b'\xe5\xa4\xb9', b':')  # U+65306

# 替换所有形式的中文破折号 → 顿号
content = content.replace(b'\xe2\x80\x94', b'\xe3\x80\x81')  # em-dash → 中点
content = content.replace(b'\xe2\x9e\x9a', b'\xe3\x80\x81')  # 水平破折号 → 中点

with open('article.html', 'wb') as f:
    f.write(content)
```

**什么时候用这个**：正则替换后 preflight 仍然报相同错误；或 preflight 报告「中文冒号 N 次」但 grep 找不到（U+FF1A 的 grep 模式不一样）。二进制替换永远终结问题。

## 调试建议

如 preflight 失败后修了某个问题，重跑前先手动 grep 确认同类问题已清干净：
```bash
# 冒号（在文本内容中查找）
grep "：" /tmp/article.html
# 破折号
grep "——" /tmp/article.html
# 作者行字号
grep "文 / 刘生" /tmp/article.html
```

**注意**：grep "：" 只能匹配 U+65306，对 U+FF1A（`ef bc 9a`）无效。如 grep 未命中但 preflight 仍报中文冒号，直接跑上面的二进制替换法。
