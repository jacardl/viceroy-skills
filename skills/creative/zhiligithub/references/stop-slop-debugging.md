# Stop-slop 检测假阳性调试指南

> 当 validate_zhili_article.py 报告「不是X是Y」×N 处，但你不确定哪些是真实问题、哪些是误报时，按本指南诊断。

## 已知设计缺陷（2026-07-02 已修复，但备查）

`check_stop_slop` 和 `check_renwei` 曾经使用全局正则：

```python
re.findall(r"不是.+?[，,].+?是", content)  # ❌ 旧版：跨段落匹配
```

`content` 是去 HTML 标签后的纯文本（整个文档拼成一个大字符串）。`.+?` 可以跨越 `</p><h2>` 等块级标签，吞掉 H2 里的 `是` 字符，导致**假阳性**。

典型假阳性场景：

| 句子 | 触发原因 |
|---|---|
| `还真不是炒概念。确实能跑起来。`（无逗号） | `不是炒概念` 的逗号在 01 段，但 `是` 出现在 02 段 H2「**怎么做**的是」里 |
| `你用的是透明存档系统；不是黑盒` | `；` 被渲染成 `，`，跨段匹配到 H2「MCP协议+多券商连接器+安全守卫」里的 `是` |

**已修复**（2026-07-02）：两个函数改为按段落 split 后分别检测，并跳过含 H2 标记的段落。

## 当脚本再次报「不是X是Y」时，快速诊断流程

```python
import re

with open('/tmp/vibe_trading_article.html') as f:
    html = f.read()

content = re.sub(r'<[^>]+>', '', html)

# 段落级检测（同当前版本）
paragraphs = re.split(r'(?:</p>|<br\s*/?>|\n){2,}', content)
for i, para in enumerate(paragraphs):
    if re.search(r'<h[1-6][^>]*>', para):
        continue  # 跳过含 H2 的段落
    if re.search(r'不是[^，。,\n]{1,40}[，,][^是\n]{1,40}是', para):
        print(f'段落 {i}: {repr(para.strip()[:80])}')
```

## 常见误报模式

1. **句中无逗号但被跨段匹配**：检查 `不是X` 句子是否在句尾有句号 `。` 而不是逗号
2. **H2 标题里的 `是`**：H2 含「做到了的是」「是什么」「对不对的是」等，`是` 不是正文句子
3. **`；` 被渲染成 `，`**：原文分号在 HTML 渲染后变成逗号，导致跨段误触

## 修复原则

- 不要用全局 `.+?` 跨段落匹配
- 先 split 段落，再在单段内检测
- 跳过含 `<h[1-6]>` 的段落（H2 标题里的 `是` 不代表正文有问题）
- 「不是X是Y」的语义问题：改写比删除更容易——把 `不是X是Y` → `并非X，也算不上Y`，或直接拆分两个分句

## validate 失败后的正确工作流（2026-07-14 hallmark 实坑）

当 validate_zhili_article.py 报告 renwei 命中率 ≥ 1 时，**不要在 HTML 上做修复**，按以下顺序操作：

```
validate 报告 N 处问题
  → 确认具体是哪一项（破折号 / 不是X是Y / AI黑话 / 套话词）
  → 回到 markdown 草稿（/tmp/hallmark_draft.md）
  → 在 markdown 中修复对应句子
  → re-render：python3 render_zhili_article.py draft.md article_new.html
  → 注入 mmbiz 图片、<title>
  → validate article_new.html
  → 确认 PASS 后再 push
```

**不要做的事**：
- ❌ 在 HTML 上用 `sed` / Python patch 修复——render 后注入的图片和标题会丢失，需要重新来过
- ❌ 用 `grep -o` 在 HTML 上手动搜索问题位置——`grep -o` 只显示匹配文本，没有前后文，很难判断哪句话触发了检测器
- ❌ 修复后不 re-render 直接 re-push——HTML 里残留的上一次渲染内容不会被 validate 扫描到，但 push 到微信草稿时用户会看到

**每次 render 后必须做的**（无论是否修改了 markdown）：
1. 重新注入 mmbiz 图片（如果是从头的 HTML 则需要重注）
2. 确认 `<title>` 已注入（render 脚本不生成 title）
3. validate 确认 PASS 后再 push

## 常见误报中需要特别说明的模式

**「UI 组件库」误触「不是X是Y」检测（2026-07-14 hallmark）**

正则 `不是[^，。安置]{1,40}[，,][^是\n]{1,40}是` 会在以下句子触发误报：

| 句子 | 检测结果 | 实际情况 |
|------|----------|----------|
| `Hallmark 不是 UI 组件库，也不是主题商店` | 「不是X是Y」| `UI` 是英文缩写，`不是` 后面没有「X」——整句是「不做 A 也不做 B」的意思，不是「不是 X 是 Y」结构 |

**解法**：遇到这类英文缩写的「不是」触发检测时，把句子改写成「不做 A，也不做 B」或「它不做 A，不做 B」，彻底去掉「是」字的二元对比结构。

**「落地」AI 黑话（2026-07-14 hallmark）**

```python
# ❌ 触发 AI 黑话检测
"SaaS 落地页"

# ✅ 改写
"SaaS 产品页"
```

「落地」属于 stop-slop AI 黑话池（落地 → 实施），在 SaaS / 产品类文章中极易出现。看到 validate 报 AI jargon 先查「落地」。

**「核心价值」赞美形容词（2026-07-14 hallmark）**

「核心价值」在 renwei 第 11 项「AI 赞美形容词」中，按「项」计不是按「次」计——同一篇文章出现 1 次算命中 1 项。改写策略：把「核心价值是 X」改成具体描述这件事解决了什么问题。
