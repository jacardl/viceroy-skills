---
name: zhiligithub
description: >-
  微信公众号长文发布技能，专为「直隶按察使」GitHub 黑马项目方向定制（1500-2000字）。
  触发：用户说「写文章」「发长文」「GitHub」「黑马」。
  技能边界：本技能只管 GitHub 黑马长文，**不替兄弟技能定规范**。短评/Reaction → `creative/zhilicomments/`；日常复盘 → `openclaw-imports/zhili-publish/`。
---

# 直隶按察使 · GitHub 黑马文章技能

## 技能边界

- **要写短评 / 观点 / Reaction** → 使用 `creative/zhilicomments/`（独立技能）
- **要发日常复盘 / 公众号通告** → 使用 `openclaw-imports/zhili-publish/`
- 本技能**不接管** zhilicomments 的字数/段式/字段规范
## 写作哲学基础（human-writing）

本技能写作基于 `human-writing` 活人感写作体系，核心是"材料→推进→中文"三关。

> ⚠️ **硬性前置要求：每次写作前必须先 `skill_view(name='human-writing')` 加载写作体系，用它的框架指导写作，而不是事后用 renwei 查漏补缺。** renwei 是中文关的自动化检查器，不是写作工具。写作时不加载 human-writing、事后依赖 renwei 修复，会导致多轮「扩充→违规→修复」循环，效率低下且容易遗漏。

**材料关**：六段式每个章节必须先确认有东西可写，再动笔。"三、架构设计"和"五、实战场景"是核心段，每段需要 3-4 个具体技术细节或尝试弧线。材料不够就研究，研究后仍不够就缩短篇幅，绝不用解释和举例灌字数。

**推进关**：每个新段落必须带来新东西——新事实、新动作、新例子、新区别或新后果。同一观点换说法不叫推进，H2 之间的过渡句直接砍掉。

**中文关**：白话打底。古意从词序、停顿和分寸里自然出现，不靠生僻字和成串成语。不用冒号、破折号、"不是X是Y"句式。不用商业汇报黑话替普通事情抬价。

六段式是骨架，骨架里的内容必须用上述三关填充。renwei 自检是三关的自动化检查器。

---

## 字数与结构

| 字段 | 值 |
|------|-----|
| 字数 | **1500-2000 中文字**（纯中文，不含 HTML/CSS/代码块/URL） |
| 结构 | 六段式（默认）/ 编号盘点（多项目合集） |
| 配图 | 项目截图 + 封面（正文必须至少 1 张 mmbiz 图） |
| 用途 | 项目介绍 / 教程 / 深度分析 / 行业观察 |

---

## 完整工作流（7 步）

```
0. 写作前：skill_view(name='human-writing') 加载写作体系，用其三关框架指导写作
1. 候选评估（收到 Trending 候选时必走）→ 不通过直接放下
2. 写 markdown 草稿（1500-2000字，六段式）
3. renwei 自检（zhili-style.md 第3节）→ 修复草稿
4. 渲染 HTML：python3 scripts/render_zhili_article.py /tmp/draft.md /tmp/article.html
5. 验证：python3 scripts/validate_zhili_article.py --title "<标题>"
6. 配图 + 封面 → python3 scripts/push.py --html /tmp/article.html --cover /tmp/cover.jpg
```

> ⚠️ 详细工作流（含 renwei 预扫、图片注入路径、常见错误速查）见 `references/practical-writing-workflow.md`。
> ⚠️ CSS / stop-slop / renwei / pre-submit 清单 → 见 `zhili-shared/references/zhili-style.md`。

---

## Step 1：候选评估（必走）

收到 Trending 候选（`"zhiligithub :6️⃣ xxx"` 格式）后，先评估值不值得写。

**6 步评估**（详见 `references/candidate-evaluation-checklist.md`）：

1. **客观事实**：GitHub API 查 stars / forks / license / open issues / topics
2. **黑马分复核**：月均 stars，单日 +X today 不算黑马信号
3. **公众号合规**：监管 / 版权 / 政治 / 平台审核 / 品牌调性 5 维度
4. **六段式可写性**：「三、架构设计」和「五、实战场景」能否各写 350-500 字不灌水？
5. **主题匹配**：核心读者是开发者/AI 技术爱好者，Windows 专属可写，IPTV/灰色消费级不写
6. **输出推荐**：✅ 推荐写 / ⚠️ 可写但有风险 / ❌ 不写

**评估结论不通过就直接放下**，不要硬写。黑马分只是参考，合规和可写性才是硬约束。

---

## Step 2：六段式正文

> ⚠️ **先加载 human-writing，再用三关框架指导写作，不要 renwei 事后查漏。** human-writing 的三关（材料关·推进关·中文关）是在写作过程中实时遵守的准则，不是写完后才拿来检查的工具。写作时每段都要过一遍三关自检，renwei 只在草稿阶段做最终清零。

### 章节结构

| 序号 | 章节 | 内容要求 |
|------|------|----------|
| 一 | 项目名称 | GitHub 链接 + Stars + 语言 + License |
| 二 | 项目介绍 | 2-3 段：痛点场景 → 引入项目 → 一句话定位 + 数据 |
| 三 | 架构设计 | **核心段**（350-450字），3-4 个技术细节分点 |
| 四 | 快速上手 | 安装命令 / CDN 引入 / 关键 API |
| 五 | 实战场景 | **核心段**（400-500字），3-4 次尝试弧线（失败→介入→成功） |
| 总结 | （无 H2） | 一句核心判断 + 留钩子，跟在 `· · ·` 之后 |

> ⚠️ 初稿低于 1500 字，最常见原因是「三、架构设计」或「五、实战场景」被写薄了。

### 扩充模式警告（rewrite vs. fresh writing）

**现象**（实测多篇）：
- 用 human-writing 风格**改写**现有文章时，输出字数通常比原始版本少 20-30%
- 改写模式容易把「六段式骨架 + 现有内容」压缩成精炼但单薄的版本
- 草稿阶段显示 1500+，render 后降到 1380-1450 区间，推送时 api 报告进一步偏低

**对策（三同步原则）**：
1. **目标线上调**：改写模式时，markdown 草稿目标定在 **1700-1800 字**（比 1500-2000 下限高 200-300），确保 render+推送后仍落在范围内
2. **扩充检查点**：每写完一节，立即用 `python3 scripts/render_zhili_article.py /tmp/draft.md /tmp/article.html` 实时看 render 报告的字数，不要等全文写完才发现不够
3. **两轮扩充法**：第一次 render 字数 < 1500 时，不要逐句修补，直接在「三、架构设计」和「五、实战场景」各补一个完整技术细节段（100-150 字/段），效率最高

> ⚠️ 不要依赖 agent 总结里报的「字数 X」，要以 render 脚本输出的 `[OK] 中文字数=N` 为准。两者经常不一致。

### 精简规则（必遵守）

> ⚠️ 以下规则是 human-writing"中文关"在 GitHub 黑马文语境下的具体落地。不要理解为格式要求——它们的作用是防止"穿论坛服装"和模型腔进入正文。

**三关快速自检（写每段时心里过一遍）**：
- **材料关**：这个段落有没有具体技术细节、具体数字、具体尝试弧线（失败→介入→成功）？
- **推进关**：这段比起上一段，有没有新东西（新技术点、新场景、新判断）？
- **中文关**：这句话换成真实项目负责人会怎么说？有没有 AI 黑话、破折号、"不是X是Y"？

1. **body 不放装饰元素**：无顶部分类标签、无 H1、无「刘生 · 2026年X月」副标题、无作者页脚
2. **H2 之间无过渡句**：H2 本身就是转场信号，「说完了 X 和 Y」直接砍
3. **「六、总结」H2 禁止写入 markdown**：总结内容在 `· · ·` 之后自然流入。**不要在 markdown 里写 `## 六、总结`**。render 脚本会把 markdown 里的 `## 六、总结` 原样输出为 HTML H2，validate 的「body 无『六、总结』H2」检查就会失败。这不是 render 脚本的问题，是 markdown 里就不应该出现这个 H2。
4. **Pull Quote → 普通段落**：金句独立成段即可，不需要左边框+斜体+淡灰底三重强调
5. **✅/❌ 标签盒不要**：边界条件融进最后一段散文

### 写作格式

**元信息卡片**（每个项目开头）：
```
**GitHub**：https://github.com/{owner}/{repo}
**Stars**：{Xk} | **语言**：{Language} | **License**：{License}
```

**元信息表**（文末汇总）：
```
| # | 项目 | Stars | 语言 | 适合场景 |
|---|------|-------|------|----------|
| 1 | name | Xk | Python | xxx |
```

---

## Step 3：renwei 自检

> ⚠️ renwei 是三关的最终清零步骤，不是写作过程中的检查工具。写作时用 human-writing 三关实时指导，写完后再用 renwei 做最终扫描。

**经验来源**：OpenCut 和 Graphify 两篇文章的第一稿均含 3-5 处破折号、1-2 处「不是X是Y」、1-2 处 AI 黑话，导致渲染后 validate 失败 2-3 轮。

**必扫高频 violation（草稿阶段）**：

```bash
# 破折号 —— （出现率最高）
grep -n "——" /tmp/draft.md

# 不是X是Y 句式
grep -n "不是.*是" /tmp/draft.md

# AI 黑话：落地 / 完美 / 非常 / 极其 / 赋能 / 闭环 / 持续 / 构建 / 迭代 / 颠覆
grep -n "落地\|完美\|非常\|极其\|赋能\|闭环\|持续\|构建\|迭代\|颠覆" /tmp/draft.md

# 意义拔高（更X/还X/甚至X 紧接形容词或名词）
grep -n "更是\|更是\|还有\|甚至" /tmp/draft.md
```

**⚠️ 内容扩展必然引入新 renwei 违规（不是可能，是每次都会）**：字数不够时，在现有段落后追加新段落是最快达标方法。但追加内容同样受 renwei 约束，破折号、AI黑话、filler words 几乎每次扩展都会重新出现。经验值：每扩展一次会产生 1-3 处新违规，文章通常需要 2-3 次「扩充→扫描→修复」循环才能同时满足字数和 renwei 双目标。不要把 renwei 扫描视为「一次性检查」，而是每次扩充后都必须重跑的必要步骤。

**标题字节预检（草稿阶段）**：
```python
title = "你的标题"
byte_count = sum(3 if ord(c) > 127 else 1 for c in title)
print(byte_count)  # 必须 ≤60
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
| 意义拔高 | Blender 更是需要专门培训 | Blender 得专门培训才能上手 |
| 意义拔高 | 这不仅是 X，更是 Y | 删「更」字或拆成两句 |

**扫描后**：确认全部清零后再渲染草稿。任意一项有结果都需要修复。

```bash
python3 /root/.hermes/skills/creative/zhiligithub/scripts/render_zhili_article.py /tmp/draft.md /tmp/article.html
```

> ⚠️ 章节标题用 `## 一、项目名称`，不能用 `# 一、项目名称`（render 识别 `## ` 前缀）。

**渲染后必须手动注入 `<title>`**：
```python
with open('/tmp/article.html') as f:
    html = f.read()
html = html.replace('<head><meta charset="utf-8">',
    '<head><meta charset="utf-8"><title>正确标题</title>')
with open('/tmp/article.html', 'w') as f:
    f.write(html)
```

---

## Step 5：验证

```bash
python3 /root/.hermes/skills/creative/zhiligithub/scripts/validate_zhili_article.py /tmp/article.html --title "<标题>"
```

---

## Step 6：配图 + 推送

### 封面图生成（两条路径）

**路径 A（推荐）**：预生成封面图后推草稿
```bash
# ① 用 PIL 将封面裁剪为 900×383
# ② 推草稿（跳过自动封面生成 + 跳过自动配图）
cd /tmp && python3 /root/.hermes/skills/creative/zhiligithub/scripts/push.py \
  --html /tmp/article.html --cover /tmp/cover.jpg --skip-illustration --skip-cover
```

**路径 B（跳过封面）**：`--skip-cover`

### 正文配图

- 每个 H2 章节后至少 1 张截图（mmbiz URL 必须嵌入 HTML）
- GitHub OG 图：`https://opengraph.githubassets.com/1/{owner}/{repo}`
- 上传到 `media/uploadimg` 获取 mmbiz URL，注入到 HTML 对应位置

### 重新发布（删旧草稿）

```bash
cd /tmp && python3 /root/.hermes/skills/creative/zhiligithub/scripts/push.py \
  --html /tmp/article.html --delete-first <old_draft_id>
```

> ⚠️ 必须从 `/tmp` 目录运行（脚本内部依赖相对路径）。
> ⚠️ `html` 必须含 `<title>` 标签（push.py 从中读取标题）。

---

## Pre-submit 检查清单

> ⚠️ 发布前必须跑 `zhili-shared/references/zhili-style.md` 第 4 节的统一检查清单（格式篇 + 内容篇 + AI 套话篇）。

### 格式篇（7 项）

- [ ] 标题 ≤ 22 字节
- [ ] body 无 H1 标题行
- [ ] body 无「刘生 · 2026年X月」副标题
- [ ] body 无顶部分类标签 span
- [ ] body 无「作者：刘生 / 来源：直隶按察使」页脚
- [ ] 无「六、总结」H2
- [ ] 无 ✅/❌ 适合/不适合 标签盒

### 内容篇（8 项）

- [ ] 中文冒号 `：` 为 0
- [ ] 中文破折号 `——` 为 0
- [ ] 中文双引号 `""` 为 0
- [ ] 无排比三连
- [ ] 无「不是 X 是 Y」二元结构
- [ ] renwei 命中率 < 3 项
- [ ] `grep -n '\*\*' /tmp/article.html` → 空（无 Markdown 残留）
- [ ] `grep -n '^$' /tmp/article.html` → 空（无纯空行）

### Stop-slop 扫描（在草稿 markdown 上做，不在 HTML 上）

> ⚠️ validate_zhili_article.py 检查的是渲染后 HTML，但 HTML 里中文标点已被 strip，所以破折号/冒号检测是给 markdown 用的。**filler words 的实际检测在草稿阶段**，render 后 HTML 无法复现。必须先清零再 render。

```bash
# 破折号（高频，render 后 HTML 检测不到）
grep -n "——" /tmp/draft.md

# filler words：值得注意的是 / 实际上 / 其实 / 那么 / 大家都知道 / 当然也不排除 / 在某种程度上 / 一定程度上 / 不难看出
grep -n "那么\|实际上\|其实\|值得注意的是\|大家都知道" /tmp/draft.md

# AI 黑话
grep -n "落地\|完美\|非常\|极其\|赋能\|闭环\|颠覆" /tmp/draft.md

# 不是X是Y 句式
grep -n "不是.*是" /tmp/draft.md
```

命中率 ≥ 1 → 先清零再 render。不能在 render 后等 validate 报 HTML 里找不到再回去改草稿。

---

## 凭证配置

凭证存储在 `references/config.md`（APPID / APPSECRET），不输出到对话。

## 已知限制

| 功能 | 状态 | 解决 |
|------|------|------|
| 直接群发 | ❌ 个人号无权限 | 草稿箱手动发布 |
| 部分分类 | ⚠️ category_id 不稳定 | 手动在后台选择 |
| WeChat `uploadimg` 返回 40137 | PNG 上传失败 | 转 JPEG 再上传 |
| `urllib.request` multipart 上传报 41005 | Python urllib 上传图片返回 41005 | 改用 subprocess + curl |
| push.py 自动配图超时 | 生成+上传 2+ 张配图时 120s 内完不成 | 先 `--skip-illustration` 推草稿，再单独生成图补推 |
| GitHub raw 超时 | `raw.githubusercontent.com` 超时 | 用 API + base64 解码 |
