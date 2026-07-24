---
name: skill-github-sync
description: "将本地 Skills 同步到 viceroy-skills GitHub 仓库，维护 README"
metadata: { "openclaw": { "emoji": "🔄" } }
---

# Skill GitHub Sync

将本地 Skills 同步到 `jacardl/viceroy-skills` 仓库。

## 分类（6个，不可新增）
`ai` · `assistant` · `creative` · `developer` · `operations` · `product`

## 仓库信息
- 公开仓库：`https://github.com/jacardl/viceroy-skills`
- Token：`~/.hermes/keys/github_token.txt`
- 本地工作区：`/tmp/viceroy-skills_sync`

## ⚠️ 预检（sync 前必做，3 步）

跳过预检会踩坑。读完后才执行 sync。

### 步骤 0：凭证安全扫描

扫描本地凭证文件，**发现真实密钥立即停下**：

```bash
for f in $(find ~/.hermes/skills ~/.agents/skills ~/.openclaw/skills \
  -path "*/references/config.md" 2>/dev/null); do
  grep -iE "appsecret|api_key|secret|password|token|wx_|private_key" "$f" | \
    grep -v "REDACTED\|\\*\\*\\*\\*\\*" && echo "⚠️ $f 含明文密钥，STOP"
done
```

命中真实值 → 跳过该 skill，不 push。

### 步骤 1：fetch 远端

```bash
git fetch origin && git log --oneline origin/main -5
```

### 步骤 2：确认云端路径

```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://api.github.com/repos/jacardl/viceroy-skills/contents/skills/<cat>" | \
  python3 -c "import sys,json; [print(x['name']) for x in json.load(sys.stdin)]"
```

## 核心流程

### 克隆
```bash
git clone "https://jacardl:$(cat ~/.hermes/keys/github_token.txt)@github.com/jacardl/viceroy-skills.git" \
  /tmp/viceroy-skills_sync
```

### 同步（先删后 cp）
```bash
rm -rf /tmp/viceroy-skills_sync/skills/<cat>/<skill>
cp -r /path/to/local/<skill> \
  /tmp/viceroy-skills_sync/skills/<cat>/<skill>
```

### 凭证还原（若 cp 覆盖了脱敏文件）
```bash
git -C /tmp/viceroy-skills_sync checkout HEAD -- \
  skills/<cat>/<skill>/references/config.md
```

### 提交 + push
```bash
cd /tmp/viceroy-skills_sync
git add <files> && git commit -m "feat: sync <skill>"
GIT_ASKPASS=echo git push
```

443 超时 → `sleep 5 && git push`
rejected → `GIT_TERMINAL_PROMPT=0 git pull --rebase --autostash origin main && git push`

## README 更新

每次增删技能后同步更新 `README.md` 和 `README.en.md`。

格式规范见 `references/readme-template.md`。

## 坑详情

11 个实战踩坑的详细复盘见 `references/sync-pitfalls.md`（完整 11 坑）。

**关键规则**：
- 本地路径 ≠ 云端分类（本地 `~/.hermes/skills/<域>/` vs 云端 `skills/<6大分类>/`）
- 云端落后 → 以本地为准，直接覆盖
- **禁止 git merge-file** 做三方合并，会导致重复累积
- cp 后 push 前逐个 `git diff` 检查改动文件

**关键规则**：
- 本地路径 ≠ 云端分类（本地 `~/.hermes/skills/<域>/` vs 云端 `skills/<6大分类>/`）
- 云端落后 → 以本地为准，直接覆盖
- **禁止 git merge-file** 做三方合并，会导致重复累积
- cp 后 push 前逐个 `git diff` 检查改动文件
