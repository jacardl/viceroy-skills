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

## 完整工作流（8 步）

```
0. 写作前：skill_view(name='human-writing') 加载写作体系，用其三关框架指导写作
0.5. 数据事实核查：用户提供的内容含具体数字时，动笔前必须溯源核验（见 references/practical-writing-workflow.md 第 0.5 节；核查记录模板 references/fact-check-template.md）
1. 候选评估（收到 Trending 候选时必走）→ 不通过直接放下
2. 写 markdown 草稿（1500-2000字，六段式）
3. renwei 自检（zhili-style.md 第3节）→ 修复草稿
4. 渲染 HTML：python3 scripts/render_zhili_article.py /tmp/draft.md /tmp/article.html --title "<文章标题>"
5. 验证：python3 scripts/validate_zhili_article.py --title "<文章标题>"
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
2. **扩充检查点**：每写完一节，立即用 `python3 scripts/render_zhili_article.py /tmp/draft.md /tmp/article.html --title "<文章标题>"` 实时看 render 报告的字数，不要等全文写完才发现不够
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

# filler words（实际上是 renwei 第2项，但 markdown 扫描更准）
grep -n "那么\|实际上\|其实\|值得注意的是\|大家都知道" /tmp/draft.md

# AI 黑话
grep -n "落地\|完美\|非常\|极其\|赋能\|闭环\|颠覆\|构建\|迭代\|持续" /tmp/draft.md

# 意义拔高（更X/还X/甚至X 紧接形容词或名词）
grep -n "更是\|更是\|还有\|甚至" /tmp/draft.md
```

**⚠️ 内容扩展必然引入新 renwei 违规（不是可能，是每次都会）**：字数不够时，在现有段落后追加新段落是最快达标方法。但追加内容同样受 renwei 约束，破折号、AI黑话、filler words 几乎每次扩展都会重新出现。经验值：每扩展一次会产生 1-3 处新违规，文章通常需要 2-3 次「扩充→扫描→修复」循环才能同时满足字数和 renwei 双目标。不要把 renwei 扫描视为「一次性检查」，而是每次扩充后都必须重跑的必要步骤。

**⚠️ 修复后必须重新验证再渲染（2026-09-16 实测警示）**：扫描发现问题 → 修复 → **必须重新跑同样的扫描命令确认清零**，才能进入渲染步骤。修复后直接渲染而不重扫，等于没有修复。典型翻车路径：grep 发现 colons → 批量替换 → 渲染 → validate 仍然报 colons → 回退重找原因。根因是批量替换没覆盖所有出现位置，或修复点后文又引入了新的违禁词。重扫确认清零，是每次修复后不可跳过的闭眼操作。

**⚠️ H2 标题含「不是…是」会触发假阳性（2026-08-23 实测）**：validate 脚本把 HTML 标签 strip 后，H2 标题文本会和紧随其后的段落拼在一起，正则 `不是[^，。,\n]{1,40}[，,][^是\n]{1,40}是` 会跨标题-正文边界匹配。本session写出「五、实战用法：过滤网，不是撒网」后 validate 报 1 处命中，markdown grep 却干净——原因是 H2 拼接后正则捕获了「过滤网，不是撒网光有工具」。**解法**：H2 标题里不要同时出现「不是」和「是」；如果标题含「不是X是Y」结构，改写成不含「是」的形式（如「精准过滤，按需投递」），或者在「不是」和「是」之间插入超过 40 个字符使正则窗口失效。修完标题后重新渲染验证。

**⚠️ 总结段落里「不是X是Y」是高频误用地雷（2026-09-27 实测）**：写手自然会在结尾reach for「Paperclip解决的不是X，是Y」这个句式。但 validate 的 `不是.{0,30}是` 会命中它——因为它不只抓「不是X是Y」语法结构，而是抓任何「不是」和「是」出现在30字符窗口内的情况，包括同一段落内的任何共现。**安全写法**：彻底不用「不是」，改用「只有一个」「要回答的是」「核心是」等肯定句式。验证清零方法是 grep 草稿确认无任何「不是」再 render。

**⚠️ 草稿里不要写「六、总结」H2（2026-09-27 实测）**：技能文档里写了不要写，但实践中写手会在草稿末尾加 `## 六、总结`。validate 检查会因此 fail。**操作约束**：写完草稿后，第一件事就是确认 markdown 末尾没有 H2 章节标题。render 脚本不会自动去掉它，它会原样进 HTML。

**标题字节预检（草稿阶段必须做，不要等 validate）**：
```python
title = "你的标题"
byte_count = sum(3 if ord(c) > 127 else 1 for c in title)
print(byte_count)  # 必须 ≤60
```
超了就先改草稿标题再渲染，否则 HTML 里改了还要重新跑 validate。常见超标模式见 `references/title-byte-precheck.md`。

---

## 0.5 微信原文拉取失败时的决策（2026-08-15 新增）

**触发条件**：用户提供微信文章链接 → 所有自动化手段（直接 curl / baoyu-url-to-markdown / 浏览器）均失败（Cloudflare 验证墙 / 时代证券 / 访问拒绝）

**用户指令优先级**：
- 用户说「直接写」「不管了」「先写」→ **跳过拉取，凭摘要动笔**
- 用户没说话 → 先尝试 Wayback Machine、百度缓存等备用源（≤5 分钟），仍未果再询问

**操作步骤**（跳过拉取时）：
1. 用用户提供的摘要/要点直接动笔
2. 在摘要信息后加一句「内容未经原文核验，如有问题请在后台修改」
3. 不在正文里说「由于无法访问原文」这类暴露信源缺陷的句子
4. 写完后明确告知用户「未能核验原文，请后台确认关键数据」

**⚠️「直接写」不是偷懒借口**：用户没有明确说「直接写」之前，必须尝试备用源。5 分钟内无法解决才询问。
**常见修复对照**：

| 违规 | 原文 | 改后 |
|------|------|------|
| 破折号（解释） | A——B | A，B |
| 破折号（转折） | A——B | A。B |
| 不是X是Y | 问题不是A，是B | 问题不在于A，而在于B |
| 不是X是Y | 代码不是文本，代码是图 | 代码是图，不是文本 |
| 不是X是Y（隐性） | 这个项目不是玩具，可以接入真实生产流程，108k stars…… | 完全删除「不是」，改「可以直接接入」 |
| AI 黑话 | 一旦落地 | 一旦实现 |
| AI 黑话 | 它现在还不完美 | 它现在还不够完善 |
| AI 黑话 | 会非常明显 | 会很明显 |
| AI 黑话 | 功能非常强大 | 功能很强 |
| 意义拔高 | Blender 更是需要专门培训 | Blender 得专门培训才能上手 |
| 意义拔高 | 这不仅是 X，更是 Y | 删「更」字或拆成两句 |

**⚠️「不是X是Y」比名字更隐性（2026-08-19 实测）**：

validate 的 regex 是 `不是.{0,30}是`，它不只抓「不是X是Y」语法结构，而是抓**任何「不是」和「是」出现在30字符窗口内**的情况，包括：
- `不是玩具，可以接入真实生产流程，……是……` ← 第三轮修复后仍然命中（"不是玩具" + "是" 在30字符内）
- `问题不是A，是B` ← 经典结构
- `真正要解决的不是X，而是Y` ← 「不是」和「而是」紧邻，「是」在「而」后30字符内

**解法原则**：只要句子里同时出现「不是」和「是」，不管它们是什么语法关系，都会被抓。修复时**彻底删除「不是」**，用主动/中性表述替代：
- ❌ `不是玩具，可以接入真实生产流程` → 「不是」和「是」都在，regex 30字符窗口还在
- ✅ `可以直接接入真实生产流程` → 删掉「不是」，换主动句
- ❌ `真正要解决的不是X，而是Y` → 「不是」和「是」都在30字符内
- ✅ `真正要回答的问题只有一个，能不能X` → 没有「不是」，没有「是」

**⚠️ "落地页" vs AI jargon 假阳性（2026-08-12 实测）**

renwei AI黑话池含「落地→实现」，但「落地页」（landing page）是合法行业术语，单独出现不应触发。validate 扫描仍会命中是因为正则按子串匹配。**解法**：写作时遇到 landing page 相关内容，直接用「着陆页」替代「落地页」，避免假阳性打回。判断标准：「落地」单独作动词→替换；「落地页」作复合名词→保持或换「着陆页」。

**扫描后**：确认全部清零后再渲染草稿。任意一项有结果都需要修复。

```bash
python3 /root/.hermes/skills/creative/zhiligithub/scripts/render_zhili_article.py /tmp/draft.md /tmp/article.html --title "<文章标题>"
```

> ⚠️ 章节标题用 `## 一、项目名称`，不能用 `# 一、项目名称`（render 识别 `## ` 前缀）。

### ⚠️ 硬性前置检查（在任何 render 之前必须完成）

写完草稿到 render 之间，有三件事**必须先做**，缺一不可：

1. **标题字节预检**：`python3 -c "title='你的标题'; print(sum(3 if ord(c)>127 else 1 for c in title))"` → 必须 ≤ 60。超标则先改标题再 render，render 后再改要重新跑 validate。
2. **停用词扫描**（在 markdown 上跑，不在 HTML 上）：`grep -n "——\|：\|不是.*是" /tmp/draft.md` → 必须全清零再 render。渲染后 HTML 检测不到中文标点，所以草稿阶段的扫描不可跳过。
3. **字数预估**：markdown 字数 vs render 字数有 10-15% 差值。1500+ 的草稿 render 后通常落在 1350-1550 区间。低于 1500 的草稿先扩充再 render，避免 render 后发现不够再返工。

render 脚本将 `<title>` 直接写入 HTML。**`--title` 参数必传**，否则脚本报错。

> ⚠️ 旧方案（渲染后手动 `replace` 注入 `<title>`）已废弃：render 每次重新生成 HTML 都会覆盖之前注入的 title，导致 push.py 读到空标签后回退为「GitHub 黑马项目」。用 `--title` 参数一次搞定。

> ⚠️ 章节标题用 `## 一、项目名称`，不能用 `# 一、项目名称`（render 识别 `## ` 前缀）。

## Step 5：验证

```bash
python3 /root/.hermes/skills/creative/zhiligithub/scripts/validate_zhili_article.py /tmp/article.html --title "<文章标题>"
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
> ⚠️ render 时加 `--title` 参数，push.py 从 HTML `<title>` 读取文章标题。

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

> ⚠️ **H2 标题「不是X是Y」误检**：validate 对 HTML 去掉标签后的纯文本做正则检测，H2 标题和紧随其下的正文被拼到同一段落，导致 H2 里的「不是」和下文的「是」触发误检。解法：H2 标题完全避免「不是...是...」句式（不等同于正文清零）。详见 `references/h2-title-not-xy-pattern.md`。

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
