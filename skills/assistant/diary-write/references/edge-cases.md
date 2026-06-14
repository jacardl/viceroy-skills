# Edge Cases (11 from 2026-06-14 session)

## 1. 触发词剥离边界 (LRN-20260614-005)

**Q**: 佳哥发"写日记，我刚才看了希特勒的电影" → 写啥？

- ✅ 推荐 A: 只写后半段"我刚才看了希特勒的电影"
- ❌ 整条照写（含"写日记"）
- ❌ 加润色 / 拼写修正

**实施**: 用正则替换 (中文触发词列表)

## 2. 节标题"只时间" vs "时间+摘要" (LRN-20260614-005/006)

- 旧 005: 标题用摘要 (例 `## 22:50 — 看了希特勒的电影`)
- 新 006: 标题**只** `HH:MM:SS` (例 `## 22:50:00`)
- 后续位置节用 `## HH:MM:SS — 名称` (LRN-20260614-009)

**实施**: 节标题生成 = 字符串模板，不做语义分析

## 3. 重复消息 (LRN-20260614-010 同秒去重)

**Q**: 23:03 + 23:04 同原文"我发给你地址的时候..."两条都收到

**实施**:
- 飞书 inbound 给 messageId
- 维护 in-memory recent_messages (last 5 min) by content hash
- 同内容同秒 → 丢弃早的
- 5 分钟后清缓存

## 4. 跨午夜

- 上条 block 23:58, 下条 00:01 → 差 3 分钟
- 应合并到 23:58 块
- 但**文件已变** (00:01.md vs 23:58.md)
- **处理**: 跨午夜的差 < 5 分钟 = 写新文件，不跨文件合并
- 例外: 00:00 之前发的写入 23:58.md; 00:00 之后写入 00:00.md

## 5. 5 分钟边界歧义

- 严格 < 5: 23:09 - 23:04 = 5:00 不算入 → 错误（应入）
- 严格 <= 5: 23:09 - 23:04 = 5:00 算入 → 正确
- **统一用 <=**

## 6. exec 输出被吞 (LRN-20260614-003)

- `cat file` 输出被 zsh 解析成 `8 matches in 2F` 模式
- `## ` 在文件里被 zsh 当 recursive glob
- `sed -n '1,200p' file` 同样被吞
- 兜底:
  ```bash
  awk '{printf "L%d|%s\n", NR, $0}' file | head -N
  ```
  用 `L%d|` 前缀避开 `##` glob 解析
  - 或: `python3 -c "print(open('f').read())"`
  - 或: `read` 工具 with offset/limit

## 7. heredoc + docker exec psql 解析 bug (LRN-20260611-002)

- `docker exec radar-db psql <<EOF ... EOF` 被 OpenClaw exec 解析吞
- INSERT 不执行但无报错
- **统一改用** `echo "INSERT SQL;" | docker exec -i radar-db psql -U radar -d radar`
- 写后必须 `SELECT COUNT(*)` 复核

## 8. 飞书消息 payload 字段截断

- `message.action=read` 拿不到 message_type
- 位置消息的 `contentType: "text"`, `content` 才是 JSON
- **识别**: `content` 解析 JSON, 看有没有 `longitude` 字段

## 9. 凭据 inline 脚本模式 (LRN-20260613)

- 涉及 access_token / AppSecret 等敏感数据
- 用一次性脚本 `/tmp/_<task>_YYYY-MM-DD.py`:
  1. 凭证 inline 写脚本
  2. `tee > log.txt` 全程写盘
  3. 跑完 `rm -f` 清理
- 结果 (mmbiz URL / thumb_media_id) 落盘到另一个文件，**不含 token**

## 10. 触发词识别冲突

- 文字"今天我要写日记记流水账" → 含"写日记"+含"记" → 触发
- 但"日记" 出现在句子中间，剥离会断句
- **策略**: 只剥离**句首**的触发词 + 紧跟的逗号/冒号
  - 正则: `^(写日记|记到 obsidian|obsidian 日记|写入 obsidian)[，,：:]?\s*`
- 中间出现"日记" 保留

## 11. 位置消息多选点

- 飞书客户端可一次选多个位置（罕见）
- 目前处理: 第一条 location 消息独立节
- 多选点: 后续每条都独立节 (按各自时间戳)
- 未来可加: 同一秒多个位置 = 合并到一个独立节 (多条 `## HH:MM:SS — name1` `## HH:MM:SS — name2`)
