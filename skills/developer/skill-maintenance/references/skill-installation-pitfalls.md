# skill-installation-pitfalls

Real pitfalls caught during skill install / maintenance sessions. Not a theoretical list — each entry is a transcript of what actually broke.

---

## Pitfall A: GitHub TOKEN 变量注入导致 bash eval 语法错误

**症状**：在 heredoc 或多行 command string 里写 `TOKEN=$(cat ~/.hermes/keys/github_token.txt)"`（多打了一个闭括号外的 `"`），触发：
```
/bin/bash: eval: line N: syntax error near unexpected token `)'
```
整个 terminal 调用链失败，后续 API 请求全部跳步。

**根因**：`TOKEN=*** ~/.hermes/keys/github_token.txt)"` 这个模式在 heredoc 里被 shell 展开为 `TOKEN=<实际token值)"` —— 末尾多出来的闭括号让 bash 把整行解析成一个未闭合的子shell。

**复现场景**：
```bash
# ❌ 错误模式（会失败）
curl -s -H "Authorization: token $TOKEN" \
  "https://api.github.com/repos/..." \
  | python3 -c "import sys,json; ..."

# 在 heredoc 里更隐蔽：
cat > /tmp/script.py << 'EOF'
TOKEN=*** ~/.hermes/keys/github_token.txt)"
...
EOF
```

**解法**：始终用 Python 脚本文件而非 heredoc 拼 bash。写 `.py` 到 `/tmp/` 然后 `python3 /tmp/script.py`：
```python
#!/usr/bin/env python3
from pathlib import Path
TOKEN = open(Path.home() / ".hermes/keys/github_token.txt").read().strip()
# 然后正常用 urllib.request，不走 shell TOKEN 展开
```

**判断标准**：只要一个 terminal 调用里同时出现 `(...)` subshell 和 `"` 引号，优先写成 Python 文件。宁可多一个文件，少踩一次。

---

## Pitfall B: YAML `***` 分隔符导致双文档解析失败

**症状**：
```
YAML 错误: expected a single document in the stream
  in "<unicode string>", line 2, column 1:
    name: zhiliComments
    ^
but found another document
  in "<unicode string>", line N, column 1:
    ---
```

**根因**：SKILL.md frontmatter 里 description 折叠块（`description: >`）末尾有一行裸 `***`（无缩进），YAML 1.2 规范里 `---` 是文档分隔符，而 `***` 在某些解析器里也被当成分隔标记。`yaml.safe_load()` 把同一个 frontmatter 当成两个 YAML 文档。

**触发条件**：description 值里写内部分隔线 `***`，且该 `***` 行没有缩进（顶格）。

**解法**：给 `***` 加两个空格缩进，让它完全落在 description 折叠块内部：
```yaml
description: >
  执行前必读...
  ***

---
# 正文从这里开始
```

缩进后 YAML 解析器把它当成 description 值的一部分，而不是文档分隔符。

**预防**：写 SKILL.md 时，避免在 frontmatter 里裸写 `---` 或 `***` 作为分隔符。若必须用，改用 `***` 加缩进。

---

## Pitfall C: skill-maintenance 三向 merge 的 git merge-file 局限性

**症状**：三向 merge 后文件末尾出现重复行，或 `git merge-file` 产生的 conflict marker 被删掉但内容有遗漏。

**根因**：`git merge-file` 是为纯文本文件设计的，对 markdown 的语义结构（标题层级、列表项、代码块）无法感知。当两份 markdown 各自在末尾加了同样的行但顺序不同，merge-file 可能产生行重复。

**解法**：
1. merge 后立即检查 `tail -5 <file>`，看是否有重复行
2. 检查 `grep -n "^---$" <file>`，frontmatter 区域不应有额外的 `---`
3. 如有重复，手动用 patch 修正

**预防**：三向 merge 后，merge status 为 `conflict_resolved` 时，**必须**跑以下检查再推送 GitHub：
```bash
# 1. 检查 frontmatter 结构
grep -n "^---$" <file>  # 应只有两处：开头和闭口

# 2. 检查行尾重复
tail -5 <file>  # 不应有连续相同行

# 3. YAML 合规验证
python3 -c "import yaml; yaml.safe_load(open('<file>').read())"
```

---

## Pitfall D: `~/.agents/skills/` 子目录结构导致 skill 嵌套

**症状**：从 viceroy-skills 安装 skill 时，目录结构为 `skills/developer/skill-maintenance/SKILL.md`。安装后 `~/.agents/skills/` 里出现 `developer/skill-maintenance/` 嵌套路径。Hermes loader 根据 frontmatter `name:` 字段定位 skill，但 `skills_list` 显示的路径会反映实际目录结构。

**根因**：viceroy-skills 仓库用 `skills/{category}/{skill}/SKILL.md` 三层结构；本地安装时若直接按原路径复制，会在 `~/.agents/skills/` 和 `~/.hermes/skills/` 里重建同样的嵌套。

**对 Hermes 的影响**：Hermes 的 `skill_view(name="skill-maintenance")` 能正常加载，因为 loader 遍历所有子目录读取 frontmatter。但 `skills_list` 输出会显示分类前缀（如 `developer/skill-maintenance`）。

**解法**（2026-06-28 实测）：安装时按原路径复制是**正确行为**——保持 viceroy-skills 的分类结构：
```bash
for ROOT in ~/.agents/skills ~/.hermes/skills; do
  mkdir -p "$ROOT/developer"
  curl -sL "https://raw.githubusercontent.com/jacardl/viceroy-skills/main/skills/developer/skill-maintenance/SKILL.md" \
    -o "$ROOT/developer/skill-maintenance/SKILL.md"
done
```
`skill_view(name="skill-maintenance")` 能找到，loader 靠 frontmatter 解析，不依赖目录名。

---

## Pitfall E: 云端 skill 存在但 references/ 子目录未创建

**症状**：`skill_view(name="X")` 能正常加载，但 `skill_view(name="X", file_path="references/foo.md")` 报 404。云端 viceroy-skills 的 `SKILL.md` 里 `linked_files` 引用了不存在的 references 文件。

**根因**：SKILL.md 的 `linked_files` 字段是人工维护的，容易过期。云端更新 SKILL.md 时可能加了新 reference 但忘了实际创建文件。

**复现**：2026-06-28，`skill-maintenance` 的 `references/skill-installation-pitfalls.md` 在 viceroy-skills 里不存在（404），但 SKILL.md 的 frontmatter `linked_files` 里列着它。

**解法**：安装后主动 probe references 是否存在：
```bash
SRC='https://raw.githubusercontent.com/jacardl/viceroy-skills/main'
for ref in config.md format.md wechat-pitfalls.md; do
  status=$(curl -s -o /dev/null -w "%{http_code}" "$SRC/skills/creative/zhilicomments/references/$ref")
  if [ "$status" = "200" ]; then
    echo "  ✓ $ref"
  else
    echo "  ✗ $ref 云端不存在（SKILL.md linked_files 需清理）"
  fi
done
```

发现 404 时，**不要**下载 404 文件，在本地也不创建该 reference，只要把 `linked_files` 里的条目删掉或注释即可（下次该 skill 作者更新 SKILL.md 时会同步）。

---

## Pitfall F: 多 `---` 文档分隔符导致 YAML 解析器误判

**症状**：执行三向 merge 时，`yaml.safe_load()` 报 `expected a single document`。本地 SKILL.md 文件含 5 个 `---` 分隔符（应为 2 个）。

**根因**：SKILL.md 历史上多次编辑，在 body 内累积了多个 YAML 文档分隔符 `---`：
- 行 1：`---`（frontmatter 开始）
- 行 12：`---`（frontmatter 结束 + 空文档）
- 行 13：`---`（body section 开始 + 空文档）
- 行 29：`---`（第二个 body section 开始）
- 行 612：`---`（第三个 body section 开始）

`yaml.safe_load()` 读到第二个 `---` 就停止第一段解析；但第三、四个 `---` 在 body 内会让多文档解析器报 `expected a single document`。

**诊断命令**：
```bash
# 统计文件中所有 --- 的行号（应为恰好 2 个）
grep -n '^---$' <SKILL.md>
```

**解法**：删除 body 内多余的 `---`，只保留 frontmatter 边界：
```python
from pathlib import Path
lines = Path("SKILL.md").read_bytes().decode('utf-8', errors='replace').splitlines()
new_lines = [l for i, l in enumerate(lines) if l.strip() == '---' and i+1 not in {保留的行号}]
Path("SKILL.md").write_text('\n'.join(new_lines))
```

**实战案例（zhiligithub, 2026-07-03）**：5 个 `---`（行 1/12/13/29/612），删除行 13/29/612 后只剩 2 个，YAML 合规检查通过。

**预防**：编辑 SKILL.md 时，**不要**在 body 内用 `---` 作为 section 分隔符（只用空行即可）。

---

## Pitfall G: Python `read_bytes()` vs `read_text()` 的字节/字符数差异

**症状**：`stat().st_size` ≠ `len(read_text())`。本地文件 `read_bytes()` 返回 89061 字节，但 `read_text()` 后只有 56388 字符。GitHub API 的 `size` 字段是字节数，导致"本地比云端小 32KB"的假象（实际是同一份文件）。

**根因**：macOS APFS 存储 UTF-8 文件时以字节计大小（stat），Python `len(text)` 是 Unicode 码点数。当 SKILL.md 含多字节 Unicode（中文、emoji）时，1 个字符可能占 3 字节，导致字节数 > 字符数。

**正确比对方式**（判断本地 vs 云端是否相同）：
```python
# ✅ 正确：比对原始字节
local_bytes = Path("SKILL.md").read_bytes()
cloud_bytes = base64.b64decode(cloud_api_response['content'])
assert local_bytes == cloud_bytes  # 字节级比对

# ❌ 错误：比对解码后字符数
assert len(local_text) == cloud_size  # cloud_size 是字节数，不相等
```

**实战案例（zhiligithub, 2026-07-03）**：`stat().st_size` = 89061 字节，`len(read_text())` = 56388 字符（差 32673 = UTF-8 多字节字符数）。`cmp` 字节比对确认本地和云端完全相同，无须 merge。
