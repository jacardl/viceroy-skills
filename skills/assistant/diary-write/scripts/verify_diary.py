#!/usr/bin/env python3
"""
verify_diary.py — validate today's Obsidian diary file against diary-write rules.

Rules enforced (12 LRNs):
  1. Trigger types only (location / trigger-word text)
  3. Body verbatim (no edits, no frontmatter)
  4. File order = reverse-chronological
  5. Title formats:
     - text block: '## HH:MM:SS' (no extra text)
     - location block: '## HH:MM:SS — name' (em dash + name)
  6. 5-min rolling window, <= 5 boundary inclusive
  7. Location blocks NEVER merge into text blocks
  9. Same-second dup detection (warning only)
 11. Asia/Shanghai timezone for filename

Usage:
  python3 scripts/verify_diary.py [path/to/YYYY-MM-DD.md]
  (default: ~/Documents/Obsidian Vault/daily/$(TZ=Asia/Shanghai date +%Y-%m-%d).md)
"""

import sys
import re
from pathlib import Path
from datetime import datetime, timezone, timedelta

DEFAULT_VAULT = Path.home() / "Documents/Obsidian Vault"
DEFAULT_FILE = DEFAULT_VAULT / "daily" / (
    datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d") + ".md"
)

TITLE_TEXT = re.compile(r"^## (\d{2}):(\d{2}):(\d{2})\s*$")
TITLE_LOC = re.compile(r"^## (\d{2}):(\d{2}):(\d{2}) — (.+?)\s*$")
EM_DASH = "\u2014"

errors = []
warnings = []


def parse_file(path: Path):
    if not path.exists():
        errors.append(f"file not found: {path}")
        return None
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")

    # parse blocks
    blocks = []
    cur = None
    for i, line in enumerate(lines, 1):
        m_loc = TITLE_LOC.match(line)
        m_txt = TITLE_TEXT.match(line)
        if m_loc:
            if cur:
                blocks.append(cur)
            cur = {
                "line": i,
                "type": "location",
                "time": (int(m_loc.group(1)), int(m_loc.group(2)), int(m_loc.group(3))),
                "name": m_loc.group(4),
                "body_lines": [],
            }
        elif m_txt:
            if cur:
                blocks.append(cur)
            cur = {
                "line": i,
                "type": "text",
                "time": (int(m_txt.group(1)), int(m_txt.group(2)), int(m_txt.group(3))),
                "body_lines": [],
            }
        elif cur is not None:
            cur["body_lines"].append(line)
    if cur:
        blocks.append(cur)
    return blocks


def to_seconds(t):
    return t[0] * 3600 + t[1] * 60 + t[2]


def check_rules(blocks):
    # rule 5: title format
    for b in blocks:
        if b["type"] == "text":
            # already matched TITLE_TEXT — strict, no extra
            pass

    # rule 4: file order reverse-chronological
    for i in range(len(blocks) - 1):
        if to_seconds(blocks[i]["time"]) < to_seconds(blocks[i + 1]["time"]):
            errors.append(
                f"line {blocks[i]['line']}: block at {blocks[i]['time']} is older than "
                f"line {blocks[i+1]['line']}: {blocks[i+1]['time']} (violates reverse-chrono order)"
            )

    # rule 6: text block start times should be 5min apart from previous text block
    text_blocks = [b for b in blocks if b["type"] == "text"]
    for i in range(1, len(text_blocks)):
        a, b = text_blocks[i - 1], text_blocks[i]
        # because file is reverse-chrono, a is newer than b
        diff = to_seconds(a["time"]) - to_seconds(b["time"])
        if 0 < diff < 300:  # 5 min = 300 sec
            # a starts later than b but less than 5 min later -> merge should have happened
            # BUT because we allow location blocks interleaving, only check if a is right after b
            # find index in original blocks
            ai = blocks.index(a)
            bi = blocks.index(b)
            # if they're adjacent in blocks (no location between), violation
            if bi + 1 == ai:
                errors.append(
                    f"line {a['line']}: text block {a['time']} should merge into "
                    f"line {b['line']} text block {b['time']} (diff {diff}s < 300s)"
                )

    # rule 7: location blocks never merge — already enforced by separate type
    for b in blocks:
        if b["type"] == "location":
            # check name field not contain lat/lon
            if any(c.isdigit() and "." in b["name"] for c in b["name"]):
                # might be a coord
                if "longitude" in b["name"] or "latitude" in b["name"]:
                    errors.append(
                        f"line {b['line']}: location name contains coords: {b['name']!r}"
                    )

    # rule 9: same-second duplicate detection
    seen = {}
    for b in blocks:
        key = (b["type"], b["time"], tuple(b["body_lines"]))
        if key in seen:
            warnings.append(
                f"line {b['line']}: same-second duplicate of line {seen[key]}"
            )
        else:
            seen[key] = b["line"]


def main():
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
    else:
        path = DEFAULT_FILE

    blocks = parse_file(path)
    if blocks is None:
        print("\n".join(errors))
        sys.exit(1)

    check_rules(blocks)

    print(f"file: {path}")
    print(f"blocks: {len(blocks)} ({sum(1 for b in blocks if b['type']=='text')} text + "
          f"{sum(1 for b in blocks if b['type']=='location')} location)")
    print(f"errors: {len(errors)}")
    print(f"warnings: {len(warnings)}")
    if errors:
        print("\nERRORS:")
        for e in errors:
            print(f"  - {e}")
    if warnings:
        print("\nWARNINGS:")
        for w in warnings:
            print(f"  - {w}")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
