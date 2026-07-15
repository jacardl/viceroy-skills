# 2026-06-17 · Anthropic Claude Code 40 万会话研究 · 实战 case

**素材**：Anthropic 2026-06-16 报告《Agentic coding and persistent returns to expertise》
（https://www.anthropic.com/research/claude-code-expertise）

**字数**：4785 中文字符（zhililong 硬下限 4000 ✓）

**结构**：5 节主体 + 1 反转 + 1 行动（zhililong 默认 7 节模板）

## 关键决策（renwei 风格典型案例）

### 1. 反常识切入选"程序员正在变成普通职业"
- **错误选择**：AI 让程序员越来越值钱（这是大众预期，no 反常识）
- **正确选择**：AI 让所有职业都能干程序员的事，程序员不再是特殊群体
- **关键句**："5 类职业干程序的活不输工程师" — 律师、管理者、医生、会计、设计师

### 2. 加粗策略：5 处关键词加粗（每节 1 处），不是段落级加粗
- 命中"干编程这件事的成功率都差不多"（第二节）
- 命中"它干活"（第三节，工作重心迁移）
- 命中"判断"（第四节，专长真实形状）
- 命中"80% 的事，懂一点就够 Claude 用了"（第五节）
- 命中"看你懂不懂你干的那件事"（行动段）

### 3. 反 AI 词全部清零
- "非常"全部 → "特别"或删
- "值得"全部 → "配得上"/"该带走"/"有意思的是"
- 替换 5 处后命中 = 0

### 4. "判断越来越值钱"被重写
- 错误：写成"你做判断，AI 做执行。你做判断，AI 做执行"（排比套话）
- 正确：写成"你出题，AI 答题"循环（具体动作）

## 微信发布参数

- **标题**：40 万次对话重看程序员（10 字，≤10 ✓）
- **作者**：刘生（2 字 ✓）
- **摘要**：Claude Code 40 万次会话：专长回报持续。（49 字节，≤54 ✓）
- **封面 thumb_media_id**：`kiuyle4KZHC7JKxpTQssMIJ2t12oakt0X_H3Q9saAOFIyPT1sDUOKN2Vazw2FUa6`
- **草稿 media_id**：`kiuyle4KZHC7JKxpTQssMGPU_6_p_lP9hPZi-MC8dIHJYBozZjzlcvzIRc5BOK0_`

## 关键踩坑（已 patch 到 skill）

1. **publish_zhili.py CLI 模式 + `$(python3 -c "...")` 嵌套失败**
   - 根因：`terminal()` 工具双引号字符串里反斜杠转义先被 bash 吃掉一层
   - 解决：放弃 CLI，**直接 import 内部函数**（已写进 zhili-publish SKILL.md）

2. **mmbiz Gate 强制图片**
   - v1 长文原本没图，脚本拒绝发布（`'mmbiz' in content` 检查）
   - 解决：紧急用 PIL 画一张"专长回报曲线"信息图（900×540，4 点折线）
   - 设计选择：把配图放在第 4 节"专长真实形状"前（曲线图 = 讲这节）

3. **digest 字节数严格 ≤54**
   - UTF-8 中文 = 3 字节/字，数字/英文 = 1 字节
   - 测试 1: "Anthropic 用 40 万次 Claude Code 会话证明..." → 90 字节（超）
   - 最终: "Claude Code 40 万次会话：专长回报持续。" → 49 字节 ✓

## 落点

```
/Users/apple/Projects/New-Radar/Final Report/transcripts/anthropic-claude-code-expertise/
├── 公众号-claude-code-40万会话研究.md          (审稿版)
├── 公众号-claude-code-40万会话研究-body.md     (纯正文 7 节)
├── 封面图-claude-code-40万会话研究.jpg         (900×540)
└── 配图-专长回报曲线.jpg                       (900×540, 4 点折线)
```

## 数据校对（已写入正文）

| 数据点 | 数值 | 来源 |
|--------|------|------|
| 总会话数 | 40 万次 | 报告摘要 |
| 用户数 | 23.5 万 | 报告摘要 |
| 时间窗口 | 2025-10 至 2026-04 | 报告方法学 |
| 职业分布 | 70% 可推断 | 报告 §2 |
| 软件工程师占比 | 30% | 报告 §2 |
| 其他职业占比 | 26% | 报告 §2 |
| 任务价值涨幅 | +27% | 报告 §3 |
| building 涨幅 | +43% | 报告 §3 |
| operating 涨幅 | +34% | 报告 §3 |
| fixing 涨幅 | +32% | 报告 §3 |
| 7 个月任务分布：debug | 33% → 19% | 报告 §3 |
| 7 个月任务分布：运维 | 14% → 21% | 报告 §3 |
| 7 个月任务分布：分析写作 | 10% → 20% | 报告 §3 |
| 人 planning vs execution | 70% / 20% | 报告 §3 |
| 专长 5 级：新手成功率 | 15% | 报告 §4 |
| 专长 5 级：中级成功率 | 28-30% | 报告 §4 |
| 专长 5 级：专家成功率 | 33% | 报告 §4 |
| 放弃率（新手 vs 专家） | 19% vs 5-7% | 报告 §4 |

## 关键金句（反转段引用）

> "Coding agents are not substituting for domain expertise; the more understanding a worker brings to an agent, the more quality work the agent is able to do."

— Anthropic 报告 §5 核心洞察

## 复盘价值

这次任务是 zhililong **首次跑通"无视频素材 + 直接 URL 抓文章"** 的完整流程（含 Step 8 发布）。以前都是从视频/音频转写出发的，这次证明了 zhililong 也适用于"任何可解析的文本源"。

也证明了：**zhililong 默认结构 7 节（5+1+1）适用于非视频/非教程类内容**（如行业研究报告、人物特写、社会观察）。
