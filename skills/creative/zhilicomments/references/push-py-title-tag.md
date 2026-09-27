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

## 已知残留问题（2026-09-04）

即使 HTML 包含 `<title>` 标签，push.py 有时仍输出旧缓存标题（与 HTML 内容完全不符）。今天实测：HTML 写明 `<title>OpenAI Astra：能力最强，透明度最差</title>`，但 push.py 终端输出显示 "GPT-6 Astra:编码追平 Fable 5，价格却翻 2.5 倍"。

**临时解法**：推送后在微信公众平台后台手动修正标题后再发布。

**注**：根因未完全确认，可能是 `/tmp/article.html` 在某次操作后被覆盖，或 push.py 对 title 标签有特殊解析逻辑。建议后续调试时，先 `cat /tmp/article.html | grep title` 确认标签内容，再执行 push.py。
