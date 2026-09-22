# Production Changelog v4.x — radar 采集脚本历史修复记录

> 本文档记录 radar-data-collection 在 v4.x 阶段的字段索引 / 数据源 / 改写链修复历史。
> 当前生产脚本（`~/.shared-agent-skills/operations/radar-data-collection/scripts/`）
> 已是最新版，但历史 bug 修复逻辑值得保留，方便未来字段再变动时回溯。

## v4.1（2026-08 初）— 字段索引关键修正

### 国际金价（hf_GC，腾讯财经）
- 原始字段数组：`var hq_str_hf_GC="4071.592,,4072.100,4092.400,4069.200,..."`
- **v4.1 关键修正**：
  - `[0]` = 当前价（USD/oz）
  - `[1]` = 涨跌额（USD）
  - **`[5]` = 昨收（USD）** ← **不是 [4]**，v4 错用 [4] 算出 0 或乱值
- `intl_price_change` = `(今-昨)/昨 × 100%`（百分比，不是绝对额）

### 国内金价（东财 push2.eastmoney.com f43/f60/f169/f170）
- **v4.1 关键修正**：
  - `f43` = 最新价（分，÷100 转元/g）
  - **`f60` = 昨收（分，÷100 转元/g）** ← **不是 f170**，v4 错用 f170 当昨收算出 5 万%
  - `f169` = 涨跌额（分，÷100 转元/g）
  - `f170` = 涨跌幅 × 100（÷100 转百分比）

## v4.3 — GitHub content 字段停写 + description 中文改写（2026-08-08）

**变更**：
- 停写 `content` 字段（v4.1 之前塞的 `Language/Total Stars/Stars Today/...` 拼接 metadata 文本）
- `description` 改为中文：gh_collect.py 新增 `_gen_zh_desc(text)` helper
- 调 9Router `minimax-cn/MiniMax-M3` chat（`max_tokens=220, temperature=0.2, timeout=15s`）
  把英文 repo desc 改写为 80-150 字中文简介
- 已是中文时跳过 chat（节省配额）
- 失败 fallback 英文原文前 200 字（0 阻断）

**写入字段（v4.3）**：`title` / `description`(中文) / `source`(=lang) / `url` /
`lang`(=en) / `blacklist_score` / `stars_count` / `period_new_stars` /
`is_new_project`（**❌ 不再写 `content`**）

## v4.1 description 字段修复历史（GitHub）

- 早期 v4 塞了 `* N today | total* N | lang | desc[:80]` 拼接文本
- v4.1 改为纯 `desc[:300]`
- v4.3 再升级为 chat 改写中文

## 写入字段映射（生产环境，v4.3）

| 类目 | 写入字段 |
|------|----------|
| AI | `title` / `content` / **`summary`** / **`description`** / `source` / `url` / `lang` / `blacklist_score` / `region` |
| GitHub | `title` / **`description`**(中文) / `source`(=lang) / `url` / `lang`(=en) / `blacklist_score` / `stars_count` / `period_new_stars` / `is_new_project` |

## `gold_note` 字段格式（已验证 2026-09-05）

```
采集于 2026-09-05 | 国际GC=$4484.26 (+1.64%) | 国内AU9999=¥958.00 (-0.82%) | 美10Y TIPS=4.780% (+0.010pp)
```

验证金价时直接查 `gold_note` 即可获取完整汇总。

## 脚本路径历史

- **早期（v4.x 之前）**：脚本权威源在 `~/.openclaw/workspace/scripts/radar/{collect.py, gh_collect.py}`
- **v4.x**：skill 内 `scripts/` 是 symlink，指向 workspace 路径
- **2026-09 当前**：权威源已迁至 `~/.shared-agent-skills/operations/radar-data-collection/scripts/`
- **修改原则**：只改 shared 路径，symlink 自动同步

## 警示：v4.x 注释里的「脚本统一声明」是过时的

如果未来再看到 SKILL.md / 注释里出现以下表述，说明是 v4.x 残留：
- `~/.openclaw/workspace/scripts/radar/` ← 该路径已不存在
