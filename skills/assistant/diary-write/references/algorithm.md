# 5-Minute Rolling Window Algorithm (A2)

## Definition

- **Block title** = first message's `HH:MM:SS`
- **Window** = `[block_start, block_start + 5min]` (boundary inclusive, `<= 5`)
- **New message** vs most recent text block start:
  - diff ≤ 5:00 → merge into that block (append at bottom)
  - diff > 5:00 → new block (new block title = new message time)
- **Location messages** are always standalone blocks (NEVER merged)

## Worked example (from 2026-06-14 session)

| 实际时刻 | 原文（前 30 字） | 划档 |
|----------|-----------------|------|
| 22:40:00 | 今天我看了希特勒的电影 | 22:40 块起 |
| 22:44:00 | 你只往Obsidian中写入我发给你的原文 | 22:40 块 (差 4) |
| 22:46:00 | 我刚才看了希特勒的电影 | 22:46 块起 (差 6 超) |
| 22:48:00 | 不要把触发词写入... | 22:46 块 (差 2) |
| 22:49:00 | 严格 | 22:46 块 (差 3) |
| 22:50:00 | 我刚才调试了飞书... | 22:46 块 (差 4) |
| 22:52:00 | 日记中的二级标题... | 22:52 块起 (差 6 超) |
| 22:53:00 | 每次写入日记时... | 22:52 块 (差 1) |
| 22:54:00 | 用我手机端的位置信息 | 22:52 块 (差 2) |
| 22:55:00 | 当我给飞书发消息时... | 22:52 块 (差 3) |
| 22:56:00 | 你能不能直接获取飞书... | 22:52 块 (差 4) |
| 22:57:00 | 位置消息（独立） | 22:57 独立节 |
| 22:58:00 | 只写入完整的地址信息... | 22:58 块起 (差 6 超) |
| 22:59:00 | 在每一次我给你发... | 22:58 块 (差 1) |
| 23:00:00 | 如果我给你发了地址... | 22:58 块 (差 2) |
| 23:01:00 | 位置消息（独立） | 23:01 独立节 |
| 23:02:00 | 把地址写到二级标题... | 22:58 块 (差 4) |
| 23:04:00 | 我发给你地址的时候... | 23:04 块起 (差 6 超) |
| 23:05:00 | 把日记按照5分钟分段... | 23:04 块 (差 1) |
| 23:07:00 | A方案 | 23:04 块 (差 3) |
| 23:09:00 | a2 方案 | 23:04 块 (差 5 含边界) |

## Final block order (倒序)

```
## 23:04:00
[4 lines, oldest at top, newest at bottom]
## 23:01:00 — 蓝天绿地商务广场
## 22:58:00
[4 lines]
## 22:57:00 — 上海市静安区...
## 22:52:00
[5 lines]
## 22:46:00
[4 lines]
## 22:40:00
[2 lines]
```

## Pseudo-code

```python
def insert(message, file_blocks):
    if message.type == 'location':
        return prepend_standalone_block(file_blocks, message)
    # text path
    cleaned_body = strip_trigger_words(message.text)
    if not cleaned_body:  # only trigger words, no body
        return file_blocks  # skip
    
    # find most recent text block
    last_text = find_last_text_block(file_blocks)
    if last_text and (message.time - last_text.start) <= timedelta(minutes=5):
        # merge: append body at end of last_text
        return append_to_block(file_blocks, last_text, cleaned_body)
    else:
        # new block
        return prepend_new_block(file_blocks, message.time, cleaned_body)
```

## Edge cases

- **Same-second duplicates**: keep the latest `message_id` (or last received); drop earlier
- **跨午夜**: 文件名 `YYYY-MM-DD.md` 用北京日期；如果上一条 block 在 23:58，下一条 00:01 差 3 分钟 = 应合并，但文件日期已变 → **新建文件**（00:01 块在新文件）
- **5:00 边界** (含): 入**上一** block (e.g. 23:09:00 vs 23:04:00 块 → 5:00 整 → 入 23:04 块)
- **5:01 边界** (含): 入**新** block
