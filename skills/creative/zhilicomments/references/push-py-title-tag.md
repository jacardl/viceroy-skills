# push.py TITLE 默认值污染（2026-07-11 实坑）

## 问题描述

`scripts/push.py` 顶部有硬编码的 `TITLE` 和 `DIGEST` 默认值：

```python
TITLE = "Anthropic 的设计提示词被人扒出来开源了，还顺手教 AI 识别AI味儿"
DIGEST = "Anthropic 设计提示词被反向工程开源，14项技能里藏着AI味儿检测器"
```

如果 HTML 文件里没有 `<title>` 标签，`push.py` 会 fallback 到这两个默认值，导致**草稿标题是上一篇文章的标题**，静默错误。

## 症状

运行 `push.py --html /tmp/article.html` 后，打印出的标题是正确的，但草稿实际使用的是旧的默认值：
```
标题: Anthropic 的设计提示词被人扒出来开源了，还顺手教 AI 识别AI味儿 (39 字符)  ← 实际草稿标题
```

## 根因

`push.py` 第 445-446 行读取 HTML title：
```python
title_match = re.search(r"<title>(.*?)</title>", html)
live_title = title_match.group(1).strip() if title_match else TITLE  # ← 没有 title 标签就走 TITLE 默认值
```

## 修复

**每篇 HTML 必须在 `<body>` 标签前包含 `<title>` 标签：**

```html
<title>文章标题</title>
<body style="...">
<div style="...">
```

这样 push.py 就能正确提取标题，不会 fallback 到上一次的值。

## 相关坑

- `DIGEST` 也有同样问题，但 digest 是从 HTML 正文第一个 `<p>` 提取，通常不会漏
- 草稿创建后应在微信后台确认标题是否与 HTML 内容一致
