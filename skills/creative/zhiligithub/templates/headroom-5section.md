# 5 段式 Markdown 写作模板（zhiliGitHub 黑马项目介绍）

> **适用**：单项目 GitHub 黑马介绍（chopratejas/headroom 类）
> **字数**：纯中文 1500-2000 字（不含代码块）
> **结构**：1 开头段（无 H2）+ 5 编号段（01-05，共 5 个 H2）
> **首次验证**：2026-06-04 headroom 9.5k 实战
> **用法**：复制本文档，替换 `[占位符]`，按 H2 数字顺序写每段

---

## 📐 段位结构 + 字数预算

| 段 | 章节 | 字数 | 必含元素 |
|---|------|------|----------|
| 开头 | 项目名 + meta + 一句话定位 + 痛点钩子 | 200-280 | 1 句震撼数据 + meta 行（GitHub / Stars / 语言） |
| 01 | 它能做什么 | 250-350 | 三层用法 / 兼容性 / 杀手锏 |
| 02 | 它怎么做到的 | 300-400 | 架构 / 关键模块 / 设计亮点 |
| 03 | 怎么用 | 150-250 | 一行命令 / 代码块主导（2-3 个） |
| 04 | 实测数据 | 200-300 | 真实 workload 压缩比 + 准确度数据 |
| 05 | 它凭什么是黑马 | 300-400 | 升维观察 + 适合谁/不适合谁 + Star 号召 |

**总字数校验**：`len(re.sub(r'[^一-鿿]', '', text))` 应在 1500-2000。

---

## 📝 模板正文（复制后替换 `[xxx]`）

### 开头段（无 H2，200-280 字）

```
最近在找 [解决某类问题] 工具的时候，发现了一件有意思的事：

[项目英文名]（[项目中文名]）—— [GitHub 链接]—— 上线 [N 天]，star 涨了 [N k]，直接干到了 [大数字]。

[用 1 句震撼数据开场，最好是 "X → Y，压缩 N%" 的对比 / "X 万 token → Y 千 token" 的实测量级]

[一句话项目定位：它是个 [品类] 工具，跟 [同类] 不一样的点是 [一句话差异]。

[一句话痛点钩子：它解决的核心痛点是 [具体场景] 下 [痛点描述]。
```

**示例（headroom）**：
> 最近在写一个 agent 项目的时候，发现了一件有意思的事：
>
> chopratejas/headroom（headroom）—— github.com/chopratejas/headroom—— 上线 22 天，star 涨了 9.5k，**今日单日 +3,528**。
>
> 它号称能把 LLM 的输入 token 压掉 60-95%，且**不丢准确度**。
>
> agent 时代最缺的是什么？context window。一个 Claude Code 会话 65,694 token 才能讲清的事，headroom 给你压到 5,118 token 还能讲同样清楚。

---

### 01 它能做什么（250-350 字）

```
## 01 [动词]：三层用法，零代码也能上手

[一段话总述：[品类] 不只是"装一个库"的事，它有三种用法覆盖不同人群]

[用法 1（库/SDK）]：
[一句话定位]：
[一段代码块 — install + import + 1 行核心调用]

[用法 2（代理/Proxy）]：
[一句话定位]：
[一段代码块 — 启动命令 + 端口]

[用法 3（包装/wrap）]：
[一句话定位：兼容 [N 个主流 agent]，无需改代码]
[一段代码块 — wrap 一行命令]

[一句话杀手锏]：[它跟 [同类] 不一样的点是 [独占特性 1-2 个]]
```

**示例（headroom）**：
> ## 01 三种姿势：库、代理、wrap，零代码也能上手
>
> headroom 不是只能"装个库"。它有三种姿势覆盖不同人群。
>
> **第一种，库**。pip install headroom，from headroom import compress，调一行 compress(messages)，把消息列表丢进去就压完了。
>
> **第二种，代理**。headroom proxy --port 8787 开一个本地代理，所有 [agent 框架名] 流量走它，自动透明压缩。
>
> **第三种，wrap**。一行命令 headroom wrap claude，原本的 Claude Code 不用改一行代码，就接入了压缩层——同样支持 codex、cursor、aider、copilot。
>
> 它最让我眼前一亮的不是"压得多"，是 **CCR**——可逆压缩。压缩后的 token 看起来是删掉了一些，但原文本地留着，需要时能 1:1 还原。

---

### 02 它怎么做到的（300-400 字）

```
## 02 [设计名/架构名]：[核心机制一句话]

[一段话总述：[品类] 的核心机制是 [机制名]，它解决了 [传统方案] 的 [局限]。

[架构三件套，**用散文化叙述，不要用 markdown 表格**（表格转 HTML 会被当 p 渲染成脏行）]：

第一件是 [模块 1]。[一句话功能]。

第二件是 [模块 2]。[一句话功能]。

第三件是 [模块 3]。[一句话功能]。

[核心创新 / 杀手锏的 1-2 句解释 + 为什么这设计巧]

[一句话收束：这架构的优势是 [N 大点]——压缩率/可控性/兼容性/可调试性]
```

**表格散文化公式**（避免 markdown 表格转 HTML 渲染问题）：
- ❌ 表格：`| 场景 | 压缩前 | 压缩后 | 比例 |`
- ✅ 散文化："最猛的两个场景是 [场景 A] 和 [场景 B]，第三猛是 [场景 C]。[场景 A] 从 [X token] 压到 [Y token]，**省 N%**。"

**示例（headroom）**：
> ## 02 CCR：可逆压缩 + 6 种 compressor + 杀手锏 headroom learn
>
> headroom 的核心机制叫 **CCR**（Cache-Conscious Reduction），三个组件串成一条流水线。
>
> 第一件是 **CacheAligner**。它把消息按 cache 边界对齐，避免 LLM 的 prompt cache 失效——这个不起眼，但很多压缩方案压完发现 cache miss 反而更慢了，CacheAligner 直接绕开这个坑。
>
> 第二件是 **ContentRouter**。消息丢进来后它判断"这段该用哪种 compressor"——是带代码的丢给 code compressor，是对话的丢给 dialogue compressor，是 JSON 数据的丢给 json compressor。
>
> 第三件是 **CCR 本身**。它的关键设计是"原文本地保留"——压完看起来 token 少了，但实际原文在另一个 store 里，需要时能 1:1 还原。
>
> 配合 6 种 compressor（code / dialogue / json / tool-call / search-result / RAG-context）按需调用，CCR 已经是相当工程化的设计。
>
> 但真正的杀手锏是 **`headroom learn`**。它能挖你过去失败的 session 总结成"什么 prompt 会让 agent 跑偏"的经验，写进 AGENTS.md——这个压缩不是"省 token"，是"让你的 agent 不再犯同样的错"。
>
> 加上**跨 agent memory**（跨 Claude/Codex/Gemini，自动去重），headroom 已经从"压缩工具"变成"agent 经验管理平台"。

---

### 03 怎么用（150-250 字）

```
## 03 怎么用：一行命令的事

[一段话铺垫：60 秒 onboarding]

**安装**（[一行]）：
[代码块]

**开代理**（[一行]）：
[代码块]

**接 MCP**（[一段 JSON]）：
[代码块]

**wrap 你的 agent**（[一行]）：
[代码块]

[一句话收束：开箱即用，不需要改现有代码]
```

**示例（headroom）**：
> ## 03 怎么用：60 秒的事
>
> ```bash
> pip install headroom
> ```
>
> 开代理：
>
> ```bash
> headroom proxy --port 8787
> ```
>
> 接 MCP server（给 Claude Desktop / Cursor 用）：
>
> ```json
> {"mcpServers": {"headroom": {"command": "headroom", "args": ["mcp"]}}}
> ```
>
> wrap 你的 Claude Code：
>
> ```bash
> headroom wrap claude
> ```
>
> 就这样，不需要改现有任何代码。claude / codex / cursor / aider / copilot 都支持。

---

### 04 实测数据（200-300 字）

```
## 04 实测数据：真的能省这么多吗

[一句话铺垫：[品类] 压缩率吹得猛，实测数据怎么样？]

**4 个真实 workload 的压缩比**（**用散文化**）：
- 最猛的是 [场景 A]，[X token] 压到 [Y token]，**省 N%**。
- 第二猛是 [场景 B]，[X token] 压到 [Y token]，**省 N%**。
- 第三个是 [场景 C]，[X token] 压到 [Y token]，**省 N%**。
- [场景 D] [X token] 压到 [Y token]，**省 N%**。

**准确度不掉**（**用 4 个 benchmark 散文化**）：
- [Benchmark 1] 原始 [X]，压缩后 [Y]，**±N**。
- [Benchmark 2] 原始 [X]，压缩后 [Y]，**+N**。
- [Benchmark 3] 原始 [X]，压缩后 [Y]，**+N% 压缩**。
- [Benchmark 4] 原始 [X]，压缩后 [Y]，**+N% 压缩**。

[一句话收束：这些数据 [来源] 复现命令是 [一行]]
```

**示例（headroom）**：
> ## 04 实测数据：真的能省这么多吗
>
> headroom 团队在 4 个真实 workload 上跑了对比：
>
> - 最猛的是 **SRE 事故调试**，65,694 token 压到 5,118 token，**省 92%**。
> - 第二猛是**代码搜索**，17,765 token 压到 1,408 token，**省 92%**。
> - 第三个是 **GitHub issue triage**，54,174 token 压到 14,761 token，**省 73%**。
> - **代码库探索** 78,502 token 压到 41,254 token，**省 47%**。
>
> 关键问题：压这么多，模型还答得对吗？4 个 benchmark 数据：
>
> - **GSM8K** 0.870 ± 0（基本不掉）。
> - **TruthfulQA** 从 0.530 升到 0.560，**+0.030**（还涨了）。
> - **SQuAD v2** 97% 准确度，**+19% 压缩**。
> - **BFCL** 97% 准确度，**+32% 压缩**。
>
> 复现命令：headroom benchmark --suite sre-debug --compression-ratio。
>
> 数据来源：[GitHub repo](https://github.com/chopratejas/headroom)，2026-06-04 验证。

---

### 05 它凭什么是黑马（300-400 字）

```
## 05 它凭什么是黑马：[升维观察一句话]

[一段话总述：跟 [同类] 比起来，headroom 的本质区别是 [一句话升维判断]。这反映了 [行业大趋势] 的一个关键变化——[2025 → 2026 的转折]。

[一段话"为什么这件事重要"：从 [旧范式] 进化到 [新范式]，核心驱动是 [关键变量]。以前大家 [旧做法]；现在 [新做法]，因为 [新条件]。

**适合谁**（绿色标签）：
- [场景 1]：[具体描述]
- [场景 2]：[具体描述]
- [场景 3]：[具体描述]

**不适合谁**（暖灰标签）：
- [场景 1]：[具体描述]
- [场景 2]：[具体描述]

[一段话我的判断：[一句话洞察]——这个项目 [本质判断]。它做对了 [N 件事]，但还要看 [N 个不确定]。

[收尾金句 + Star 号召]：如果你也觉得这个方向有意思，欢迎 star chopratejas/headroom，一起把 agent 的 context 经济学做对。
```

**示例（headroom）**：
> ## 05 它凭什么是黑马：context engineering 时代来了
>
> headroom 跟同类压缩工具（llmlingua、recomp、Selective Context）比起来，本质区别是它把"压缩"从省 token 升级到"agent 经验管理"——`headroom learn` + 跨 agent memory 让它不只是个节省工具，而是个"让你的 agent 越来越聪明"的平台。
>
> 这反映了 2025→2026 的一个关键转折：**prompt engineering 时代结束，context engineering 时代开始**。以前大家卷"怎么写好 prompt"；现在大家卷"怎么管理 agent 看到的 context"——包括历史 session、跨 agent 知识、压缩策略。
>
> 适合谁：
> - 跑长 agent session 的（Claude Code / Cursor / Codex 用户）
> - 团队里多个 agent 协作的（跨 agent memory 价值大）
> - 已经在用 RAG 但觉得 context 成本高的
>
> 不适合谁：
> - 单次 prompt 调用的（压缩节省对一次性调用没意义）
> - 上下文本来就 < 4k token 的（边际收益小）
> - 强实时性、低延迟要求的（压缩有 ~10-50ms 开销）
>
> 我的判断：headroom 是个**工程化程度超预期**的项目。CCR + 6 种 compressor + `headroom learn` + 跨 agent memory 这套组合，**不是**"又一个压缩库"——它在做"agent 时代的 context 操作系统"。
>
> 它做对了 3 件事：可逆压缩保留原文、按场景路由不同 compressor、把失败 session 沉淀成可复用经验。但还要看 2 个不确定：MCP 生态成熟度、跨厂商 agent 协议标准化。
>
> 如果你也觉得这个方向有意思，欢迎 star [chopratejas/headroom](https://github.com/chopratejas/headroom)，一起把 agent 的 context 经济学做对。

---

## ✅ 写完后必查（7 项 preflight）

1. ✓ 纯中文字数 ∈ [1500, 2000]：`len(re.sub(r'[^一-鿿]', '', text))`
2. ✓ 标题 ≤ 60 字节（推荐 14-22 字节）：`sum(3 if ord(c)>=0x3000 else 2 if '\u4e00'<=c<='\u9fff' else 1 for c in title)`
3. ✓ 0 空行（`grep -c '^$' article.md` = 0）
4. ✓ 0 `**` 残留（`grep -n '\*\*' article.md` 空）
5. ✓ 0 表格（`grep -n '^|' article.md` 空）—— 表格已散文化
6. ✓ 5 个 H2 标题（开头 + 5 编号段）
7. ✓ 4-5 个代码块（开头 1 + 01 段 1 + 02 段 1 + 03 段 1-2 + 04 段 1）

## ⚠️ 不要做的事

- ❌ 不写六段式（"一、xxx 二、xxx..."），只写 5 段式
- ❌ 不留 markdown 表格（转 HTML 会被当 p 渲染成脏行）
- ❌ 不出现"卡兹克 / zhiliGitHub / 本文由 / 一键三连"等 branding
- ❌ 不写超过 2 段连用 bullet point 罗列（卡兹克风格禁）
- ❌ 不超过 2000 字（zhiliGitHub 上限）
