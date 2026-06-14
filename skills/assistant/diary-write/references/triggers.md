# Trigger Words & Message Types

## Inbound classification (Flybook / 飞书)

### Type 1: Location message (触发)

Client UI: `+` button → 位置 → select point → send.

飞书 MCP `message.action=read` payload example (2026-06-14 23:01):
```json
{
  "messageId": "om_x100b6dd86b741ca0b11625c6406cfed",
  "chatId": "oc_cdff0f5cfb6d9fc770005a23ffccb372",
  "senderId": "ou_5ded4476a110b6eccdeafdc6ea3cf3b2",
  "contentType": "text",  // ← 位置消息也被标成 text!
  "content": "{\"name\":\"蓝天绿地商务广场\",\"longitude\":\"121.460947\",\"latitude\":\"31.263692\"}",
  "createTime": 1781448961000
}
```

**关键识别**: `content` 是 JSON 字符串 + 含 `longitude`/`latitude` 字段。

**写入规则**:
- 标题: `## HH:MM:SS — <name>`
- 正文: 空（地址已在标题里）
- 绝不写经纬度
- 独立节，不合并

### Type 2: Trigger-word text (触发)

Client UI: 文字输入 → 包含以下任一触发词 → 发送。

触发词（按 23:00 当日最终版）:
- `日记` (核心最短)
- `写日记`
- `记到 obsidian`
- `obsidian 日记`
- `写入 obsidian`

**识别方法**: 正则 `日记` (中文) / 上述英文变体。

**写入规则**:
1. 触发词从 `content` 中删除（仅触发词部分，正文保留）
2. 标题: `## HH:MM:SS` (无破折号)
3. 正文: 触发词剥离后的原文
4. 正文为空 (只有触发词) → **不写** (skip)

### Type 3: 其他 (不触发)

- 普通文字问候 / 确认回执 / 闲聊 → skip
- 规则类消息（"X 是 Y 规则"）→ skip（按 LRN-20260614-011）
- 飞书 image / file / audio → skip
- 富文本消息（带 @ / 表情）→ 仅 `text` 部分 + 触发词判定

## Timezone 关键陷阱

- OpenClaw runtime = UTC
- isolated session **不继承** 主机时区
- **必须** `export TZ=Asia/Shanghai` **第一行** prompt
- 文件名日期 = 北京日期（不是 UTC）
- createTime 字段 = 毫秒 UTC 时间戳
- 取 createTime → 转北京时间 = `createTime/1000 + 8*3600` (粗糙) → 用 `date -d @<秒> '+%Y-%m-%d %H:%M:%S' -u` + 8 hour

## 飞书 MCP 读消息限制 (重要!)

**不能列历史消息** (read needs explicit messageId). 流程:
- inbound 事件 = 单条 user 消息，含 messageId
- 不能主动拉用户之前发的位置 / 历史
- 处理逻辑: 收到一条 → 判断 → 写一条
- 缓存: 自己 memory 记最近一次 position 留作 fallback (但只在新触发条件允许时才用)
