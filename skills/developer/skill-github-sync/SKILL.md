---
name: skill-github-sync
description: 将 Skills 同步到 GitHub 仓库（skillshub 公开仓库 + 私有专属仓库）。当用户说"同步skills到GitHub"、"上传skill到github"、"推送skill到远程"、"更新skillshub仓库"、"维护GitHub上的skill仓库"时使用此技能。包含完整的 GitHub API 推送流程：获取token、整理目录结构、计算文件sha、按层级创建/更新文件、生成README。
---

# Skill GitHub Sync

将本地 Skills 同步到 GitHub 仓库的完整流程。

## 现有分类（必须使用）

| 英文分类 | 中文名 | 说明 |
|---------|--------|------|
| `ai` | AI模型 | knowledge-agent, 9router |
| `assistant` | 助理 | babysit, do, make-plan, mem-search, smart-explore, wiki-* |
| `creative` | 创意 | remotion-best-practices, wowerpoint, brandkit |
| `developer` | 开发 | design-is, version-bump, taste-skill, neat-freak |
| `operations` | 运营 | aihot, baoyu-url-to-markdown, github-daily-trending, scrapling |
| `product` | 产品 | conducting-user-interviews, hv-analysis, llm-wiki, markdown-to-report |

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

### 第三步：映射本地分类到远程分类

本地 `.claude/skills/` 使用中文分类名（如 `运营/`、`产品/`），需映射到英文分类：

| 本地分类 | 远程分类 |
|---------|---------|
| `运营/` | `operations/` |
| `产品/` | `product/` |
| `助理/` | `assistant/` |
| `创意/` | `creative/` |
| `开发/` | `developer/` |
| `AI模型/` | `ai/` |

### 第四步：上传 Skill 文件

遍历 skill 目录下所有文件，使用 GitHub API 上传：
- 先 GET 获取已存在文件的 sha（防冲突）
- 再 PUT 上传（带 sha 则更新，不带则创建）

### 第五步：更新 README（必须保留现有风格）

同步完成后，必须读取远程 `README.md` 当前内容，并按现有格式做**最小增量 patch**：

- 禁止用固定模板全量重写 README；
- 禁止删除、重排、改写已有 sections、badges、说明文案；
- 只在对应分类表格中新增或更新该 skill 的一行；
- 如顶部 Skills badge 存在，按技能总数只更新数字；
- 如果 README 结构无法识别，先停止并询问用户，不要自动重建。

当前 `viceroy-skills` README 风格是：顶部居中标题 + badges + 分类目录 + 各分类表格。新增 skill 时应在对应分类的 Markdown table 中插入一行。

## 推送命令示例（curl）

```bash
TOKEN=$(cat ~/.hermes/keys/github_token.txt)
REPO="jacardl/skillshub"
BASE="/c/Users/jacar/.claude/skills"

# 上传到 operations
curl -s -X PUT -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message":"chore: add SKILL.md","content":"'"$(base64 -w 0 "$BASE/运营/baoyu-url-to-markdown/SKILL.md")"'"}' \
  "https://api.github.com/repos/$REPO/contents/skills/operations/baoyu-url-to-markdown/SKILL.md"

# 上传到 product
curl -s -X PUT -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message":"chore: add SKILL.md","content":"'"$(base64 -w 0 "$BASE/产品/markdown-to-report/SKILL.md")"'"}' \
  "https://api.github.com/repos/$REPO/contents/skills/product/markdown-to-report/SKILL.md"
```

## 注意事项

1. **先读仓库结构**：每次同步前必须 GET `/repos/{owner}/{repo}/contents/skills` 确认分类存在
2. **使用英文分类名**：operations, product, assistant, creative, developer, ai
3. **不要新增分类**：如果仓库没有对应分类，将技能放入最接近的现有分类
4. **更新 README**：同步完成后必须保留现有 README 风格，只做最小增量 patch，禁止全量重建
5. **Token 权限**：确认 PAT 有 `repo` 写入权限

## README 更新模板（保留 viceroy-skills 当前风格）

当前 README 使用如下结构：

```md
<div align="center">

**中文** · [English](./README.en.md)

# 🧰 viceroy-skills

...
[![Skills](https://img.shields.io/badge/Skills-60-10B981?style=for-the-badge)](#-skills)
...
</div>

---

## 📋 目录
...

## 📦 安装
...

## ✨ Skills

### 🤖 AI Models
| Name | One-liner |
|------|-----------|
| [**9router**](skills/ai/9router/SKILL.md) | ... |

### 🧑‍💼 Assistant
| Name | How to trigger |
|------|----------------|
| [**obsidian**](skills/assistant/obsidian/SKILL.md) | ... |

### 🎨 Creative
...

### 🛠️ Developer
...

### 📊 Operations
...

### 📦 Product
| Name | How to trigger |
|------|----------------|
| [**hv-analysis**](skills/product/hv-analysis/SKILL.md) | 研究这个公司 / 产品 |
```

### README patch 规则

1. 先 GET 当前 `README.md`，保留原文。
2. 根据 skill 远程分类找到对应 heading：
   - `ai` → `### 🤖 AI Models`
   - `assistant` → `### 🧑‍💼 Assistant`
   - `creative` → `### 🎨 Creative`
   - `developer` → `### 🛠️ Developer`
   - `operations` → `### 📊 Operations` 或必要时 `### 📊 Operations — 其他`
   - `product` → `### 📦 Product`
3. 只在该 heading 下方的 Markdown table 中插入或更新一行：

```md
| [**skill-name**](skills/{category}/{skill-name}/SKILL.md) | 一句话触发说明 |
```

4. 插入位置：
   - 默认按 skill name 字母序插入；
   - 如果现有 section 明显不是字母序，则追加到该表格末尾；
   - 不要重排已有行。
5. 如顶部 badge 存在 `Skills-N-10B981`，将 `N` 更新为远程 `skills/*/*/SKILL.md` 的总数。
6. 仅 PUT 更新 README.md 这一处 patch 后的内容。
7. 如果找不到目标 section 或 table，停止并询问用户，不要自动生成新 README。

### Python patch 示例

```python
import re

CATEGORY_HEADING = {
    "ai": "### 🤖 AI Models",
    "assistant": "### 🧑‍💼 Assistant",
    "creative": "### 🎨 Creative",
    "developer": "### 🛠️ Developer",
    "operations": "### 📊 Operations",
    "product": "### 📦 Product",
}

def patch_readme(readme: str, category: str, skill_name: str, one_liner: str, total_count: int) -> str:
    # 1) 更新顶部 Skills badge 数量
    readme = re.sub(r"Skills-\d+-10B981", f"Skills-{total_count}-10B981", readme)

    # 2) 找到分类 section
    heading = CATEGORY_HEADING[category]
    start = readme.find(heading)
    if start == -1:
        raise ValueError(f"README section not found: {heading}")

    next_section = readme.find("\n### ", start + len(heading))
    if next_section == -1:
        next_section = len(readme)

    before = readme[:start]
    section = readme[start:next_section]
    after = readme[next_section:]

    row = f"| [**{skill_name}**](skills/{category}/{skill_name}/SKILL.md) | {one_liner} |"

    # 3) 已存在则更新该行，不存在则插入到表格末尾
    pattern = rf"\| \[\*\*{re.escape(skill_name)}\*\*\]\(skills/{re.escape(category)}/{re.escape(skill_name)}/SKILL\.md\) \| .*? \|"
    if re.search(pattern, section):
        section = re.sub(pattern, row, section)
    else:
        lines = section.splitlines()
        insert_at = None
        for i, line in enumerate(lines):
            if line.startswith("---"):
                break
            if line.startswith("| [**"):
                insert_at = i + 1
        if insert_at is None:
            raise ValueError(f"No skill table found in section: {heading}")
        lines.insert(insert_at, row)
        section = "\n".join(lines)

    return before + section + after
```

**铁律**：README 是项目门面，不是纯机器索引。除非用户明确要求重建，否则永远只 patch，不 regenerate。