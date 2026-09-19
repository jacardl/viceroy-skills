# zhili-publish 样式 A 权威值

> 完整 CSS 块见 `../assets/style-a.css`。本文档列出关键颜色 / 字号 / 间距，供 SKILL 引用 + 模板改造参考。

## 色彩（CSS variables）

| 变量 | 值 | 用途 |
|---|---|---|
| `--bg` | `#f5f4ed` | body 背景米黄 |
| `--ink` | `#2c2c2c` | 正文墨色 |
| `--brand` | `#1B365D` | 主色墨蓝（H2 / h1 / 分类标签 / 链接） |
| `--accent` | `#00d4aa` | accent 绿（spicy 左边框） |
| `--rust` | `#c9553d` | 翻译标题红褐 |
| `--yellow` | `#fff3b0` | intro 背景 |
| `--muted` | `#7c6f64` | 灰色文字（元信息 / 二级） |

## 关键组件样式

| 组件 | 字号 | 颜色 | 间距 |
|---|---|---|---|
| body | 默认 | `--ink` | max-width 680px / padding 24/16/60 / line-height 1.85 |
| h1（标题） | 28px | `--brand` | margin 0 0 4px 0 / line-height 1.3 |
| h2（次级） | 13px | `--brand` | border-bottom 1px solid `#e3e0d4` / uppercase |
| .section-h2（板块标题） | 16px | `--brand` | border-bottom 2px solid `--brand` / 加粗 / padding-bottom 8px |
| .section-count | 12px | `--muted` | margin-left 6px |
| .item-cat（分类标签） | 12px | 白字 | 背景 `--brand` / 圆角 3px / padding 3px 8px |
| .item-title（条目标题） | 18px | `--brand` | display inline / 加粗 |
| .title-zh（中文翻译标题） | 17px | `--rust` | 加粗 / margin 6px 0 4px 0 / line-height 1.5 |
| .item-summary | 16px | 默认 | line-height 1.8 / margin 10px 0 |
| .meta（元信息） | 12px | `--muted` | margin 6px 0 0 0 |
| .meta-internal（内参标注） | 12px | `--muted` | italic（斜体） |
| .toc | 默认 | -- | background `#fbf8ef` / border-left 3px `--brand` |
| .footer | 12px | `--muted` | border-top 1px `#e3e0d4` |

## CSS 块原始位置

完整 CSS 块在 `src/geo_report/report/templates/weekly.html.j2` 的 `{% raw %}...{% endraw %}` 之间（line 8-260），已抽到 `../assets/style-a.css`。

## inline 化原理

- WeChat 不解析 `<style>` 块 + 类选择器
- 所有 CSS 必须 inline 到 `style="..."` 属性
- 元素无 class 时套用 tag 规则（如 `body` / `h1`）
- inline 化后总字节 +30%（每个元素 style 属性内联）
- 工具：`scripts/16_inline_css.py`

## 已知 bug + 修复

- ❌ inline 后 `<h2 style="..." id="sec-N" class="section-h2">` 的 class 在第 197 字节
- ✅ `scripts/15_split_zhili.py` 改用 `re.finditer` 自然顺序（不再用 200 字节窗口）