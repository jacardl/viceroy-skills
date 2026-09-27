# 内容抓取引入的 Unicode 伪标点（2026-08-07 新增）

网页内容通过 curl/python 提取时，会产生 `、、`（双 ideographic comma）序列。preflight 的标点扫描**不检测此项**，会静默通过，但文章里出现 `、、` 极不正式。

## 高危场景

- 提取英文报道时，连续逗号被拼在一起变成 `、、`
- 原文的 `,` 在中文标点映射过程中被错误处理

## 症状

- preflight 标点扫描全部通过（0 次冒号、0 次破折号、0 次双引号）
- 但文章里肉眼可见 `记住了、、` 这样的双逗号伪标点
- 微信草稿里出现不规范的标点序列

## 解法

preflight 通过后，额外扫描并清理：

```python
with open('/tmp/article.html', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace('、、', '，')  # 双逗号 → 正常逗号
content = content.replace('。。', '。')  # 双句号 → 正常句号
with open('/tmp/article.html', 'w', encoding='utf-8') as f:
    f.write(content)
```

## 为什么 preflight 漏报

preflight 的标点扫描只检查以下三项：
- `：` 中文冒号（U+FF1A 和 U+65306）
- `——` 中文破折号（U+2014 双连）
- `""` 英文双引号

`、、`（U+3001 ideographic comma 双连）不在检查范围内，所以 preflight 静默通过。

> **这不是 preflight bug**——preflight 按设计检查这三项，不检查其他标点。
> **这是写作流程的盲区**——内容抓取引入的伪标点需要额外清理步骤。
