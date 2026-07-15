# HTML 转码常见坑（zhililong → zhili-publish 衔接）

zhililong 产出的 HTML 要塞进微信草稿箱，必须避开这些坑。这些都是从"冰鉴"实战里踩出来的。

## 坑 1：`<` `>` 误转义破坏 HTML 标签

**问题**：
```python
# 错误：先转义再添加 <strong> 标签
b = b.replace("<", "&lt;")  # 把已有 <strong> 变成 &lt;strong
# 之后 add <strong> 标签 → 已经损坏
```

**结果**：
```html
<p>这一段有个<strong>重点</strong>。</p>
<!-- 被转义后变成：-->
<p>这一段有个&lt;strong&gt;重点&lt;/strong&gt;。</p>
<!-- 微信渲染成纯文本"<strong>重点</strong>" -->
```

**修复**：
```python
# 正确：先做完所有结构转换（含 <strong>），最后再转义非标签字符
# 或用 BeautifulSoup 解析后再 dump
# 或用正则只转义非标签内的 < >
import re
b = re.sub(r'(?<!<)\<(?!/?(?:strong|em|p|br|img)\>)', '&lt;', b)
```

## 坑 2：HTML 块内换行符导致微信渲染多余空行

**问题**：
```html
<p style="...">
  这是第一段内容
</p>

<p style="...">
  这是第二段内容
</p>
```
微信会把每个 `\n` + 紧跟的 `<` 识别为段落分隔符，产生"双倍空行"。

**修复**：
```python
# 正确：每个 block 完全内联一行，块间零分隔符
blocks = [
    '<p style="...">第一段内容</p>',
    '<p style="...">第二段内容</p>',
]
html = ''.join(blocks)  # ← 无任何分隔符
```

## 坑 3：margin-top + margin-bottom 叠加

**问题**：微信容器对 block 元素的 margin 会叠加，写 `margin:16px 0` 会变成 32px。

**修复**：**只设 margin-bottom，不用 margin-top**：
```html
<!-- ✅ 正确 -->
<p style="margin:0 0 16px 0;">段落</p>
<h2 style="margin:24px 0 12px 0;">标题</h2>

<!-- ⚠️ 危险：上下都设 -->
<p style="margin:16px 0;">段落</p>
```

## 坑 4：标题长度超限

微信限制 `title` ≤ 60 字节（UTF-8 中文 3字节/字）= ≤ 20 个中文字。

**实测安全范围**：≤ 16 个中文字。

**冰鉴案例**：`《冰鉴》的识人术，到底硬核在哪` = 15 字 + 4 个标点 = 49 字节 ✅

## 坑 5：作者长度超限

`author` 字段 ≤ 2 个中文字（API 限制，**超出必报 45003 author size out of limit**）。

**冰鉴案例**：`刘生` = 2 字 ✅

## 坑 6：图片格式

- **封面图**：`add_material?type=image` 接受 JPEG/PNG 都行，但建议 JPEG（体积小）
- **内容图**：`uploadimg` **只接受 JPEG**。PNG 必须先转：
  ```python
  img = Image.open(png_path)
  if img.mode != "RGB":
      img = img.convert("RGB")
  img.save(jpg_path, "JPEG", quality=88)
  ```

## 坑 7：HTML 中必须有 mmbiz URL

`publish_zhili.py` 有硬 Gate：HTML 不含 `mmbiz` URL 直接拒绝发布。

**修复**：
```python
# 上传图片后，URL 嵌入 HTML 第一段
mmbiz_url = upload_image(token, '/path/to/img.jpg')
html = html.replace('FIRST_PARAGRAPH', f'<img src="{mmbiz_url}" style="width:100%;..." />FIRST_PARAGRAPH')
```

## 坑 8：双层文章结构不一致

`draft/add` 字段是 **`articles` 复数数组**（不是 `content` 字符串，也不是 `content.news_item` 嵌套）。**以 publish_zhili.py 源码为准**：

```python
# ✅ 正确
{
    "title": "...",
    "articles": [{
        "title": "...",
        "content": html,
        "thumb_media_id": "...",
        ...
    }]
}

# ❌ 错误（44003 empty news data）
{
    "title": "...",
    "content": html,
}

# ❌ 错误（44003 empty news data）
{
    "title": "...",
    "content": {
        "news_item": [{...}]
    }
}
```

## 坑 9：sandbox 凭证脱敏

`execute_code` 写文件时会把 `APPSECRET=*** 整行替换**（含 `SECRET`/`PASSWORD`/`TOKEN` 关键词）。

**修复**：用 `os.popen("... | base64")` 读凭证，**不**在 Python 源码里出现明文 secret。

## 坑 10：空行残留

```bash
# 必查
grep -c '^$' /tmp/article.html
# 应为 0
```

如非 0，用 `cleanup_html.py` 清理（zhili-publish scripts/ 目录下）。

## 坑 11：三级标题 `### xxx` 被脚本吞掉

**问题**（2026-06-18 增广贤文实战发现）：

`markdown_to_html.py` **只识别 `##` 二级标题**，对 `###` 三级标题不做任何处理。结果 `### 5.1 命里有时终须有...` 这种子节标题，原文直接被当成普通段落输出，前面的 `### 5.1` 与正文流成一行：

```html
<!-- 输入 -->
### 5.1 命里有时终须有，命里无时莫强求
很多人看到这句，会觉得这是消极宿命论。

<!-- 输出（错误） -->
<p>...5.1 命里有时终须有，命里无时莫强求 很多人看到这句...</p>
<!-- 整段粘一起，"5.1 命里..." 失去视觉强调 -->
```

**修复**：子节用 `**5.1 xxx**` 加粗代替 `###`：

```markdown
## 五、命运与重构：命不强求，阿魏无真，青山在

这一节把《增广贤文》最后三句最深的金句放一起讲，因为它们是一个完整体系。

**5.1 命里有时终须有，命里无时莫强求**

很多人看到这句...
```

`<strong style="color:#e63946;">5.1 ...</strong>` 在微信渲染里视觉权重够用，且不会被脚本吞。

**为什么不修脚本**：当前 markdown_to_html.py 设计就是"只处理 ## / 段落 / 引用 / 加粗"4 种语法，加 `###` 支持会引入新 H3 样式决策（字号/颜色/层级），比 workaround 更脆。

## 坑 12：`> **...**` 引用块内加粗残留

**问题**（2026-06-18 增广贤文实战发现）：

行动段或反转段常出现这种结构——一句话很重要，想用 `**加粗**` 强调，再包在 `>` 引用里当"金句"：

```markdown
> **打开手机里任意一个家族群、同学群、老乡群，把你最近 6 个月发过的、关于自己收入、买房、跳槽、考证、转行、家人健康的核心信息，能删的删，能撤回的撤回。**
```

`markdown_to_html.py` 把整行 `> ` 后的内容当作 blockquote 文本输出，**不会二次处理内部的 `**...**` 加粗语法**。结果 HTML 里残留字面 `**`：

```html
<blockquote>**打开手机里任意一个家族群...删的删，能撤回的撤回。**</blockquote>
<!-- 微信渲染："**打开手机里..." 字面带星号，破坏阅读 -->
```

**修复**：blockquote 里**不要用 `**` 加粗**。如果一定要强调，把整句做成普通段落再用 `**加粗关键词**`：

```markdown
<!-- ✅ 正确：blockquote 内不加粗 -->
> 打开手机里任意一个家族群、同学群、老乡群，把你最近 6 个月发过的、关于自己收入、买房、跳槽、考证、转行、家人健康的核心信息，能删的删，能撤回的撤回。

<!-- ✅ 备选：纯段落 + 关键词加粗（牺牲引用块的视觉权重）-->
**打开手机里任意一个家族群、同学群、老乡群**，把你最近 6 个月发过的、关于自己收入、买房、跳槽、考证、转行、家人健康的核心信息，能删的删，能撤回的撤回。
```

**为什么不修脚本**：和坑 11 同理，blockquote 内做嵌套语法解析的复杂度 > workaround 的代价。
