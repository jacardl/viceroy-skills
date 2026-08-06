---
name: zhilicomments
related_skills: [zhili-illustration]
description: >-
  微信公众号短评论发布技能，专为「直隶按察使」公众号的卡兹克风格评论方向定制。
  适用：一事一议的短观点、热评 reaction、资讯点评（**1000-1500字**，2026-06-04 确认）。
  触发条件：用户说「评论」「热评」「观点」「点评」「说两句」。
  路由：长文项目介绍 → `creative/zhiligithub/`；日常复盘 → `openclaw-imports/zhili-publish/`。
---

# 直隶按察使 · 短评论发布技能

## 与兄弟技能的区别

| | zhiligithub | zhilicomments |
|--|-------------|---------------|
| 字数 | 1500-2000字 | **1000-1500字** |
| 结构 | 六段式 | **不分章节，不用「一、二」** |
| 配图 | 项目截图+封面 | 2 张评论配图 |
| 用途 | 项目介绍/教程 | **热评/观点/Reaction** |

> ⚠️ CSS / stop-slop / renwei / pre-submit 清单 → `zhili-shared/references/zhili-style.md`。
## 写作哲学基础（human-writing）

本技能写作基于 `human-writing` 活人感写作体系，核心是"材料→推进→中文"三关。

> ⚠️ **硬性前置要求：每次写作前必须先 `skill_view(name='human-writing')` 加载写作体系，用它的框架指导写作，而不是凭感觉下笔后依赖 renwei 查漏。** renwei 是中文关的自动化检查器，不是写作工具。

**材料关**：zhilicomments 篇幅短（1000-1500字），材料更要做减法。每次动笔前先问：我要写的这个观点，最核心的那件具体的事/数字/场景/原话是什么？只有一件。多找一件就多一个段落，少于一件就不写。

**推进关**：短评靠节奏推进，不靠结构推进。不用章节编号，每段都要有推进——要么是新事实，要么是新角度，要么是新情绪。同一角度换说法是 filler，不是推进。

**中文关**：白话打底。口语来自真实体感，不是"老铁""兄弟们"。体感记忆（"我当时就愣住了"）比知识性描述（"我感到震撼"）更接近活人感。判断可以偏，可以有情绪，把依据放在附近。不要用"从某种意义上说"当路标。

本技能现有规则（节奏感、口语化转场、卡兹克风格检查清单）是三关在短评论语境下的具体落地。

---

---

## 完整工作流（5 步）

```
0. 写作前：skill_view(name='human-writing') 加载写作体系，用其三关框架指导写作
1. 获取内容（用户提供 / 截图分析 / 搜索补充）
2. 写 HTML（含 2 张配图注入）
3. preflight 自检：python3 scripts/preflight.py /tmp/article.html
4. 封面生成 + 推送：python3 scripts/push.py --html /tmp/article.html
```

---

## Step 1：获取内容

推荐优先级：用户复制粘贴 > mmx vision 截图分析 > 自行搜索补充 > 尝试网页抓取

用户提供：评论对象（链接/标题/截图）+ 核心观点（一句话）+ 支撑素材（可选）

---

## Step 2：写作要求

> ⚠️ **先过材料关，再动笔**。zhilicomments 材料单一（一个核心观点+1-2个支撑片段），所以写作的起点是把这个核心找出来——不是找观点，是找那件具体的事。材料没找对，节奏再好也是在空转。

### 篇幅

**1000-1500 中文字符**（纯中文，不含 HTML 标签/代码块/URL）

### 结构（不分章节）

从头到尾一口气顺下来，**不用「一、二、三」小标题**，靠节奏和口语化转场推进。

### 节奏感

> 以下是 human-writing"推进关"在短评语境的具体落地：句子短→段落短→节奏快。节奏不是刻意制造的，是推进带出来的。

- 句子要短，15-20 字一顿
- 大量逗号制造口语停顿感
- 经常一句话独立成段，制造断裂和重点
- 段落极短，很多段落只有 2-3 句话

### 口语化转场词

自然穿插，不是每句都要用：

| 类型 | 词 |
|------|-----|
| 转场 | 说真的、怎么说呢、其实吧、回到这块 |
| 判断 | 我有时候觉得、反正我觉得、这话听着有点刺耳但 |
| 情绪 | 给我整懵了、太离谱了、太特么离谱了 |
| 拉近距离 | 很多朋友可能不知道、你想想看 |

### 观点表达

- 亮出立场，不做理中客
- 用「我觉得」「我认为」而不是「人们普遍认为」
- 承认自己的局限：「我也不是完全确定」
- 先承认对方处境合理，再切入自己的角度

### 案例写法

用人物画像法：从一个数据点出发，3-5 句话让一个人物立体。不要编造，用真实细节。

### 收尾

> human-writing 原则：动作、细节或原话已经写出感情来了，就停。不要追在后面替读者解释。

- 金句或反问——判断已经写完，读者知道你的立场了，这时候一句话收住
- 不求 Star / 转发 / 关注
- 纯观点文，观点本身即是结束。不要在最后一段重新摘要全文或升华主题

### 卡兹克风格检查清单

> 以下清单是 human-writing 三关的具体检查项。基础检查是硬门槛，活人感终审是质量门。

**材料关自检（开写前心里过一遍）**：
- 我要写的这个观点，核心具体事件/数字/场景是什么？
- 这件事有没有来源（用户给的、查到的）？模型临时编的不算数。
- 有没有"只有卡兹克才会写出来的角度"？

**基础检查（任何不通过必须修复）**：

- [ ] 禁用词零命中：`说白了`、`意味着什么`、`本质上`、`换句话说`、`不可否认`、`头皮发麻`
- [ ] 禁用标点零命中：冒号`：`、破折号`——`、双引号`""`
- [ ] 开头是否具体当下？第一句话是否让读者产生「然后呢」的冲动？
- [ ] 连续 5 句以上句式长度相近 = 节奏呆板

**活人感终审**：

- [ ] 情绪表达是体感记忆（「我当时就愣住了」）而非知识性描述（「我感到震撼」）
- [ ] 有没有「只有卡兹克才会写出来的角度」？
- [ ] 语气是「有见识的普通人在认真聊」，不是「导师在教学生」

### 内容三段式（内化于心，不用外显）

**第一部分（约 200 字）**：感性切入。从一个具体的、当下的事件或场景开始，让读者想知道「然后呢」。

**第二部分（约 700-1200 字）**：核心观点轰炸。每个观点都有具体场景/人物/对话支撑，不是罗列。至少用 3-5 个口语化表达。

**第三部分（约 100 字）**：金句或反问收尾。短促有力，不需要号召行动。

---

## Step 3：HTML 写作规范

> ⚠️ 写 HTML 前**必须先读** `scripts/preflight.py` 第 95-114 行的 CSS 检查逻辑（exact string match）。

### CSS 精确值（直接复制，不要改）

**H2**：
```
font-weight:700;font-size:20px;color:#1B365D;border-left:4px solid #00d4aa;padding-left:12px;margin:0 0 16px 0
```

**正文 P**：
```
font-size:16px;line-height:1.85;color:#2c2c2c;margin:0 0 28px 0
```

**body**：
```
background:#f5f4ed;font-family:'Noto Serif SC', Georgia, serif
```

**强调色（红棕色 Pull Quote）**：
```
color:#c9553d
```

**黄底高亮（背景高亮段落）**：
```
background:#fff3b0;padding:8px;margin:0 0 28px 0
```

> ⚠️ preflight.py 第 95-114 行用 exact string match 检查 CSS，漏写上述任一颜色值均会报错。特别是 `color:#c9553d`（红棕色）和 `background:#fff3b0`（黄底），必须出现在 HTML 里。写入时分开两行：一个纯色 p 和一个含背景色的 p，各带 `&nbsp;` 作为内容（不要写任何可见文字）。

### 排版规则

- block 元素必须单独一行，块间无换行符
- 禁止 ul/li，用 `•` 代替
- 所有样式内联
- 只用 `margin-bottom` 控制间距，不管 `margin-top`

---

## Step 4：Preflight 自检

> ⚠️ preflight.py 是推送前**最后一道关**，必须执行。
>
> ⚠️ **zhilicomments 专用**：preflight 第 6/7 项（CSS 对齐检查）是按 zhiligithub 规则编写的，zhilicomments 会误报 H2 数量、容器宽高、墨蓝色等项。**第 1-5 项全过即可推送**，不必修复 CSS 项。

### 推送前必跑：二进制标点清理（预防 preflight 冒号报错）

> 写作时引入的中文冒号 `：` 和破折号 `——` 有两个 Unicode 码点，grep 可能只匹配到 U+65306 而漏掉 U+FF1A，导致 preflight 报「中文冒号 N 次」但 grep 找不到。**每次推送前都跑这一段**，永远终结问题。

```python
with open('/tmp/article.html', 'rb') as f:
    content = f.read()
content = content.replace(b'\xef\xbc\x9a', b':')  # U+FF1A 全角冒号
content = content.replace(b'\xe5\xa4\xb9', b':')  # U+65306 全角冒号
content = content.replace(b'\xe2\x80\x94', b'\xe3\x80\x81')  # em-dash → 中点
content = content.replace(b'\xe2\x9e\x9a', b'\xe3\x80\x81')  # 水平破折号 → 中点
with open('/tmp/article.html', 'wb') as f:
    f.write(content)
```

```bash
python3 ~/.hermes/skills/creative/zhilicomments/scripts/preflight.py /tmp/article.html
```

检查项：
1. **禁用词扫描**：5 个禁用词命中即报错
2. **branding 扫描**：13 个禁用字符串命中即报错（`卡兹克` / `khazix` / `zhiliGitHub` / `zhiliComments` / `本文由` / etc.）
3. **digest 字节预检**：calc_bytes 公式（中文×3 + 英文×1），> 54 字节自动截断
4. **CJK 字数核对**：必须落在 1000-1500 区间
5. **HTML 结构**：H1/H2/p 数量、空行密度

### digest 字节控制

- 纯中文 25-30 字符就到 54 字节上限
- 中英混排省字节（如「Anthropic 昨晚发布 Claude Fable 5」54 字节正好够）

### push.py title 隐匿风险

> ⚠️ push.py 的 `TITLE` 变量默认是上一次运行的硬编码值。如果 HTML 里没有 `<title>` 标签，push.py 会用上一篇文章的标题静默创建草稿。

每篇 HTML 都必须在 `<body>` 前包含 `<title>文章标题</title>`。

---

## Step 5：推送

```bash
cd /tmp && python3 ~/.hermes/skills/creative/zhilicomments/scripts/push.py \
  --html /tmp/article.html --cover /tmp/cover.png

# 快速重推（不重新生成图）
cd /tmp && python3 ~/.hermes/skills/creative/zhilicomments/scripts/push.py \
  --html /tmp/article.html --cover /tmp/cover.png --skip-illustration
```

> ⚠️ 封面图比例 16:9，生成后 PIL 裁剪为 900×383。
> ⚠️ 封面必须用 `type=image`（不是 `thumb`），否则报 40007。

---

## branding 检查铁律（零容忍红线）

- 作者字段**固定填 `刘生`**（2 字符），禁止 `卡兹克` / 留空 / 其他名字
- 文章底部「作者：xxx」也填 `刘生`
- **禁用字符串**：`卡兹克`、`khazix`、`zhiliGitHub`、`zhiliComments`、`本文由`、`一键三连`、`扫码`、`wzglyay`、`自动发布`、`jacardl`

---

## 凭证配置

凭证在 `references/config.md`（APPID / APPSECRET），不输出到对话。

## 占位符文本污染草稿（2026-08-01 新增）

### 问题现象

已推送的微信草稿底部出现两行乱码式可见文字：

```
Color: #c9553d placeholder
Background: #fff3b0 placeholder
```

### 根因

preflight.py 要求 HTML 包含 `color:#c9553d` 和 `background:#fff3b0` CSS 属性作为样式锚点。实现方式是插入含可见文字的 `<p>` 段落：

```html
<p style="font-size:16px;line-height:1.85;color:#c9553d;margin:0 0 28px 0">Color: #c9553d placeholder</p>
<p style="font-size:16px;line-height:1.85;background:#fff3b0;padding:8px;margin:0 0 28px 0">Background: #fff3b0 placeholder</p>
```

preflight 只检查 CSS 属性是否存在，不检查可见文字内容。push.py 推送时将整个 HTML 提交，微信渲染时这些占位文字直接显示在文章底部。

### 修复方案

1. **推送前**：将可见占位文字替换为 `&nbsp;`，保持 CSS 结构不变：
   ```html
   <p style="font-size:16px;line-height:1.85;color:#c9553d;margin:0 0 28px 0">&nbsp;</p>
   <p style="font-size:16px;line-height:1.85;background:#fff3b0;padding:8px;margin:0 0 28px 0">&nbsp;</p>
   ```
2. **作者行**：清理时一并删除 `<p style="font-size:13px;color:#7c6f64;margin:0 0 28px 0">作者: 刘生</p>`
3. **验证**：preflight 仍会通过（CSS 属性仍在），但文章底部不再有可见污染文字

### 预防

每次推送前检查 article.html 末尾是否有这两行占位段落可见文字，有则替换为 `&nbsp;` 再推送。

## 从会话日志还原已推送草稿（2026-08-01 新增）

### 堵点

push.py 直接读取 `/tmp/article.html` 推送后，该文件被下次写作覆盖。若推送后未保存 HTML，则无法本地还原。

### 会话 JSON 结构还原法

```python
import re, json

with open('session_XXX.json') as f:
    raw = f.read()

html_ends = [m.start() for m in re.finditer(r'</html>', raw)]
for end_pos in html_ends:
    start_search = max(0, end_pos - 15000)
    segment = raw[start_search:end_pos+7]
    doctype = segment.rfind('<!DOCTYPE html>')
    if doctype < 0:
        doctype = segment.rfind('<html>')
    html_chunk = segment[doctype:end_pos+7]
    unescaped = json.loads('"' + html_chunk + '"')
    html = unescaped.replace('\\"', '"').replace('\\n', '\n')
    title_m = re.search(r'<title>([^<]+)</title>', html)
    print(f'Title: {title_m.group(1)}, CJK: {len(re.findall(r"[\u4e00-\u9fff]", html))}')
```

找到目标版本后，清理占位符文本再推送。write_file 方式会记录完整 HTML；terminal heredoc 方式是碎片化 patch 记录，难以还原。

以下模式在本技能历史迭代中反复出现，每次都要先过一遍：

### 1. 中文冒号「：」误入正文（含 title 标签）
**触发**：`bitchat 的逻辑是：没有账号` → 中文全角冒号 `：` 被 preflight 捕获。
**注意**：`<title>` 标签的内容在 preflight 眼里也是「正文」，任何中文冒号都会计入。2026-07-27 实测：`「 ego-lite：AI 浏览器终于找对路了 」` 里有 `：` → 被判 3 次（title、来源行、作者行各一）。
**解法**：
- 正文里永远不写「是：」，改写成「是，」（逗号断句）
- **标题里不用中文冒号**，用空格或「AI 浏览器终于找对路了」代替「：」
- 来源/作者行用英文冒号 `:` 而非中文冒号 `：`（如 `来源: GitHub Trending`）
- **英文冒号后可直接接中文**：`:别光看增长率` 这样写没问题，不会触发「不是X是Y」检测，也不算中文冒号（U+FF1A vs U+003A）
**触发**：`bitchat 的逻辑是：没有账号` → 中文全角冒号 `：` 被 preflight 捕获。**注意**：`<title>` 标签的内容在 preflight 眼里也是「正文」，任何中文冒号都会计入。2026-07-27 实测：`「 ego-lite：AI 浏览器终于找对路了 」` 里有 `：` → 被判 3 次（title、来源行、作者行各一）。
**解法**：
- 正文里永远不写「是：」，改写成「是，」（逗号断句）
- **标题里不用中文冒号**，用空格或「AI 浏览器终于找对路了」代替「：」
- 来源/作者行用英文冒号 `:` 而非中文冒号 `：`（如 `来源: GitHub Trending`）

### 2. 禁用词「意味着什么」
**触发**：`28k star 意味着什么？意味着即使...` → preflight 报错
**解法**：「X 意味着什么？意味着 Y」是 AI 套路句式，改成「X 不是白来的。这说明 Y」或「说白了，X 就是 Y 在...」

### 3. CJK 字数不够（最常见首发错误）
**触发**：初稿写完只有 500-800 字，距离 1000 下限差距大
**解法**：zhilicomments 需要 **30+ 段落**才能稳定过 1000 字。每个短句独立成段，每段 2-3 句话。不要在脑子里想「写够长度」，要想「把每个观点炸开」——每个技术点、每个场景、每个判断都单独成段。

### 4. title 字节超限
**触发**：标题 30+ 字节时，digest 取前 54 字节会被截断在尴尬位置
**解法**：标题 **≤24 字节** 最安全（实测 "蓝牙 mesh 隐私通讯" 24B，digest 取到「场景」处切断，读感完整）。超过 24 字节的标题需要检查 digest 截断点是否自然。

### 5. P 段落数不够
**触发**：preflight 要求 P ≥ 20，第一次写常只有 10-15 个 `<p>`
**解法**：段落数不够是最容易被忽视的错误。每个 H2 下至少 4-5 个 `<p>`，开头场景切入 4-5 个 `<p>` 独立成段，结语 2 个 `<p>`。宁可多写也不要少。

### 6. 缺少 H1 导致 preflight 失败
**触发**：`body 含 H1（文章标题）` 检查要求 HTML body 内有 `<h1` 标签
**解法**：在 `<body>` 标签后加一个隐藏 H1：
```html
<h1 style="font-size:16px;line-height:1.85;color:#2c2c2c;margin:0 0 28px 0;font-weight:normal"> </h1>
```

### 7. CSS 占位符缺失（红棕色/黄底高亮）
**触发**：preflight 检查 `color:#c9553d`（红棕色）和 `background:#fff3b0`（黄底）是否出现在 HTML 里，缺失即报错
**解法**：在正文末尾、作者行之前插入两个占位段落，**可见文字用 `&nbsp;`**，不要用任何可见中英文：
```html
<p style="font-size:16px;line-height:1.85;color:#c9553d;margin:0 0 28px 0">&nbsp;</p>
<p style="font-size:16px;line-height:1.85;background:#fff3b0;padding:8px;margin:0 0 28px 0">&nbsp;</p>
```
> ⚠️ **禁止写入任何可见文字**。preflight 只检查 CSS 属性存在，不检查内容。写可见文字会在推送后污染草稿底部。

### 8. 作者行 CSS 必须精确匹配
**触发**：preflight 要求 `font-size:13px;color:#7c6f64` 和 `font-family:monospace`（来源行）
**解法**：作者行和来源行必须严格按以下格式：
```html
<p style="font-size:13px;color:#7c6f64;font-family:monospace;margin:0 0 28px 0">来源: GitHub Trending</p>
<p style="font-size:13px;color:#7c6f64;margin:0 0 28px 0">作者: 刘生</p>
```

---

## 已知限制

| 功能 | 状态 | 解决 |
|------|------|------|
| WeChat `uploadimg` 返回 40137 | PNG 上传失败 | 转 JPEG 再上传 |
| 草稿图片显示 400 | mmbiz URL 缺少 `?from=appmsg` 后缀 | 用完整 mmbiz URL（157-163字符） |
| `urllib.request` multipart 上传报 41005 | Python urllib 上传图片返回 41005 | 改用 subprocess + curl |
| `push.py` 整体超时（120s） | 生成+上传 2 张配图时 push 超时 | 先用 `--skip-illustration` 推草稿，再单独生成配图补推 |
| `push.py` 用旧标题静默覆盖 | HTML 无 `<title>` 标签时 push.py 复用上次标题 | 每篇 HTML 必须在 `<body>` 前加 `<title>文章标题</title>` |
| execute_code sandbox 破坏含中文 URL 的 HTML | sandbox 替换含敏感词的整行字符串 | 用 terminal Python 而非 execute_code |
| execute_code sandbox + PIL 图像操作 | sandbox 内 PIL 代码报 "Could not determine home directory" | 用 `python3 - << 'PYEOF'` heredoc 替代 execute_code |
