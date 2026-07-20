# GitHub 项目调研工作流（新项目首次发布专用）

> 适用于：**评估通过后**用 GitHub API 5 步调研法挖真实数据。
> **更上游**：`references/candidate-evaluation-checklist.md`（该不该写——黑马分复核、合规检查、6 段式可写性）
> **更下游**：`references/practical-writing-workflow.md`（调研完之后怎么写 + 转 HTML + 7 项验证）
> **核心原则**：**用 GitHub API 拿真实数据，不要照搬用户描述、不要相信官网 changelog**。

## 调研五步法（按顺序执行）

### 第 1 步：项目基础元信息（必做）

```bash
curl -s "https://api.github.com/repos/{owner}/{repo}" | python3 -c "
import json, sys
d = json.load(sys.stdin)
for k in ['full_name', 'stargazers_count', 'forks_count', 'language',
         'license', 'description', 'updated_at', 'created_at',
         'topics', 'homepage', 'size', 'open_issues_count', 'default_branch']:
    v = d.get(k)
    if k == 'license' and v: v = v.get('spdx_id')
    print(f'{k}: {v}')
"
```

**关键字段**：
- `stargazers_count` / `forks_count`：写到数据卡片
- `license.spdx_id`：**如果返回 `NOASSERTION` 或 `None`，必须去 raw.githubusercontent.com 拉 LICENSE.txt 看实际条款**（monorepo 常见问题）
- `topics`：写到介绍段
- `created_at`：判断项目年龄（5 年以上 = 老牌，3 年以下 = 新生）

### 第 2 步：最近 5 个 Releases 找大版本号

```bash
curl -s "https://api.github.com/repos/{owner}/{repo}/releases?per_page=5"
```

看 `tag_name` 和 `published_at`，找最近的主版本（**跳过纯 patch / rc**，关注 v11.8.0 这种 minor/major）。

⚠️ **release body 经常很简短甚至空**（很多项目把 changelog 写在单独页面）—— 不要从 release body 找功能变更。

### 第 3 步：从 release 分支的 commits 找实际变更（核心）

```bash
# 拿到 release 分支名
BRANCH="release-$(echo $TAG | sed 's/v//' | cut -d. -f1-2)"  # e.g. v11.8.0 → release-11.8

curl -sL "https://api.github.com/repos/{owner}/{repo}/commits?sha=$BRANCH&per_page=30"
```

按 `commit.message` 第一行看，每个 commit 看 `MM-XXXXX`（Mattermost 风格 issue 编号）或 `(#12345)` PR 编号。

**目的**：找到 5-8 个关键 PR/commit 当作"v11.8.0 主要变更"写入文章。这比 changelog 可靠，因为 GitHub API 直接给数据，没有 SPA 渲染问题。

### 第 4 步：搜索 release 相关的 merged PRs（备选数据源）

```bash
curl -sL "https://api.github.com/search/issues?q=repo:{owner}/{repo}+release-11.8+is:merged&per_page=20"
```

返回 `items[].title` 和 `items[].number`。**比 commits 噪声小**（commit 里有 "Update interdependency" 这种机器合并），但可能没有项目自己的 issue 标签系统（很多项目用 MM-XXXXX 而不是 release-11.8 标签）。

### 第 5 步：License 特殊情况处理

**坑**：monorepo 项目在根目录没放 LICENSE.txt 时，GitHub API `license.spdx_id` 返回 `NOASSERTION`。

**处理**：
```bash
# 1. 查根目录有没有 LICENSE 文件
curl -sL "https://raw.githubusercontent.com/{owner}/{repo}/master/LICENSE.txt" -w "%{http_code}\n" -o /tmp/lic.txt

# 2. 头部前 30 行就是实际条款
head -30 /tmp/lic.txt

# 3. 常见双层 license 模式（要在文章里讲清楚）：
#    - 官方编译版 = MIT
#    - 源码 = AGPL-3.0（或 GPL-3.0）
#    - 配置文件 / admin tools = Apache-2.0
#    例：Mattermost、GitLab、HashiCorp 系产品
```

**避坑指南**：
- ❌ 不要相信 `NOASSERTION` = 没 license —— 可能是文件位置问题
- ❌ 不要相信官网"pricing 页"的 license 描述 —— 那是商业 license，不是开源 license
- ✅ 实际条款看 LICENSE 文件前 30 行

## 官网/文档页的可靠性

| 页面 | 可靠性 | 原因 |
|------|-------|------|
| 项目根 README | ✅ 高 | 几乎都是 markdown，curl 抓得到 |
| GitHub Release notes | ⚠️ 中 | body 可能空，changelog 经常在外链 |
| 官网 / 产品介绍页 | ❌ 低 | 营销话术 + SPA 渲染，curl 抓不到有价值内容 |
| 官方 changelog 页 | ❌ 低 | 多数是 SPA（Vue/React 渲染），curl 拿不到 |
| 官方 blog 文章 | ⚠️ 中 | markdown 多但部分页面是 ghost/contentful |

**调研原则**：**项目真实信息以 GitHub API 为准**，官网只用来确认品牌定位、客户群、目标行业。

## 数据冲突时的优先级

```
GitHub API（真实数据）
  > 用户提供的项目描述（一手）
  > 第三方报道 / 分析（二手）
  > 官网营销文案
  > 第三方百科（百度百科、搜狗百科等）— ⚠️ 不可靠
```

### ⚠️ 第三方百科不可信（Baidu Baike 等）

**已验证案例**：QClaw（2026-07-14 session）
- 百度百科词条声称：QClaw 由"腾讯电脑管家团队"于 2026-03-09 发布
- GitHub 事实：qiuzhi2046/QClaw 创建于 **2026-03-28**，Owner 是个人账号（type=User），README 自述"秋芝2046团队开发"，已暂停维护
- 结论：百科内容与 GitHub 事实严重不符，不可引用

**百科核查流程**（当用户引用百科内容时）：
1. 用 GitHub API 查 repo `created_at`、`owner.type`（User/Organization）
2. 读 raw README 自述（`curl -s https://raw.githubusercontent.com/{owner}/{repo}/main/README.md`）
3. 查 npm/package.json 的 `author` 字段
4. 交叉验证官网域名的自我介绍
5. 如果百科声称的"开发主体"与 GitHub/npm/README 不一致，**不要引用百科内容**，告知用户百科信息有误，以 GitHub 事实为准

如果用户描述和 GitHub API 冲突，**以 GitHub API 为准**——并在文章里用更精确的数据（不要照搬用户措辞）。

例：用户说"Mattermost 主打企业级审计与私有化"，文章里改成更具体的事实：
- "MIT（官方编译版）/ AGPL-3.0（源码）双层 license"
- "v11.8.0 的 12 个 PR 几乎全是安全合规硬化（ABAC、OAuth、跨频道消息所有权）"
- "客户群：美国国防部、NATO、Five Eyes、关键基础设施企业"

## 配图获取（仅在确认要发布时执行）

调研阶段**不下载图片**。如果用户说"要发布"，再走标准流程：

1. GitHub OG 图（最通用）：`https://opengraph.githubassets.com/1/{owner}/{repo}` （无需认证，1200×600 PNG）
2. 项目 user-attachments：`https://github.com/user-attachments/assets/<hash>` （curl 可下，质量高）
3. README 截图（last resort）：PIL 渲染 markdown

⚠️ **调研阶段不下载图片**——避免无用的素材处理。

## 调研后写文章的工作流

1. 把第 1-5 步收集到的数据填到「文章信息表」（数据卡片、H2 大纲、PR/commits 列表）
2. 写 markdown 草稿（1500-2000 字）
3. 转 HTML（用 `references/practical-writing-workflow.md` 的脚本）
4. 7 项验证（字数 / 标题字节 / 空行 / branding / H2 边框 / 代码块换行 / Markdown 残留）
5. **询问用户**："内容 OK 吗？要发布吗？"
6. 用户点头后，再走封面图 + mmbiz 上传 + 草稿创建流程

⚠️ **关键纪律**：用户给素材 ≠ 用户要发布。**默认只输出内容 + 询问，不自动推送**。

## 实战样本

### Mattermost v11.8.0（2026-06-13 session）

**调研发现**：
- Stars 37.7k, Forks 8.7k
- v11.8.0 发于 2026-06-09，11.8.1 紧随其后（2026-06-10）
- release-11.8 分支 30+ commits，**12+ 个安全/合规硬化 PR**
- License = NOASSERTION（monorepo 根目录 LICENSE.txt 实际是双层：MIT 编译版 + AGPL 源码 + Apache admin tools）

**关键 PR 列表**（按时间倒序，从 release-11.8 commits 抓取）：
- MM-68830 Preserve unknown permissions during migrations on downgrade
- MM-68618 Harden file removals
- MM-69010 Validate incoming webhook user membership
- MM-69057 Verify post ownership on inbound shared-channel edit/delete
- MM-68952 Resolve public channel mentions for non-members under Compliance
- MM-68995 reject deactivated guests on REST magic-link login
- MM-68978 Harden ABAC masking guards
- MM-68845 Tighten authorization on /share-channel autocomplete
- MM-68840 Apply team sanitization on scheme teams endpoint
- MM-68983 Tighten OAuth token issuance and cleanup

**文章主线**：v11.8.0 几乎全是安全加固 → 这恰好说明 Mattermost 在企业级赛道的真正价值——"朴素本身就是企业级"。

## 相关文件

- `references/candidate-evaluation-checklist.md` — 候选该不该写（黑马分复核 / 公众号合规检查 / 6 段式可写性）— **本文件的上游**
- `references/practical-writing-workflow.md` — 写作 + 转换 HTML + 7 项验证 — **本文件的下游**
- `references/project-screenshot-workflow.md` — 配图（仅发布时用）
- `references/republish-fallback-workflow.md` — 旧文复扒（内容已知场景）
- `references/format-guide.md` — 元素清单（标题公式、列表格式等）
