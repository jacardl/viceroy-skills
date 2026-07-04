# Cross-Skill Citation Alignment Check

When a skill explicitly references another skill in its workflow
(e.g., "配图：调用 zhili-illustration"), verify that the citation
is accurate against the referenced skill's actual requirements.
Blind citation copies decay over time as the referenced skill evolves.

## When to run

- After installing a new skill that mentions other skills
- When a skill's description lists callers/callees
- After bulk skill updates or merges
- When the user asks "does X correctly reference Y?"

## Method: bilateral comparison

### Step 1: Extract the cited workflow snippet

Read the calling skill's reference to the callee. Example from zhiliGEO:

> 配图：调用 zhili-illustration 技能（读取 HTML → 提取 shot list
> → xiaohu-ip-studio 生成图片 → 注入 HTML → 上传微信素材获取 media_id）

Note that this is a **summary** — the caller paraphrases the callee's
workflow. The check verifies the paraphrase is still correct.

### Step 2: Read the callee's full requirements

Grep the callee's SKILL.md for mandatory steps, constraints, and
warnings that the caller might have omitted. Key signals:

| Signal | grep pattern |
|--------|-------------|
| User confirmation required | `必须等用户\|用户确认\|wait for user` |
| Prompt format requirements | `prompt.*格式\|--prompt-file\|三段式` |
| Engine / backend choice | `xiaohu-ip-studio\|mmx-cli\|comfyui` |
| Limits (count, size, ratio) | `上限\|最多\|不超过\|only\s+\d+\s+image` |
| Covers that bypass the engine | `不走\|不要用\|封面\|cover` |

### Step 3: Table comparison

For each citation, build a table:

| # | Severity | Issue | Callee requirement | Caller says |
|---|----------|-------|-------------------|-------------|
| 1 | 🔴 HIGH | Missing mandatory step | "Must wait for user to confirm IP and style before generating" | Omitted |
| 2 | 🟡 LOW | Format detail not described | "/tmp/illo_prompt.md three-section format required" | Not mentioned |

### Step 4: Severity classification

| Symbol | Meaning | When |
|--------|---------|------|
| 🔴 | Will break the workflow if ignored | User confirmation skipped, wrong engine, conflicting path |
| 🟡 | Quality degradation, not breaking | Format details omitted, limits not stated |
| ⚪ | Informational | Minor wording differences, same meaning |

## Full example: zhiliGEO ↔ zhili-illustration (2026-06-28)

### Caller (zhiliGEO line 172)

```
2. 配图：调用 zhili-illustration 技能（读取 HTML → 提取 shot list
→ xiaohu-ip-studio 生成图片 → 注入 HTML → 上传微信素材获取 media_id）
```

### Callee (zhili-illustration) requirements extracted

| Requirement | Line | Text |
|------------|------|------|
| User confirm IP + style | 52 | "Shot list 提取完成后，必须等用户确认 IP 和风格再生成图片" |
| Prompt file format | 65-81 | `/tmp/illo_prompt.md` three-section: [Task] / [Content] / [Visual Requirements] |
| Cover bypass | 119 | "封面图不走 xiaohu-ip-studio" |
| Workflow steps | 19-31 | ① extract shot list → ② generate → ③ inject HTML → ④ upload |

### Results

- ✅ Workflow steps: all 4 steps mapped correctly
- ✅ No cover conflict (zhiliGEO's line 172 is about body illustrations, not cover)
- 🔴 User confirmation swallowed — zhili-illustration requires it, zhiliGEO doesn't mention it
- 🟡 Prompt format not described — `/tmp/illo_prompt.md` three-section format not mentioned

### Decision

2 issues found. zhiliGEO is cleaner than zhililong (5 issues) because it doesn't
claim to generate covers via xiaohu-ip-studio (which zhili-illustration forbids
for covers) and doesn't set arbitrary limits.

## Pitfalls

1. **Don't compare descriptions, compare requirements.** The caller's
   description of the callee ("配图技能") is marketing — the callee's
   body text ("must wait for user") is the contract.

2. **Grep both directions.** The callee's description might also list
   the caller. Cross-validate.

3. **Cover images are a frequent misalignment.** Many writing skills
   lump "generate all images" together, but zhili-illustration
   explicitly separates body illustrations from cover (cover has its
   own 900×383 spec and does NOT go through xiaohu-ip-studio).

4. **Path references rot silently.** If the callee moves from one
   category to another, the caller's hardcoded paths break.
