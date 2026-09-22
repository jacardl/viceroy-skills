# send_message 推送常见坑（2026-09-04 实测）

## 坑 1：裸 `target="feishu"` 触发 230001

**症状**：
```
Feishu send failed: [230001] Your request contains an invalid request parameter, ext=invalid receive_id
```

**原因**：send_message 要求 target 是 `<platform>:<chat_id>[:<topic>]` 形式；裸平台名只在 home channel 已注册且无歧义时才生效。

**修复**：用 `target="feishu:oc_cc7fb62a9fa4c081ada01dfa60af669d"`（home DM chat_id，写在 USER_PROFILE memory 里）。

**不要做**：连续 4 次裸 `target="feishu"` 重试 — 不会变对，直接 list → 选 chat_id → 重发。

## 坑 2：loop warning 触发条件

连续 ≥3 次同工具同错失败会触发 `tool_loop_warning`。本次踩到 4 次（4 条消息同错）。即便循环警告触发，**不要切换到纯文本回复**，继续用工具但换参数。loop warning 是诊断信号，不是工具禁用信号。

## 坑 3：4 条独立推送 vs 单条合并

skill 铁律禁止分割线合并。即便 4 条都失败重试，也要保持 4 次独立 send_message 调用，而不是把 4 条塞进一条 markdown 里发。

## 历史故障时间线

- 2026-09-04：首次发现 target 格式问题，4 条 MSG 全部 230001 → list 诊断 → 用显式 chat_id 重发成功 → 已写入 SKILL.md 主体。
