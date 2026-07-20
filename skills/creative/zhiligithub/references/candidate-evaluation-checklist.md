# ZhiliGitHub 候选评估清单（候选接收 → 决策写不写）

> **本文件是 zhiligithub 工作流的最上游**。在调 GitHub API 调研、写文章之前，先回答"这个候选值不值得发公众号"。
>
> **下游**：`references/project-research-workflow.md`（决定要写之后怎么用 GitHub API 5 步调研）

## 何时触发

- 用户从 GitHub Trending 日报 / 手动发现 / 黑马扫描工具发来候选
- 典型格式：`Zhiligithub :N️⃣ owner/repo（语言 · Xk⭐ · +Y today · 黑马分 Z）— 一句话描述。URL`
- 用户没说"写"也没说"不写"——评估是你的责任

## 6 步评估流程（按顺序执行，不要跳）

### 步骤 1：客观事实表（GitHub API 一查就有）

```
GET https://api.github.com/repos/{owner}/{repo}
GET https://api.github.com/repos/{owner}/{repo}/contents/
```

| 字段 | 关注点 | 红旗阈值 |
|---|---|---|
| Stars | 与用户标的数字核对 | 差异 >5% = 用户描述或 Trending 数据滞后 |
| Forks | fork/star 比 | >10% = 异常（社区分裂 / 批量 fork） |
| License | `license.spdx_id` | `null` 或 `NOASSERTION` = **必须查 LICENSE 文件**，文件都没有 = 红旗 |
| Created at | 项目年龄 | >3 年 + 中等 stars = 黑马速度不成立 |
| Updated vs Pushed | 区分活跃类型 | `updated_at` today 但 `pushed_at` 6 月前 = 僵尸活跃（issues 在动，代码没动） |
| Open issues | 维护负担 | >100 = 维护负担明显 |
| Topics | 描述准确性 | 缺乏语言/技术 topic + 高 stars = 描述可疑 |
| README size | 内容深度 | < 2000 chars = 文档薄，难做架构段 |
| Size (KB) | 代码规模 | < 100KB = wrapper 项目，架构段难写 |

**踩坑提醒**：read_file/read 工具会**自动脱敏 secret**，显示 `token=***` ≠ 文件已脱敏。验证 License / API key 等明文是否真存在，用 patch diff 或原始流。

### 步骤 2：黑马分复核（不轻信系统给的数字）

**黑马速度计算**：
- 月均 stars = total_stars / months_since_creation
- 日增 +X today 单独看**不算黑马信号**（playlist/awesome/crack 仓库刷星是常态）
- 真黑马 = 近期陡峭增长 + **真实活跃 commit**

**黑马分红旗**：
- ❌ 5 年老项目 + 17k stars = 月均 290 颗（不黑马）
- ❌ +361 today 单独冲量，话题是 IPTV/playlist/crack/free
- ❌ commit history 稀少但 stars 暴涨
- ❌ fork/star > 10%

**黑马分绿灯**：
- ✅ < 1 年 + > 1k stars（年轻项目冷启动）
- ✅ commit 频率稳定 + stars 持续陡增
- ✅ 跨平台 HackerNews / Product Hunt / Twitter 多渠道提及

### 步骤 3：公众号合规性检查（关键！直隶按察使是大陆 公众号）

| 风险维度 | 红旗示例 | 处理 |
|---|---|---|
| **监管** | IPTV/M3U、proxy、VPN、crack、keygen、cheat | 直接不写 |
| **版权** | "免费"资源聚合、盗版下载站镜像、爬虫绕过付费墙 | 写但角度绕开内容 |
| **政治** | 涉及台/港/藏/疆话题（即使纯技术） | 直接不写 |
| **平台审核** | WeChat 内容审核敏感词（"破解""免费看""白嫖""付费绕过"） | 写但标题措辞极克制 |
| **品牌调性** | 消费级灰色地带 vs AI/技术前沿 | 看是否值得冒险 |

**重要免责原则**：
- **作者免责 ≠ 平台免责**（推荐 IPTV 仓库出问题，平台连带责任）
- **License = NONE 时推荐风险大**（不只是合规，是开源伦理问题）
- 涉及灰色话题时必须加"频道/资源可用性随时变化、自行验证合规性"免责

### 步骤 4：6 段式可写性检查

zhiliGitHub 默认六段式：**「三、架构设计」和「五、实战场景」必须各有 350-500 字**。

| 项目类型 | 架构段可写性 | 实战场景可写性 | 结论 |
|---|---|---|---|
| 框架 / 库 / 工具 | ✅（核心抽象、API 设计） | ✅（典型应用场景） | 优选 |
| CLI / DevOps 工具 | ✅（命令设计、配置模式） | ✅（运维场景） | 优选 |
| 数据集 / Awesome list | ❌（核心是数据不是代码） | ❌（没什么可"实战"） | **难写** |
| 教程 / 教科书 | ⚠️（写作方法论可写） | ⚠️（学习路径可写） | 需适配 |
| 文档 / Cheat sheet | ❌（没法写"架构"） | ❌ | 不写 |
| 聚合 / playlist 仓库 | ❌ | ❌ | 不写 |

**核心问题**：「三、架构设计」和「五、实战场景」两段能写出 350-500 字**不灌水**吗？如果答案是"硬挤"，**不写**。

### 步骤 5：主题与读者匹配度

**直隶按察使读者画像**：开发者 / 技术爱好者，AI / 前沿技术关注度高，macOS / Linux 偏多。

| 主题 | 匹配度 |
|---|---|
| AI / LLM / Agent / RAG | ⭐⭐⭐⭐⭐ 核心 audience |
| DevOps / CLI / 性能优化 | ⭐⭐⭐⭐ 核心 audience |
| Web 框架 / 全栈 | ⭐⭐⭐ 中等 |
| Windows 专属 | ⭐⭐ 窄但可写 |
| 移动端（iOS/Android） | ⭐⭐ 窄 |
| 区块链 / Web3 | ⭐ 偏离主线 |
| IPTV / 灰色消费级 | ❌ 调性错位 |

### 步骤 6：输出推荐（必须明确二选一）

每个候选必须明确给出：

- **✅ 推荐写**：列出 3 个写作角度供用户挑
- **❌ 不写**：说明理由（合规 / 调性 / 黑马分虚高 / 数据型项目难写）

**模糊地带**：给出"可写但有风险" + 角度必须绕开什么 + 用户拍板

---

## 完整输出模板（评估后直接套用）

```
【项目名】速查

| 项 | 值 | 评估 |
|---|---|---|
| Stars | X | 与用户标的对一致 |
| Forks | X | fork/star X%（正常/异常） |
| License | X | GPL v3 / MIT / NONE（红旗） |
| 出生 | YYYY-MM-DD | X 月大 |
| ... | ... | ... |

【黑马分 X 评估】
- ✅ ...
- ⚠️ ...
- ❌ ...

【公众号合规检查】
- 监管：✅ / ⚠️ / ❌
- 版权：✅ / ⚠️ / ❌
- 调性：✅ / ⚠️ / ❌

【6 段式可写性】
- 架构设计：能 / 难 / 不能
- 实战场景：能 / 难 / 不能

【写作角度（任选）】
1. xxx
2. xxx
3. xxx

【我的建议】：写 / 不写（理由）
```

---

## 真实踩坑案例（2026-06-16）

### optimizerDuck（642）→ ✅ 推荐写

- 7.5 月 3.6k stars + 321 today = **真黑马速度**
- GPL v3 + 11 语言 + 独立官网文档站，成熟度不像 7 个月项目
- WPF + .NET 10 + 反射式发现机制 = 架构段有深度可挖
- Windows-only = narrow 但不致命
- 三个角度：「Windows 11 bloatware 终于有人做对了」/ 「WPF + .NET 10 反射式优化发现」/ 「7.5 个月 3.6k stars 凭什么火」

### Free-TV/IPTV（541）→ ❌ 不写

- License = **NONE**（Python 脚本无授权）
- 5 年老项目 17k stars 月均 290 颗 = **黑马速度不成立**（+361 today 是 playlist 仓库刷星常态）
- **公众号监管风险**（IPTV/M3U 灰色地带）
- 主题与品牌调性错位（消费级灰色 vs AI/技术）
- 6 段式架构段**没东西写**（核心是 518KB M3U 数据文件，不是代码）
- fork/star 14.8% 异常
- 217 open issues 维护负担

**学到的**：
1. **黑马分 > 600 不代表必写**——541 也能因为合规拒绝
2. **License = NONE 是双重红旗**（合规 + 开源伦理）
3. **数据型项目（聚合/playlist）** 6 段式天生难写，**架构段是拦路虎**
4. **主题与公众号调性** 是常被忽视的硬约束

### 百度百科 QClaw 词条（2026-07-14）→ 信息不可引用

- 用户发来百度百科词条，声称 QClaw 由"腾讯电脑管家团队"于 2026-03-09 发布
- GitHub 事实：qiuzhi2046/QClaw 创建于 **2026-03-28**，Owner 是个人账号（type=User），README 自述"秋芝2046团队开发"，已暂停维护
- **真实生态位**：OpenClaw 社区第三方封装（秋芝2046）vs 腾讯官方 WorkBuddy（codebuddy.cn/work）
- 百度百科的"腾讯电脑管家团队背书"与 GitHub 事实严重不符

**学到的**：
1. **第三方百科（百度/搜狗）不可信**——任何人可编辑，无人审核，错误信息嫁接官方背书
2. **鉴别方法是 GitHub API**：owner.type（User/Organization）+ created_at + README 自述，三重验证足以戳穿百科谎言
3. **开源生态里有大量社区封装 vs 官方产品的混淆**（如 QClaw vs WorkBuddy），百科词条倾向于把知名开源项目的衍生品安到"大厂"头上以增强可信度
4. 当用户引用百科内容时，**先核查再引用**，不要因为用户提供了就默认可信

---

## 跟其他文件的关系

```
candidate-evaluation-checklist.md（本文件：该不该写）
  ↓ 决定写
project-research-workflow.md（怎么用 GitHub API 调研）
  ↓ 调研完
practical-writing-workflow.md（怎么写 + 转 HTML + 7 项验证）
  ↓ 用户点头发布
zhili-publish（封面 + mmbiz + 草稿）
```
