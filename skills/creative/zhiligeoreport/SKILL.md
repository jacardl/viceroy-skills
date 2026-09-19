---
name: zhiligeoreport
description: |
  端到端生产并发布 GEO 周报到「直隶按察使」公众号草稿箱：从抓信源 → 强 GEO 筛选 → 双语翻译 → 2 板块分类 → 4 项验证门禁 → 渲染 HTML → 样式 A inline 化 → 按字节拆篇 → 推 WeChat 草稿箱。Auto-loaded when user mentions 跑周报 / 写周报 / 生成 GEO 周报 / 本周 GEO 资讯 / 出周报 / 推草稿箱 / publish weekly / geo-report run. Do not use for 单条 GEO 资讯查询（直接查 DB）or 正式发布公众号（仅做草稿，正式发布由用户在微信公众平台后台完成）。
displayNames:
  zh-Hans: "GEO 周报"
---

# GEO 周报生产与发布

> v1.17。覆盖写作（fetch → render）+ 发布（inline → split → push）端到端。2 板块分类（GEO 技术科普 + GEO 行业动态），不再细分 8 行业。

## Inputs to collect

无前置输入。直接跑端到端命令即可。

如用户指定：
- **日期**：跑非本周数据（默认本周）
- **parts**：默认 3（拆 3 篇）；可用 2（上/下）
- **per-section-cap**：默认 12
- **--skip-push**：只渲染不推草稿箱

## Procedure

### 一行命令（推荐）

```bash
cd /Users/apple/Downloads/User/geo-report
uv run python3 -m geo_report.cli publish-weekly \
  --parts 3 --per-section-cap 12 --cover /tmp/zhili_cover.jpg
```

这条命令完成 7 步：

### 分步详解

**Step 1 — 抓信源**（`fetch-all`）
- 失败重试 3 次（1s / 5s / 25s）
- 连续 3 次失败的 source 自动 `enabled = false` + 写 errors 表 + 告警
- 约束见 [references/constraints.md §1-9](references/constraints.md)

**Step 2 — 渲染 HTML**（`scripts/13_render_only.py`）
- 4 项验证门禁 one-by-one（相关性 / 板块分类合法性 / 中文翻译 / 时效）
- 输出 `data/reports/liusheng_geo_<YYYY-MM-DD>.html`（北京时间文件名）
- 约束见 [references/constraints.md §10-12](references/constraints.md)

**Step 3 — 样式 A inline 化**（`scripts/16_inline_css.py`）
- WeChat 不解析 `<style>` 块 + 类选择器，必须 inline 到 `style="..."`
- 输出 `data/reports/liusheng_geo_<DATE>_inline.html`
- 详细原理见 [references/constraints.md §13](references/constraints.md) + [references/style-a.md](references/style-a.md)

**Step 4 — 按字节拆篇**（`scripts/15_split_zhili.py`）
- ≤64KB/篇（WeChat 草稿 content 上限），建议 ≤60KB 更稳
- parts=3：上 = GEO 技术科普 + 医药 + 本地服务；中 = 消费品 + 高客单；下 = 电商 + B2B SaaS
- 标题后缀：(上)/(中)/(下)，每个 26 字节
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
- 依次打开 3 篇周报预览，确认样式 A 渲染（H2 下划线 / 墨蓝分类标签 / 红褐翻译标题 / 行距 1.8）

## Output contract

### 端到端成功标志

1. ✅ 7 步全跑通，无失败退出码
2. ✅ `data/reports/liusheng_geo_<DATE>_inline_part{1,2a,2b}.html` 三文件存在
3. ✅ 每篇字节 ≤ 64KB
4. ✅ 3 篇草稿 `draft/add` 全部返回 media_id
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

- 标题：`刘生 GEO 周报（上/中/下）`
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
4. **inline 化字节过大** → 元素太多导致内联 style 字节膨胀。考虑降低 per-section-cap 或改 parts=3。
5. **WeChat 草稿箱无样式** → inline 化未做或 `<style>` 块残留。重跑 `scripts/16_inline_css.py` 后再推。

### 失败降级策略

- 抓信源失败：3 次重试（1s/5s/25s）后 disable source，不阻断流程
- 翻译失败：GT → minimax 兜底；都失败则 `title_zh`/`summary_zh` 留空，由验证门禁剔除
- LLM 总结失败：`_strip_body_commentary` + 截前 500 字兜底
- 推草稿箱失败：返回 `media_id` 为空，整批中断；用户需要看 stdout 错误

### 何时停下来问用户

- **板块分类错位**（用户明显感知）→ 触发 v1.17 待办里的代码改造
- **WeChat 凭据缺失**（APP_SECRET / 封面图）→ 阻塞流程，问用户补
- **style A 改动请求**（用户要求改样式）→ 是 spec 变更，先改 spec 再改模板

## v1.17 待办

- [ ] `classify.classify_industry` 改造：板块从 9 行业简化到 2 个
- [ ] `weekly.html.j2` 改造：模板只渲染 2 板块
- [ ] `SPEC_ITEM_PIPELINE.md` §1.11 更新：板块分类规则文档化
- [ ] `SPEC_REPORT_TEMPLATE.md` 更新：模板结构文档化
- [ ] `classify.GEO_TECH_SCIENCE_KEYWORDS` + `GEO_SERVICE_PROVIDER_KEYWORDS` 重新整理

详细见 [references/sections.md](references/sections.md)。

## Examples

### Example 1: 完整跑本周周报 + 推草稿箱

```bash
$ cd /Users/apple/Downloads/User/geo-report
$ uv run python3 -m geo_report.cli publish-weekly --parts 3 --per-section-cap 12

📰 渲染 weekly.html (2026-09-19)
✂️  拆分 (3 篇，每板块 ≤ 12 条)
📤 推送草稿箱
  ✅ part1: draft_id=kiuyle4KZHC7JKxpTQssMG_xrXoadpDy0_...
  ✅ part2: draft_id=kiuyle4KZHC7JKxpTQssMD_RmnKSxobrs...
  ✅ part3: draft_id=kiuyle4KZHC7JKxpTQssMHs9-67rFJ3wS6...
```

### Example 2: 只渲染不推送

```bash
$ uv run python3 -m geo_report.cli publish-weekly --skip-push --parts 3
```

输出 `data/reports/liusheng_geo_<DATE>_inline_part{1,2a,2b}.html`，不调 push.py。

### Example 3: 单独校验产物

```bash
$ node ~/.minimax/skills/zhiligeoreport/scripts/validate-weekly.js \
    data/reports/liusheng_geo_2026-09-19_inline.html

=== 校验 .../liusheng_geo_2026-09-19_inline.html ===
[OK] 字节 120006 ≤ 65536
[OK] 中文字 18055 ≥ 18000
[OK] 无 <style> 块
[OK] 板块数 8 合理  ⚠️ v1.17 待改造为 2 板块
[OK] 条目数 59
```