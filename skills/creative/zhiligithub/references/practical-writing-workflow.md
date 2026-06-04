# zhiliGitHub 实操工作流（2026-06-03 验证可用）

> 本文档记录**实际写一篇文章的端到端过程**，包含每一道硬性检查关卡。
> 配合主 SKILL.md 使用——主文档说"必须做什么"，本文档说"具体怎么做 + 怎么验"。

## 端到端工作流（7 步）

```
1. 加载样式A 权威来源（streambert-reference.html）
2. 写 markdown 草稿（1500-2000 中文字）
3. 字数预检（纯中文字符数）
4. Stop-slop 自检（去掉废话填充词 + AI 黑话）
5. 转 HTML（套样式A，H2 加 #00d4aa 左边框）
6. 验证（字数 / 标题字节 / 空行 / branding / 残留）
7. （发布前）生成封面 + 上传 mmbiz + 调 zhili-publish 推草稿
```

---

## 1. 加载样式A 权威来源（必做，禁凭记忆）

```bash
# 必须从这个文件读 CSS，不是从主 SKILL.md
skill_view("zhiliGitHub", "references/streambert-reference.html")
```

**关键 CSS 值（直接用，不要二次记忆）**：

| 元素 | CSS |
|------|-----|
| body | `background-color:#f5f4ed;font-family:Georgia,'Times New Roman',serif;margin:0;padding:0;` |
| h1 | `font-size:28px;font-weight:bold;color:#1B365D;margin:20px 0 10px;line-height:1.3;` |
| **h2** | `font-size:20px;font-weight:bold;color:#1B365D;border-left:4px solid #00d4aa;padding-left:12px;margin:28px 0 12px 0;` |
| p | `font-size:16px;line-height:1.85;color:#2c2c2c;margin:0 0 14px 0;` |
| strong (关键词) | `color:#1B365D;font-weight:bold;` |
| strong (数据) | `color:#c9553d;font-weight:bold;` |
| pre (代码块) | `background:#1e1e1e;border-radius:6px;padding:14px 16px;margin:12px 0;overflow-x:auto;` |
| code | `font-family:Consolas,Monaco,Courier New,monospace;color:#e8e8e8;font-size:14px;line-height:1.5;` |

**⚠️ H2 左边框是样式A 的标志性特征**——`border-left:4px solid #00d4aa;padding-left:12px;` 不许省略。

---

## 2. 写 markdown 草稿

### 6 段式结构（2026-06-03 验证可用字数分布）

| 段 | 标题 | 字数预算 | 实际样本 |
|---|------|---------|---------|
| 一 | 项目名称（含 GitHub meta + 一句话定位 + 痛点钩子） | 200-280 | 242 |
| 二 | 项目介绍 | 250-350 | 298 |
| 三 | 架构设计 | 300-400 | 353 |
| 四 | 快速上手 | 150-250 | 159（代码块主导可少） |
| 五 | 实战场景 | 200-300 | 217 |
| 六 | 总结（适合/不适合 + 升维 + Star 号召） | 300-400 | 354 |

**总字数 = 1500-2000 中文字**（纯中文，不含 HTML 标签、不含代码块、不含 URL）。

### 风格延续性

参照最近 3 篇已发布文章，延续以下要素：
- **钩子库**：「你最近有没有过这种经历」「你猜 X 是干嘛的」「事情是这样的」「最近 X 圈有个明显的现象」
- **数字链**：3-5 个具体数字连用，制造密度感
- **引语自评价**：用"行业里人才懂的内行评价"代替"我觉得很牛"
- **升维收尾**：不只是夸项目，放回范式/趋势/历史进程里讲

### 段落节奏

- 3-5 行短段为主，便于手机扫读
- 长段（10+ 行）不超过 2 处
- 关键金句独立成段

---

## 3. 字数预检

```python
import re
with open('/tmp/draft.md') as f:
    md = f.read()
cn = re.sub(r'[^\u4e00-\u9fff]', '', md)
print(f"中文字数: {len(cn)}  (目标 1500-2000)")
```

如果超 2000，砍段六或段三；如果不到 1500，扩段三（架构设计）或段五（实战场景）。

---

## 4. Stop-slop 自检（写完必查，不通过不转 HTML）

```python
import re
with open('/tmp/draft.md') as f:
    content = f.read()

filler_words = [
    "值得注意的是", "实际上", "其实", "那么", "大家都知道",
    "从某种意义上", "归根结底", "不得不承认", "想必", "应该",
    "毫无疑问", "必须承认", "我想说的是", "众所周知"
]
ai_jargon = [
    "颠覆性创新", "赋能", "持续迭代", "深度赋能", "构建生态",
    "引领变革", "核心价值", "解决方案", "助力", "落地", "闭环", "矩阵"
]
structural = [
    "首先", "其次", "最后", "总之",  # 「最后」在"最后一轮打磨"这类上下文OK
    "随着.*的发展", "一方面", "另一方面"
]

for word in filler_words + ai_jargon:
    if re.search(word, content):
        print(f"  ❌ 删除: {word}")
```

**常见 LLM slop（我这次栽过的）**：「其实」/「实际上」/「从某种意义上」会无意识溜进来，**写完必须 grep 一遍**。

**结构词陷阱**：「最后」在"上线前的最后一轮打磨"是 OK 的，但在"最后说说我的看法"是结构词，要避免。

---

## 5. 转 HTML

**正确流程**（block-level 单行 + `''.join()`）：

```python
import re

# 切分 markdown 为 blocks
def md_to_blocks(md):
    blocks = []
    lines = md.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            i += 1; continue
        if stripped.startswith('# ') and not stripped.startswith('## '):
            blocks.append(('h1', stripped[2:].strip())); i += 1; continue
        if stripped.startswith('## '):
            blocks.append(('h2', stripped[3:].strip())); i += 1; continue
        if stripped.startswith('```'):
            code = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                code.append(lines[i]); i += 1
            i += 1
            blocks.append(('code', '\n'.join(code))); continue
        if stripped == '---':
            blocks.append(('divider', None)); i += 1; continue
        # 段落
        para = [stripped]; i += 1
        while i < len(lines) and lines[i].strip() and not lines[i].strip().startswith(('#', '##', '```', '---')):
            para.append(lines[i].strip()); i += 1
        blocks.append(('p', ' '.join(para)))
    return blocks

# 渲染 p（处理 **bold** → <strong>）
def render_p(text):
    parts = re.split(r'(\*\*[^*]+\*\*)', text)
    out = []
    for p in parts:
        if p.startswith('**') and p.endswith('**'):
            out.append(f'<strong style="color:#1B365D;font-weight:bold;">{p[2:-2]}</strong>')
        else:
            out.append(p)
    return ''.join(out)

# 渲染 code（**关键**：用 <br> 分隔多行，不用真实换行符）
def render_code(code):
    escaped = code.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    return ('<pre style="background:#1e1e1e;border-radius:6px;padding:14px 16px;margin:12px 0;overflow-x:auto;">'
            '<code style="font-family:Consolas,Monaco,Courier New,monospace;color:#e8e8e8;font-size:14px;line-height:1.5;">'
            + '<br>'.join(escaped.split('\n'))
            + '</code></pre>')

# CSS 常量
H2_STYLE = 'font-size:20px;font-weight:bold;color:#1B365D;border-left:4px solid #00d4aa;padding-left:12px;margin:28px 0 12px 0;'
H1_STYLE = 'font-size:28px;font-weight:bold;color:#1B365D;margin:20px 0 10px;line-height:1.3;'
P_STYLE = 'font-size:16px;line-height:1.85;color:#2c2c2c;margin:0 0 14px 0;'
DIVIDER = '<div style="text-align:center;color:#c9553d;margin-bottom:24px;font-size:18px;letter-spacing:6px">· · ·</div>'

# 渲染并拼装
blocks = md_to_blocks(md_content)
out = []
for b in blocks:
    if b[0] == 'h1': out.append(f'<h1 style="{H1_STYLE}">{b[1]}</h1>')
    elif b[0] == 'h2': out.append(f'<h2 style="{H2_STYLE}">{b[1]}</h2>')
    elif b[0] == 'p': out.append(f'<p style="{P_STYLE}">{render_p(b[1])}</p>')
    elif b[0] == 'divider': out.append(DIVIDER)
    elif b[0] == 'code': out.append(render_code(b[1]))

body = ''.join(out)  # ← 零分隔符，不要用 '\n\n'.join()

HTML = f'''<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background-color:#f5f4ed;font-family:Georgia,'Times New Roman',serif;">
<div style="max-width:680px;margin:0 auto;padding:24px 16px 60px">
{body}
</div>
</body>
</html>'''
```

**❌ 错误做法**（会产生空行）：
- `'\n\n'.join(blocks)` → 微信 JSON payload 携带 `\n`，渲染产生空段
- 多行字符串块 `'<p>...</p>\n  <p>...</p>'` → 块内换行无法被 cleanup 移除

---

## 6. 验证清单（必查 7 项，1 项不过就改）

```python
import re

with open('/tmp/article.html') as f:
    html = f.read()

# 1. 中文字数（去掉 HTML 标签后只数汉字）
cn = re.sub(r'<[^>]+>', '', html)
cn = re.sub(r'[^\u4e00-\u9fff]', '', cn)
assert 1500 <= len(cn) <= 2000, f"❌ 字数 {len(cn)} 超出 [1500, 2000]"

# 2. 标题字节（硬限 60）
title = re.search(r'<h1[^>]*>(.+?)</h1>', html).group(1)
title_bytes = len(title.encode('utf-8'))
assert title_bytes <= 60, f"❌ 标题 {title_bytes} 字节 > 60（微信 45003）"
# 推荐安全范围 14-22 字节（实测不会被前端截断）

# 3. 连续空行（必须 0）
empty = re.findall(r'\n\s*\n', html)
assert not empty, f"❌ {len(empty)} 个连续空行"

# 4. Markdown 残留（必须 0）
md_residual = re.findall(r'(?<![">])\*\*[^*\s][^*]*\*\*', html)
assert not md_residual, f"❌ {len(md_residual)} 处 ** 残留"

# 5. branding（必须 0）
for term in ['卡兹克', 'zhiliGitHub', '本文由', '一键三连', '扫码', 'wzglyay']:
    assert term not in html, f"❌ branding 残留: {term}"

# 6. H2 左边框完整性
h2_count = len(re.findall(r'<h2[^>]*>', html))
border_count = html.count('border-left:4px solid #00d4aa')
assert h2_count == border_count, f"❌ H2={h2_count} 边框={border_count}"

# 7. 代码块换行（不能含真实 \n 在 <code> 内）
code_blocks = re.findall(r'<code[^>]*>(.+?)</code>', html, re.DOTALL)
for c in code_blocks:
    assert '\n' not in c, "❌ 代码块内有真实换行符（应用 <br>）"

print("✅ 全部 7 项通过")
```

---

## 标题字节限制（实测值，2026-06-03 确认）

**三级标题长度策略**：

| 级别 | 字节 | 中文数 | 触发后果 |
|------|------|--------|---------|
| **硬限** | 60 字节 | 约 16-20 个中文字 | 超过 → `errcode: 45003` 拒绝创建草稿 |
| **推荐安全** | 14-22 字节 | 5-7 个中文字 | 前端不会截断，分享卡片完整显示 |
| **实测稳定** | 22 字节 | 7-8 个中文字 | 多次发布验证，前端显示完整 |

**写作策略**：先写 14-22 字节短标题测试通过，再考虑加长。**不要**直接写 50+ 字节的长标题赌一把。

**踩过的坑（2026-06-03）**：原本写"3.2 万星 Impeccable：把 AI 设计的「千篇一律」，一次给你根治"= **79 字节** → 超限。改为"3.2万星Impeccable：把AI设计slop一次根治"= **49 字节** → 通过。

**减字优先级**：先砍装饰（"千篇一律"），保留钩子动词（"一次根治"）。如果还不够，砍副标题（"用嘴做"、"真正能用的"）。

---

## 常见错误速查（2026-06-03 实战踩坑）

| 错误 | 现象 | 修复 |
|------|------|------|
| 标题 79 字节 | 微信 45003 拒绝 | 缩到 ≤22 字节 |
| 3 处"其实"散落正文 | 读起来像 AI 写 | 全部删除或改写 |
| H2 漏写左边框 | 视觉上辨识度低，章节边界不清晰 | 强制 `border-left:4px solid #00d4aa;padding-left:12px;` |
| 代码块用真实 `\n` | 微信渲染成多段 | 改用 `<br>` |
| `**文字**` 未转 `<strong>` | 草稿箱显示 `**文字**` 字面量 | Python 切分后逐段替换 |
| 段落含 branding "卡兹克" | 旧文迁移时常见 | 替换为「刘生」 |

---

## 跟主 SKILL.md 的关系

本文档是**实操层**，主 SKILL.md 是**规范层**。两者一致性检查：
- 字数：主 SKILL.md 说 1500-2000，本文档一致
- H2 CSS：主 SKILL.md 要求 #00d4aa 左边框，本文档给出完整 inline CSS
- 6 段式：主 SKILL.md 给章节名，本文档给字数预算和实测样本

**矛盾点提醒**：主 SKILL.md 内部有"标题 ≤22 字节"和"标题 ≤60 字节"两处不同论述。**硬限是 60，推荐目标是 14-22**。本文档统一以"14-22 字节推荐 / 60 字节硬限"为标准。
