---
name: zhiliGEO
related_skills: [zhili-illustration]
description: 写直隶按察使公众号 GEO 垂直系列文章。当用户说「写一篇 GEO 文章」「帮我写 GEO""「GEO 系列」「GEO 选题」「GEO 文章」「写个 GEO 稿」或类似需求时触发。为直隶按察使公众号撰写 GEO 垂直类文章——对比 SEO 与 GEO、分析 GEO 案例、解读 AI 搜索趋势、讲解品牌在 AI 时代的信息基础设施。故事驱动 + 数据锚点 + 结尾洞察，格式为微信草稿箱 HTML。
---

# zhiliGEO · 直隶按察使 GEO 垂直写作技能

> ⚠️ **硬性前置要求：每次写作前必须先 `skill_view(name='human-writing')` 加载写作体系，用它的框架指导写作，而不是凭感觉下笔后依赖 renwei 查漏。** renwei 是中文关的自动化检查器，不是写作工具。

## 核心定位

为「直隶按察使」公众号写 GEO（Generative Engine Optimization，生成式引擎优化）垂直系列文章。

**不是** SEO 教程，不是行业报告，是**品牌在 AI 搜索时代如何被准确理解**的实战故事。

## 参考范文

**必读**：`references/geo-article-sample.md` — GEO 系列第一篇原文，含全文骨架、每个模块的实际写法要点、金句位置、数据密度参考。写新 GEO 文章前通读一遍。

## 品牌参数

| 参数 | 值 |
|------|-----|
| 公众号名 | 直隶按察使 |
| 作者 | 刘生 |
| 样式 | Georgia, Noto Serif SC / #f5f4ed 背景 / 强调色 #c9553d |
| 分隔符 | `· · ·`（三颗居中墨点） |
| 发布 | 微信草稿箱 JSON 编码：`json.dumps(payload, ensure_ascii=False).encode("utf-8")`，Content-Type: application/json |

## 文章结构铁律

每篇文章必须包含以下六个模块，顺序固定：

> ⚠️ **章节标题必须用 `## ` 开头**（如 `## 一、信源路径`），禁止写纯中文数字 `一、` 开头。因为 `render_zhili_article.py` 只识别 `## ` 格式作为 H2，不识别 `一、`。违反则 H2 数量为 0，样式A的 `#00d4aa` 左边框全部丢失。

### 1. 开头钩子（150–300字）

开头有五种形态，每次写新文章前先决定用哪一种，**不要每次都选同一种**：

1. **数据反常开场**：一个让你意外的数字，引导读者追问为什么
2. **认知矛盾开场**：一个和常识相反的事实，让读者产生「等等，真的是这样？」的疑惑
3. **行业事件开场**：最近发生的真实事件，从具体新闻切入
4. **直接设问开场**：用一个精准的问题把读者拉进思考，不绕弯子
5. **类比推进开场**：用一个强比喻先建立感知框架，再展开

**写法要求**：
- 场景要具体（行业、产品、具体数字）
- 语气是「我告诉你一件让我自己都重新想了一遍的事」
- 结尾落在一个具体的痛点上，这个问题整篇文章会回答
- 每次只选一种开头形态，**不要叠加**（比如既讲故事又甩数据又反常识全上）

**禁忌**：
- ❌ 不要每次都用「朋友求助」「客户困惑」——这个套路已经用滥了
- ❌ 不要用「事情是这样的」这种模板句
- ❌ 不要用「近年来」「随着 AI 的发展」这类空洞开头
- ❌ 开头不要堆两个以上的数据点，读者还没进入语境

### 2. 核心数据锚点（200–400字）

引入一个具体的研究数据。必须是可溯源的数字，不是模糊的"很多"。

来源优先顺序：
1. 权威机构报告（Moz、Ahrefs、SparkToro、Search Engine Land）
2. 平台官方文档（Google AI Overview 官方指南）
3. 大规模数据研究（N>1000 样本）

**格式**：数字 + 来源 + 一句话解读。不要堆数字，每个数据只服务一个观点。

### 3. 逻辑展开（800–2000字）

用**对比**推进思考。推荐结构：

- SEO 逻辑 vs GEO 逻辑（用户行为变了什么）
- 旧世界 vs 新世界（可抓取 vs 可理解）
- 做 X 像发传单 vs 做 Y 像开咨询处（强比喻）

每次切换对比，在 `· · ·` 分隔符后另起一段。

**禁忌**：
- ❌ 罗列 bullet point
- ❌ 堆砌"第一第二第三"
- ❌ 超过 200 字没有新信息点
- ❌ 企业名（用"某品牌""某平台"或品类词代替）

### 4. 行动框架（200–500字）

给出具体可操作的东西。结构选择：

- **五步法**（最简单的清单，但用故事解释每步为什么重要）
- **两种状态对比**（做 GEO 前 vs 做 GEO 后）
- **三个常见误区**（先破后立）

### 5. 行业信号（200–400字）

用真实商业事件收尾。优先选：
- 招标市场的变化（哪个品牌把 GEO 写进了标书）
- 行业服务的乱象（KPI 设得离谱会逼出什么）
- 大厂动作（Google、百度、字节的 AI 搜索产品更新）

这节证明 GEO 不是概念，是正在发生的事情。

### 6. 结语钩子（80–150字）

最后一段回扣开头故事，给出一个认知升级。

格式：
> 这大概就是 GEO 的本质。不是 ____，不是 ____，是 ____。
> （一句金句收尾，不加 CTA）

## 写作风格规范

### 必须遵守
- **口语对话感**：读起来像作者在跟你喝茶聊天，不是写论文
- **具体 > 模糊**：用真实数字、真实案例、真实对话
- **立场鲜明**：作者有观点，不做理中客
- **用强比喻**：每个抽象概念必须配一个生活化的比喻

### 严禁出现
- ❌ 任何 emoji 或表情符号
- ❌ 任何 bullet point（`· ` 开头或 `- ` 开头的列表）
- ❌ 企业全名（可用"某品牌""某平台"或品类词代替）
- ❌ "本文由 xxx 自动发布"等 branding
- ❌ 超过 3 个分隔符 `· · ·`（每篇文章用 2–3 个最佳）
- ❌ 超过 5 个数据点（每个数据用深用透，不要堆砌）

### 标点与格式
- 中文引号「」代替英文引号
- 数字用阿拉伯数字（"3年"不是"三年"）
- 百分比用 % 符号（"88%"不是"百分之八十八"）
- 英文术语第一次出现附中文翻译（"GEO（生成式引擎优化）"）

## 文章标题规范

| 位置 | 规则 |
|------|------|
| 标题 | 16–24 字，含 GEO 或 AI 搜索相关词 |
| 副标题 | 可选，补充角度或悬念 |
| 标题风格 | 悬念感 > 概括感（"用户不搜了，AI 替你选了" > "GEO 与 SEO 的区别"）|

## 参考文件

| 文件 | 用途 |
|------|------|
| `references/geo-article-sample.md` | GEO 系列第一篇原文，含全文骨架、写法要点、金句位置 |
| `references/style-guide.md` | 六模块结构与开头钩子规范 |
| `references/geo-knowledge.md` | GEO 核心概念（信源路径 / 算法权重 / AIBE / Prompt Map 等） |
| `references/renderer-pitfalls.md` | `render_zhili_article.py` 已知限制（H2 格式/图片接口/超时处理） |

## 渲染标准（样式A）

> ⚠️ **不要手写 HTML**。所有 HTML 必须通过 `render_zhili_article.py` 脚本生成，以确保样式A标准一致。

**样式A CSS（不可修改）：**

| 元素 | 样式 |
|------|------|
| 正文背景 | `#f5f4ed` |
| 正文字体 | `Georgia, 'Times New Roman', serif` |
| H2 标题 | `border-left: 4px solid #00d4aa` + `#1B365D` 色 + 左边框是标志性特征 |
| 强调色 | `#c9553d` |
| 段落行高 | `line-height: 1.85` |
| 段落字重 | `16px` |
| 分隔符 | `· · ·`（居中墨点，`color: #c9553d`） |

**渲染脚本用法：**

```bash
# 1. 渲染 HTML（自动应用样式A）
python3 scripts/render_zhili_article.py --title "文章标题" draft.md output.html

# 2. 验证 HTML（4 重验证）
python3 scripts/validate_zhili_article.py output.html --title "文章标题"

# 3. 生成封面
python3 scripts/cover_pil.py draft.md cover.png

# 4. 推送草稿
python3 scripts/push.py --html output.html --cover cover.png
```

**推送后自检清单：**
- 作者 =「刘生」| 无 emoji | 无 bullet point | 无企业全名 | 分隔符 ≤ 3 | 标题 16–24 字
- H2 全部带 `border-left: 4px solid #00d4aa` 左边框
- 正文冒号 `：` 全为 0（中文冒号是验证器红线）
- 破折号 `——` 全为 0

## 选题库（GEO 系列可写方向）

1. **SEO vs GEO 本质区别**：用户行为变了什么
2. **品牌在 AI 搜索里的可见度**：数据说话（外链 vs 口碑相关性）
3. **国内 vs 海外 GEO 规则差异**：封闭平台 vs 开放网页
4. **GEO 进入招标市场**：品牌如何应对标书要求
5. **GEO 的三个常见误区**：被提及 ≠ 被推荐
6. **AI 搜索时代的品牌信息基础设施**：从可抓取到可理解
7. **具体品牌 GEO 实战案例**（脱敏处理）

## 发布流程

### WeChat 草稿推送 · 标准步骤

> ⚠️ `render_zhili_article.py` 需要 **两个位置参数**（输入路径 输出路径），不是管道单参数。`push.py` 用 `--html` / `--cover` flag 传参。

**标准步骤：**

1. 渲染 HTML：
   ```bash
   python3 scripts/render_zhili_article.py --title "文章标题" draft.md output.html
   ```
2. 验证 HTML：
   ```bash
   python3 scripts/validate_zhili_article.py output.html --title "文章标题"
   ```
3. 生成封面：
   ```bash
   python3 scripts/cover_pil.py draft.md cover.png
   ```
4. 推送草稿：
   ```bash
   python3 scripts/push.py --html output.html --cover cover.png
   ```
5. 飞书汇报：标题 + 字数 + 草稿 ID

### WeChat 草稿推送 · API 关键陷阱（2026-09-06 实坑）

**封面图 media_id 类型决定草稿是否成功创建：**

| 接口 | type 参数 | 返回字段 | 能否用于 `draft/add` |
|------|-----------|---------|---------------------|
| `media/upload` | `thumb` | `thumb_media_id` | ❌ 导致 40007 invalid media_id |
| `material/add_material` | `image` | `media_id` | ✅ 可用于 `thumb_media_id` 字段 |

**推送草稿的标准步骤**：

1. 用 `material/add_material?access_token=...&type=image` 上传封面图 → 获得 `media_id`
2. 用 `media/uploadimg` 上传正文配图 → 获得 CDN URL（`http://mmbiz.qpic.cn/...`）
3. 将 CDN URL 直接写入 HTML 的 `img src`
4. `draft/add` 的 `thumb_media_id` 填第 1 步获得的 `media_id`，不是 `thumb_media_id`

**错误原因**：微信内部 `thumb_media_id` 字段只认 `material/add_material` 的返回值，不认 `media/upload` 的 `thumb_media_id`。两者格式完全不同。

以上 API 细节由 `push.py` 内部处理，外部只需按标准步骤执行即可。
