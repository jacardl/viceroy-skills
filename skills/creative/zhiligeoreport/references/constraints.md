# 关键约束（v1.24）

> 写代码时违反会进验证门禁违规清单 + 自动从 section 剔除。

> 写代码时违反会进验证门禁违规清单 + 自动从 section 剔除。

## 1. 严格 7 日窗口

- 所有源必须 `published_at IS NOT NULL AND published_at >= cutoff`，不再用 `fetched_at` 兜底
- 普通 RSS / JSON / HTML / wechat_oa 源没有可靠 `published_at` 时，不能入周报
- 外部搜索源必须二次抓原文页发布时间；无发布时间或过期计入 `stale_or_undated` 并跳过
- obsidian 源必须额外满足 `meta_json.created_at >= cutoff`，缺 `created_at` 的历史行不能入周报
- obsidian 创建时间来源优先级：macOS `st_birthtime` → frontmatter `created` / `date` → 文件名日期；`mtime` 只记录，不作为依据
- 防 `ON CONFLICT DO UPDATE` 刷新 fetched_at、iCloud 同步刷新 mtime 让老内容复活
- 不允许：把超过 7 日的 stale 条目混进周报
- 不允许：把公众号一次性历史采集条目（如 `enabled=false` 的小布 GEO 智库）算进"过去 7 天"

## 2. 强 GEO 筛选（`is_strongly_geo`）

- 标题 / 正文命中 GEO / AI 搜索 / AI research / 生成式引擎 等
- 不允许：把无关 SEO 新闻（如纯关键词工具更新、PPC 平台变更）混入

## 3. 负向样本剔除（`is_geo_false_positive`）

18 条 GEO_FALSE_POSITIVE_PATTERNS：
- Geo Magazine / Geology / Geo-targeting / GEO 化妆品 等品牌/地理歧义
- OTC 商品类：ToolPan OTC 7608 / Smartwool Geo Peaks Print OTC
- Geo 品牌/型号：Geo Specialty Chemicals / Alpin Expe / Wallis Travel / Geo Voyages / Geo Group Insurance / Geo Holdings / Geo-Konzept 等

## 4. 客户品牌剔除（`has_client_brand`）

Haleon / 芬必得 / Bayer / Roche / Pfizer / Sanofi / GSK / J&J / Novartis / Merck / Abbvie / MSD / 韶音 / Shokz / 阳狮 / Publicis / WPP / GroupM / Mindshare / Omnicom / IPG / 蓝色光标 / OMD

## 5. 草稿/标记剔除（`has_draft_marker`）

brief / RFP / 标书 / 投标 / NDA / MOU / 占位 / 待补充 / 草稿 / placeholder / todo / 待定 / 仅供参考

## 6. GEO 厂商营销稿剔除（`has_geo_vendor_marketing`）

- 剔除：GEO 服务商/厂商/公司榜单、推荐、排名、排行、盘点、评测、TOP 榜
- 剔除：选型、怎么选、选择指南、哪家好、哪家靠谱、找靠谱 GEO、价格、报价、费用、套餐、合作参考
- 剔除：以「GEO 公司」「GEO 优化公司」「GEO 优化服务」「GEO 服务商」为落地页标题的厂商获客页
- 剔除：智能营销、智能获客、外贸获客、精准获客、广告投放、解决方案、服务方案、一站式服务、实力领跑、全域增长等销售导向软广
- 保留：真实品牌方实践、可复用经验、最佳实践、方法指南、趋势、行业分享、研究数据、白皮书、benchmark、中性服务商新闻

## 7. 双语翻译（`translate_zh_batch`）

- GT 的 `sl=auto`（**不是 en**），自动检测波兰/捷克/荷兰/法语
- GT 翻译后若 `title_zh` 不含中文字符 → 自动回退到 `translate_zh` 走 minimax LLM 兜底
- 抓 article 成功但 LLM 总结失败 → 兜底调用 `translate_zh`（minimax + GT 双层）；仍失败则返回空摘要并由门禁剔除
- 标题上限 40 字（截到 80 字兜底），正文上限 500 字（截到 500 字兜底）
- 并发默认 concurrency=8（`httpx.AsyncClient`）
- 限速：minimax 走 OpenAI 配额；GT 匿名端点限速约 100 req/min

## 8. obsidian 强制 LLM 总结（≤500 字）

- 剥 YAML frontmatter（`---\n...\n---\n`）再喂 LLM
- LLM 失败：摘要置空，由门禁剔除；禁止截原文作为可发布摘要

## 9. 每信源 max 5 条（PER_SOURCE_CAP=5）

- search 聚合源（`source_type='search'`）不参与 cap

## 10. source 内近标题去重（v1.13.3）

- `(source_id, date, title[:24])` 去重
- 同一 source 同日同一主题只占 1 个 cap 槽位

## 11. 每板块最多 N 条（PER_INDUSTRY_CAP）

- 按 `geo_score` 降序截断
- 防 search 源把单 section 占满

## 12. HTML 模板约束

- 模板：`src/geo_report/report/templates/weekly.html.j2`
- 标题：`<YYYY-MM-DD> 刘生 GEO 资讯`（HTML `<title>`、正文 H1、WeChat 草稿标题统一；日期为报告生成日北京时间）
- 拆篇后仍必须保留正文头部 kicker、H1、source meta、intro；单篇正文 H1 必须等于 HTML `<title>`
- WeChat 推送版不得保留本地锚点 TOC 链接（如 `href="#sec-2"`），否则 `draft/add` 可能报 `45166 invalid content`
- 内参标注：「📚 来自内参」
- toc 和 section 都过滤空 section（`{% if sec.items %}`）
- 包含完整 zhili-publish 样式 A
- 目录/正文都用零换行内联 style（WeChat 渲染友好）

## 13. 验证门禁 4 项（`scripts/13_render_only.py` 自动跑）

1. **相关性**：title 或 summary 必须含 `GEO|AI 搜索|AI search|AI research|生成式引擎`
2. **板块分类合法性**：`it.industry` 必须 ∈ {`geo_service_provider`, `brand_practice`, `tool_platform`, `industry_research`, `international_market`}（v1.18 后）
3. **中文翻译**：title 不含中文时，`title_zh` 和 `summary_zh` 都必须含中文字符（**不是非空**）
4. **摘要质量**：可发布摘要必须含中文、长度达标，且不能是原文直接截断
5. **编码质量**：标题和摘要不得含 U+FFFD 解码失败字符
6. **营销稿质量**：不得命中 GEO 厂商榜单/推荐/排名/选型/报价/获客/方案/自夸模式
7. **时效性**：`published_at` 距今天 ≤ 7 日

## 14. 生产级质量门槛（v1.19 新增）

> 用户硬性要求：宁可减少数量也不接受低质量。

- `title` 字符长度 ≥ 10（强 GEO 阶段直接剔除）
- `body` 字符长度 ≥ 300（SEO meta / 转载片段拒收）
- `title` 或 `body[:500]` 中文占比 ≥ 30%（机翻广告拒收）
- 上述任一不达 → 强 GEO 阶段直接剔除，不再进 Item 列表
- 之前 6 项门禁仍生效：相关性 / 章节合法性 / 中文翻译 / 摘要质量 / 营销稿 / 时效

## 15. 内参优先排序（v1.19 新增）

- `obsidian_vault.SUBDIRS["raw/wechat"]` 标记 `internal_brief=True`，`ingest_raw.meta_json.internal_brief=true`
- `ingest_raw.meta_json.created_at` / `created_at_source` 记录内参创建时间证据
- `source_weight`：`internal_brief 3.0` / `obsidian 2.0` / `wechat_oa 1.5` / `其余 1.0`
- `geo_score *= source_weight` 后按降序截断
- obsidian 内参板块上限 25，非内参板块保持 12
- obsidian 转载文件首行是裸 URL（mp.weixin.qq.com）→ 跳过，继续向下取 `# ` 标题

## 16. inline CSS 化约束（WeChat 兼容）

- WeChat 不解析 `<style>` 块 + 类选择器
- 所有 CSS 必须 inline 到 `style="..."` 属性
- 元素无 class 时套用 tag 规则（如 `body` / `h1`）
- 块之间零换行（避免微信把换行识别为段落分隔符）
- inline 化后总字节 +30%（每个元素 style 属性内联）

## 17. 拆篇约束

- WeChat 草稿 content 上限 64KB，建议 ≤ 60KB 更稳
- per-section-cap 默认 8；发布时可手动用 12
- parts=1：默认单篇，所有板块合并，必须 ≤64KB（建议 ≤60KB）
- parts=2：上 = GEO 服务商动态 + 国际市场；下 = 品牌方实战 + 工具平台更新 + 行业研究与数据
- parts=3：上 = GEO 服务商动态 + 国际市场；中 = 品牌方实战 + 工具平台更新；下 = 行业研究与数据
- 标题后缀：(上)/(中)/(下)，每个 26 字节（实际 API 接受 64 字节）
- 拆篇输出必须保留正文头部；不得把文章从第一个 `<h2>` 开始截断
- 推送版必须移除本地锚点目录链接（`href="#sec-*"`），保留 H2 的 `id` 可接受