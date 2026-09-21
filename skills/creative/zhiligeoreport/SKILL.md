---
name: zhiligeoreport
description: |
  端到端生产并发布 GEO 周报到「直隶按察使」公众号草稿箱：从抓信源 → 强 GEO 筛选 → 通读原文中文总结 → 双语翻译 → 5 角色章节分类 → 4 项验证门禁 → 渲染 HTML → 样式 A inline 化 → 按字节拆篇 → 推 WeChat 草稿箱。Auto-loaded when user mentions 跑周报 / 写周报 / 生成 GEO 周报 / 本周 GEO 资讯 / 出周报 / 推草稿箱 / publish weekly / geo-report run. Do not use for 单条 GEO 资讯查询（直接查 DB）or 正式发布公众号（仅做草稿，正式发布由用户在微信公众平台后台完成）。
displayNames:
  zh-Hans: "GEO 周报"
---

# GEO 周报生产与发布

> v1.24。覆盖写作（fetch → render）+ 发布（inline → split → push）端到端。5 章节分类（GEO 服务商动态 / 品牌方实战 / 工具平台更新 / 行业研究与数据 / 国际市场）。草稿标题统一为 `YYYY-MM-DD 刘生 GEO 资讯`，拆篇后保留正文 H1，推送版移除本地锚点 TOC。
> **v1.21 关键变更**：
> - **标题前 label 动态提取**：`extract_title_label(title, max_n=2)` 从标题抽品牌名/行业词（如「阿里·搜索」「腾讯·阿里」「医药·医疗」「报告·趋势」），不再直接显示章节名
> - `Item.label` 字段新增，模板 `{{ it.label or it.category }}` 兜底
> - raw/wechat 本周 7 天 mtime 窗口确认 4 篇新建（GEO 每日简报 14/17/18/20）已入库

> **v1.20 关键变更**：
> - **单篇发布模式**（默认）：`--parts 1` 把所有板块拼成一篇公众号文章，单篇 bytes ≤64KB
> - `--per-section-cap` 默认 8（更精）
> - 仍保留 `--parts 2 / 3` 多篇模式用于备选

> **v1.19 关键变更**：
> - obsidian 内参（`raw/wechat` + `wiki/sources` + `wiki/concepts`）作为权威信源优先（`source_weight = 3.0`，板块上限 25）
> - 搜索引擎内容降权（`source_weight = 1.0`，板块上限 12），只作为补充
> - 生产级质量门槛：标题 ≥ 10 字、正文 ≥ 300 字、中文占比 ≥ 30%；不达标直接剔除
> - obsidian 转载首行 URL 自动跳过，向下取 `# ` 标题

## Inputs to collect

无前置输入。直接跑端到端命令即可。

如用户指定：
- **日期**：跑非本周数据（默认本周）
- **parts**：默认 1（单篇）；可用 2 / 3 作为字节过大时备选
- **per-section-cap**：默认 12
- **--skip-push**：只渲染不推草稿箱

## Procedure

### 一行命令（推荐）

```bash
cd /Users/apple/Downloads/User/geo-report
uv run python3 -m geo_report.cli publish-weekly \
  --parts 1 --per-section-cap 12 --cover /tmp/zhili_cover.jpg
```

这条命令完成 7 步：

### 分步详解

**Step 1 — 抓信源**（`fetch-all`）
- 失败重试 3 次（1s / 5s / 25s）
- 连续 3 次失败的 source 自动 `enabled = false` + 写 errors 表 + 告警
- 约束见 [references/constraints.md §1-9](references/constraints.md)

**Step 2 — 渲染 HTML**（`scripts/13_render_only.py`）
- 验证门禁 one-by-one（相关性 / 板块分类合法性 / 中文翻译 / 摘要质量 / 编码 / 营销稿 / 时效）
- 输出 `data/reports/liusheng_geo_<YYYY-MM-DD>.html`（北京时间文件名）
- 约束见 [references/constraints.md §10-12](references/constraints.md)

**Step 3 — 样式 A inline 化**（`scripts/16_inline_css.py`）
- WeChat 不解析 `<style>` 块 + 类选择器，必须 inline 到 `style="..."`
- 输出 `data/reports/liusheng_geo_<DATE>_inline.html`
- 详细原理见 [references/constraints.md §13](references/constraints.md) + [references/style-a.md](references/style-a.md)

**Step 4 — 按字节拆篇**（`scripts/15_split_zhili.py`）
- ≤64KB/篇（WeChat 草稿 content 上限），建议 ≤60KB 更稳
- parts=1：所有板块合并为单篇；parts=3 仅作备选：上 = GEO 服务商动态 + 国际市场；中 = 品牌方实战 + 工具平台更新；下 = 行业研究与数据
- 标题后缀：(上)/(中)/(下)，每个 26 字节
- 拆篇输出必须保留正文头部的 kicker、H1、source meta、intro；推送版必须移除本地锚点目录链接（`href="#sec-*"`），否则 WeChat `draft/add` 可能报 `45166 invalid content`
- 重要 bug 修复：h2 切分用 `re.finditer` 自然顺序，不再用 200 字节窗口查 class=（inline 后超窗口）
- 详细见 [references/constraints.md §14](references/constraints.md)

**Step 5 — 推 WeChat 草稿箱**（`push.py`）
- 每篇调一次 `push.py --html <part> --cover /tmp/zhili_cover.jpg --skip-illustration --skip-cover`
- 凭据见 [references/credentials.md](references/credentials.md)

**Step 6 — 产物自检**（可选，`scripts/validate-weekly.js`）
- 校验 inline HTML 字节 / 中文字数 / 板块数 / 条目数 / 标题后缀
- 单独跑：`node ~/.minimax/skills/zhiligeoreport/scripts/validate-weekly.js data/reports/liusheng_geo_<DATE>_inline.html`

**Step 7 — 草稿箱验证**（用户在微信公众平台后台）
- 打开 https://mp.weixin.qq.com → 草稿箱
- 打开单篇周报预览，确认样式 A 渲染（H2 下划线 / 墨蓝分类标签 / 红褐翻译标题 / 行距 1.8）

## Output contract

### 端到端成功标志

1. ✅ 7 步全跑通，无失败退出码
2. ✅ `data/publish/liusheng_geo_<DATE>_zhili_part1.html` 单篇文件存在
3. ✅ 单篇字节 ≤ 64KB（建议 ≤60KB）
4. ✅ 单篇草稿 `draft/add` 返回 media_id
5. ✅ 微信公众平台后台草稿箱渲染样式 A

### 文件清单

| 文件 | 来源 | 大小（实测） |
|---|---|---|
| `data/reports/liusheng_geo_<DATE>.html` | Step 2 | ~93KB（含完整样式 A） |
| `data/reports/liusheng_geo_<DATE>_inline.html` | Step 3 | ~120KB（inline +30%） |
| `data/reports/liusheng_geo_<DATE>_inline_part1.html` | Step 4 | ~25KB |
| `data/reports/liusheng_geo_<DATE>_inline_part2a.html` | Step 4 | ~35KB |
| `data/reports/liusheng_geo_<DATE>_inline_part2b.html` | Step 4 | ~59KB |

### WeChat 草稿属性

- 标题：`<YYYY-MM-DD> 刘生 GEO 资讯`（单篇默认；多篇备选才加上/中/下后缀）
- 作者：刘生
- digest：首段中文前 40 字
- thumb_media_id：`/tmp/zhili_cover.jpg`（900×383，墨蓝 #1B365D）
- need_open_comment：1
- only_fans_can_comment：0
- original：1

## Failure handling

### 常见故障

完整表见 [references/troubleshooting.md](references/troubleshooting.md)。关键 5 条：

1. **拆篇后 partN 字节爆炸（>100KB）** → h2 切分窗口 bug。已用 `re.finditer` 自然顺序修复。**症状**：曾误把"处方药 1 条"算成 112KB。
2. **推草稿箱报 invalid media_id** → `draft/get` API 限制，draft/add 成功但 get 查不到是正常现象。用微信公众平台后台验证。
3. **验证门禁违规 "title_zh 不含中文"** → `translate_zh_batch` 已自动回退 minimax；若仍违规，给标题加 `min()` 处理。
4. **inline 化字节过大** → 元素太多导致内联 style 字节膨胀。先降低 per-section-cap；仍超 64KB 再改 parts=3。
5. **WeChat 草稿箱无样式** → inline 化未做或 `<style>` 块残留。重跑 `scripts/16_inline_css.py` 后再推。

### 失败降级策略

- 抓信源失败：3 次重试（1s/5s/25s）后 disable source，不阻断流程
- 翻译失败：GT → minimax 兜底；都失败则 `title_zh`/`summary_zh` 留空，由验证门禁剔除
- LLM 总结失败：返回空摘要，由验证门禁剔除；禁止截取原文或 current_summary 作为可发布摘要
- 推草稿箱失败：返回 `media_id` 为空，整批中断；用户需要看 stdout 错误

### 何时停下来问用户

- **板块分类错位**（用户明显感知）→ 触发 v1.17 待办里的代码改造
- **WeChat 凭据缺失**（APP_SECRET / 封面图）→ 阻塞流程，问用户补
- **style A 改动请求**（用户要求改样式）→ 是 spec 变更，先改 spec 再改模板

## v1.24 已落地

- [x] `scripts/15_split_zhili.py`：拆篇输出保留正文头部 kicker、H1、source meta、intro，单篇正文 H1 与 HTML `<title>` 一致
- [x] `scripts/15_split_zhili.py`：推送版移除本地锚点 TOC，避免 WeChat `draft/add` 报 `45166 invalid content`

## v1.23 已落地

- [x] `src/geo_report/report/html.py`：新增 `build_report_title(date_label)`，统一生成 `<YYYY-MM-DD> 刘生 GEO 资讯`
- [x] `scripts/13_render_only.py` / `src/geo_report/cli.py`：HTML `<title>`、正文 H1、WeChat 草稿标题来源统一为报告日期标题
- [x] `scripts/15_split_zhili.py`：保留基础标题，多篇模式只追加 `（上）/（中）/（下）`

## v1.22 已落地

- [x] `scripts/13_render_only.py`：所有源必须 `published_at IS NOT NULL AND published_at >= cutoff`，删除 `fetched_at` 兜底
- [x] `scripts/13_render_only.py`：obsidian 额外要求 `meta_json.created_at >= cutoff`，缺 created_at 的旧行不可渲染
- [x] `collector/obsidian_vault.py`：按创建时间扫描，优先 `st_birthtime`，再 frontmatter `created|date`，再文件名日期；`mtime` 只入审计元数据
- [x] `collector/industry_search.py`：搜索结果必须抓原文发布时间，7 天内才写库，无发布时间/过期计入 `stale_or_undated`
- [x] `publish-weekly`：渲染前刷新普通信源、行业搜索、obsidian

## v1.18.2 已落地

- [x] `classify.classify_industry` 改成 5 角色章节（替换 v1.17 旧章节链）
- [x] `weekly.html.j2` 支持 5 章节渲染并过滤空章节
- [x] `classify.SECTION_KEYWORDS` 维护 5 个章节关键词表
- [x] `SPEC_ITEM_PIPELINE.md` §1.22 / §1.61 约束总结失败行为
- [x] `classify.has_geo_vendor_marketing` 剔除 GEO 厂商营销稿（榜单/推荐/排名/选型/报价/获客/方案/自夸）
- [x] `scripts/13_render_only.py` 门禁剔除空摘要、非中文摘要、疑似原文截断摘要、含 U+FFFD 编码失败字符、GEO 厂商营销稿摘要

## v1.19 已落地

- [x] `obsidian_vault.SUBDIRS["raw/wechat"]` 标记 `internal_brief=True`，元数据写 `meta_json.internal_brief=true`
- [x] `scripts/13_render_only.py` 计算 `source_weight`：`internal_brief 3.0` / `obsidian 2.0` / `wechat_oa 1.5` / `其余 1.0`；`geo_score *= source_weight` 后按降序截断
- [x] obsidian 内参板块上限 25，非内参板块保持 12
- [x] 质量门槛：标题 ≥ 10 字、正文 ≥ 300 字、中文占比 ≥ 30%（任一不达标即剔）
- [x] obsidian 标题提取跳过裸 URL 行（公众号转载首行是 mp.weixin.qq.com URL）

## v1.19 拒绝低质量内容

跑完 `publish-weekly` 后若 `✅ 强 GEO 相关: N 条（N<v1.18.2 上限）`，**正常**。说明搜索引擎本周质量不达标，obsidian 内参数就是本周可发条数。不要手动放宽门禁去填充；那会拉低周报整体质量。

详细见 [references/sections.md](references/sections.md) + [references/constraints.md](references/constraints.md)。

## Examples

### Example 1: 完整跑本周周报 + 推草稿箱

```bash
$ cd /Users/apple/Downloads/User/geo-report
$ uv run python3 -m geo_report.cli publish-weekly --parts 1 --per-section-cap 12

📰 渲染 weekly.html (2026-09-19)
✂️  拆分 (1 篇，每板块 ≤ 12 条)
📤 推送草稿箱
  ✅ part1: draft_id=kiuyle4KZHC7JKxpTQssM...
```

### Example 2: 只渲染不推送

```bash
$ uv run python3 -m geo_report.cli publish-weekly --skip-push --parts 1
```

输出 `data/publish/liusheng_geo_<DATE>_zhili_part1.html`，不调 push.py。

### Example 3: 单独校验产物

```bash
$ node ~/.minimax/skills/zhiligeoreport/scripts/validate-weekly.js \
    data/reports/liusheng_geo_2026-09-19_inline.html

=== 校验 .../liusheng_geo_2026-09-19_inline.html ===
[OK] 字节 120006 ≤ 65536
[OK] 中文字 18055 ≥ 18000
[OK] 无 <style> 块
[OK] 板块数 5 合理
[OK] 条目数 59
```