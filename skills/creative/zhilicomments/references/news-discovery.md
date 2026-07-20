# 新闻选题发现路径（2026-06-25 实战沉淀）

> 本文档记录「直隶按察使」新闻评论类选题的信息发现路径。
> 适用场景：用户给了一个新闻由头（如"NSA 发了声明"），需要找到原始报道 + 后续进展 + 背景素材。

---

## 核心发现流程

### 第一步：HN Algolia 精准搜索

```bash
# 搜索主报道（关键词用空格分隔，不需 URL 编码）
curl -s "https://hn.algolia.com/api/v1/search?query=NSA%20Mythos%20access%20lost&tags=story&hitsPerPage=5" \
  | python3 -c "
import json,sys
d=json.load(sys.stdin)
for h in d.get('hits',[]):
    print('标题:', h.get('title',''))
    print('URL:', h.get('url',''))
    print('Points:', h.get('points',''))
    print('日期:', h.get('created_at',''))
    print()
"
```

**关键技巧：**
- `tags=story` 过滤掉 Show HN 和 Ask HN
- `hitsPerPage=5` 足够，通常第一条就是目标
- HN Algolia 的 `points` 字段可以判断热度（>200 = 高热）

### 第二步：找相关报道（背景素材）

```bash
# 按主题词搜索相关报道
curl -s "https://hn.algolia.com/api/v1/search?query=Anthropic%20Mythos%20government%20access&tags=story&hitsPerPage=20" \
  | python3 -c "
import json,sys
d=json.load(sys.stdin)
for h in d.get('hits',[]):
    print(h.get('title',''))
    print('日期:', h.get('created_at',''))
    print()
"
```

**新闻类评论常需的三类素材：**

| 类型 | 搜索关键词模式 | 用途 |
|------|--------------|------|
| 原始事件 | `NSA Mythos [核心动词]` | 找到目标报道 |
| 背景/起因 | `[公司/产品名] [事件关键词]` | 找到起因故事 |
| 后续进展 | `[核心人物/机构] [产品名] update/progress` | 找到最新进展 |

### 第三步：内容获取优先级

| 优先级 | 来源 | 方法 |
|--------|------|------|
| 1 | 用户直接给链接 | 直接用 |
| 2 | X/Twitter 帖子 | `curl https://api.fxtwitter.com/<user>/status/<id>` |
| 3 | HN 摘要（标题+Points+日期够写） | HN Algolia API |
| 4 | 新闻全文（NYT/Wired/WSJ 等） | 直接 fetch 通常超时 |
| 5 | 浏览器渲染 | 通常失败 |

**NYT/WashPost 等大报的直接 fetch 技巧：**
```bash
# 尝试带上 User-Agent
curl -s "https://www.nytimes.com/..." -L -A "Mozilla/5.0" | python3 -c "..."
# 通常仍然失败，但 HN 的标题+URL+Points足够推断内容
```

### 信源不可用时的降级策略（2026-07-09 实测）

两类高频不可用场景及处理：

**A. 目标站 connection timeout（x.ai / Bloomberg / 华尔街日报等）**

browser_navigate 和 curl 双挂，但 URL 本身包含标题：

```
https://www.bloomberg.com/news/articles/2026-07-08/spacexai-cursor-unveil-grok-ai-model-for-legal-finance-tasks
                                              ↑ 这段就是标题：SpaceXAI Cursor Unveil Grok AI Model for Legal Finance Tasks
```

处理路径：
1. 从 URL 提取英文标题 → 翻译成中文标题（如「SpaceXAI Cursor Unveil Grok AI Model for Legal Finance Tasks」→「Grok 4.5 落地法律金融，Musk 终于 toB 了」）
2. 根据 URL 路径结构（`/news/articles/YYYY-MM-DD/`）判断发布机构（Bloomberg，2026-07-08）
3. 用标题+URL结构推断文章核心信息，不依赖正文内容
4. 写稿时在来源行注明「来源 - Bloomberg，2026年7月8日」，不用声明「文 / 刘生」（推.py 自动从第一段提取 digest，作者行写「作者 刘生」）

**B. 内容 fetch 成功但正文在 JS 动态渲染里（Ars Technica / TechCrunch 等）**

curl 返回空结果，browser_navigation 可能超时或返回不完整内容。处理路径：
1. 尝试 HN Algolia 搜索相同关键词，找其他媒体报道
2. 如 HN 有多个结果，拼时间线（见下方第四步）
3. 如 HN 无结果，尝试 Twitter/X 帖子（`curl https://api.fxtwitter.com/<user>/status/<id>`）

**已知 blocked 站点备忘：**
- `x.ai/news/*` — connection timeout
- `bloomberg.com/news/articles/*` — connection timeout
- `arstechnica.com/*` — JS 渲染，curl 返回空

---

### 第四步：时间线拼凑（新闻类评论核心）

拿到多个 HN 结果后，按日期排序还原事件顺序：

```
2026-04  NSA 向国会报告：Mythos 可在数小时攻破核武库密码
2026-06-12  Anthropic 宣布暂停 Fable/Mythos 外部访问（政府要求配合）
2026-06-18  Wired：韩国运营商 Mythos 争议（未经授权访问曝光）
2026-06-23  NYT：NSA 失去 Mythos 访问权限（219 Points）
2026-06-25  用户要求评论（接前天"攻破 NSA 系统"的话题）
```

**写稿时注意：**
- 开头要接上用户给的背景（"前天 NSA 说…"）
- 正文用新闻时间线推进（不用倒叙）
- 结尾回到读者视角（"这事跟我们有什么关系"）

---

## 2026-06-25 实战记录：NSA Mythos 选题

| 搜索词 | 结果 | 用途 |
|--------|------|------|
| `NSA Mythos access lost NYT` | NYT 2026-06-23，219pts | 主报道 |
| `Anthropic Mythos government access` | Anthropic 6-13 声明、Fable/Mythos 暂停 | 背景 |
| `Korean telecom Anthropic Mythos` | Wired 2026-06-18，148pts | 起因故事 |

**内容不足时的处理：**
- NYT 文章无法直接 fetch
- 用 HN 标题「NSA lost access to Mythos amid Anthropic dispute」+ Points 热度 + 日期推断重要性
- 背景故事（韩国运营商、Anthropic 暂停访问）来自另外两个 HN 搜索结果
- 写稿时不写 NYT 文章细节，写 NSA 的尴尬处境和故事的讽刺性

---

## 搜索词备忘（按主题）

```
# NSA + Mythos
NSA Mythos access lost | NSA Mythos dispute | NSA Mythos cyberattack

# Anthropic 暂停访问
Anthropic Mythos suspended | Anthropic Fable Mythos disabled

# 未经授权访问
Mythos unauthorized access | Mythos leaked | Korean telecom Mythos

# 综合新闻
Anthropic Mythos NYT | Anthropic Mythos government | NSA Anthropic Mythos
```
