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

## 字数与结构

| 字段 | 值 |
|------|-----|
| 字数 | **1500-2000 中文字**（纯中文，不含 HTML/CSS/代码块/URL） |
| 结构 | 六段式（默认）/ 编号盘点（多项目合集） |
| 配图 | 项目截图 + 封面（正文必须至少 1 张 mmbiz 图） |
| 用途 | 项目介绍 / 教程 / 深度分析 / 行业观察 |

---

## 完整工作流（6 步）

```
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

### 精简规则（必遵守）

> ⚠️ 以下是佳哥亲自改稿提炼的硬规则，不是建议。

1. **body 不放装饰元素**：无顶部分类标签、无 H1、无「刘生 · 2026年X月」副标题、无作者页脚
2. **H2 之间无过渡句**：H2 本身就是转场信号，「说完了 X 和 Y」直接砍
3. **「六、总结」H2 不要了**：总结内容在 `· · ·` 之后自然流入
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

> ⚠️ **必须扫描全文**（zhililong 从零写，每段都算"动过"，不是只扫动过的地方）。

完整清单 → `zhili-shared/references/zhili-style.md` 第 3 节。

**快速扫描命令**：
```bash
# 破折号（出现率最高）
grep -n "——" /tmp/draft.md

# 不是X是Y 句式
grep -n "不是.*是" /tmp/draft.md

# AI 黑话
grep -n "落地\|完美\|非常\|极其\|赋能\|闭环" /tmp/draft.md
```

**命中率 ≥ 3 项 → 先打回重写，不要一边改一边扫**。

---

## Step 4：渲染 HTML

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
# ① 用 zhili-illustration/mmx 生成封面 → PIL 裁剪 900×383
# ② 上传封面（material/add_material?type=image）→ 拿 media_id
# ③ 推草稿
cd /tmp && python3 /root/.hermes/skills/creative/zhiligithub/scripts/push.py \
  --html /tmp/article.html --cover /tmp/cover.jpg --skip-illustration
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
| GitHub raw 超时 | `raw.githubusercontent.com` 超时 | 用 API + base64 解码 |
