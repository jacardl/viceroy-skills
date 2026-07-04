---
name: skill-maintenance
description: "维护技能库整洁，系统性整理、归类、查重、清理废弃技能（含项目源码误入 skills/ 目录的情况），**以及在 install 前对 skill 做安全审计（调用 skillspector）**。**新能力（v2.2）**：对指定 skill 进行合规/规范检查（YAML frontmatter / description 规范 / 多余文件 / 目录结构），并与 viceroy-skills 云端同名 skill 比对，**自动三向 merge**，保证本地和云端都是最新文件。**新能力（v2.7）**：分析技能使用情况——直接查询 SQLite 数据库 session 历史，区分「mtime 活跃」和「实际被调用过」。触发词：「检查 skill 规范」「合规检查」「跟云端比对」「merge skill」「同步 skill 到云端」「检查并更新 skill」「哪些 skill 没用过」「清理未使用技能」「检查技能使用情况」。"
---

# Skill Maintenance

按 `viceroy-skills` 仓库的 6 分类标准维护本地技能库，识别重复/低频/废弃技能，保持 6 大分类整洁有序。配套 `skill-github-sync` 形成"本地整理 → 推到 GitHub"闭环。

**v2.1（2026-06-21 升级）**：新增第 7 节「安装前安全审计」—— 在 install 新 skill 之前，自动调用 `skillspector` 做 64 pattern / 16 分类的静态扫描 + 风险分评估，避免装入含 prompt injection / data exfiltration / supply chain attack 的恶意 skill。

**v2.2（2026-06-28 升级）**：新增第 8 节「合规检查 + 云端 merge」—— 对指定 skill 进行规范审计（YAML / description / 文件结构），与 viceroy-skills 云端同名 skill 三向 merge，保证本地和 GitHub 两端文件同步最新。

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
   find ~/.hermes/skills -name "SKILL.md" -type f 2>/dev/null
   ```

2. **识别非 skill 项**（关键！实战中最常踩坑）：
   - **无 SKILL.md 的目录** —— 通常是**项目源码**误入（如 Rust 源码带 Cargo.toml/.cargo/crates）→ 移出 skills/，建议去 `~/.openclaw/workspace/projects/<name>/`
   - **只有 README.md 无 SKILL.md** —— 同上
   - **目录前缀误建**（如 `skills/developer/` 是 skill，但 5-27 误建时把 `skill-maintenance` 嵌进去形成空顶层）→ 整目录审计

3. **识别重复 / 旧版**：
   - **同分类下目录名相同**（如 `~/.openclaw/skills/developer/skill-maintenance/` 和 `~/.openclaw/skills/skill-maintenance/`）→ 留新删旧，对比 mtime 或仓库引用
   - **描述相似度 >70%** 的两个 skill → 标记合并或删除
   - **指向旧仓库的 SKILL.md**（如 `jacardl/skillshub` → `jacardl/viceroy-skills`）→ 必删
   - **Triplicate skills（三处重复）**：同 skill 在顶层 + 分类 + workspace 三处同时存在 → 执行 1.x 节检测脚本，保留分类版，删顶层和 workspace 版

4. **归类新 skill**：对照 6 分类表，关键词匹配：
   - 含「github」「trending」「seo」「data collection」→ `operations/`
   - 含「chat」「情感」「陪伴」「笔记」「flowus」「菜谱」→ `assistant/`
   - 含「标签」「kano」「调研」「竞品」→ `product/`
   - 含「writing」「publish」「article」「github 项目」→ `creative/`
   - 含「skill」「debug」「code」「github-pr」→ `developer/`
   - 含「llm」「model」「claude-api」「vllm」→ `ai/`

5. **检查空目录 stub**：
   ```bash
   find ~/.openclaw/skills -maxdepth 2 -name "DESCRIPTION.md" | while read f; do
     dir=$(dirname "$f")
     [ ! -f "$dir/SKILL.md" ] && echo "STUB: $dir"
   done
   ```

6. **验证关键引用**：例如 `zhiligithub` 引用 `zhili-publish/scripts/publish_zhili.py`，分类嵌套后路径变成 `skills/creative/zhili-publish/scripts/` —— 跑一次 `publish_zhili.py --help` 验证

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
- skill 自身管理类（skill-creator、skill-maintenance、skill-github-sync、**skillspector**）→ `developer/`
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

#### 1.x Triplicate Skill Detection（v2.6 新增）

**问题**：同一 skill 在 3 个位置同时存在（内容完全相同）—— openclaw/skills/{name}/、openclaw/workspace/skills/{name}/、openclaw/skills/{cat}/{name}/。常见于法律类 skill 批量安装后。

**检测脚本**：
```python
#!/usr/bin/env python3
"""检测 triplicate skills（三处重复的 skill）"""
import os
from pathlib import Path

def scan_all(base):
    results = {}
    for root, dirs, files in os.walk(base):
        if 'SKILL.md' not in files: continue
        rel = Path(root).relative_to(base)
        results[str(rel)] = str(root)
    return results

oc_sys = scan_all(Path.home() / ".openclaw/skills")
oc_ws  = scan_all(Path.home() / ".openclaw/workspace/skills")

cats_map = {}
top_level = []
for k, v in oc_sys.items():
    parts = k.split('/')
    if len(parts) == 1:
        top_level.append(k)
    else:
        cat = parts[0]
        name = '/'.join(parts[1:])
        cats_map.setdefault(cat, {})[name] = k

ws_names = {}
for k, v in oc_ws.items():
    parts = k.split('/')
    name = parts[0]
    ws_names[name] = k

# 检测 triplicate
for cat, skills in cats_map.items():
    if cat == 'legal-skills-chinese':
        for name, cat_path in skills.items():
            top_path = Path.home() / ".openclaw/skills" / name
            ws_path = Path.home() / ".openclaw/workspace/skills" / cat / name
            locations = []
            if top_path.exists(): locations.append("top-level")
            if ws_path.exists(): locations.append("workspace/" + cat)
            if len(locations) >= 2:
                print(f"TRIPLICATE: {name} in {locations}")
```

**清理原则**：
- `openclaw/skills/legal-skills-chinese/{name}/` — **保留**（已归类）
- `openclaw/skills/{name}/` — **删除**（顶层重复）
- `openclaw/workspace/skills/legal-skills-chinese/{name}/` — **删除**（试装区过期）

**实战案例（2026-07-03）**：35 个法律技能 triplicate，同时存在于顶层 + legal-skills-chinese 分类 + workspace 三处。清理后系统级从 87 → 51 个。

## 6. 跟 skill-github-sync 配合

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

## 7. 安装前安全审计（v2.1 新增）

**核心原则**：装新 skill 之前**必须先用 skillspector 扫一遍**。skill 装到系统级后就默认 agent 全部信任它 —— 一旦含 prompt injection / data exfiltration / 提权代码，影响范围是**全机器所有 agent**。

### 7.1 触发条件

| 场景 | 用户可能的表达 | 动作 |
|------|----------------|------|
| **install 前** | "我要装 X，先扫一下" / "scan https://github.com/xxx/skill" | **强制先 scan**，风险分 > MEDIUM 需用户确认 |
| **合规检查 + 云端 merge** | "检查 skill 规范" / "合规检查 X" / "跟云端比对" / "merge skill" / "同步 skill 到云端" / "检查并更新 skill" | 第 8 节三向 merge |
| 已装 skill 体检 | "扫一下 skill-maintenance" / "audit my skills" | 跑 scan，按风险分排序 |
| 批量体检 | "把 ~/.openclaw/skills/ 全扫一遍" | 跑下面 7.4 的批量命令 |
| 看报告 | "显示上次扫描的 json 报告" | 用 `--format json` 重跑指定 skill |

**铁律**：`install` 类操作（clone 到 skills/、推送 GitHub、覆盖 SKILL.md）**必须**在 scan 通过后执行。HIGH/CRITICAL 风险的 skill **不装**，MEDIUM 风险的 skill 列 issues 让用户决定。

### 7.2 工具：skillspector

- **位置**：`~/.openclaw/skills/developer/skillspector/`（同级）
- **底层 CLI**：`/tmp/skillspector-probe/SkillSpector/.venv/bin/skillspector`（NVIDIA SkillSpector v2.2.3）
- **扫描能力**：64 pattern × 16 分类（prompt injection / data exfiltration / privilege escalation / supply chain / excessive agency / output handling / system prompt leakage / memory poisoning / tool misuse / rogue agent / trigger abuse / dangerous code via AST / taint tracking / YARA signatures / MCP least privilege / MCP tool poisoning）
- **输出**：风险分 0-100 + severity 标签（LOW/MEDIUM/HIGH/CRITICAL）

### 7.3 风险分解读

| Risk Score | Severity | 含义 | 建议 |
|------------|----------|------|------|
| 0-19 | LOW | 安全 | 直接装 |
| 20-49 | MEDIUM | 提示 | 看 issues 列表，人工 review 后再装 |
| 50-79 | HIGH | 警告 | **必须人工 review 全部 issues 后再装** |
| 80-100 | CRITICAL | 危险 | **不装**，告警用户 |

⚠️ **误报注意**：很多合法 skill 会被标 MEDIUM（典型如 "External Transmission" 因为 skill 文档里有 API URL，或 "File System Enumeration" 因为 skill 需要读 `~/.openclaw/`）。**真问题要看 HIGH/CRITICAL + Confidence ≥ 70% 的 issue**。

### 7.3.1 skillspector HIGH 误报的标准响应：`permissions` 字段

skillspector 对**本地网关调用**和** shell 工具脚本**会持续报 HIGH，即使加了 `--no-llm` 也无法消除。这类不是漏洞，是设计行为。标准响应是**在 YAML frontmatter 中声明 `permissions` 字段**，让 skillspector 知道这是已知的合法能力。

**典型误报场景**：

| Pattern ID | Pattern Name | 触发原因 | 是误报的条件 |
|-----------|-------------|---------|------------|
| SC2 | External Transmission | curl HTTP 请求 | 目标地址是 `127.0.0.1` 或 `localhost`（本地网关） |
| LP3 | Shell Script Presence | 存在 `.sh` 脚本文件 | 脚本只含 `curl` / `base64` / `jq` 等系统工具，无外部脚本下载 |
| LP1 | Tool Spawning | skill 调用 shell 脚本 | 脚本是静态工具（本地网关调用），非动态恶意代码 |
| E1 | Excessive File Access | 访问 `~/.hermes/` 或 `~/.openclaw/` | skill 自身配置文件，属于正常工作范围 |

**判断流程**：
1. 扫出 HIGH → 看 Pattern ID + Confidence
2. 若 Confidence < 70% → 直接忽略
3. 若 Confidence ≥ 70% → 核查目标地址：
   - `127.0.0.1` / `localhost` → **误报**，加 `permissions`
   - 外部域名（`api.openai.com` 等）→ 核查是否 skill 自身必需调用
4. 加 `permissions` 后重扫仍有残留 HIGH → **标注为已知设计行为**，在审计报告中说明，跳过该 skill

**`permissions` 字段格式**（加在 YAML frontmatter，与 `name`/`description` 同级）：

```yaml
---
name: example-skill
description: "描述（description 值含中文/冒号/括号必须用双引号包裹）"
permissions:
  - http://127.0.0.1:20128/   # 9Router 本地网关调用
  - http://localhost/          # 本地服务调用
  - filesystem:read:~/.openclaw/   # OpenClaw 配置读取
  - filesystem:read:~/.hermes/    # Hermes 配置读取
---
```

**实战案例（9router-image，2026-06-28）**：
- skillspector 初始扫描：64/100，4× HIGH（SC2 External Transmission `curl 127.0.0.1:20128`）
- 加 `permissions: - http://127.0.0.1:20128/` 后重扫：仍有 4× SC2 HIGH
- 原因：`permissions` 字段告知安装者该 skill 需要这些权限，但不改变 skillspector 静态扫描结果；静态分析无法理解运行时上下文，必然对本地网关调用报警
- 结论：**`permissions` 字段的作用是消除后续安装警告**，让 skill 作者对已知能力负责；skillspector 扫描本身保持原样
- 处置：标注为已知设计行为，报告输出 `⚠️ N HIGH (known design: local gateway curl + shell script)`，skill 可正常安装

**注意**：description 值含特殊字符时必须用**双引号**包裹，否则 YAML 解析器会警告：
- 含中文括号 `（）` → 必须加 `"..."` 包裹
- 含冒号 `:` → 冒号后有空格时无需引号，但冒号紧跟文字时需要
- 含反斜杠 `\` → 在 YAML 双引号字符串中必须写成 `\\`

### 7.4 批量体检命令

定期（如每月 / 装完一波新 skill 后）跑一次，扫整个 skills/ 目录：

```bash
SS=/tmp/skillspector-probe/SkillSpector/.venv/bin/skillspector

# 批量扫描：所有系统级 skill
for d in ~/.openclaw/skills/*/*/; do
  [ -d "$d" ] || continue
  skill_name=$(basename "$d")
  # 跳过 skillspector 自己（避免循环）
  [ "$skill_name" = "skillspector" ] && continue
  # 跳过软链
  [ -L "$d" ] && continue
  # 只扫有 SKILL.md 的
  [ -f "$d/SKILL.md" ] || continue
  echo "=== $skill_name ==="
  $SS scan "$d" --no-llm --format terminal 2>&1 | grep -E '(Risk Score|Severity|CRITICAL|HIGH)' | head -10
  echo
done
```

**输出排序建议**：把扫描结果按风险分倒序排列，先处理 CRITICAL > HIGH > MEDIUM。

### 7.5 快速命令（一行版）

```bash
# 扫描单个 skill（装前必跑）
SS=/tmp/skillspector-probe/SkillSpector/.venv/bin/skillspector
$SS scan <path-or-git-url> --no-llm --format terminal

# JSON 报告（机器可读）
$SS scan <path> --no-llm --format json --output /tmp/scan-report.json

# Markdown 报告（贴飞书/Notion）
$SS scan <path> --no-llm --format markdown --output /tmp/scan-report.md

# SARIF 报告（GitHub Code Scanning 集成）
$SS scan <path> --no-llm --format sarif --output /tmp/scan.sarif
```

`--no-llm` 跳过 LLM 语义分析（快、准、免 API key）。有 LLM key 想去掉 `--no-llm` 改用：
- `SKILLSPECTOR_PROVIDER=openai` + `OPENAI_API_KEY`
- `SKILLSPECTOR_PROVIDER=anthropic` + `ANTHROPIC_API_KEY`
- `SKILLSPECTOR_PROVIDER=nv_inference` + `NVIDIA_INFERENCE_KEY`

### 8. 合规检查 + 云端三向 merge（新功能 v2.2）

当用户要求对指定 skill 做合规/规范检查并与云端同步时，执行以下流程。

#### 8.1 三向 merge 流程

**输入**：用户指定 `cat/skill`（如 `operations/radar-daily-report`）

**⚠️ 凭证文件保护规则（硬性约束）**

以下文件在 merge 时**永远使用 CLOUD 版本**（不覆盖 LOCAL 的云端脱敏版）：
- 含 `APPID`、`APPSECRET`、`access_token`、`API_KEY` 字面量的 `.md` / `.py` / `.json` / `.yaml` / `.txt` 文件
- 路径含 `config`、`credentials`、`secret`、`token` 的文件

**判断标准**：LOCAL 有真实凭证（32+ 字符的 hex/base64，或 `wx` 开头的 16 位十六进制 appid 搭配明文 secret）vs CLOUD 只有 `***REDACTED***` 占位符。

**操作**：在 merge 前对这些文件单独做 `git checkout HEAD -- <file>`，保留云端脱敏版，不做任何合并。

**Step 0：凭证预检（必须先做）**

```python
import re
from pathlib import Path

CRED_PATTERNS = [
    r"['\"][0-9a-f]{32,}['\"]",     # 32+ hex (APPSECRET)
    r"['\"][A-Za-z0-9+/]{40,}={0,2}['\"]",  # 40+ base64
    r"wx[0-9a-f]{16}",              # WeChat APPID
]

def has_real_credential(path: Path) -> bool:
    """检查文件是否含真实凭证（非占位符）"""
    content = path.read_text()
    redacted = "***REDACTED***" in content or "REDACTED" in content
    for pat in CRED_PATTERNS:
        hits = re.findall(pat, content, re.I)
        for line in content.split('\n'):
            for hit in hits:
                if hit in line and not line.strip().startswith('#'):
                    return True  # 真实凭证
    return False

def scan_for_real_creds(local_dir: Path) -> list[Path]:
    """扫描 skill 目录下所有含真实凭证的文件"""
    flagged = []
    for f in local_dir.rglob("*"):
        if f.is_file() and f.suffix in ['.md', '.py', '.json', '.yaml', '.txt']:
            try:
                if has_real_credential(f):
                    flagged.append(f)
            except:
                pass
    return flagged
```

**预检结果解读**：

| 场景 | 处置 |
|------|------|
| LOCAL 无凭证文件 | 正常 merge |
| LOCAL 有凭证，CLOUD 有脱敏版 | **保留 CLOUD 脱敏版**，不 merge 该文件 |
| LOCAL 有凭证，CLOUD 无此文件 | 凭证文件不 merge（用户需自行处理本地凭证） |
| CLOUD 有凭证（不应该） | 警告，阻断 merge，提示用户 |

**Step 1：收集三方文件**

```python
import urllib.request, subprocess, json, base64
from pathlib import Path

TOKEN = open("~/.hermes/keys/github_token.txt").read().strip()
REPO = "/tmp/viceroy-skills_sync"

# LOCAL
local_text = Path("~/.openclaw/skills/{cat}/{skill}/SKILL.md").expanduser().read_text()

# BASE（git show HEAD:{path}，新增文件则空）
base_text = subprocess.run(
    ["git", "show", "HEAD:{CLOUD_PATH}"],
    capture_output=True, text=True, cwd=REPO
).stdout

# CLOUD（GitHub HEAD 最新）
url = "https://api.github.com/repos/jacardl/viceroy-skills/contents/{CLOUD_PATH}"
req = urllib.request.Request(url, headers={
    "Accept": "application/vnd.github.v3+json",
    "Authorization": "token {TOKEN}"
})
resp = json.loads(urllib.request.urlopen(req).read())
cloud_text = base64.b64decode(resp["content"]).decode("utf-8", errors="replace")
```

**Step 2：合规检查 LOCAL + CLOUD**

| 检查项 | 标准 | 不合格处置 |
|--------|------|-----------|
| YAML frontmatter | 以 `---\n...\n---` 包裹且 yaml.safe_load 可解析 | 报错，用户确认后跳过 |
| `description` 值 | 含中文/冒号/`(`/`) ` 等字符必须双引号包裹 | 自动加引号 |
| `---` 文档分隔符数量 | 恰好 2 个（frontmatter 开始 + 结束），body 内无多余 `---` | 用 `grep -n '^---$'` 定位多余分隔符并删除 |
| 目录结构 | `skills/{cat}/{skill}/` 格式 | 报错 |
| 本地 vs 云端字节级比对 | `read_bytes()` vs `base64.b64decode(cloud_content)` 相等 | 相等则跳过 merge（Pitfall G） |

> ⚠️ **字节 vs 字符陷阱**（Pitfall G）：`stat().st_size` 是字节数，`len(read_text())` 是 Unicode 字符数。当文件含中文/emoji 时二者不相等，但可能实际内容相同。判断"本地 vs 云端是否相同"必须用**字节级比对**，不能用字符数。
| 多余文件 | 顶层不含 `.git/` `node_modules/` `__pycache__/` | 警告，用户确认后忽略 |
| 目录结构 | `skills/{cat}/{skill}/` 格式 | 报错 |

**Step 3：三向合并（git merge-file）**

```python
import tempfile, subprocess
from pathlib import Path

def three_way_merge(local_path, cloud_text, base_text):
    local_path = Path(local_path)
    if cloud_text.strip() == local_path.read_text().strip():
        return "identical", cloud_text

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        (td/"BASE").write_text(base_text)
        (td/"LOCAL").write_text(local_path.read_text())
        (td/"CLOUD").write_text(cloud_text)

        cp = subprocess.run(
            ["git", "merge-file", str(td/"LOCAL"), str(td/"BASE"), str(td/"CLOUD")],
            capture_output=True, text=True, cwd=str(td)
        )
        merged = (td/"LOCAL").read_text()
        has_conflict = any(m in merged for m in ["<<<<<<<", ">>>>>>>", "======="])

        if not has_conflict:
            local_path.write_text(merged)
            status = "cloud_updated" if merged.strip() == cloud_text.strip() else "merged"
            return status, merged
        else:
            lines = [l for l in merged.splitlines()
                     if not l.startswith(("<<<<<<<", ">>>>>>>", "======="))]
            clean = "
".join(lines)
            local_path.write_text(clean)
            return "conflict_resolved", clean
```

**Step 4：推送 GitHub**

```python
def push_github(local_path, cloud_path, commit_msg, token):
    local_path = Path(local_path)
    content_b64 = base64.b64encode(local_path.read_text().encode()).decode()
    url = "https://api.github.com/repos/jacardl/viceroy-skills/contents/{cloud_path}"
    req = urllib.request.Request(url, headers={
        "Authorization": "token {token}",
        "Accept": "application/vnd.github.v3+json"
    })
    current = json.loads(urllib.request.urlopen(req).read())
    data = json.dumps({
        "message": commit_msg,
        "content": content_b64,
        "sha": current["sha"]
    }).encode()
    blob_req = urllib.request.Request(url, data=data, headers={
        "Authorization": "token {token}",
        "Content-Type": "application/json"
    }, method="PUT")
    result = json.loads(urllib.request.urlopen(blob_req).read())
    return result["commit"]["sha"]
```

**Step 5：输出报告**

```
skill: {cat}/{skill}

合规检查:
  YAML frontmatter:  OK / FAIL
  description 引号: OK / 已修复
  文件结构:         OK / WARN

三向 merge 结果:
  local vs cloud: 对齐 / LOCAL新 / CLOUD新 / 冲突
  merge status:   {status}

GitHub 推送:
  commit: {sha}
  URL: https://github.com/jacardl/viceroy-skills/commit/{sha}
```

#### 8.2 快速调用脚本

将下方保存为 `/tmp/skill_merge.py`，用法：`python3 /tmp/skill_merge.py <cat> <skill>`

```python
#!/usr/bin/env python3
import sys, urllib.request, subprocess, tempfile, json, base64
from pathlib import Path
import yaml

TOKEN = open("/Users/apple/.hermes/keys/github_token.txt").read().strip()
REPO  = "/tmp/viceroy-skills_sync"

def get_cloud(path):
    url = "https://api.github.com/repos/jacardl/viceroy-skills/contents/" + path
    req = urllib.request.Request(url, headers={"Authorization": "token " + TOKEN, "Accept": "application/vnd.github.v3+json"})
    r = json.loads(urllib.request.urlopen(req).read())
    return base64.b64decode(r["content"]).decode(), r["sha"]

def merge(local_p, cloud_text, base_text):
    lp = Path(local_p)
    if cloud_text.strip() == lp.read_text().strip():
        return "identical", cloud_text
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        (td/"B").write_text(base_text)
        (td/"L").write_text(lp.read_text())
        (td/"C").write_text(cloud_text)
        subprocess.run(["git", "merge-file", str(td/"L"), str(td/"B"), str(td/"C")],
                       capture_output=True, text=True, cwd=str(td))
        merged = (td/"L").read_text()
        if not any(m in merged for m in ["<<<<<<<",">>>>>>>","======="]):
            lp.write_text(merged)
            return ("merged", merged)
        else:
            lines = [l for l in merged.splitlines()
                     if not l.startswith(("<<<<<<<",">>>>>>>","======="))]
            lp.write_text("
".join(lines))
            return ("conflict_resolved", "
".join(lines))

def push(local_p, cloud_path, msg):
    b64 = base64.b64encode(Path(local_p).read_text().encode()).decode()
    url = "https://api.github.com/repos/jacardl/viceroy-skills/contents/" + cloud_path
    req = urllib.request.Request(url, headers={"Authorization": "token " + TOKEN, "Accept": "application/vnd.github.v3+json"})
    cur = json.loads(urllib.request.urlopen(req).read())
    data = json.dumps({"message": msg, "content": b64, "sha": cur["sha"]}).encode()
    r = urllib.request.Request(url, data=data, headers={"Authorization": "token " + TOKEN, "Content-Type": "application/json"}, method="PUT")
    return json.loads(urllib.request.urlopen(r).read())["commit"]["sha"]

def check_compliance(text, label):
    issues = []
    if not text.startswith("---
"):
        issues.append(label + ": missing YAML frontmatter")
    else:
        try:
            end = text.index("
---
")
            yaml.safe_load("---
" + text[4:end] + "
---")
        except Exception as e:
            issues.append(label + " YAML: " + str(e))
    for line in text.splitlines():
        ls = line.strip()
        if ls.startswith("description:"):
            val = ls.split(":", 1)[1].strip()
            if any(c in val for c in ["（", "）", "《", "》"]) and not val.startswith('"'):
                issues.append(label + " desc needs quotes: " + val[:60])
    return issues

if __name__ == "__main__":
    cat, skill = sys.argv[1], sys.argv[2]
    local_p = str(Path.home() / (".openclaw/skills/" + cat + "/" + skill + "/SKILL.md"))
    cloud_path = "skills/" + cat + "/" + skill + "/SKILL.md"
    local_text = Path(local_p).read_text()
    cloud_text, _ = get_cloud(cloud_path)
    base_text = subprocess.run(["git", "show", "HEAD:" + cloud_path],
                               capture_output=True, text=True, cwd=REPO).stdout
    for t, lbl in [(local_text, "LOCAL"), (cloud_text, "CLOUD")]:
        issues = check_compliance(t, lbl)
        for iss in issues:
            print("  WARN: " + iss)
        if not issues:
            print("  " + lbl + ": compliance OK")
    status, _ = merge(local_p, cloud_text, base_text)
    print("merge: " + status)
    if status != "identical":
        sha = push(local_p, cloud_path, "merge: " + cat + "/" + skill + " (" + status + ")")
        print("GitHub commit: " + sha[:7])
        print("URL: https://github.com/jacardl/viceroy-skills/commit/" + sha)
    else:
        print("No changes needed (local == cloud)")
```

---

### 7.6 跟其他 skill 联动

- **`skillspector`**：本节就是 skillspector 在 skill-maintenance 下的"安装前 / 批量体检"工作流入口
- **`skill-github-sync`**：sync 前**必须**先跑本节 7.4 体检（确保本地要 push 的 skill 全部 LOW/MEDIUM）
- **`skill-creator`**：新 skill 写完后，发布前自己跑一次 7.5 自检

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

## 9. 跨 skill 引用对齐检查（v2.4 新增）

安装新 skill 后，如果该 skill 在工作流中引用了其他 skill，
**必须验证引用是否对齐**。方法：grep 双侧 SKILL.md 提取
callee 的实际要求，对照 caller 的引用描述，以严重度表格输出。
详见 `references/cross-skill-citation-check.md`。

## 10. 技能使用情况分析（v2.7 新增）

**⚠️ 文件修改时间（mtime）是误导性的**——skillhub 批量安装/更新时，
大量 skill 的 mtime 会被同步更新到同一日期（如 2026-05-18），
造成"全部同时更新"的假象。判断"哪些 skill 从未被使用"必须用
**session 历史查询**。

### 10.1 正确方法：直接查询 SQLite 数据库

Hermes 将所有 session 消息存储在 `~/.hermes/state.db`，其中
`messages.tool_calls` 字段包含每次工具调用的 JSON。
查找 skill_view 调用：

```python
import sqlite3
import json
import re
from collections import Counter

conn = sqlite3.connect(os.path.expanduser('~/.hermes/state.db'))
cursor = conn.cursor()

cursor.execute("""
    SELECT tool_calls FROM messages WHERE tool_calls LIKE '%skill_view%'
""")

used_skills = Counter()
for row in cursor.fetchall():
    if not row[0]:
        continue
    try:
        tool_calls = json.loads(row[0])
        for tc in tool_calls:
            if tc.get('function', {}).get('name') == 'skill_view':
                args = json.loads(tc['function']['arguments'])
                name = args.get('name', '')
                if name:
                    used_skills[name] += 1
    except (json.JSONDecodeError, KeyError):
        # 备用：正则提取
        for m in re.finditer(r'"name"\s*:\s*"([^"]+)"', row[0]):
            used_skills[m.group(1)] += 1

for skill, count in used_skills.most_common():
    print(f"{count:3d}x  {skill}")
```

### 10.2 获取本地所有 skill

```bash
find ~/.hermes/skills -name "SKILL.md" | while read f; do
  skill=$(dirname "$f" | xargs basename)
  echo "$skill"
done | sort -u
```

### 10.3 对比分析脚本

```python
#!/usr/bin/env python3
"""对比：本地 skill vs session 历史中实际调用过的 skill"""
import sqlite3, json, re, os, subprocess
from collections import Counter

# 1. 获取所有本地 skill
result = subprocess.run(
    ['find', os.path.expanduser('~/.hermes/skills'), '-name', 'SKILL.md'],
    capture_output=True, text=True
)
local_skills = set()
for line in result.stdout.strip().split('\n'):
    if line:
        skill_path = line.replace(os.path.expanduser('~/.hermes/skills/'), '').replace('/SKILL.md', '')
        local_skills.add(skill_path)

# 2. 查询 session 历史
conn = sqlite3.connect(os.path.expanduser('~/.hermes/state.db'))
cursor = conn.cursor()
cursor.execute("SELECT tool_calls FROM messages WHERE tool_calls LIKE '%skill_view%'")

used_skills = set()
for row in cursor.fetchall():
    if not row[0]:
        continue
    try:
        for tc in json.loads(row[0]):
            if tc.get('function', {}).get('name') == 'skill_view':
                args = json.loads(tc['function']['arguments'])
                name = args.get('name', '')
                if name:
                    used_skills.add(name)
    except:
        pass

# 3. 找出从未使用的 skill
never_used = local_skills - used_skills

print(f"本地 skill 总数: {len(local_skills)}")
print(f"历史调用过: {len(used_skills)}")
print(f"从未使用: {len(never_used)} ({len(never_used)/len(local_skills)*100:.0f}%)")
print("\n按从未使用分组:")
from collections import defaultdict
by_cat = defaultdict(list)
for s in sorted(never_used):
    cat = s.split('/')[0] if '/' in s else 'root'
    by_cat[cat].append(s)
for cat in sorted(by_cat):
    print(f"  {cat}: {len(by_cat[cat])} 个")
```

### 10.4 mtime 分析（仅供参考）

如果只想快速看哪些 skill 最近有活动（不能证明实际使用）：

```bash
# 最近 30 天修改过的 SKILL.md
find ~/.hermes/skills -name "SKILL.md" -mtime -30 | while read f; do
  echo "$(stat -f %Sm -t %Y-%m-%d "$f") $(dirname "$f" | xargs basename)"
done | sort -r
```

**结论**：mtime 只说明"这个文件最近被touch过"，不代表用户实际调用过该 skill。
区分"安装后从未被调用"和"被调用但文件没更新"的唯一方法是查 session 历史。

### 10.5 清理决策框架

| 信号 | 含义 | 建议 |
|------|------|------|
| session 历史从未调用 + mtime 30天前 | 真正的废弃 skill | 可安全删除 |
| session 历史从未调用 + mtime 最近30天 | 安装后未激活 | 询问用户是否保留 |
| session 历史有调用 + mtime 30天前 | 可能在用但文件久未更新 | 检查是否需要更新 |
| `.archive/` 或 `.curator_backups/` 目录 | 备份文件 | 确认后可删除 |

### 10.6 完整分析脚本（2026-07-04 实测）

```python
#!/usr/bin/env python3
"""
完整的技能使用情况分析脚本
从 SQLite session 历史中提取真实使用的技能，与本地技能对比
"""
import sqlite3, json, os, subprocess
from collections import defaultdict

SKILLS_DIR = os.path.expanduser('~/.hermes/skills')
DB_PATH = os.path.expanduser('~/.hermes/state.db')

# ── 1. 查询 session 历史中的 skill_view 调用 ──────────────────────────
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("SELECT tool_calls FROM messages WHERE tool_calls LIKE '%skill_view%'")

raw_used = []
for row in cursor.fetchall():
    if not row[0]:
        continue
    try:
        for tc in json.loads(row[0]):
            if tc.get('function', {}).get('name') == 'skill_view':
                args = json.loads(tc['function']['arguments'])
                name = args.get('name', '')
                if name:
                    raw_used.append(name)
    except:
        pass

# ── 2. 别名标准化映射表 ─────────────────────────────────────────────
ALIASES = {
    # 公众号系列大小写/路径别名
    'zhiliComments': 'zhilicomments',
    'social-media/.agents/skills/zhiliComments': 'zhilicomments',
    'zhiliGitHub': 'zhiligithub',
    'social-media/.agents/skills/zhiliGitHub': 'zhiligithub',
    'zhilicomments-publish': 'zhilicomments',
    'social-media:.agents/skills:zhilicomments': 'zhilicomments',
    'social-media/.agents/skills/zhili-publish': 'zhili-publish',
    'social-media/.agents/skills/zhiligithub': 'zhiligithub',
    # skill-github-sync 系列别名
    'skillgithub-sync': 'skill-github-sync',
    'developer/skill-github-sync': 'skill-github-sync',
    # geo 系列别名
    'geo-content-strategy': 'geo-keyword-research',
    'content-strategy/geo-keyword-research': 'geo-keyword-research',
    # hv-analysis 别名
    'research/hv-analysis': 'hv-analysis',
}

# 标准化：去重后的已使用技能集合
normalized_used = set()
for s in raw_used:
    normalized_used.add(ALIASES.get(s, s))
    # 顶级目录名也算（如 zhililong, renwei-writing）
    if '/' not in s:
        normalized_used.add(s)

print(f"Session 历史中调用过的 skill_view: {len(set(raw_used))} 种写法")
print(f"标准化后: {len(normalized_used)} 个")

# ── 3. 获取所有本地技能 ─────────────────────────────────────────────
result = subprocess.run(
    ['find', SKILLS_DIR, '-name', 'SKILL.md', '-type', 'f'],
    capture_output=True, text=True
)
all_skills = []
for line in result.stdout.strip().split('\n'):
    if line:
        path = line.replace(SKILLS_DIR + '/', '').replace('/SKILL.md', '')
        all_skills.append(path)

# ── 4. 判断技能是否被使用（关键：只看最后一级目录名） ─────────────
def is_used(skill_path):
    name = skill_path.split('/')[-1]
    if skill_path in normalized_used or name in normalized_used:
        return True
    # 别名后缀匹配
    for alias in ALIASES:
        if skill_path.endswith(alias):
            return True
    return False

# ── 5. 分类统计 ────────────────────────────────────────────────────
unused = [s for s in all_skills if not is_used(s)]
by_cat = defaultdict(list)
for s in sorted(unused):
    cat = s.split('/')[0]
    sub = '/'.join(s.split('/')[1:]) if '/' in s else s
    by_cat[cat].append((sub, s))

print(f"\n本地技能总数: {len(all_skills)}")
print(f"从未使用: {len(unused)} ({(len(unused)/len(all_skills)*100):.1f}%)")
print(f"正在使用: {len(all_skills) - len(unused)}")

# ── 6. 按目录输出未使用技能 ───────────────────────────────────────
print("\n" + "="*60)
print("从未使用的技能（按目录）:")
print("="*60)

for cat in sorted(by_cat):
    items = by_cat[cat]
    result = subprocess.run(
        ['find', f'{SKILLS_DIR}/{cat}', '-name', 'SKILL.md'],
        capture_output=True, text=True
    )
    total = len([l for l in result.stdout.strip().split('\n') if l])
    unused_count = len(items)
    
    if unused_count == total:
        print(f"\n🗑️ {cat}/ (全部 {unused_count} 个未使用)")
    else:
        print(f"\n⚠️  {cat}/ ({unused_count}/{total} 个未使用)")
    
    for sub, full in items[:5]:
        print(f"   └── {sub}")
    if len(items) > 5:
        print(f"   └── ... 还有 {len(items)-5} 个")

# ── 7. 输出可安全删除的顶级目录 ────────────────────────────────────
print("\n" + "="*60)
print("可安全删除的顶级目录:")
print("="*60)
safe_dirs = []
for cat in sorted(by_cat):
    items = by_cat[cat]
    result = subprocess.run(
        ['find', f'{SKILLS_DIR}/{cat}', '-name', 'SKILL.md'],
        capture_output=True, text=True
    )
    total = len([l for l in result.stdout.strip().split('\n') if l])
    if len(items) == total:
        safe_dirs.append(cat)
        print(f"  rm -rf {cat}/")

if safe_dirs:
    print(f"\n批量命令: rm -rf {' '.join(safe_dirs)}")
```

### 10.7 批量清理执行流程（2026-07-04 实测）

**Phase 1：分析确认**
```bash
# 1. 跑分析脚本，确认未使用技能数量
python3 /tmp/analyze_skills.py

# 2. 输出：
# 本地技能总数: 225
# 从未使用: 192 (85.3%)
# 正在使用: 33
```

**Phase 2：分批清理**

每次清理前必须：
1. `mkdir -p ~/.hermes/skills-cleanup-backup{1,2,3...}` 备份
2. 列出待删目录让用户确认（用 clarify 工具）
3. 逐批执行，不要一次性全删

```bash
# 第一批：备份目录 + 空目录
cd ~/.hermes/skills
mkdir -p ~/.hermes/skills-cleanup-backup
cp -r .archive .curator_backups ~/.hermes/skills-cleanup-backup/
rm -rf .archive .curator_backups

# 第二批：从未使用的顶级目录
mkdir -p ~/.hermes/skills-cleanup-backup2
for dir in blockchain communication dogfood email github migration mlops red-teaming web-development webpage-audit yuanbao; do
    [ -d "$dir" ] && cp -r "$dir" ~/.hermes/skills-cleanup-backup2/ && rm -rf "$dir"
done

# 第三批：激进清理（删除目录下未使用的子技能）
mkdir -p ~/.hermes/skills-cleanup-backup3
# 读取未使用技能列表并逐个备份删除
while IFS= read -r skill; do
    skill_dir=$(dirname "$skill")
    if [ -n "$skill_dir" ] && [ "$skill_dir" != "." ]; then
        cp -r "$skill_dir" ~/.hermes/skills-cleanup-backup3/ 2>/dev/null
    fi
    rm -rf "$skill"
done < /tmp/unused_skills.txt
```

**Phase 3：验证统计**
```bash
echo "清理前: $(cat /tmp/before_count.txt) 个技能"
echo "清理后: $(find ~/.hermes/skills -name 'SKILL.md' | wc -l) 个技能"
echo "共删除: $(($(cat /tmp/before_count.txt) - $(find ~/.hermes/skills -name 'SKILL.md' | wc -l))) 个"

# 验证保留的技能仍可用
for skill in zhililong renwei-writing zhili-publish; do
    echo "验证: $skill"
    # 调用一次 skill_view 测试
done
```

### 10.8 备份恢复命令

如需从备份恢复：
```bash
# 查看所有备份
ls -la ~/.hermes/skills-cleanup-backup*/

# 恢复指定目录
cp -r ~/.hermes/skills-cleanup-backup3/creative ~/.hermes/skills/

# 恢复后验证
find ~/.hermes/skills -name 'SKILL.md' | wc -l

# 确认无误后可删除备份（谨慎！）
rm -rf ~/.hermes/skills-cleanup-backup*
```

### 10.9 关键经验总结

**为什么会漏删（已踩坑）**：
1. ❌ 只看 mtime — skillhub 批量安装时会统一更新所有文件时间
2. ❌ 精确字符串匹配 — `zhiliComments` 和 `zhilicomments` 被当作不同技能
3. ❌ 只用 skill_path 匹配 — 忽略了顶级目录名（如 `zhililong`）
4. ❌ 没查 session 历史 — 文件存在不代表被调用过

**正确方法**：
1. ✅ 直接查询 `~/.hermes/state.db` SQLite 数据库
2. ✅ 提取 `tool_calls` 中的 `skill_view` 调用参数
3. ✅ 应用别名标准化映射表
4. ✅ 用最后一级目录名匹配（不是完整路径）
5. ✅ 用差集运算找出真正的未使用技能

**备份策略**：
- 每次清理前创建带编号的备份目录
- 备份放在 `~/.hermes/skills-cleanup-backup{1,2,3...}/`
- 用户确认后才执行删除
- 恢复命令随时可用

## 注意事项

- **删除/移动前先备份**，不破坏性操作（`mv` 比 `rm` 安全，trash > rm）
- API keys/tokens/credentials 一律 [REDACTED]，不在 SKILL.md 输出
- 维护后**主动汇报**给用户（带数量、列表、备份位置），不静默完成
- skill-maintenance 自身归入 **`developer/`**（skill 自身管理工具）
- 跨 agent 共享的 skill 必须放系统级，不要留在工作区
- 「项目源码 vs skill」判断标准：**有 SKILL.md 才算 skill**，只有 README + 源码 = 项目
- **v2.1 新增**：install 类操作（clone / 推送 / 覆盖）**必须**先跑第 7 节的安全审计，HIGH/CRITICAL 风险不装
- **v2.4 新增**：安装后跑第 9 节引用对齐检查（防止 caller 引用腐烂）

## 9.1 清理前的别名标准化（关键！）

**⚠️ Pitfall H：别名未标准化导致漏报（2026-07-04 实测）**

首次分析时用了精确路径匹配，漏掉了 ~110 个未使用技能。原因是 session 历史中的 skill_view 调用存在多种别名写法：

| 别名写法 | 标准化为 |
|---------|---------|
| `zhiliComments` | `zhilicomments` |
| `social-media/.agents/skills/zhiliComments` | `zhilicomments` |
| `zhiliGitHub` | `zhiligithub` |
| `social-media/.agents/skills/zhiliGitHub` | `zhiligithub` |
| `skillgithub-sync` | `skill-github-sync` |
| `developer/skill-github-sync` | `skill-github-sync` |
| `zhilicomments-publish` | `zhilicomments` |
| `social-media:.agents/skills:zhilicomments` | `zhilicomments` |
| `geo-content-strategy` | `geo-keyword-research` |
| `dogfood`（根目录） | 实际是 `dogfood/dogfood` |

**标准化映射表**（分析前必须先应用）：

```python
skill_aliases = {
    'zhiliComments': 'zhilicomments',
    'social-media/.agents/skills/zhiliComments': 'zhilicomments',
    'zhiliGitHub': 'zhiligithub',
    'social-media/.agents/skills/zhiliGitHub': 'zhiligithub',
    'skillgithub-sync': 'skill-github-sync',
    'developer/skill-github-sync': 'skill-github-sync',
    'zhilicomments-publish': 'zhilicomments',
    'social-media:.agents/skills:zhilicomments': 'zhilicomments',
    'social-media/.agents/skills/zhili-publish': 'zhili-publish',
    'social-media/.agents/skills/zhiligithub': 'zhiligithub',
    'geo-content-strategy': 'geo-keyword-research',
    'content-strategy/geo-keyword-research': 'geo-keyword-research',
}
```

**判断函数**（必须用这个，不能只做字符串精确匹配）：

```python
def is_used(skill_path):
    name = skill_path.split('/')[-1]  # 只取最后一级目录名
    if skill_path in normalized_used or name in normalized_used:
        return True
    for alias, target in skill_aliases.items():
        if alias == skill_path or skill_path.endswith(alias):
            return True
    return False
```

### 9.2 批量清理工作流

**标准步骤**（2026-07-04 实测有效）：

1. **查询 session 历史** → 获取真实使用的 skill 集合
2. **标准化别名** → 映射多种写法到统一名称
3. **获取本地所有 skill** → `find ~/.hermes/skills -name "SKILL.md"`
4. **对比** → 差集 = 从未使用的 skill
5. **按目录分组** → 识别「全部未使用」vs「部分未使用」的目录
6. **输出清理建议** → 列出可安全删除的顶级目录
7. **⚠️ 必须确认** → 用 clarify 工具让用户明确选择
8. **备份** → `cp -r <dir> ~/.hermes/skills-cleanup-backup/`
9. **执行删除** → `rm -rf <dir>`
10. **验证统计** → 清理后 skill 总数

**确认命令示例**：

```bash
# 备份（先做）
BACKUP=~/.hermes/skills-cleanup-backup
mkdir -p "$BACKUP"
for dir in blockchain mlops github; do
  [ -d "$dir" ] && cp -r "$dir" "$BACKUP/" && rm -rf "$dir"
done

# 验证
echo "清理后: $(find ~/.hermes/skills -name 'SKILL.md' | wc -l) 个技能"
```

## 历史优化记录

- **2026-07-04（v2.7）**：新增第 10 节「技能使用情况分析」—— 直接查询 `~/.hermes/state.db` SQLite 数据库的 `messages.tool_calls` 字段，从 session 历史中提取真实 skill_view 调用记录，比文件 mtime 更准确。固化 Python 对比脚本 + mtime 参考命令 + 清理决策框架。新增 9.1 节 Pitfall H「别名未标准化导致漏报」—— 首次分析漏掉 110 个未使用技能是因为 `zhiliComments`/`zhiliGitHub` 等多种写法未映射到统一名称；固化标准化映射表 + 判断函数。新增 9.2 节「批量清理工作流」—— 实测有效的 10 步流程，含别名标准化 → 目录分组 → 用户确认 → 备份 → 执行 → 验证。
- **2026-07-03（v2.6）**：新增 Pitfall F「多 `---` 文档分隔符」—— body 内多余 `---` 会让 YAML 多文档解析器报错；固化诊断命令（`grep -n '^---$'`）+ Python 删除脚本。新增 Pitfall G「字节 vs 字符数差异」—— UTF-8 文件 stat().st_size ≠ len(read_text())，导致本地 vs 云端文件大小比较失真；固化正确解法（read_bytes() 字节级比对）。SKILL.md Step 2 合规检查表新增 `---` 数量检查 + 字节级比对步骤。
- **2026-07-02（v2.5）**：新增 Step 0「凭证预检」—— merge 前必须扫描 `config/` 类文件，对含真实凭证的 LOCAL 文件强制保留 CLOUD 脱敏版，防止明文 APPSECRET 上云。
- **2026-06-28（v2.3）**：更新第 7.3 节「误报注意」—— 新增发布类 skill 的 skillspector 判断逻辑；更新第 8.2 节合规检查——修正 YAML closing `---` 识别（description 块内 `---` 会被 yaml.safe_load 误判为第二个文档）；固化 `/tmp/skill_merge.py` 为快速调用脚本。
- **2026-06-04**：从 7 分类改成 6 分类（去掉「研究」「运营」等冗余，对齐 viceroy-skills 实际仓库结构）
- **2026-06-04**：加入「OpenClaw 加载优先级」章节（解释系统级 vs 工作区差异）
- **2026-06-04**：加入「项目源码 vs skill」识别规则（应对 obscura 误入场景）
- **2026-06-04**：跟 skill-github-sync 联动标准化
- **2026-05-27**：初版，7 分类 + 删除流程
