# zhiliGitHub 实操工作流（2026-07-15 更新）

> 本文档记录**实际写一篇文章的端到端过程**，包含每一道硬性检查关卡。
> 配合主 SKILL.md 使用——主文档说"必须做什么"，本文档说"具体怎么做 + 怎么验"。

## 端到端工作流（8 步）

```
0. 写完草稿后、渲染前：运行 renwei 预扫（见第 1 节）→ 修复草稿 → 渲染
1. python3 scripts/render_zhili_article.py <draft.md> <article.html>
2. python3 scripts/validate_zhili_article.py <article.html> --title "<title>"
3. （失败时）改稿重跑 1-2 步
4. 图片：嵌入 mmbiz URL（见下方两种路径）
5. 手动在 HTML <head> 内添加 <title>文章标题</title>
6. cd /tmp && python3 scripts/push.py --html /tmp/article.html --cover /tmp/cover.jpg --skip-illustration
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

# AI 黑话：落地 / 完美 / 非常 / 极其 / 赋能 / 闭环
grep -n "落地\|完美\|非常\|极其\|赋能\|闭环" /tmp/draft.md
```

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

**扫描后**：确认 4 项全部清零后再渲染草稿。任意一项有结果都需要修复。

---

## 2. 渲染 + 验证

```bash
python3 scripts/render_zhili_article.py /tmp/draft.md /tmp/article.html
python3 scripts/validate_zhili_article.py /tmp/article.html --title "标题"
```

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
→ 上传图片到微信 `media/uploadimg` 获取 mmbiz URL
→ 手动注入 `<img src="mmbiz_url">` 到 HTML
→ push.py 用 `--skip-illustration`

**路径 B 完整注入步骤（2026-07-14 实测）**：

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

## 5. 手动添加 <title> 标签（必须，2026-07-08 实坑）

render 脚本**不生成** `<title>`，必须手动加：

```html
<head><meta charset="utf-8"><title>文章标题</title></head>
```

缺少时 push.py 默认标题为"GitHub 黑马项目"。

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
| 「不是X是Y」句式 | validate 打回命中率 ≥1 | **pattern**: `不是[^，。安置]{1,40}[，,][^是\n]{1,40}是`；**解法**: 改写句子结构，如"问题不是 A，而是 B" → "问题不在于 A，而在于 B" |
| 封面上传 40007 | thumb type 被拒 | 必须用 `type=image` |
| 重推草稿标题仍错误 | 旧草稿未删 | 用 `--delete-first <draft_id>` 删除旧草稿 |
| 用户说 MIT 但 API 返回 None | 文章 License 写错 | 写前先 curl GitHub API 核实 `license.spdx_id` |
| 路径 B marker 在 HTML 中找不到 | 注入失败 | markdown 强渲染后 HTML 标签变化，用 `grep -o '关键词.*</p>'` 确认 marker 精确形式 |
| 注入后 HTML 出现双重 p 标签 | 微信渲染异常 | marker 以 `</p>` 结尾时，inject 应直接拼接在 `</p>` 之后而非形成嵌套 p |
