# zhiliGitHub 实操工作流（2026-07-15 更新）

> 本文档记录**实际写一篇文章的端到端过程**，包含每一道硬性检查关卡。
> 配合主 SKILL.md 使用——主文档说"必须做什么"，本文档说"具体怎么做 + 怎么验"。

## 端到端工作流（8 步）

```
0. 写完草稿后、渲染前：运行 renwei 预扫（见第 1 节）→ 修复草稿 → 渲染
1. python3 scripts/render_zhili_article.py <draft.md> <article.html> --title "<文章标题>"
2. python3 scripts/validate_zhili_article.py <article.html> --title "<文章标题>"
3. （失败时）改稿重跑 1-2 步
4. 图片：嵌入 mmbiz URL（见下方两种路径）
5. cd /tmp && python3 scripts/push.py --html /tmp/article.html --cover /tmp/cover.jpg --skip-illustration
```

---

## 1. renwei 预扫（2026-07-15 新增：减少渲染→验证循环）

> 经验来源：OpenCut 和 Graphify 两篇文章的第一稿均含 3-5 处破折号、1-2 处「不是X是Y」、1-2 处 AI 黑话，导致渲染后 validate 失败 2-3 轮。
> 在草稿阶段做一次快速扫描，提前修复，可以跳过渲染直接改草稿。

**必扫高频 violation（草稿阶段）**：

```bash
# 破折号 —— （出现率最高）
grep -n "——" /tmp/draft.md

# 不是X是Y 句式
grep -n "不是.*是" /tmp/draft.md

# AI 黑话 / 赞美形容词（完整列表，见 zhili-style.md renwei 第 11 项 + AI黑话池）
grep -n "落地\|完美\|非常\|极其\|赋能\|闭环\|颠覆\|强大\|卓越\|优雅\|惊艳\|出色\|优秀\|极致\|持续\|构建\|迭代" /tmp/draft.md
```

> ⚠️ 上面的 grep 包含了 validate renwei 第 11 项「AI 赞美形容词」的完整列表。首次扫描后若有任何命中，先清零再渲染，不要带任何一项进 validate 循环。

**常见修复对照**：

| 违规 | 原文 | 改后 |
|------|------|------|
| 破折号（解释） | A——B | A，B |
| 破折号（转折） | A——B | A。B |
| 不是X是Y | 问题不是A，是B | 问题不在于A，而在于B |
| 不是X是Y | 代码不是文本，代码是图 | 代码是图，不是文本 |
| AI 黑话 | 一旦落地 | 一旦实现 |
| AI 黑话 | 它现在还不完美 | 它现在还不够完善 |
| AI 黑话 | 会非常明显 | 会很明显 |
| AI 黑话 | 功能非常强大 | 功能很强 |
| 意义拔高 | Blender 更是需要专门培训 | Blender 得专门培训才能上手 |
| 意义拔高 | 这不仅是 X，更是 Y | 删「更」字或拆成两句 |

**扫描后**：确认 4 项全部清零后再渲染草稿。任意一项有结果都需要修复。

**⚠️ 诊断技巧：区分「有命中」和「有多少个」**

`grep -n` 只显示行号，当同一行出现多个匹配时会掩盖实际数量。正确做法是用 `grep -o` 提取每个匹配词，再 `sort | uniq -c` 计数：

```bash
# 误判：只看行号
grep -n "落地\|完美\|非常" /tmp/draft.md
# Line 89: ...非常迫切...
# （可能误以为只有 1 处，实际「非常」只出现 1 次，这个结果是准的）
# 但如果一行里有两个「完美」，grep -n 只显示一次

# 准判：计数每个词
grep -o "落地\|完美\|非常" /tmp/draft.md | sort | uniq -c
#   1 非常
#   2 完美
# 清楚看到「完美」出现 2 次，需要逐行定位修复
```

每次 renwei 扫描后，优先跑计数版，确认每个词的实际出现次数。

**⚠️ 多处破折号批量替换**

草稿扩展时容易在多处引入新的 `——`，多次 sed 替换容易遗漏。用 Python 全文替换最可靠：

```python
with open('/tmp/draft.md') as f:
    content = f.read()
content = content.replace('——', '，')  # 解释类 → 逗号
content = content.replace('——', '。')  # 转折类 → 句号（需要两次调用分别处理不同语境）
# 更简洁：一次性全部替换为句号，再人工调整少数用逗号更合适的地方
with open('/tmp/draft.md', 'w') as f:
    f.write(content)
```

**标题字节预检（草稿阶段必须做，不要等 validate）**：`
```python
title = "你的标题"
byte_count = sum(3 if ord(c) > 127 else 1 for c in title)
print(byte_count)  # 必须 ≤60
```
超了就先改草稿标题再渲染，否则 HTML 里改了还要重新跑 validate。

---

## 2. 渲染 + 验证

**顺序不能颠倒**：
1. 修复 draft.md 中的 renwei 错误
2. **重新渲染** `python3 scripts/render_zhili_article.py /tmp/draft.md /tmp/article.html --title "<文章标题>"`
3. 再 validate

validate 读取的是渲染后的 HTML。如果只改了 draft.md 但没重新渲染，validate 看到的还是旧 HTML，会报假阳性。如果只改了 HTML 但 draft.md 没同步，下次重新渲染会把错误带回来。

**renwei 假阳性（HTML 特有）的处理原则**：「不是X是Y」等 renwei 项可能在 HTML 中出现而 markdown 中没有（渲染改变换行/上下文，导致 validate 的 30 字符窗口捕获了复合句）。处理流程：
1. 在 HTML 中定位匹配（`python3 -c "import re; print([m.group() for m in re.finditer(r'不是.{0,30}是', open('/tmp/article.html').read())])"`)
2. 改写 HTML 中的句子
3. 同步修 markdown（防止重新渲染带回来）
4. 重新渲染验证

---

## 3. 写 markdown 草稿（字数分配参考）

| 段 | 字数预算 |
|---|---------|
| 一、项目名称 | 50-80 |
| 二、项目介绍 | 200-300 |
| 三、架构设计 | 350-450（最容易写薄） |
| 四、快速上手 | 200-300 |
| 五、实战场景 | 400-500（最容易写薄） |
| 总结（无 H2） | 200-300 |

**总字数 = 1500-2000 中文字**（纯中文，不含 HTML 标签、代码块、URL）。

---

## 4. 图片流程两种路径

render 输出 `图片占位=N`：

**路径 A（有占位符）**：markdown 写了 `[mmbiz <图注>]`
→ render 后 HTML 有 `<img src="PLACEHOLDER">`
→ 替换占位符为 mmbiz URL
→ push.py 不用 `--skip-illustration`

**路径 B（直接嵌入）**：markdown 纯文字无图片语法（输出 `图片占位=0`）
→ 这种输出完全正常，纯介绍文章（无 demo 截图、无 UI 界面）自然没有截图时会出现
→ 上传封面图后直接推草稿，不需要手动注入配图
→ push.py 用 `--skip-illustration`

**路径 B 完整注入步骤（2026-07-14 实测）**：

① 下载 GitHub OG 图后**必须验证是真实图片**，不是 HTML 重定向页面：
```bash
curl -sL "https://opengraph.githubassets.com/1/{owner}/{repo}" -o /tmp/og.png
file /tmp/og.png          # 必须是 PNG/JPEG/GIF，不是 HTML
wc -c < /tmp/og.png      # 真实图片通常 > 10KB
```
GitHub OG 图下载有时会返回 HTML 错误页面（只有几 KB），直接上传到微信会失败。验证不过则改用 GitHub 项目页截图或官方文档截图。

① 上传图片获取 mmbiz URL（push.py 有 `get_access_token`）：
```python
import sys, os, json, subprocess, urllib.request
sys.path.insert(0, '/root/.hermes/skills/creative/zhiligithub/scripts')
from push import get_access_token

token = get_access_token()

def upload_mmbiz(path):
    ext = os.path.splitext(path)[1].lstrip('.') or 'jpg'
    with open(path, 'rb') as f:
        img_data = f.read()
    boundary = '----PythonFormBoundary7MA4YWxkTrZu0gW'
    body = (
        f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="media"; filename="img.{ext}"\r\n'
        f'Content-Type: image/{ext}\r\n\r\n'
    ).encode('utf-8') + img_data + f'\r\n--{boundary}--\r\n'.encode('utf-8')
    url = f'https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={token}&type=image'
    req = urllib.request.Request(url, data=body, method='POST',
        headers={'Content-Type': f'multipart/form-data; boundary={boundary}'})
    with urllib.request.urlopen(req, timeout=30) as r:
        result = json.loads(r.read())
    return result.get('url', '')

mmbiz1 = upload_mmbiz('/tmp/project/screenshot1.jpg')
mmbiz2 = upload_mmbiz('/tmp/project/screenshot2.jpg')
```

② 注入图片到 HTML（**marker 必须从渲染后的 HTML 中找，不是 markdown**）：
```python
with open('/tmp/article.html') as f:
    html = f.read()

mmbiz1 = 'http://mmbiz.qpic.cn/...'
mmbiz2 = 'http://mmbiz.qpic.cn/...'
inject1 = f'<p style="margin:16px 0;text-align:center;"><img src="{mmbiz1}" style="width:100%;max-width:660px;border-radius:8px;" /></p>'
inject2 = f'<p style="margin:16px 0;text-align:center;"><img src="{mmbiz2}" style="width:100%;max-width:660px;border-radius:8px;" /></p>'

# 先用 grep -o '关键词.*</p>' 确认 marker 在渲染后 HTML 中的精确形式
marker1 = '二、项目介绍段落末尾的关键词句。</p>'
marker2 = '五、实战场景段落末尾的关键词句。</p>'

if marker1 in html:
    html = html.replace(marker1, marker1 + inject1, 1)
if marker2 in html:
    html = html.replace(marker2, inject2 + marker2, 1)

with open('/tmp/article.html', 'w') as f:
    f.write(html)
```

**⚠️ 找 marker 正确方法**：先渲染 HTML，用 `grep -o '关键词.*</p>'` 确认 marker 在渲染后 HTML 中的精确形式。markdown 中的 `**加粗**` 渲染后变成 `<strong>` 标签，纯文本 marker 可能找不到。

**⚠️ 注入后双重 p 标签**：如果 marker 本身以 `</p>` 结尾，`replace(marker, marker + inject)` 会产生 `</p><p>...</p>` 的嵌套 p 标签（外层 p 被内层 img p 包含）。正确做法是确保 inject 紧跟在 `</p>` 之后、不被外层 p 包裹。

---

## 5. 注入 <title> 标签（必须，2026-07-08 实坑，每篇都会忘）

render 脚本**不生成** `<title>`，而且**每次重新渲染都会覆盖掉**之前注入的 `<title>`。这意味着：

- 你注入了 title，运行 push.py 之前改了一句话，重新渲染了 → title 没了
- push.py 读不到 `<title>`，默认标题变成"GitHub 黑马项目"
- 这件事在每个 agent 上每篇文章都会发生，是结构性遗忘点

**正确的完整序列（每篇文章都会走至少两遍）**：

```
1. python3 scripts/render_zhili_article.py /tmp/draft.md /tmp/article.html --title "<文章标题>"
2. python3 - << 'PYEOF'
   with open('/tmp/article.html', 'r') as f: html = f.read()
   import re
   html = re.sub(r'<head><meta charset="utf-8">',
       '<head><meta charset="utf-8"><title>你的标题</title>', html)
   with open('/tmp/article.html', 'w') as f: f.write(html)
   PYEOF
3. python3 scripts/validate_zhili_article.py /tmp/article.html --title "<文章标题>"
4. [如有失败：改 draft.md → 回到步骤 1]
5. [上传图片，注入 mmbiz URL]
6. cd /tmp && python3 scripts/push.py --html /tmp/article.html --cover /tmp/cover.jpg --skip-illustration
```

**不要依赖 `inject_title.py`**（已废弃，render 脚本自带 `--title` 参数）。

缺少 `<title>` 时 push.py 默认标题为"GitHub 黑马项目"（而非任何合理标题），此时草稿在公众平台后台标题错误，需删掉重推。

---

## 6. push.py 发布

```bash
cd /tmp && python3 /root/.hermes/skills/creative/zhiligithub/scripts/push.py \
  --html /tmp/article.html \
  --cover /tmp/cover.jpg \
  --skip-illustration

# 若需替换已有草稿，加 --delete-first：
# --delete-first <old_draft_id>

# ⚠️ 必须从 /tmp 目录运行（脚本内部依赖相对路径）。
# ⚠️ 封面参数是 --cover 不是 --cover-path（已实测，2026-07-08）。
```

---

## 常见错误速查

| 错误 | 现象 | 修复 |
|------|------|------|
| HTML 无 `<title>` | 草稿标题变成 "GitHub 黑马项目" | 在 `<head>` 加 `<title>` |
| 路径 B 漏加 `--skip-illustration` | push.py 覆盖手动注入图片 | 必须加 `--skip-illustration` |
| 标题超 22 字 | 微信 45003 | 缩到 ≤22 字节 |
| H2 漏写左边框 | 视觉上无章节边界 | 加 `border-left:4px solid #00d4aa;padding-left:12px;` |
| 代码块含真实 `\n` | 微信渲染多段 | 改用 `<br>` |
| `**文字**` 未转 `<strong>` | 显示 `**文字**` 字面量 | Python 替换 |
| 「不是X是Y」句式 | validate 打回命中率 ≥1，但 markdown 扫描干净 | **两层都要修**：①修 markdown 防止重新渲染带回来；②修 HTML（`/tmp/article.html`）才能通过本次 validate。修复后重新渲染验证。 |
| HTML 层「不是X是Y」假阳性 | validate 报 1 处命中但 markdown 无 | HTML 渲染改变换行位置，导致 validate 的 regex `不是.{0,30}是` 捕获了复合句。**解法**：改写句子使「不是」和「是」不共处 30 字符窗口内 |
| renwei 干净但 validate 报「不是X是Y」 | validate renwei ≥1，markdown grep 无结果 | HTML 特有假阳性。处理：①在 HTML 中定位匹配；②改写 HTML 句子；③同步修 markdown；④重新渲染验证 |
| 封面上传 40007 | thumb type 被拒 | 必须用 `type=image` |
| 重推草稿标题仍错误 | 旧草稿未删 | 用 `--delete-first <draft_id>` 删除旧草稿 |
| 用户说 MIT 但 API 返回 None | 文章 License 写错 | 写前先 curl GitHub API 核实 `license.spdx_id` |
| 路径 B marker 在 HTML 中找不到 | 注入失败 | markdown 强渲染后 HTML 标签变化，用 `grep -o '关键词.*</p>'` 确认 marker 精确形式 |
| 注入后 HTML 出现双重 p 标签 | 微信渲染异常 | marker 以 `</p>` 结尾时，inject 应直接拼接在 `</p>` 之后而非形成嵌套 p |
| push.py 超时 120s | 自动生成+上传配图时超时 | 先用 `--skip-illustration` 推草稿，再单独处理配图 |
| 「不是X是Y」正则假阳性 | validate 报 1 处命中但实际是正常句式 | 正则 `不是.{0,30}是` 会误杀「就是一个 Bun 服务器」「排除了截图，排除了代码」这类主系表和双重否定句；改写让「不是」和「是」不共处同一短句 |
| 总结段落写了 `## 六、总结` H2 | validate 直接报错 | **硬约束：总结段落不写 H2**，内容直接在五之后用 `· · ·` 收尾 |
| 「更是/还有/甚至」意义拔高 | validate renwei 11 项命中率 ≥1 | 「Blender 更是需要专门培训」→「Blender 得专门培训才能上手」；意义拔高检测是「更/还/甚至 + 形容词/名词」语境，删「更」字即可 |
| 标题字节超限 | validate 报「标题字节 ≤60」但草稿阶段未检 | **草稿阶段必须预检标题字节**，不要等 validate 打回才改（改 HTML 要重新验 renwei）；公式：`sum(3 if ord(c)>127 else 1 for c in title)` |
| sed 替换中文破折号失败 | `sed -i 's/——/，/g'` 跑了但 HTML 里还有破折号 | 用 `grep -n "——"` 确认位置后重复执行一次；有时替换需要两次才彻底 |
