# HTML 配图注入规范

## img 标签插入位置

配图放在对应段落 `<p>` 或 `<h2>` **之后**，用 `<div>` 包裹居中：

```html
<p>文字内容...</p>

<div style="text-align:center;margin:32px 0;">
  <img src="mmbiz://MEDIA_ID" style="width:100%;max-width:660px;border-radius:8px;" />
</div>

<p>下一段文字...</p>
```

## 样式参数

| 属性 | 值 | 说明 |
|------|-----|------|
| `text-align` | `center` | 居中 |
| `margin` | `32px 0` | 上下 32px，左右 0 |
| `width` | `100%` | 响应式宽度 |
| `max-width` | `660px` | 公众号正文最大宽度 |
| `border-radius` | `8px` | 圆角 |

## 比例与 max-width 映射

| 比例 | max-width | 适用场景 |
|------|-----------|---------|
| 4:3 | 660px | 横图（流程图/对比图） |
| 3:4 | 495px | 竖图（漏斗/阶梯/纵向） |
| 1:1 | 495px | 方图（单概念） |
| 封面 2.35:1 | 900×383px | 封面图 |

## mmbiz 协议 vs 本地路径

| 阶段 | src 值 | 示例 |
|------|--------|------|
| 本地调试 | 本地文件路径 | `src="/tmp/illustrations/img_01.png"` |
| 推送草稿前 | `mmbiz://` + media_id | `src="mmbiz://abc123xyz"` |

**绝对不要**在推送草稿箱时使用本地路径，必须先上传获取 media_id 再替换。

## 多个配图的段落结构示例

```html
<h2>一、开头钩子</h2>
<p>故事文字...</p>
<div style="text-align:center;margin:32px 0;">
  <img src="mmbiz://xxx001" style="width:100%;max-width:660px;border-radius:8px;" />
</div>

<h2>二、机制解释</h2>
<p>解释文字...</p>
<div style="text-align:center;margin:32px 0;">
  <img src="mmbiz://xxx002" style="width:100%;max-width:495px;border-radius:8px;" />
</div>

<p>继续文字...</p>
```

## 常见错误

1. **在草稿箱推送前没有上传**：微信草稿箱无法显示本地路径图片
2. **比例填错**：3:4 的图用了 max-width:660px，导致图片在手机上被裁剪过多
3. **缺少 text-align:center**：图片左对齐而不是居中
4. **margin 用了 margin-top**：应该只用 `margin:32px 0`（上下），不混用 margin-top
