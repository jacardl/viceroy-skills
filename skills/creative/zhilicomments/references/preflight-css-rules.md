# preflight CSS 精确匹配规则（2026-07-09 更新）

preflight.py 第 6/7 节对 CSS 的检查是**精确子串匹配**，不是模糊检查。以下是容易出错的地方，生成 HTML 时直接复制整段 style，不要拆开。

## H2 style 完整字符串

生成 HTML 时**完整复制这段**，不要拆开或改顺序：

```
font-weight:700;font-size:20px;color:#1B365D;border-left:4px solid #00d4aa;padding-left:12px;margin:0 0 16px 0
```

preflight 检查的子串是 `font-size:20px;color:#1B365D`（两者必须相邻，中间无其他属性）。

- `font-weight:700` 必须写在最前
- `font-size:20px` 和 `color:#1B365D` 必须相邻
- 缺少任何一个属性，或中间插入了其他属性，preflight 都会失败

## font-family 完整字符串

```
'Noto Serif SC', Georgia, serif
```

注意逗号后有空格。preflight 检查的是完整子串，缺少空格则不命中。

## body 背景色

```
background:#f5f4ed
```

不是 `background-color:`，是一律用 `background:`。

## P 段落

- 字号行高：`font-size:16px;line-height:1.85`
- 颜色：`color:#2c2c2c`
- 段距：`margin:0 0 28px`（不是 14px）

## 作者行

- 颜色：`#7c6f64`（不是 `#6b665b`）
- font-family：`'Noto Serif SC', Georgia, serif`（逗号后有空格，与 font-family 完整字符串一致）

## 来源行

```
font-family:monospace
```

## 常见失败原因

| 错误 | preflight 报错项 | 正确写法 |
|------|-----------------|---------|
| H2 写了 `font-size:20px;font-weight:700`（顺序反了） | H2 基础 | `font-weight:700;font-size:20px` |
| H2 在 `font-size` 和 `color` 之间插了其他属性 | H2 基础 | 完整 style 字符串直接复制 |
| font-family 逗号后没空格 | 字体栈（Noto 在前） | `'Noto Serif SC', Georgia, serif` |
| 作者行颜色用了 `#6b665b` | 作者行 | `#7c6f64` |
| 作者行字号用了 `14px` | 作者行 | `font-size:13px` |
| P 段距写了 `margin:0 0 14px` | P 段距 28px | `margin:0 0 28px` |
