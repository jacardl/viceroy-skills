# 关键约束（v1.15 / v1.16 / v1.17 累积）

> 写代码时违反会进验证门禁违规清单 + 自动从 section 剔除。

## 1. 严格 7 日窗口

- `published_at` 优先；无则用 `fetched_at` 兜底
- obsidian 源强制走 `published_at`（文件 mtime），不用 `fetched_at` 兜底
- 防 `ON CONFLICT DO UPDATE` 刷新 fetched_at 让老 obsidian 文件复活
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

## 6. 双语翻译（`translate_zh_batch`）

- GT 的 `sl=auto`（**不是 en**），自动检测波兰/捷克/荷兰/法语
- GT 翻译后若 `title_zh` 不含中文字符 → 自动回退到 `translate_zh` 走 minimax LLM 兜底
- 抓 article 成功但 LLM 总结失败 → 兜底调用 `translate_zh`（minimax + GT 双层），保证 summary 永远是中文
- 标题上限 40 字（截到 80 字兜底），正文上限 500 字（截到 500 字兜底）
- 并发默认 concurrency=8（`httpx.AsyncClient`）
- 限速：minimax 走 OpenAI 配额；GT 匿名端点限速约 100 req/min

## 7. obsidian 强制 LLM 总结（≤500 字）

- 剥 YAML frontmatter（`---\n...\n---\n`）再喂 LLM
- LLM 失败兜底：`_strip_body_commentary` + 截前 500 字

## 8. 每信源 max 5 条（PER_SOURCE_CAP=5）

- search 聚合源（`source_type='search'`）不参与 cap

## 9. source 内近标题去重（v1.13.3）

- `(source_id, date, title[:24])` 去重
- 同一 source 同日同一主题只占 1 个 cap 槽位

## 10. 每板块最多 N 条（PER_INDUSTRY_CAP）

- 按 `geo_score` 降序截断
- 防 search 源把单 section 占满

## 11. HTML 模板约束

- 模板：`src/geo_report/report/templates/weekly.html.j2`
- 标题：「刘生 GEO 周报」
- 内参标注：「📚 来自内参」
- toc 和 section 都过滤空 section（`{% if sec.items %}`）
- 包含完整 zhili-publish 样式 A
- 目录/正文都用零换行内联 style（WeChat 渲染友好）

## 12. 验证门禁 4 项（`scripts/13_render_only.py` 自动跑）

1. **相关性**：title 或 summary 必须含 `GEO|AI 搜索|AI search|AI research|生成式引擎`
2. **板块分类合法性**：`it.industry` 必须 ∈ {`geo_tech_science`, `geo_industry_dynamics`}（v1.17 后）
3. **中文翻译**：title 不含中文时，`title_zh` 和 `summary_zh` 都必须含中文字符（**不是非空**）
4. **时效性**：`published_at` 距今天 ≤ 7 日

## 13. inline CSS 化约束（WeChat 兼容）

- WeChat 不解析 `<style>` 块 + 类选择器
- 所有 CSS 必须 inline 到 `style="..."` 属性
- 元素无 class 时套用 tag 规则（如 `body` / `h1`）
- 块之间零换行（避免微信把换行识别为段落分隔符）
- inline 化后总字节 +30%（每个元素 style 属性内联）

## 14. 拆篇约束

- WeChat 草稿 content 上限 64KB，建议 ≤ 60KB 更稳
- per-section-cap 默认 12
- parts=2：上 = GEO 技术科普 + 医药 + 本地服务；下 = 其他
- parts=3：上 = GEO 技术科普 + 医药 + 本地服务；中 = 消费品 + 高客单；下 = 电商 + B2B SaaS
- 标题后缀：(上)/(中)/(下)，每个 26 字节（实际 API 接受 64 字节）