# 推送新 Skill 到 GitHub（云端不存在）

当 `curl .../skills/<cat>/<skill>/SKILL.md` 返回 **HTTP 404** 时适用。

## 判断条件

| 条件 | HTTP 状态 | 操作 |
|------|-----------|------|
| 云端 404（skill 不存在） | 404 | 全新推送，不需要 rebase ✅ |
| 云端 200（skill 已存在） | 200 | 走坑 11 决策树，需判断 rebase 策略 |

## 完整流程（约 2 分钟）

```bash
SKILL_DIR=~/.hermes/skills/<local_area>/<skill>
TARGET=/tmp/viceroy-skills_sync/skills/<cat>/<skill>
TOKEN=$(cat ~/.hermes/keys/github_token.txt)

# Step 1: 凭证扫描（credentials* / config.md 有无明文）
grep -rE "appsecret|api_key|secret|password|token" "$SKILL_DIR/references/" 2>/dev/null && echo "⚠️ 发现敏感词" || echo "✅ 无敏感词"
# 命中 api_key: sk-you...here → 是占位符，安全 ✅
# 命中 api_key: sk-0d68d...（真实值）→ 立即停下，检查 git diff

# Step 2: 克隆 + 复制
rm -rf /tmp/viceroy-skills_sync
GIT_TERMINAL_PROMPT=0 git clone https://github.com/jacardl/viceroy-skills.git /tmp/viceroy-skills_sync
mkdir -p "$TARGET"
cp -r "$SKILL_DIR"/* "$TARGET/"

# Step 3: 字节数核对（逐文件，差值必须 0）
for f in SKILL.md references/... scripts/...; do
  LOCAL=$(wc -c < "$SKILL_DIR/$f")
  CLOUD=$(wc -c < "$TARGET/$f")
  [ "$LOCAL" = "$CLOUD" ] && echo "✅ $f: $LOCAL bytes" || echo "❌ $f 本地=$LOCAL 云端=$CLOUD"
done

# Step 4: 更新 README（中文 + 英文）
#  Badge 数字 +1
#  Creative 表格末尾追加一行：| [**skill-name**](skills/creative/skill-name/SKILL.md) | 一句话描述 |

# Step 5: 提交推送
cd /tmp/viceroy-skills_sync
git add skills/<cat>/<skill> README.md README.en.md
git commit -m "feat(<cat>): add <skill-name> skill"
git remote set-url origin "https://jacardl:$TOKEN@github.com/jacardl/viceroy-skills.git"
GIT_TERMINAL_PROMPT=0 git push origin main
```

## 关键原则

- **不需要 rebase**：云端没有这个 skill，HEAD 不可能落后，直接 push 即可
- **先删后建**：`rm -rf "$TARGET" && cp -r` 防嵌套（`skill/skill/`）
- **凭证扫描优先于 git add**：发现真实凭证 → `git checkout HEAD --` → 跳过该 skill
- **README 中英双语同步**：Badge 数字 + 表格条目，两者缺一不可

## 验证清单

- [ ] HTTP 404 确认（`curl -o /dev/null -w "%{http_code}"`）
- [ ] 凭证扫描通过（只有占位符，无真实密钥）
- [ ] 字节数逐文件核对，差值 0
- [ ] README Badge 数字 +1
- [ ] README 中英文表格都追加了条目
- [ ] push 成功（远端 SHA 变化）
- [ ] 远端验证 `curl raw.githubusercontent.com` 内容正确
