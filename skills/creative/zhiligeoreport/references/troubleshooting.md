# 故障排查表

| 症状 | 根因 | 修复 |
|------|------|------|
| obsidian 旧文件重新同步后误入周报 | 旧逻辑用 `mtime` / `fetched_at` 兜底，iCloud 同步会刷新 | v1.22 起只认 `meta_json.created_at` + `published_at`；`mtime` 只审计 |
| 行业搜索新增 0 条 | 原文页没有发布时间或发布时间早于 7 天 | 正常，宁缺毋滥；不放宽为 `fetched_at` |
| 验证门禁违规 "title_zh 不含中文" | GT 漏翻企业名/术语 | `translate_zh_batch` 已自动回退 minimax；若仍违规，给标题加 min() 处理 |
| 验证门禁违规 "summary 不含中文" | summarize_full_article 抓 article / LLM / 翻译均失败 | 空摘要由门禁剔除；禁止截原文兜底 |
| "0 条" 空板块显示 | template 不过滤空 section | j2 加 `{% if sec.items %}` |
| obsidian 内容是原文 markdown | obsidian:// URL httpx 抓不到 → 旧 fallback 截原文 | obsidian 走独立路径强制 LLM 总结；失败置空并由门禁剔除 |
| PER_SOURCE_CAP 太严卡掉独立主题 | sid=104 search 聚合源一个 query 多次刷复占 cap | search 源 bypass cap + source 内去重 |
| 标题含 GEO 但 body 是 Geo 化妆品等品牌歧义 | false positive | 已加 18 条 GEO_FALSE_POSITIVE_PATTERNS |
| 客户品牌词条未剔除 | has_client_brand 漏判 | 维护 `CLIENT_BRAND_PATTERNS`，持续补全 |
| 草稿/标记未剔除 | has_draft_marker 漏判 | 维护 `DRAFT_PATTERNS`，含 brief / RFP / 标书等 |
| 渲染 HTML 含原始 markdown 残留 | obsidian frontmatter 没剥 | 走 obsidian 独立 collector，强制剥 `---\n...\n---` |
| WeChat 草稿箱无样式 / 类选择器不渲染 | inline 化未做 / `<style>` 块残留 | 重跑 `scripts/16_inline_css.py` 后再推 |
| 拆篇后 partN 字节爆炸（>100KB） | h2 切分用 200 字节窗口查 class=，inline 后超窗口 | 用 `re.finditer` 自然顺序（已修） |
| 推草稿箱报 invalid media_id | `draft/get` API 限制（draft/add 成功但 get 查不到） | 用微信公众平台后台验证；不依赖 get API |
| 标题超 22 字节 | 中英文混排字节数算错 | `(上)/(中)/(下)` 后缀每个 5 字节，总 26 字节，OK |
| 板块分类错位（旧行业混入） | 旧 classify 行业链或工具残留 | v1.18.1 门禁只允许 5 角色章节，其余剔除 |
| 抓 source 连续 3 次失败 | 信源抓取故障 | `enabled = false` + 写 errors 表 + 告警 |
| translate minimax 429 | 并发 8 触发限速 | 失败 fallback 走 GT；降低 concurrency |
| 摘要 < 100 字 | 短内容源 | 走 `enrich_short_summary_batch` LLM 扩写（v1.0 强化） |
| 端到端 `publish-weekly` 失败但 render 成功 | inline 化 / split / push 任一步失败 | 看 stdout 错误行号定位是 Step 3 / 4 / 5 |
| v1.19 强 GEO 阶段剔除大量条目 | 标题 < 10 字 / 正文 < 300 字 / 中文占比 < 30% | **正常**：宁缺毋滥；obsidian 内参仍占满内参板块 |
| 转载 obsidian md 标题是 mp.weixin.qq.com URL | 首行裸 URL 被当 title | `_extract_title_and_body` 跳过 URL 行，# 标题兜底 |