# 技能边界：独立技能互不越界（2026-06-04 沉淀）

## 核心原则

**每个独立技能只管自己的规范（字数、段式、字段、用途、来源），不替兄弟技能定规范。兄弟技能之间用"路由互引"沟通，不是用"对比表"覆盖。**

## 适用对象

所有**有兄弟技能**的 skill 都要遵守：
- `creative/zhiligithub`（长文 1500-2000字 / 六段式）
- `social-media/zhilicomments`（短评 / 轻量三段式）—— 云端 `creative/zhilicomments`
- `openclaw-imports/zhili-publish`（日常复盘 / 公众号通告）

## ❌ 错误写法（已踩坑 12 处）

老 zhiligithub SKILL.md L16-L36 路由表长这样：

```markdown
## ⚠️ 短评 vs 长文的路由规则

| | zhili-publish（长文） | zhilicomments-publish（短评） |
|--|----------------------|-------------------------------|
| 字数 | **4000-8000字** | 500-800字 |
| 结构 | 流式叙事，无显性章节标题 | 轻量三段式（事件+观点+一句话收尾） |
| 配图 | 项目截图+封面 | 1-2张评论配图（可选） |
| 用途 | 项目介绍/教程 | 热评/观点/Reaction |
| 内容来源 | khazix-writer 长文输出 | khazix-writer 短评输出 |
```

**问题**：
- zhiligithub **越界**替 zhilicomments 规定了字数、段式、配图、用途、来源
- 字数还写错了（4000-8000 是错，memory 写 1500-2000；1000-1500 是 2026-06-04 佳哥拍板的新值）
- 修改 zhilicomments 的字段时要去 zhiligithub 里改——**违反单一职责**
- zhiligithub 的引用表跟 zhilicomments 自己的规范不一致时，**两套来源打架**

## ✅ 正确写法（2026-06-04 修复后）

```markdown
## ⚠️ 路由规则（zhiliGitHub 自己的事，不替其他技能定规范）

zhiliGitHub 是**独立技能**，只管 GitHub 黑马长文（1500-2000字）。
- **要发短评 / 观点 / Reaction** → 看独立技能 `social-media/zhilicomments/`
- **要发日常复盘 / 公众号通告** → 看 `openclaw-imports/zhili-publish/`

| 字段 | zhiliGitHub 规范（**只管自己**） |
|------|---------------------------------|
| 字数 | **1500-2000字**（纯中文，不含 HTML/CSS） |
| 结构 | 六段式（默认）/ 7 段式（Telegraf）/ 编号盘点（多项目合集） |
| 配图 | 项目截图 + 封面（正文必须有 mmbiz 图） |
| 用途 | 项目介绍 / 教程 / 深度分析 / 行业观察 |
| 内容来源 | khazix-writer 长文输出（**zhilicomments 走 khazix-writer 短评输出，本技能不接管**） |
```

**改动要点**：
- 对比表第二列（zhilicomments）**整列删掉**
- 路由用「要看 X 去看独立技能 Y」的互引模式，**不替对方定字段**
- 字段表的每条都加"**只管自己**"或"**本技能不接管**"声明
- 字数 / 段式等核心数字**以 memory 为准**（1500-2000字 是 2026-05-20 + 2026-05-30 两次确认的 ground truth）

## 修复 checklist（每次改 / 装 zhiligithub 时跑一遍）

```bash
# 1. 搜越界定规范
grep -n "zhilicomments" /root/.hermes/skills/creative/zhiligithub/SKILL.md
grep -n "短评" /root/.hermes/skills/creative/zhiligithub/SKILL.md

# 2. 致命字数错误（云端版本历史上写过 4000-8000）
grep -n "4000-8000" /root/.hermes/skills/creative/zhiligithub/SKILL.md

# 3. 字数规范应该出现 1500-2000（至少 3 处：frontmatter / 路由表 / 校验脚本）
grep -n "1500-2000" /root/.hermes/skills/creative/zhiligithub/SKILL.md
```

**期望结果**：
- `grep zhilicomments` 残留应该是**路由互引**（带"由独立技能 zhilicomments 规定/不接管"）
- `grep 4000-8000` 应该 0 处
- `grep 1500-2000` 应该 ≥ 3 处

## 兄弟技能的对应改造

| 技能 | 字数 | 段式 | 用途 | 字数规范来源 |
|------|------|------|------|--------------|
| `creative/zhiligithub` | **1500-2000字** | 六段式（默认）/ 7 段式（Telegraf）/ 编号盘点 | GitHub 黑马长文 | memory 2026-05-20 + 2026-05-30 |
| `social-media/zhilicomments` | **1000-1500字**（2026-06-04 佳哥拍板） | 卡兹克轻量三段式 | 短评/观点/Reaction | memory 2026-06-04 + zhilicomments SKILL.md |
| `openclaw-imports/zhili-publish` | *待确认* | *待确认* | 日常复盘/公众号通告 | 未深入 |

## 拍板已决项（2026-06-04 收口）

旧 memory 冲突已统一为：
> 公众号字数规格：zhiliGitHub 1500-2000字，zhiliComments 1000-1500字

**拍板结论（2026-06-04 佳哥）**：zhiliComments 字数 = **1000-1500字**（从 800-1500 上调下限）。
- memory：已改
- `social-media/zhilicomments/SKILL.md`：description / 篇幅表 / 三段式字数 已同步
- 兄弟技能（khazix-writer、zhili-publish）：引用同步
- 云端 `creative/zhilicomments/SKILL.md` 旧值 2000-3000字：本次同步推 1000-1500字上去覆盖
