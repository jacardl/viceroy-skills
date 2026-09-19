# 故障排查表

| 症状 | 根因 | 修复 |
|------|------|------|
| 验证门禁违规 "title_zh 不含中文" | GT 漏翻企业名/术语 | `translate_zh_batch` 已自动回退 minimax；若仍违规，给标题加 min() 处理 |
| 验证门禁违规 "summary 不含中文" | summarize_full_article 抓 article 失败 fallback | 已改为 `translate_zh` 兜底 |
| "0 条" 空板块显示 | template 不过滤空 section | j2 加 `{% if sec.items %}` |
| obsidian 内容是原文 markdown | obsidian:// URL httpx 抓不到 → fallback 失败 | obsidian 走独立路径强制 LLM 总结 + 剥 frontmatter |
| PER_SOURCE_CAP 太严卡掉独立主题 | sid=104 search 聚合源一个 query 多次刷复占 cap | search 源 bypass cap + source 内去重 |
| 标题含 GEO 但 body 是 Geo 化妆品等品牌歧义 | false positive | 已加 18 条 GEO_FALSE_POSITIVE_PATTERNS |
| 客户品牌词条未剔除 | has_client_brand 漏判 | 维护 `CLIENT_BRAND_PATTERNS`，持续补全 |
| 草稿/标记未剔除 | has_draft_marker 漏判 | 维护 `DRAFT_PATTERNS`，含 brief / RFP / 标书等 |
| 渲染 HTML 含原始 markdown 残留 | obsidian frontmatter 没剥 | 走 obsidian 独立 collector，强制剥 `---\n...\n---` |
| WeChat 草稿箱无样式 / 类选择器不渲染 | inline 化未做 / `<style>` 块残留 | 重跑 `scripts/16_inline_css.py` 后再推 |
| 拆篇后 partN 字节爆炸（>100KB） | h2 切分用 200 字节窗口查 class=，inline 后超窗口 | 用 `re.finditer` 自然顺序（已修） |
| 推草稿箱报 invalid media_id | `draft/get` API 限制（draft/add 成功但 get 查不到） | 用微信公众平台后台验证；不依赖 get API |
| 标题超 22 字节 | 中英文混排字节数算错 | `(上)/(中)/(下)` 后缀每个 5 字节，总 26 字节，OK |
| 板块分类错位（"医药 GEO" 归到 GEO 技术科普） | 旧 classify 8 行业优先链冲突 | v1.17 改成 2 板块后分类规则互斥 |
| 抓 source 连续 3 次失败 | 信源抓取故障 | `enabled = false` + 写 errors 表 + 告警 |
| translate minimax 429 | 并发 8 触发限速 | 失败 fallback 走 GT；降低 concurrency |
| 摘要 < 100 字 | 短内容源 | 走 `enrich_short_summary_batch` LLM 扩写（v1.0 强化） |
| 端到端 `publish-weekly` 失败但 render 成功 | inline 化 / split / push 任一步失败 | 看 stdout 错误行号定位是 Step 3 / 4 / 5 |