---
name: diary-write
description: "Append 佳哥's 飞书 inbound messages to the daily Obsidian journal under the 5-minute rolling-window block rules. Triggers on 飞书 location messages or explicit 日记/写日记/记到 obsidian text; ignores everything else."
---

# Obsidian Diary Write

Append 佳哥's 飞书 inbound to today's Obsidian daily note. **Triggers on 2 message types only**:

1. 飞书 `location` 消息（+ → 位置）
2. 飞书 `text` 消息 containing `日记` / `写日记` / `记到 obsidian` / `obsidian 日记` / `写入 obsidian`

All other 飞书 inbound = **do nothing**.

## Vault & file

- Vault: `~/Documents/Obsidian Vault` (fallback; `OBSIDIAN_VAULT_PATH` unset)
- File: `daily/YYYY-MM-DD.md` (Beijing date, `export TZ=Asia/Shanghai`)
- `mkdir -p` if `daily/` missing

## Write rules (12 LRNs)

| # | Rule | Source |
|---|------|--------|
| 1 | Only 2 trigger types above — ignore everything else | LRN-20260614-011 |
| 2 | Strip trigger words (`写日记，` `日记，` ...) from body | LRN-20260614-005 |
| 3 | Write body verbatim — no edits, no frontmatter, no blockquote | LRN-20260614-004 |
| 4 | New blocks on top; file order = reverse-chronological | LRN-20260614-004 |
| 5 | Block title format: text=`## HH:MM:SS`; location=`## HH:MM:SS — name` | LRN-20260614-006/009 |
| 6 | 5-min rolling window (A2, `<= 5` boundary inclusive) | LRN-20260614-010 |
| 7 | Location blocks NEVER merge into text blocks | LRN-20260614-010 |
| 8 | Within a block, lines ordered by time asc, newest at block bottom | LRN-20260614-010 |
| 9 | Same-second duplicates: keep latest only | LRN-20260614-010 |
| 10 | Location body: only `name` field, drop `longitude`/`latitude` | LRN-20260614-008 |
| 11 | Timezone: always `Asia/Shanghai` | LRN-20260501-001 |
| 12 | After write: `stat` + `awk` to verify (zsh 吞 output) | LRN-20260614-003 |

## Workflow

1. `export TZ=Asia/Shanghai && date '+%Y-%m-%d %H:%M:%S'`
2. Classify inbound:
   - `message_type=location` → 位置 path
   - `text` containing trigger word → 文字 path
   - else → STOP (no write)
3. Read today's file (or create H1 shell if missing)
4. Apply 5-min rolling-window logic (see `references/algorithm.md`)
5. Insert new block at top; reverse-chronological order preserved
6. `stat -f '%N  %z bytes' <file>` verify; use `awk '{printf "L%d|%s\n",NR,$0}'` to bypass zsh glob `##` parsing (LRN-20260614-003)
7. If using heredoc or docker exec psql: prefer `echo "..." | docker exec -i` to avoid parse bug (LRN-20260611-002)

## Common pitfalls (zsh)

- `## ` in body → zsh recursive glob → use `awk` or `/bin/cat` (still截) → use `read` tool with offset/limit, or write Python to file then exec
- `ls -la`, `cp -R`, `rm -rf` outputs经常被吞 — fall back to `stat` per-file or `find | xargs -I {} stat -f '%N %z' {}`
- `tee /tmp/zz.txt` then `cat /tmp/zz.txt` works for grep/awk that have line-prefix output
- Avoid `cat <<EOF ... EOF` (OpenClaw exec parse bug)

## References

- `references/algorithm.md` — 5-min rolling window pseudo-code + worked example
- `references/triggers.md` — trigger word enumeration + 飞书 location payload schema
- `references/edge-cases.md` — 11 边界 cases from tonight's session (重复节 / 触发词剥离 / 块标题冲突 / 跨午夜 ...)
