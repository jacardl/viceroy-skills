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

---

## 完整工作流（5 步）

```
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

### 篇幅

**1000-1500 中文字符**（纯中文，不含 HTML 标签/代码块/URL）

### 结构（不分章节）

从头到尾一口气顺下来，**不用「一、二、三」小标题**，靠节奏和口语化转场推进。

### 节奏感

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

- 金句或反问
- 不求 Star / 转发 / 关注
- 纯观点文，观点本身即是结束

### 卡兹克风格检查清单

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

### 排版规则

- block 元素必须单独一行，块间无换行符
- 禁止 ul/li，用 `•` 代替
- 所有样式内联
- 只用 `margin-bottom` 控制间距，不管 `margin-top`

---

## Step 4：Preflight 自检

> ⚠️ preflight.py 是推送前**最后一道关**，必须执行。

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
python3 scripts/push.py --html /tmp/article.html --cover /tmp/cover.png --skip-illustration
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

## 已知限制

| 功能 | 状态 | 解决 |
|------|------|------|
| WeChat `uploadimg` 返回 40137 | PNG 上传失败 | 转 JPEG 再上传 |
| 草稿图片显示 400 | mmbiz URL 缺少 `?from=appmsg` 后缀 | 用完整 mmbiz URL（157-163字符） |
| `urllib.request` multipart 上传报 41005 | Python urllib 上传图片返回 41005 | 改用 subprocess + curl |
| execute_code sandbox 破坏含中文 URL 的 HTML | sandbox 替换含敏感词的整行字符串 | 用 terminal Python 而非 execute_code |
