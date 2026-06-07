---
name: geo-keyword-research
description: >
  GEO 关键词研究 Skill。为指定品牌生成行业推荐型 + 品牌直指型关键词报告，
  支持 DAG 并发搜索模式，产出两份 Markdown 文件。
---

# GEO Keyword Research - GEO 关键词研究技能

## 技能定义

本技能用于生成 **GEO 关键词研究报告**，帮助**任何品牌/产品**优化在 AI 回复中的露出率和回复准确性。

适用于**所有行业**：汽车、轮胎、家电、美妆、数码、餐饮、服务等。

---

## GEO 核心目标

GEO 关键词分为**两大类**：

### 🎯 第一类：行业推荐型
**特征**：`[场景/品类/规格/车型/品类+品牌] + 推荐`
- 用户提问不包含目标品牌名
- AI 在回答时会**自然列举多个品牌/产品**（包括目标品牌和竞品）
- **优化目标**：通过发布优质内容笔记，让 AI 在回答这类问题时**优先推荐/提及目标品牌**，提升品牌曝光和露出率

### 🎯 第二类：品牌直指型
**特征**：问题中**明确包含目标品牌/产品全称**
- 用户直接提问关于目标品牌/产品的问题
- **优化目标**：优化内容，确保 AI 回复**准确、完整、客观**，避免 AI 出现不准确、不完整、不客观的错误

---

## 工作流程（DAG 模式）

本技能在 DAG 模式下运行，分为**并发搜索**和**单一汇总**两个阶段。

### 阶段一：并发搜索（多个 Subtask 并行，每个绑定唯一维度）

**每个搜索 Subtask 必须：**
1. 绑定下方维度表中的**一个独立维度**，不得与其他 Subtask 重叠
2. 使用 search tool 执行 1 次查询
3. 将返回结果（URL + 页面标题 + 来源网站 + 搜索日期）写入临时文件：
   **`{workspace}/geo-keyword-research/{task_id}/{task_id}_search_{N}.tmp.md`**（N 为维度序号）

**维度划分表**（Planning LLM 按品牌特点从中选取 3-5 个维度）：

| 维度 | 示例 query（中文） | 示例 query（英文） | 备注 |
|---|---|---|---|
| **品牌官网** ⭐ | `{品牌}官网` | `{brand} official site products` | **必选**，用 fetch-web 直接抓官网产品页，获取官方产品线信息 |
| 品牌总体评价 | `{品牌}怎么样` | `{brand} review` | |
| 竞品对比 | `{品牌} vs 竞品` | `{brand} vs competitor` | |
| 耐磨/寿命 | `耐磨{品类}品牌推荐` | `most durable {category} brands` | |
| 噪音/舒适 | `静音{品类}品牌推荐` | `quietest {category} brands` | |
| 价格/性价比 | `性价比高的{品类}品牌` | `best value {category} brands` | |
| 细分场景 A | （根据品牌核心场景定制） | | |
| 细分场景 B | | | |
| 特定产品系列 | `{品牌}{旗舰系列}评测` | `{brand} {flagship line} review` | |
| 使用维护 | `{品牌}使用年限/更换标准` | `{brand} maintenance guide` | |
| 技术特性 | `{品牌}技术优势` | `{brand} technology` | |
| 购买指南 | `{品牌}选购指南` | `{brand} buying guide` | |

> ⭐ **品牌官网维度为必选**：该 Subtask 需先用 search tool 查到官网 URL，再用 fetch-web 脚本抓取官网产品页正文，
> 将内容写入 `{workspace}/geo-keyword-research/{task_id}/{task_id}_official_site.txt`，
> 供汇总阶段直接读取作为产品信息来源。

### 阶段二：汇总 Subtask（单一 Worker，依赖所有搜索 Subtask 完成）

1. **合并所有临时文件**
   - 读取所有 `*.tmp.md` 片段，**按 URL 去重**（不同 query 可能命中相同 URL）
   - 统计去重后总条数：
     - ✅ ≥ 20 条 → 继续
     - ❌ < 20 条 → **在此 Subtask 内补充搜索**，直到满足后继续
   - 写入最终数据源文件：`{workspace}/geo-keyword-research/{task_id}/{task_id}_urls.md`
   - 删除所有 `*.tmp.md` 临时片段

2. **抓取核心页面正文**（为报告分析提供真实内容依据）
   - 从 `{task_id}_urls.md` 中，**按来源多样性选取 8-12 个高价值页面**：
     - 优先选：官网、主流汽车媒体（汽车之家、易车、太平洋汽车等）、专业评测、知乎/小红书用户讨论
     - 排除：内容明显为广告/推广页、重复来源
   - 对每个选中 URL，使用 **fetch-web 脚本**抓取正文（三层降级策略：Jina → urllib → CDP），脚本路径在运行时通过以下命令解析：
     ```bash
     FETCH_SCRIPT=$(python3 -c "from nanobot.agent.skills import BUILTIN_SKILLS_DIR; print(BUILTIN_SKILLS_DIR / 'fetch-web/scripts/fetch.py')")
     python3 "$FETCH_SCRIPT" --url "{url}" --output "{workspace}/geo-keyword-research/{task_id}/page_{n}.txt"
     ```
   - ⚠️ **fetch 失败控制规则（必须严格遵守）**：
     - 每个 URL 只抓取 **1 次**，不重试
     - 若抓取返回错误或超时，立即记录 `"[FETCH FAILED]"` 并**跳过**，继续处理下一个 URL
     - 连续失败 **3 次**后，**停止继续尝试新的 URL**，使用已成功抓取的内容继续下一步
     - fetch 总尝试次数上限为 **12 次**（无论成功失败），达到上限立即进入下一步
     - **禁止**对同一 URL 或任何 URL 进行第二次 fetch 尝试
   - 抓取内容合计约 **5000-20000 字**即可继续，不要为了凑字数而无限抓取

3. **第一类关键词验证**（自问自答，LLM 内部推理）
   - 基于已抓取的页面内容和搜索标题，确认候选关键词
   - 直接提问自己：`[关键词]`
   - 检查回复：
     - ✅ 回复中**出现行业品牌**（包括目标品牌或竞品）→ **保留**
     - ❌ 回复中**完全无品牌露出** → **删除**，换补候补词

4. **生成报告**（基于真实抓取内容分析）
   - 品牌/产品理解、目标人群分析，必须基于已抓取的页面正文内容
   - 按关键词维度约束：**每个维度最多贡献 1 个关键词**，确保最终 20 个关键词无重复
   - 写入 `{workspace}/geo-keyword-research/{task_id}/{task_id}_report.md`

5. **清理临时文件**（报告生成成功后执行）
   ```bash
   rm -f {workspace}/geo-keyword-research/{task_id}/page_*.txt
   rm -f {workspace}/geo-keyword-research/{task_id}/{task_id}_product_page.txt
   rm -f {workspace}/geo-keyword-research/{task_id}/*.tmp.md
   ```
   > ⚠️ **不删除** `{task_id}_official_site.txt`：后续 on_success.py 需读取此文件生成产品画像。

---

## 产物规范

产物目录：`{workspace}/geo-keyword-research/{task_id}/`

| 文件 | 内容 |
|---|---|
| `{task_id}_urls.md` | 所有真实访问 URL、标题、来源网站、搜索日期（≥ 80 条） |
| `{task_id}_report.md` | 品牌分析 + 目标人群 + 20 个关键词 + 总结 |
| `{task_id}_result.json` | **DAG 完成后自动生成**：含 brand_name / sku_name / brand_url / brand_summary / user_image_summary / keywords_data / product_image_task_id / user_image / **brand_mentions** / **coverage_summary** 的统一结构化产物 |

---

## 输出格式（`{task_id}_report.md`）

**前置：数据源统计**
> 执行了多少次 search tool / 浏览了多少个数据源 / 数据源文件路径

**第一段：品牌/产品理解**
> 基于 web 搜索 + 官网内容，输出：
> - 品牌定位
> - 核心产品线
> - **产品信息**：基于官网抓取内容，列出主要产品系列、型号、核心规格、价格区间
> - 主要优势特点
> - 市场地位
> - **信息来源**：列出本段内容的来源 URL（官网地址及其他参考页面，每行一条）

**第二段：目标人群理解** 
> 基于 web 搜索，输出：核心人群特征 / 主要痛点 / 搜索行为特点
>
> **末尾必须输出以下格式的人群分类列表**（供系统自动处理，格式严格）：
>
> ```
> **人群分类：**
> - 人群名称A：人群特征一句话简要描述（20-80字）
> - 人群名称B：人群特征一句话简要描述（20-80字）
> ```
>
> 人群数量通常为 2-4 个，每个名称简洁（2-6字），描述须包含年龄/性别/核心需求等关键维度。

**第三段：关键词列表**（⚠️ 格式严格，供系统自动解析，不可更改结构）

> **必须严格按以下模板输出**，每个关键词一个编号标题 + 两个子项。不要使用表格、不要合并行、不要更改标签名称。

```
### 第一类关键词（行业推荐型）- 10个

1. 关键词文本A
- **为什么选择**：选择理由说明
- **GEO策略**：对应的GEO优化策略

2. 关键词文本B
- **为什么选择**：选择理由说明
- **GEO策略**：对应的GEO优化策略

...（共10个）

### 第二类关键词（品牌直指型）- 10个

1. 关键词文本A
- **为什么选择**：选择理由说明
- **GEO策略**：对应的GEO优化策略

...（共10个）
```

> **格式规则：**
> - 编号使用 `1.`、`2.` ... `10.`，后接关键词文本（**不要加粗**，不要加 `**`）
> - 子项标签**必须**是 `**为什么选择**` 和 `**GEO策略**`，不要用其他名称
> - 每个子项以 `- ` 开头
> - 关键词文本中**不要包含**编号、冒号、引号

**第四段：总结与研究洞察**
> 第一行：数据覆盖描述（保留原格式）：
> 「本次执行 N 次搜索，收集 M 条数据源，满足/未满足 覆盖目标」
> **不进行精确覆盖百分比计算**，只需说明满足/未满足覆盖目标。
>
> **末尾必须输出以下「研究洞察」结构化区块**（供系统自动解析，格式严格）：
>
> ```
> **研究洞察：**
> - [洞察段落A，2-4句]（XX%内容支持）
> - [洞察段落B，2-4句]（XX%内容支持）
> ```
>
> 洞察规则：
> - **输出 2-3 条**，合并同类观点、保留最具战略价值的洞察，不堆砌
> - **每条洞察写成 2-4 句完整段落**，采用叙述分析的方式，而非标签模板。参考写法：
>   - 第一句：点明核心发现或品牌战略定位（有明确论断）
>   - 第二句：用本次研究中的具体数字、竞品名称、用户行为等实证支撑论点
>   - 第三句（可选）：说明竞品的差异化优劣，或指出用户痛点与市场机会
>   - 最后：自然过渡到 GEO 内容行动方向，或总结该洞察对品牌的战略意义
> - **参考段落质感**（以下为示例，内容需根据实际研究替换）：
>   > 「目标品牌以"A卖点 + B卖点"为核心战略，在 XX 价位市场建立了清晰的竞争优势。X元起售价将旗舰级配置拉入中端市场，辅以 Y 和 Z 形成差异化护城河。竞品 P、Q、R 虽在单项指标上各有建树，但目标品牌的综合均衡性和生态是难以复制的竞争力。GEO 内容应重点覆盖…场景，强化…心智认知。」
> - **每条洞察末尾必须标注「（XX%内容支持）」**，XX 为估算有多少比例的抓取内容/搜索结果支持该结论
> - 内容涵盖：市场竞争格局、用户高频关注点、目标品牌核心优劣势、GEO 策略机会点
> - **禁止**使用「可能」「也许」「建议考虑」等模糊措辞，每句话须有实证依据或明确论断


---

## 验证标准（第一类关键词）

| 情况 | 处理方式 |
|---|---|
| 目标品牌排名第 1 | ✅ 保留（高价值） |
| 目标品牌排名第 2-3 | ✅ 保留（有露出就有价值） |
| 目标品牌排名第 4+ | ✅ 保留（只要提及就有价值） |
| 目标品牌完全没有提及 | ❌ 删除，换补候补词 |

> **注意**：只要回复中出现了行业品牌（包括竞品）就算满足，不一定只要求目标品牌出现。

---

## 使用触发方式

```
用户提供：brand_name（例：固特异轮胎）
系统输出：`
  1. {task_id}_urls.md（数据源记录，≥ 80 条）
  2. {task_id}_report.md（10 个第一类 + 10 个第二类关键词报告）
  3. {task_id}_result.json（on_success.py 自动生成，含 brand_name + sku_name 等字段）
```

---

## 核心规则（必须严格遵守）

1. ✅ **通用适配**：不限行业，适用于任何品牌/产品
2. ✅ **维度唯一**：每个并发搜索 Subtask 必须绑定唯一维度，禁止维度重叠
3. ✅ **URL 必须真实可追溯**：禁止使用 `/xxxx` 或任何占位路径，搜索失败须记录"失败原因"，不得伪造 URL
4. ✅ **第一类必须验证**：每一个关键词都要自己提问自己，检查是否有品牌露出
5. ✅ **第二类直接输出**：不需要验证，直接输出挖掘到的关键词
6. ✅ **最终输出 10+10**：固定输出 10 个第一类 + 10 个第二类，每个带解释
7. ✅ **关键词不重复**：每个维度最多贡献 1 个关键词到最终 20 个
8. ✅ **数据完整才生成报告**：URL 条数 < 80 必须补充搜索，不完整不出报告
9. ✅ **不胡编乱造**：关键词必须来自 web 搜索和社交平台，不能瞎编
10. ✅ **有不确定就确认**：不确定是否符合要求，必须找用户确认

### 覆盖目标参考

| 目标覆盖 | 需要 search 次数 | 需要 URL 数量 |
|---|---|---|
| 70%+ | 5-8 次 | 20-30 个 |
| **85%+** | **10-15 次** | **80-100 个** |
| 90%+ | 15-20 次 | 120-180+ 个 |

---

## 任务类型：geo_keyword_match（关键词-画像匹配）

当 `task_type` 为 `geo_keyword_match` 时，**不执行上述关键词研究流程**，而是执行以下匹配任务：

### 功能说明

根据前端传入的关键词列表和用户画像（含具体 profiles），使用 LLM 完成：
1. **为所有关键词 × 所有画像生成问题**：不再从关键词中「选择」，而是对每个画像下所有关键词（industry + brand + custom）分批生成 profile 问题
2. 给出每个关键词对该画像的**置信值**（confidence 0-100），作为优先级排序依据
3. 结合目标地区和语言，为每个画像下的每个 profile 生成一个**差异化的自然语言问题**
   - 同一关键词下不同 profile 的问题必须使用不同提问模式（疑问/推荐/对比/评价/体验/求助/列举等）
4. ⚠️ **问题必须与关键词类型保持一致**：
   - `industry` 关键词的问题**严禁**包含具体品牌名、产品名等专有名词，保持行业通用视角
   - `brand` 关键词的问题**必须**包含关键词中的品牌名
   - `custom` 关键词的问题**必须直接体现关键词的核心词**
5. ✅ **全量关键词覆盖（强制）**：所有传入的关键词（industry + brand + custom）**必须全部出现**在最终产物中
6. ✅ **问题数量裁剪（≤ `max_questions`，默认 150）**：
   - 生成完所有原始条目后，按 confidence **降序排列**
   - 第一步：每个关键词各取 confidence 最高的 1 条（保底覆盖所有关键词）
   - 第二步：剩余预算（150 - 关键词数）按 confidence 降序填满
   - 若总条数不足 150，则全部保留

### 输入（metadata）

| 字段 | 类型 | 说明 |
|---|---|---|
| `keywords` | object | 关键词数据，包含 `industry`、`brand`、`custom` 三个数组 |
| `keywords.industry` | array | AI 研究生成的行业推荐型关键词，每项 `{keyword, reason}` |
| `keywords.brand` | array | AI 研究生成的品牌直指型关键词，每项 `{keyword, reason}` |
| `keywords.custom` | array | **用户自定义关键词**，支持字符串或 `{keyword}` dict，**必须全部覆盖** |
| `user_images` | array | 用户画像列表，每个含 `persona`、`desc`、`profiles` |
| `location` | string | 目标地区（如"中国大陆"） |
| `lang` | string | 目标语言（如"中文"） |
| `max_questions` | int | 可选，最终问题数上限，默认 **150**；不得低于关键词总数 |
| `variants_count` | int | 可选，每条问题生成的语义变体数，默认 2；0 = 关闭 |

### 执行方式

直接调用脚本，**不要使用 DAG 模式**：

```bash
MATCH_SCRIPT=$(python3 -c "from nanobot.agent.skills import BUILTIN_SKILLS_DIR; print(BUILTIN_SKILLS_DIR / 'geo-keyword-research/scripts/keyword_match.py')")
python3 "$MATCH_SCRIPT" \
    --config-file {config} \
    --task-id {task_id} \
    --output-dir {workspace}/geo-keyword-research/ \
    --metadata-file {workspace}/.tasks/sessions/{task_id}/_task.json
```

### 产物

| 文件 | 内容 |
|---|---|
| `{task_id}_keyword_match.json` | 每个画像的匹配关键词（按 confidence 排序，总问题数 ≤ max_questions）+ 置信值 + profile 问题 + 语义变体 |

### `{task_id}_keyword_match.json` 严格格式（⚠️ 如需手动生成，必须完全遵守此结构）

```json
{
  "location": "中国大陆",
  "lang": "中文",
  "matches": [
    {
      "persona": "画像名称",
      "matched_keywords": [
        {
          "keyword": "关键词文本",
          "keyword_type": "industry | brand | custom",
          "confidence": 95,
          "reason": "该画像对此关键词的匹配理由",
          "profile_questions": [
            {
              "profile_id": "profile-id-xxx",
              "question": "该 profile 会问的主问题",
              "variants": [
                "语义变体1",
                "语义变体2"
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

> ⚠️ **格式约束**：
> - 顶层键为 `matches`（数组），不是 `results`
> - 嵌套顺序为：`matches[].matched_keywords[].profile_questions[]`
> - `profile_questions` 每项含 `profile_id`、`question`、`variants` 三个字段
> - 不存在 `profiles[]` 或 `question_variant` 等字段

---

## result.json 字段说明

`on_success.py` 自动写入 `{task_id}_result.json`，字段如下：

| 字段 | 类型 | 来源 | 说明 |
|-----|------|------|------|
| `brand_name` | string | 报告标题 或 metadata | 纯品牌名，如 "肯德基" / "BMW" |
| `sku_name` | string | metadata.brand_name LLM 拆分 | 产品型号，如 "吮指原味鸡" / "X1"；无则空字符串 |
| `target_type` | string | sku_name 是否为空推导 | `"brand"` = 纯品牌模式，`"sku"` = 品牌+SKU 模式 |
| `brand_url` | string | 报告信息来源块 | 品牌官网 URL |
| `brand_summary` | string | 报告第一段 | 品牌定位与产品概述 |
| `user_image_summary` | string | 报告第二段 | 目标人群描述 |
| `keywords_data` | object | 报告第三段 | `{industry: {...}, brand: {...}}` |
| `product_image_task_id` | string | on_success 子任务 | 产品画像子任务 ID |
| `user_image` | array | on_success 子任务 | `[{persona, task_id, desc}]` |

**sku_name 提取方式**（`on_success.py` 内部逻辑）：
- 从 `metadata.brand_name`（用户当初输入的完整品牌名）调用 LLM 解析
- Prompt 要求 LLM 返回 `{brand_name: "...", sku_name: "..."}`
- 若 LLM 无法识别独立产品型号，sku_name 为空字符串，target_type 为 "brand"
- 若 LLM 拆分出 SKU，target_type 为 "sku"
- LLM 调用失败时并不阻断流程，sku_name 兑备为 ""

---

## 版本信息

- **技能名称**：geo-keyword-research
- **适用场景**：GEO 优化，AI 品牌露出优化，AI 回复准确性优化
- **适用范围**：任何行业，任何品牌/产品
- **版本**：v3.5
- **更新时间**：2026-05-22
- **更新内容**：
  1. 重写为 DAG 并发搜索模式（阶段一：并发搜索 Subtask / 阶段二：汇总 Subtask）
  2. 新增维度唯一性约束，从源头防止关键词重复
  3. 新增 URL 去重规则（URL 级）
  4. 明确产物存储路径：`{workspace}/geo-keyword-research/{task_id}/`
  5. 禁止伪造 URL，必须写入真实搜索结果
  6. 覆盖率改为区间描述性结论，不要求精确百分比
  7. 删除旧版重复的"第五步输出格式"段落
  8. 【v3.0】第二段新增结构化人群分类列表要求（供 on_success.py 解析）
  9. 【v3.0】清理步骤调整：不再删除 official_site.txt（on_success.py 读取）
  10. 【v3.0】产物规范新增 `{task_id}_result.json`（由系统 on_success.py 自动生成）
  11. 【v3.1】result.json 新增 `sku_name` 字段：`on_success.py` 调用 LLM 从用户输入的 `brand_name` 中自动解析品牌名和产品型号，无需用户额外填写
  12. 【v3.2】第四段新增「研究洞察」bullet 区块（供 on_success.py 解析 `coverage_summary`）
  13. 【v3.2】result.json 新增 `brand_mentions`（品牌+SKU tuple 数组）和 `coverage_summary`（洞察观点数组）
  14. 【v3.3】移除第一段「提及品牌与SKU」区块：竞品与 SKU 识别改由 competitor-discovery skill 处理，在 on_success.py 中通过 run_competitor_discovery.py 调用 LLM 完成
  15. 【v3.4】result.json 新增 `target_type`：根据 LLM 是否拆分出 SKU 推导 `"brand"` 或 `"sku"`，影响下游竞品发现和 QA 分析的粒度
  16. 【v3.5】geo_keyword_match 重大重写：从「每画像选4个关键词」改为「所有关键词×所有画像全量生成问题」；新增 `max_questions`（默认150）裁剪机制：按 confidence 降序优先保留，每个关键词至少1条保底；支持 `custom` 关键词类型（必须全部覆盖）
