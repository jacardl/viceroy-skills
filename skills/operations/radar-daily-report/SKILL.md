---
name: radar-daily-report
description: "从 radar DB 读取今日数据，发送金价+AI+GitHub 三条飞书消息"
metadata: { }
---

# 雷达每日报告推送

执行入口：直接运行本 skill，由 cron `fbfedc879847`（每日 06:00 CST）触发。

## 执行脚本

```
python3 ~/.shared-agent-skills/operations/radar-daily-report/scripts/push.py
```

脚本输出格式（stdout）：
```
===MSG1===
<金价消息>

===MSG2===
<AI消息>

===MSG3===
<GitHub消息>

===META===
date=YYYY-MM-DD dow=N report_type=daily|weekly|monthly ai=X gh=X gold_ok=true|false
```

## 数据字段映射（push.py 读取规则）

### gold_prices 表

| DB 字段 | push.py 读取 | 显示 |
|---------|-------------|------|
| `intl_price_usd` | float | $X,XXX.XX /盎司 |
| `intl_price_change` | float（**百分比%**） | ±X.XX% |
| `domestic_price_cny` | float | ¥XXX.XX /克 |
| `domestic_price_change` | float（**百分比%**） | ±X.XX% |
| `tips_yield_10y` | float | X.XXX% |
| `tips_yield_change` | float（基点差 pp） | ±X.XXXpp |
| `gold_note` | text | 附在表格下方 |

> ⚠️ `intl_price_change` / `domestic_price_change` 存的是**百分比值**，非绝对额。
> 由 collect.py 在入库时计算：**(今-昨)/昨 × 100%**

### news_articles 表（所有 category）

读取方式：`SELECT row_to_json(...)` — 按字段名访问，不依赖分隔符。

| category | 读取字段 | 显示 |
|----------|---------|------|
| `ai` | title / **description** / source / url / blacklist_score | 序号 · 标题 · 热度分 · 来源 + 摘要 |
| `github` | title / **description**(中文) / source(=lang) / url / **stars_count** / **period_new_stars** / blacklist_score | 黑马分 · 今日+⭐ · 总⭐ + 中文简介 |

## 消息发送

### 两种触发方式，发送机制不同

| 触发方式 | 发送机制 | 操作 |
|---------|---------|------|
| cron `fbfedc879847`（每日 06:00 CST） | **cron 自动投递**（final response 直接送达飞书） | 将 ===MSG1/2/3=== + ===META=== 完整输出为 final response，不调用 send_message/hermes send |
| 手动 / 交互式会话 | 需要显式调用 send_message | 解析 push.py 输出，逐条发到 `feishu:oc_cc7fb62a9fa4c081ada01dfa60af669d` |

**本次会话是 cron 触发（2026-09-14 实测）**：执行 `hermes send` 或 `send_message` 时系统直接拒绝：
> "Skipped send_message to feishu:... This cron job will already auto-deliver its final response to that same target."
正确做法：**把 5 段输出（===MSG1/2/3 + ===META===）完整写入 final response**，cron 投递系统自动发送。

### 交互式会话的消息发送步骤

**铁律：必须实际分成 3 条独立消息发送，禁止用分割线（---/===/‖）合并为单条消息。**

解析脚本输出后，逐条调用 send_message 发送飞书：
- ===MSG1=== → send_message（金价）
- ===MSG2=== → send_message（AI）
- ===MSG3=== → send_message（GitHub）

#### send_message target 格式（铁律，必看）

裸 `target="feishu"` **会失败**，返回 `[230001] invalid receive_id`。

正确格式：`target="feishu:<chat_id>"`。本任务默认 chat_id 是 `oc_cc7fb62a9fa4c081ada01dfa60af669d`。

两种写法二选一：
1. **显式 chat_id**（推荐）：
   `send_message(target="feishu:oc_cc7fb62a9fa4c081ada01dfa60af669d", message=..., action="send")`

2. **裸平台名**：仅当 `send_message(action="list")` 返回无后缀的 `feishu:` 条目时才用。

#### 失败诊断顺序

若 send_message 报 230001：
1. 立即 `send_message(action="list")` 查可用 target
2. 选 home DM chat_id（`feishu:oc_cc7fb62a9fa4c081ada01dfa60af669d`）重发
3. 不要重复裸用 `target="feishu"` 重试（不会变成对）

## 存档

```
mkdir -p ~/.shared-agent-skills/operations/radar-daily-report/archives
# 消息内容存档到 ~/.shared-agent-skills/operations/radar-daily-report/archives/YYYY-MM-DD.md
```

## 异常处理铁律

**核心原则：永远发送日报，数据不完整时在对应消息中标注问题，不阻塞推送。**

### 数据缺失标注规则

| 条件 | MSG 处理 | 标注 |
|------|---------|------|
| gold_ok=false | MSG1 | 「⚠️ 金价数据缺失」 |
| ai < 5 | MSG2 | 「⚠️ AI热讯数据缺失」 |
| gh = 0（3次重试后） | MSG3 | 「⚠️ GitHub数据缺失」 |
| gh 1-9（3次重试后） | MSG3 正常发送 | 「⚠️ GitHub今日源数据仅N条」（不阻塞） |

### 禁止规则
- **禁止独立抓取补充数据**（已在采集阶段完成重试，仍不足则接受现状）
- **禁止 fallback 旧数据**（必须用今日采集数据）
- **禁止因数据不完整而跳过发送**（只要有任何数据就发送，缺失部分标注）

## Cron Prompt vs SKILL.md 漂移陷阱（2026-09-13 实测）

**铁律**：SKILL.md 写的策略在 cron 场景下**必须同步到 cron job 的 prompt 字段**，否则 LLM 看到 prompt 直接照办，**完全无视** SKILL.md。

**已发生事故**：本 skill SKILL.md 明文写「永远发送日报，数据不完整时在对应消息中标注问题，不阻塞推送」，但 cron job `fbfedc879847` 的 prompt 字段塞了 STEP 0 预检查：任意一项不达标 → "仅发一条「采集未就绪，今日不推送」警告...不再跑 push.py，直接 return"。结果是 gold 缺失 = 0 日报推送（用户只收到一句"不推送"告警）。

**预防**：
1. 改 SKILL.md 任何铁律时，**同时** grep `~/.hermes/cron/output/fbfedc879847/` 历史输出，确认 cron prompt 没在旧 prompt 里写反逻辑
2. 改 cron prompt 时，**必须**在 prompt 里复述 SKILL.md 的核心铁律，不能假设 LLM 会读 SKILL.md
3. 验证 cron prompt 修改效果：手动模拟 gold=0 / AI=0 / GH=0 三种场景，确认 push.py 的标注行为真的执行（不要只看 cron last_status="ok"）
4. 验收 grep（任何一天的 daily-report cron 输出）：
```bash
grep -c "send_message" ~/.hermes/cron/output/fbfedc879847/<今日>.md  # 应 ≥3
grep -c "采集未就绪" ~/.hermes/cron/output/fbfedc879847/<今日>.md  # 若 >0 → STEP 0 abort 触发
```

**已修复**：cron prompt 改为 STEP 0 只跑数据查询做观测，不 abort，全部交给 push.py 内置的 gold_ok=false / ai<5 / gh=0 标注逻辑处理。

### 验收方法

cron `fbfedc879847` 输出验证：
```bash
# cron 触发（auto-delivery）：grep ===MSG1/2/3/META 出现在最终输出
grep -c "===MSG1===" ~/.hermes/cron/output/fbfedc879847/<今日>.md  # 应 ≥1
grep -c "采集未就绪" ~/.hermes/cron/output/fbfedc879847/<今日>.md  # 若 >0 → STEP 0 abort 触发
```

交互式会话验证：
```bash
grep -c "send_message" <当日输出>.md  # 应 ≥3（每条消息一次）
```

见 `references/approved-template.md`。

版式铁律（佳哥拍板，2026-06-17）：
- ❌ 代码块 ❌ English Headline ❌ 中英对照
- ✅ 金价用 Markdown 表格（**涨跌列为百分比%**）
- ✅ GitHub 必须含今日新增⭐ + 总⭐ + 中文简介（取 description 字段）

## ⚠️ SKILL.md 铁律与 cron prompt 冲突陷阱（2026-09-13 实测）

本 SKILL.md 的「异常处理铁律」明确：**永远发送日报，数据不完整时在对应消息中标注问题，不阻塞推送**。但 cron `fbfedc879847` 的 prompt 里塞了 STEP 0 预检查："任意一项不达标 → 仅发一条「采集未就绪，今日不推送」...直接 return"。

**冲突后果**（2026-09-13 实测）：gold 缺失 → STEP 0 abort → 当日 0 日报，用户收到的是「不推送」告警，不是日报。

**改 cron prompt 时**：
- 若保留 STEP 0，必须在本 SKILL.md 同步加「中止条件」表格
- 若想保留「always send」铁律，从 cron prompt 删除 STEP 0 整个块，让 LLM 直接遵循本 SKILL.md 的标注表
- 改完后用 `~/.hermes/cron/output/fbfedc879847/<日期>.md` 验证：是否真的 grep 到 `===MSG1===`/`===MSG2===`/`===MSG3===` 三段被 send_message 发出

详见 `~/.hermes/skills/operations/radar-pipeline/SKILL.md` 的「cron 配置陷阱」章节。
