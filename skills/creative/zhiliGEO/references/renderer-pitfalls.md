# render_zhili_article.py 已知限制（2026-09-06 实测）

## 1. H2 只认 `## ` 格式，不认中文数字标题

**现象**：`zhiliGEO` 文章习惯用「一、」「二、」作为章节标题写在 markdown 里，但 `render_zhili_article.py` 的 `md_to_blocks()` 只识别以 `## ` 开头的行作为 H2 块。

**实测**：
- 输入：`一、信源路径，豆包是封闭池，千问是搜索搬运工`
- 输出：H2 数量 = 0，左边框样式全丢，整个章节变成普通段落

**解法**：写稿时直接用 `## 一、信源路径，豆包是封闭池，千问是搜索搬运工`，不要写纯中文数字 `一、`。

```python
# 内部检测逻辑（render_zhili_article.py 第134行）：
if stripped.startswith("## "):
    blocks.append(("h2", stripped[3:].strip()))
# 只会匹配 "## xxx"，不会匹配 "一、xxx"
```

**规律**：zhiligithub 和 zhiliGEO 共用同一个 `render_zhili_article.py`。zhiligithub 写稿默认就是 `## ` 格式，所以没这个问题。zhiliGEO 写稿时容易沿用内部文档习惯写 `一、`，从而触发此坑。

**结论**：zhiliGEO 写稿规范——章节标题必须以 `## ` 开头，禁止用纯中文数字 `一、` 开头的行作为章节标题。

## 2. 封面图走 `material/add_material`，正文配图走 `media/uploadimg`

**两张图走不同接口**：

| 图类型 | 接口 | 返回字段 | 用途 |
|--------|------|---------|------|
| 封面图 | `material/add_material?type=image` | `media_id` | `draft/add` 的 `thumb_media_id` |
| 正文配图 | `media/uploadimg` | CDN URL（`http://mmbiz.qpic.cn/...`） | 写入 HTML `img src` |

**坑**：两者的 `media_id` 格式不同，混用会报 40007 invalid media_id。

## 3. push.py 超时处理（配图 ≥2 张时）

**现象**：`push.py` 生成+上传 2 张配图约 40–60s，整体 120s 内几乎必然超时。

**解法**：配图已在外部生成并通过 `media/uploadimg` 拿到 CDN URL 的场景下：
1. CDN URL 直接写入 HTML 的 `img src`
2. 推送时加 `--skip-illustration`（跳过生成+上传流程）
3. 草稿箱 WebView 直接用 CDN URL 渲染

## 4. 破折号 `——` 是 renwei 验证器红线

**实测**：renwei 11 项检测里，破折号命中率独立计 1 分，≥3 分才打回。但 stop-slop 清单里破折号要求 0 处。

**解法**：正文里所有 `——` 必须在渲染前清掉，不要留着等 renwei 判断。
