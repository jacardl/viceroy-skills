# gh_collect.py Retry Loop — macOS grep -P incompatible

## 2026-10-02 session findings

### Problem: grep -P causes retry loop to always fall through

Shell loop in SKILL.md acquisition step:

```bash
result=$(python3 "$SCRIPT_DIR/gh_collect.py" "$TODAY" 2>&1)
count=$(echo "$result" | grep -oP 'Inserted \K\d+')   # BSD grep: "grep: invalid option -- P"
echo "GH count: $count"
[ "$count" -ge 1 ] && break   # [: : integer expression expected — $count is empty
```

**Root cause**: macOS `grep` is BSD-based, does not support `-P` (PCRE). The `grep -oP` silently fails and outputs nothing, leaving `$count` empty. The comparison `[ "$count" -ge 1 ]` then fails with "integer expression expected".

**Actual insert**: 11 repos each attempt — loop still worked but wasted 2 unnecessary 30s retries.

### Fix

Replace `grep -oP` with awk:

```bash
count=$(echo "$result" | awk '/Inserted [0-9]+ repos/ {print $3}')
```

Or use Python directly:

```bash
count=$(python3 -c "import subprocess; r=subprocess.run(['python3','$SCRIPT_DIR/gh_collect.py','$TODAY'],capture_output=True,text=True); m=__import__('re').search(r'Inserted (\d+)', r.stdout); print(m.group(1) if m else 0)")
```

### HP source backdating — confirmed correct behavior

ruanyf/weekly issue-413 published Friday 2026-10-02 CST morning.
gh_collect.py wrote `article_date=2026-10-01` (Thursday UTC).

This is the GitHub Trending reset at UTC~00:00 (CST~08:00). Content published before CST 08:00 belongs to the previous UTC calendar date. **Not a bug.**

Acceptance criteria: `article_date` = target_date -1 for Markdown source = normal. Only intervene if >= 2 days offset or trending repos are also wrong.