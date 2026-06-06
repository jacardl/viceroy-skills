---
name: skill-maintenance
description: 维护技能库整洁，系统性整理、归类、查重、清理废弃技能（含项目源码误入 skills/ 目录的情况）。当用户说「整理技能库」「skills太乱了」「删除重复技能」「技能库查重」「技能分类」「整理skills」时触发。配套 skill-github-sync 使用效果最佳。
---

# Skill Maintenance

按 `viceroy-skills` 仓库的 6 分类标准维护本地技能库，识别重复/低频/废弃技能，保持 6 大分类整洁有序。配套 `skill-github-sync` 形成"本地整理 → 推到 GitHub"闭环。

## 6 个固定分类（viceroy-skills 标准，2026-06 同步）

| 英文分类 | 中文 | 用途 | 路径前缀 |
|---------|------|------|----------|
| `ai` | AI模型 | LLM/agent runtime | `~/.openclaw/skills/ai/` |
| `assistant` | 助理 | 通用工具/笔记/存储/陪伴 | `~/.openclaw/skills/assistant/` |
| `creative` | 创意 | 写作/排版/设计/视频 | `~/.openclaw/skills/creative/` |
| `developer` | 开发 | 工程化/调试/部署/skill 自身工具 | `~/.openclaw/skills/developer/` |
| `operations` | 运营 | 数据采集/SEO/GitHub 项目雷达 | `~/.openclaw/skills/operations/` |
| `product` | 产品 | 调研/分析/竞品/标签打分 | `~/.openclaw/skills/product/` |

**铁律**：
- 不新增分类（与 skill-github-sync 一致）
- 同名 skill 只能存在一份
- 「工作区 skills/」是**试装区**，不是常驻位 —— 试跑通后必须推系统级

## Skill 来源优先级（OpenClaw 加载顺序）

OpenClaw 加载 skill 时按以下顺序，**高优先级覆盖低优先级同名 skill**：

| # | 来源 | 路径 | 可见性 |
|---|------|------|--------|
| 1 | **Workspace skills** | `<workspace>/skills` | 仅该 agent |
| 2 | Project agent skills | `<workspace>/.agents/skills` | 仅该工作区 agent |
| 3 | Personal agent skills | `~/.agents/skills` | 全机器所有 agent |
| 4 | **Managed/local skills** | `~/.openclaw/skills` | 全机器所有 agent |
| 5 | Bundled skills | 安装自带 | 全机器所有 agent |
| 6 | Extra dirs | `skills.load.extraDirs` | 全机器所有 agent |

**维护原则**：
- **正式 skill 全部进系统级**（`~/.openclaw/skills/<cat>/`），让所有 agent 共享
- **工作区 skills/** 只用于**临时试装**（跑通再推系统级）
- 优先级越高的位置越"私有"，越低的越"共享" —— **共享价值高的放系统级**

## 维护流程

### 1. 每周/每两周检查清单

按顺序执行：

1. **盘点所有 skill**：
   ```bash
   # 系统级（含嵌套分类目录）
   find ~/.openclaw/skills -name "SKILL.md" -type f
   # 工作区（试装区）
   find ~/.openclaw/workspace/skills -name "SKILL.md" -type f 2>/dev/null
   # 内置
   find /usr/lib/node_modules/openclaw/skills -name "SKILL.md" -type f
   ```

2. **识别非 skill 项**（关键！实战中最常踩坑）：
   - **无 SKILL.md 的目录** —— 通常是**项目源码**误入（如 Rust 源码带 Cargo.toml/.cargo/crates）→ 移出 skills/，建议去 `~/.openclaw/workspace/projects/<name>/`
   - **只有 README.md 无 SKILL.md** —— 同上
   - **目录前缀误建**（如 `skills/developer/` 是 skill，但 5-27 误建时把 `skill-maintenance` 嵌进去形成空顶层）→ 整目录审计

3. **🔒 安全合规检查（强制，新增于 2026-06-06）**：
   任何 skill 修改/新增/同步前，必须跑「脱敏四查」扫描全部云端文件，确保**零明文凭证**：

   ```bash
   # 云端 skill 目录：明文凭证检查（必须全部返回空）
   grep -rln "07b4dc" ~/.openclaw/skills/        # WeChat AppSecret
   grep -rln "tvly-dev-" ~/.openclaw/skills/ ~/.openclaw/workspace/  # Tavily
   grep -rln "sk-uRDC" ~/.openclaw/skills/ ~/.openclaw/workspace/    # Sensenova
   grep -rln "9xcxxvZqSjJPEd5l" ~/.openclaw/skills/ ~/.openclaw/workspace/  # FlowUs
   ```

   **任一项返回非空 → 中止维护，先脱敏再继续**。

   **脱敏标准**：
   - 真实凭证一律存到 `~/.openclaw/secrets/` 下对应文件（权限 600，不进 Git）
     - WeChat：`~/.openclaw/secrets/zhili-credentials.md`
     - 通用 API Key：`~/.openclaw/secrets/api-keys.md`
   - 云端文件使用占位符 `***REDACTED***`，脚本必须实现回退逻辑
   - 脚本改用 `load_config()` / `load_<key>_key()` 函数从 secrets 加载
   - 详见每个 skill 自己的 `references/config.md` 注释

   **历史教训**（2026-06-06 zhili* skills 脱敏复盘）：
   - 同一套凭证可能散落在多个 skill（如 zhiligithub / zhili-publish / zhilicomments 共用「直隶按察使」公众号 AppSecret），**只脱敏一个会漏**
   - **反面教材**也算泄露：文档里写「AppSecret 别用旧的 `07b4dc****`」= 泄露真值
   - **死代码**也算泄露：Python 脚本里的 `if "sk-uRDC" in line` 模式匹配代码（**即使是搜索模式，不应放在公开代码里**）
   - **__pycache__/** 字节码里也可能有真值残留，commit 前 `rm -rf __pycache__`
   - 推送前必须「**脱敏四查 + 远程验证**」双重确认（`api.github.com/search/code?q=KEYWORD+repo:OWNER/REPO` count 必须为 0）
   - 任何含凭证的 commit 都是**永久泄露**（git 历史可追溯），必须 amend 或新 commit 覆盖

4. **识别重复 / 旧版**：
   - **同分类下目录名相同**（如 `~/.openclaw/skills/developer/skill-maintenance/` 和 `~/.openclaw/skills/skill-maintenance/`）→ 留新删旧，对比 mtime 或仓库引用
   - **描述相似度 >70%** 的两个 skill → 标记合并或删除
   - **指向旧仓库的 SKILL.md**（如 `jacardl/skillshub` → `jacardl/viceroy-skills`）→ 必删

5. **归类新 skill**：对照 6 分类表，关键词匹配：
   - 含「github」「trending」「seo」「data collection」→ `operations/`
   - 含「chat」「情感」「陪伴」「笔记」「flowus」「菜谱」→ `assistant/`
   - 含「标签」「kano」「调研」「竞品」→ `product/`
   - 含「writing」「publish」「article」「github 项目」→ `creative/`
   - 含「skill」「debug」「code」「github-pr」→ `developer/`
   - 含「llm」「model」「claude-api」「vllm」→ `ai/`

6. **检查空目录 stub**：
   ```bash
   find ~/.openclaw/skills -maxdepth 2 -name "DESCRIPTION.md" | while read f; do
     dir=$(dirname "$f")
     [ ! -f "$dir/SKILL.md" ] && echo "STUB: $dir"
   done
   ```

7. **验证关键引用**：例如 `zhiligithub` 引用 `zhili-publish/scripts/publish_zhili.py`，分类嵌套后路径变成 `skills/creative/zhili-publish/scripts/` —— 跑一次 `publish_zhili.py --help` 验证

### 2. 删除/清理标准

满足以下任一条件**建议清理**（删除前必须向用户确认）：

| 条件 | 处理方式 |
|------|----------|
| 与现有 skill 功能完全重复（描述重叠 >70%） | 删旧留新（或合并） |
| 长期未使用（边缘领域如音乐/游戏/家居控制） | 删 |
| 依赖的外部服务已失效 | 删 |
| 描述过时且无法修复 | 删 |
| 旧版（指向已废弃仓库） | 删 |
| 嵌套在错误位置的空顶层目录 | 删整目录 |
| 项目源码误入 skills/ | 移到 `~/.openclaw/workspace/projects/` 或 `~/.openclaw/workspace/<name>/` |

### 3. 分类调整规则

- 新 skill 归入现有 6 分类，**不新建分类**
- 公众号相关（zhili*）按功能分散：
  - `zhili-publish` → `creative/`（内容生产）
  - `zhiligithub` → `operations/`（GitHub 项目雷达，类比 github-daily-trending）
  - 未来若加 `zhilicomments` → `creative/`（短评）
- 工作流类（neat-freak、flowus-crud）→ `assistant/`
- skill 自身管理类（skill-creator、skill-maintenance、skill-github-sync）→ `developer/`
- 灰区归属判断用关键词匹配，匹配不上时**主动问用户**（不要硬塞）

### 4. 删除/移动流程（强制备份）

执行前**必须**：
1. 列出待处理项及理由
2. **等用户确认**
3. **先备份**到 `/tmp/skill-mv-backup/` 或 `~/.openclaw/workspace/.backup-pre-skill-cleanup/`
4. 执行 `mv`（不要用 `rm` —— `mv` 至少可逆；SOUL.md 红线："trash > rm"）
5. 验证：跑一遍相关 skill 的 `--help` 或最简单命令
6. 更新引用（SKILL.md 内的路径、MEMORY.md、脚本里的硬编码路径）

### 5. 验证步骤

维护完成后输出：
- 当前 skill 总数（系统级 + 工作区 + 内置分别统计）
- 各分类 skill 数量 + 与 viceroy-skills 仓库的对照（diff）
- 本次新增/删除/调整列表（含备份位置）
- 遗留待处理项

## 跟 skill-github-sync 配合

skill-maintenance 不止是本地整理，**最终目的是跟 viceroy-skills 仓库同步**：

```
本地整理（skill-maintenance）→ 跟 GitHub 对照 → 推差异（skill-github-sync）
         ↑                                                  |
         └──────────────── 验证一致性 ←─────────────────────┘
```

**联动步骤**：
1. `skill-maintenance` 整理完本地结构
2. `skill-github-sync` 拉取 GitHub 端最新 skill 列表
3. 对比：哪些本地有但 GitHub 没有（push）、哪些 GitHub 有但本地没有（pull 候选）
4. 用 `skill-github-sync` 推本地独有 + 有价值的 skill
5. 跟仓库分类标准对齐（参考本 skill 第 1 节的 6 分类表）

## GitHub API 推送权限要求（陷阱）

向 `jacardl/viceroy-skills` 推送 skill 文件使用 GitHub REST API（blobs/trees/commits/refs）。**必须使用有写入权限的 Token**：

- **Classic PAT**（推荐）：https://github.com/settings/tokens/new，勾选 `repo` scope
- **Fine-grained PAT**：需单独设置：
  - Repository access → 选择 `jacardl/viceroy-skills`
  - Repository permissions → Contents 设置为 **Read and write**（默认只有 Read）

**验证方法**（创建 blob 不报 403 即代表有写入权限）：
```bash
curl -s -X POST -H "Authorization: token <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"content":"test","encoding":"utf-8"}' \
  "https://api.github.com/repos/jacardl/viceroy-skills/git/blobs"
# 成功返回 {"sha":"..."}，403 = 无写入权限
```

Token 凭证保存路径：`~/.hermes/keys/github_token.txt`（兼容多环境：`~/.openclaw/openclaw.json` 也可）

### GitHub 推送路径规范

所有 skill 推送到 `jacardl/viceroy-skills` 时，路径格式：

```
skills/{category}/{skill-name}/SKILL.md
```

示例：
```
skills/operations/aihot/SKILL.md
skills/product/tag-scoring/SKILL.md
skills/developer/skill-github-sync/SKILL.md
skills/ai/9router/SKILL.md
```

推送完成后验证：
```bash
curl -s -H "Authorization: token $TOKEN" \
  "https://api.github.com/repos/jacardl/viceroy-skills/git/trees/main?recursive=1" | \
  python3 -c "import sys,json; [print(f['path']) for f in json.load(sys.stdin)['tree'] if f['path'].endswith('SKILL.md')]"
```

## 快速命令

```bash
# 统计 SKILL.md 文件数（系统级）
find ~/.openclaw/skills -name "SKILL.md" -type f | wc -l

# 列出所有 skill 名称（去重）
find ~/.openclaw/skills -name "SKILL.md" -type f | xargs -I{} dirname {} | xargs -I{} basename {} | sort -u

# 按分类统计
for cat in ai assistant creative developer operations product; do
  count=$(find ~/.openclaw/skills/$cat -name "SKILL.md" -type f 2>/dev/null | wc -l)
  echo "$cat: $count"
done

# 清理空目录 stub
find ~/.openclaw/skills -maxdepth 2 -name "DESCRIPTION.md" | while read f; do
  dir=$(dirname "$f")
  [ ! -f "$dir/SKILL.md" ] && echo "STUB: $dir"
done

# 跟 GitHub 仓库对照（需要 token）
python3 << 'EOF'
import urllib.request, json, os
token = open(os.path.expanduser("~/.hermes/keys/github_token.txt")).read().strip()
github = {}
for cat in ['ai','assistant','creative','developer','operations','product']:
    url = f"https://api.github.com/repos/jacardl/viceroy-skills/contents/skills/{cat}"
    req = urllib.request.Request(url, headers={'Accept':'application/vnd.github.v3+json', 'Authorization':f'token {token}'})
    r = json.loads(urllib.request.urlopen(req, timeout=15).read())
    github.update({item['name']: cat for item in r if item.get('type')=='dir'})

import os
local = set()
for root, _, files in os.walk(os.path.expanduser("~/.openclaw/skills")):
    for f in files:
        if f == "SKILL.md":
            local.add(os.path.basename(root))

print("本地独有（候选 push）:", sorted(local - set(github.keys())))
print("GitHub 独有（候选 pull）:", sorted(set(github.keys()) - local))
EOF
```

## 注意事项

- **删除/移动前先备份**，不破坏性操作（`mv` 比 `rm` 安全，trash > rm）
- API keys/tokens/credentials 一律 [REDACTED]，不在 SKILL.md 输出
- 维护后**主动汇报**给用户（带数量、列表、备份位置），不静默完成
- skill-maintenance 自身归入 **`developer/`**（skill 自身管理工具）
- 跨 agent 共享的 skill 必须放系统级，不要留在工作区
- 「项目源码 vs skill」判断标准：**有 SKILL.md 才算 skill**，只有 README + 源码 = 项目

## 历史优化记录

- **2026-06-06**：加入「🔒 安全合规检查」步骤，**强制**在所有维护动作前跑「脱敏四查」（07b4dc / tvly-dev- / sk-uRDC / 9xcxxvZqSjJPEd5l），沉淀 5 条 2026-06-06 zhili* skills 脱敏复盘教训（多 skill 共凭证 / 反面教材算泄露 / 死代码算泄露 / __pycache__ 字节码残留 / 远程二次验证）
- **2026-06-04**：从 7 分类改成 6 分类（去掉「研究」「运营」等冗余，对齐 viceroy-skills 实际仓库结构）
- **2026-06-04**：加入「OpenClaw 加载优先级」章节（解释系统级 vs 工作区差异）
- **2026-06-04**：加入「项目源码 vs skill」识别规则（应对 obscura 误入场景）
- **2026-06-04**：跟 skill-github-sync 联动标准化
- **2026-05-27**：初版，7 分类 + 删除流程
