# render_zhili_article.py 工作流要点（2026-07-16 实战）

## Bug 1：渲染后自动生成「六、总结」H2

render_zhili_article.py 会将 markdown 中「## 总结」识别为 H2 并生成带样式A边框的标签。但 zhiligithub 规范明确规定总结段**无 H2**（总结内容跟在五、实战场景的 `· · ·` 之后直接流入）。

**处理流程**：
1. `python3 scripts/render_zhili_article.py draft.md article.html`
2. 打开 HTML，找到 `<h2>六、总结</h2>` 整段（包含后续所有段落直到下一个 H2 或 `📌 数据来源`），全部删除
3. 注入 `<title>` 标签
4. 继续验证

## Bug 2：HTML 修改在重新渲染后会丢失

如果验证失败需要扩充内容或修复 renwei 问题，**正确的做法**是：
1. 打开原始 markdown draft（`/tmp/draft_xxx.md`）
2. 在 markdown 里扩充/修改内容
3. 重新运行 `render_zhili_article.py`
4. 重新注入 title，重新注入图片
5. 再验证

如果在 HTML 里直接改了内容，下次渲染会把所有改动覆盖。

## Bug 3：「不是X是Y」检测的边界问题

validate_zhili_article.py 用的检测 regex 是：
```
不是[^，。,\n]{1,40}[，,][^是\n]{1,40}是
```

这意味着从「不是」到文本中**任意**「是」字（最宽40字符）都会被捕获。常见误伤：

- `不是只看到「图片」，能理解「这张表格有哪几列，这页 PPT 的标题是什么」`
  → 被「标题是什么」的「是」触发
  → 修复：改为 `不只是看到「图片」，还能读出表格列数、PPT 标题、Sheet 排序方式这些结构信息`

- `问题不是 A，而是 B`
  → 被「不是...而是...」中间的「而是」触发（实际上这里的「是」是系动词，不是二元判断词）
  → 修复：`问题不在于 A，而在于 B` 或直接改写为平述句

**安全写法**：彻底避免「不是……，……是……」结构，用平行否定或直接陈述代替。

## GitHub 素材获取 Fallback（raw 超时）

当 `raw.githubusercontent.com` 超时时（服务器网络策略限制），备选方案：

1. **GitHub OG 图**（最可靠）：
   ```
   https://opengraph.githubassets.com/1/{owner}/{repo}
   ```
   用 `urllib.request` + SSL context 下载，不需要认证。

2. **GitHub API + base64 解码**：
   ```python
   GET https://api.github.com/repos/{owner}/{repo}/contents/{path}
   # response['content'] 是 base64 编码，解码后写入文件
   ```

3. **上传到微信**：
   - OG 图格式：`image/png`，上传用 `type=image`
   - 获取 `media_id` 用于草稿创建
   - 获取 `url`（mmbiz）用于 HTML 正文内嵌
