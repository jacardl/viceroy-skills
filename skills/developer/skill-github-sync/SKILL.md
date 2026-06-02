---
name: skill-github-sync
description: >
  将 Skills 同步到 GitHub 仓库（skillshub 公开仓库 + 私有专属仓库），并维护符合 khazix-skills 标准的 README。当用户说"同步skills到GitHub"、"上传skill到github"、"推送skill到远程"、"更新skillshub仓库"、"维护GitHub上的skill仓库"、"更新 README"时使用此技能。包含完整的 GitHub 推送流程和标准 README 生成规范。
---

# Skill GitHub Sync

将本地 Skills 同步到 GitHub 仓库的完整流程。

## 现有分类（必须使用）

| 英文分类 | 中文名 | 说明 |
|---------|--------|------|
| `ai` | AI模型 | 9router, mmx-cli |
| `assistant` | 助理 | **baoyu-url-to-markdown**, find-skills, markitdown, markdown-to-report, neat-freak, obsidian, obsidian-cli, storage-analyzer, wechat-article-to-markdown, youtube-transcript |
| `creative` | 创意 | khazix-writer, zhili-publish, zhilicomments, zhiligithub |
| `developer` | 开发 | setup-matt-pocock-skills, skill-creator, skill-github-sync, skill-maintenance |
| `operations` | 运营 | aihot, geo系列(3个), github-daily-trending, radar系列(3个), scrapling, SEO系列(25个) |
| `product` | 产品 | brand-product-audience-relevance, competitor-discovery, hv-analysis, patent-disclosure-skill, software-copyright-materials |

**铁律**：不要新增分类，只在现有分类中添加技能。

## 核心流程

### 第一步：读取 Token

从 `~/.hermes/keys/github_token.txt` 读取 GitHub PAT。

### 第二步：读取仓库目录结构（必须）

**同步前必须先读取仓库现有结构**，确认目标分类存在：

```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://api.github.com/repos/jacardl/skillshub/contents/skills" | \
  grep '"name"'
```

### 第三步：同步 Skill 文件

使用 git 原生 push 方式（比 GitHub API 更稳定）：

1. `git clone https://github.com/jacardl/skillshub.git /tmp/skillshub_sync`
2. 复制技能文件到对应分类目录
3. `git add → commit → GIT_ASKPASS=echo git push`

**Token 持久化方式**：将 Token 写入 `~/.netrc`：

```bash
echo "machine github.com login jacardl password $(cat ~/.hermes/keys/github_token.txt)" >> ~/.netrc
chmod 600 ~/.netrc
```

远程 URL 嵌入 Token：
```bash
git remote set-url origin https://jacardl:$(cat ~/.hermes/keys/github_token.txt)@github.com/jacardl/skillshub.git
```

### 第四步：同步后必须更新 README

每次增删技能或调整分类后，**必须同步更新 README.md 和 README.en.md**。

## README 标准格式（khazix-skills 风格）

### 必须包含的元素

| 元素 | 说明 |
|------|------|
| **LICENSE 文件** | 必须有 MIT LICENSE 文件在仓库根目录 |
| **双语 README** | 必须有 `README.md`（中文）和 `README.en.md`（英文） |
| **License Badge** | `![License](https://img.shields.io/badge/License-MIT-3B82F6?style=for-the-badge)` |
| **Skills Badge** | `![Skills](https://img.shields.io/badge/Skills-N-10B981?style=for-the-badge)` |
| **AgentSkills Badge** | `![AgentSkills](https://img.shields.io/badge/AgentSkills-Standard-8B5CF6?style=for-the-badge)` |
| **平台徽章** | Claude Code / Codex / OpenCode / OpenClaw |
| **中英切换** | `**中文** · [English](./README.en.md)` |
| **目录表** | 所有分类一览，含说明 |
| **安装方式** | 自然触发句式示例 |
| **每个技能** | 名字 + 一句话描述 + 触发示例 |
| **About** | 作者说明段落 |
| **⭐ 支持** | Star 引导 |
| **页脚** | License + Made by |

### 安装命令格式（必须用 `--skill`）

```bash
npx skills add jacardl/skillshub --skill <skill-name>
```

示例触发：
```
帮我安装 storage-analyzer
帮我安装 hv-analysis
帮我安装 khazix-writer
```

### 表格格式要求

每个技能一行，格式：

| 名字 | 一句话 | 触发示例 |
|------|--------|----------|
| [**skill-name**](path) | 简短描述 | 触发命令 |

### 系列技能合并规则

- **SEO 系列（25个）**、**GEO 系列（3个）**：合并为一行，内部用 `·` 分隔
- 剩余单个技能正常列示
- 运营分类可拆分为 `运营（operations）` + `运营（operations）— 其他`

### README 结构模板

```
# 标题 + Badge 区
<div align="center">
[中英切换]
# Skillshub
[描述]
[Badge: License, Skills, AgentSkills]
[平台徽章]
</div>

---

## 📋 目录
[分类表格]

## 📦 安装方式
[触发示例]

## ✨ Skills
[按分类列出，每技能：名字 + 一句话 + 触发示例]
[GEO系列合并行]
[SEO系列合并行]
[其他运营技能单独列出]

## 🌟 关于
[作者说明]

## ⭐ 支持

<div align="center">
[License] · [Made by]
</div>
```

## 注意事项

1. **README 必须随技能同步更新**——每次 add/commit/push 后检查 README 是否需要更新
2. **使用英文分类名**：operations, product, assistant, creative, developer, ai
3. **不要新增分类**：如果仓库没有对应分类，将技能放入最接近的现有分类
4. **Token 权限**：确认 PAT 有 `repo` 写入权限
5. **git mv 优先**：同仓库内移动文件用 `git mv` 而非 `cp + git add`（保留历史）
6. **README 数字准确性**：每次更新后核实各分类技能数量和总数

## 推送命令示例

```bash
# 克隆
git clone https://github.com/jacardl/skillshub.git /tmp/skillshub_sync

# 复制技能（如 storage-analyzer 到 assistant）
mkdir -p /tmp/skillshub_sync/skills/assistant/storage-analyzer
cp -r /path/to/skill/* /tmp/skillshub_sync/skills/assistant/storage-analyzer/

# 提交
cd /tmp/skillshub_sync
git add <files>
git commit -m "feat: add storage-analyzer skill"
GIT_ASKPASS=echo git push
```