# 2026-06-11 zhilicomments v2 重装实战记录

> **触发场景**：用户给 GitHub URL 让重装某个 skill，并明确要求"按最新技能"。
> **目的**：把"按 URL 重装"这条流程的具体操作沉淀下来，给未来同类任务做参考。

## 用户原话

> "zhilicomments 的最新技能在这里 https://github.com/jacardl/viceroy-skills/tree/main/skills/creative/zhilicomments
> 重新安装 zhilicomments ，最新技能在这里 https://github.com/jacardl/viceroy-skills/tree/main/skills/creative/zhilicomments"

**关键信息提取**：
- URL: `skills/creative/zhilicomments`（注意是 `creative`，不是 `social-media`）
- 意图：**重装**（不是 sync 也不是新装），暗示本地版可能不是最新

## 我犯的错（坑 8 第一现场）

**第一反应**（错）：
```
试 npx skills add jacardl/viceroy-skills --skill zhilicomments
→ 路径解析到了 social-media/ 而非 creative/
→ 报告"云端不存在该 skill"
```

**真实情况**：
- 云端路径：`skills/creative/zhilicomments/SKILL.md` ✅ 存在
- 本地路径：`~/.hermes/skills/social-media/.agents/skills/zhilicomments/SKILL.md`（多层嵌套）
- 两边 SKILL.md 字节数差异：本地 10534B vs 云端 27306B（**云端大 2.6 倍**）

## 正确流程（事后归纳）

1. **验证云端路径**：直接 curl URL 段对应的 raw.githubusercontent.com → 200 ✅
2. **比对字节数**：本地 10534B vs 云端 27306B → **云端是新版，本地严重过时**
3. **列云端 references/ 目录**：API 看所有支持文件 → 列出 config.md / format.md / streambert-reference.html / wechat-pitfalls.md
4. **备份本地版**：`cp -r ~/.hermes/skills/.../zhilicomments /tmp/zhi-old`
5. **逐文件覆盖**：用 curl 拉云端每个文件，覆盖到本地路径
6. **清理本地残留**：本地的 `publish_guide.md`（云端没有）移到 `.old-backups/`
7. **最终对比确认**：`wc -c SKILL.md` 与云端字节数一致

## 重装后发现的关键变更（zhilicomments v1 → v2）

| 维度 | 旧（本地残留） | 新（云端 v2） |
|---|---|---|
| 公众号 | 独立小扎喝不醉 | **直隶按察使** |
| 作者 | 默认空 / 强制卡兹克 | **刘生**（2字符） |
| 字数 | 2000-3000字 | **1000-1500字** |
| SKILL.md 字节 | 10534 | **27306** |
| 结构 | 显化三段式 | **内化三段式**（不显化） |
| CSS | 羊皮纸基础 | **+黄底高亮 / `· · ·` 分隔线** |
| 精简规则 | 无 | **7 条（5.1-5.7）**：标题≤10字、删过渡句、删虚词、删 H1、删副标题、删顶部标签、Pre-submit 5 项 |
| Branding 铁律 | 一般禁词 | **+ 13 个禁用字符串清单**（卡兹克/khazix/zhiliGitHub/本文由/一键三连/扫码/wzglyay/自动发布/jacardl 等） |

## 重装后立刻能做的事

- 提示用户：云端 SKILL.md 第 281 行引用 `scripts/preflight.py`，但云端和本地都没有这个脚本 → **缺口**，等佳哥确认要不要本地补一个
- 检查同分类兄弟 skill 是否也要重装（坑 7）：
  ```bash
  for skill in zhili-publish zhilicomments zhiligithub; do
    LOCAL=$(wc -c < ~/.hermes/skills/social-media/.agents/skills/$skill/SKILL.md 2>/dev/null || echo "MISSING")
    REMOTE=$(curl -sIL "https://raw.githubusercontent.com/jacardl/viceroy-skills/main/skills/creative/$skill/SKILL.md" | grep -i content-length | awk '{print $2}' | tr -d '\r')
    echo "$skill: 本地=$LOCAL 云端=$REMOTE"
  done
  ```

## 教训（一句话版）

> 用户给 URL 时，第一步永远是 grep 云端实存 + find 本地真实路径，**不要绕道 npx skills add 倒推路径**。