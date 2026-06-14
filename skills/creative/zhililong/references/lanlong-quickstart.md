# zhililong 一键发布快速上手（Step 7 + Step 8）

> **适用场景**：用户说"写完直接发到草稿箱"/"一键发布到直隶按察使"时，按本文件 3 步走完全程。
> **不适用**：只想产出 markdown（不发布）→ 只跑 Step 1-6，跳过本文件。

## 最小可执行流程（3 命令）

```bash
# 假设你已经产出 body.md（7 节正文，无大纲无参考资料）
# 假设配图在 /tmp/concept_1.jpg 和 /tmp/concept_2.jpg

# ============ Step 7: 封面图 ============
python3 /Users/apple/.hermes/skills/zhililong/scripts/cover_pil.py \
  --title "20 亿美元买了一个寂寞" \
  --subtitle "中美 AI 资本博弈" \
  --output /tmp/lanlong_cover.jpg
# → 900×540 JPEG，~33KB，2 秒出图

# ============ Step 6: HTML 转码 ============
python3 /Users/apple/.hermes/skills/zhililong/scripts/markdown_to_html.py \
  /tmp/article-body.md /tmp/article.html
# 验证：grep -c '^$' /tmp/article.html 应为 0；grep mmbiz 应为空

# ============ Step 8: 一键发布（自动上传配图 + 创建草稿）============
python3 /Users/apple/.hermes/skills/zhililong/scripts/publish_lanlong.py \
  --title "20 亿美元买了一个寂寞" \
  --author "刘生" \
  --digest "Meta 与 Manus 的 20 亿美元收购被强制拆开，5 节深度拆解。" \
  --html /tmp/article.html \
  --cover /tmp/lanlong_cover.jpg \
  --image-locks /tmp/concept_1.jpg \
  --image-pathway /tmp/concept_2.jpg
# → 输出草稿 media_id + 写入同目录 upload_results.json
```

## 双文件模板（来自 Meta-Manus 拆伙实战 2026-06-14）

```python
# 在 Step 5 写完整 markdown 后，立即拆分 body 副本
import re
full_md = "/Users/apple/Projects/New-Radar/Final Report/transcripts/Meta-Manus-拆伙/公众号-Meta-Manus-拆伙.md"
body_md = "/tmp/article-body.md"

md = open(full_md, encoding="utf-8").read()
body = re.sub(r"## 大纲\n[\s\S]*?(?=## 一、)", "", md)  # 删大纲段
body = re.sub(r"\n## 参考资料[\s\S]*$", "", body)         # 删参考资料
open(body_md, "w", encoding="utf-8").write(body)
```

## 配图占位符约定

在写完整 markdown 草稿时，**预留占位符**，Step 8 一键替换：

```markdown
## 二、三件事一起看

[LOCKS_PLACEHOLDER]

北京这次要的是什么？...

## 四、港股今年这一波 AI 上市潮的暗线

[PATHWAY_PLACEHOLDER]

Manus 拟募 10 亿美元赎身...
```

`publish_lanlong.py` 会按 `--image-locks` 和 `--image-pathway` 顺序，把图片上传到 `uploadimg` 拿到 mmbiz URL，再替换占位符。

## 实际落地目录结构（来自 Meta-Manus 拆伙实战）

```
/Users/apple/Projects/New-Radar/Final Report/transcripts/Meta-Manus-拆伙/
├── 公众号-Meta-Manus-拆伙.md         ← 完整版（用户审稿）
├── 公众号-Meta-Manus-拆伙.html       ← 嵌好 mmbiz 的最终 HTML
├── 封面图-Meta-Manus.jpg              ← 900×540 封面
├── 配图-三道封锁.jpg                  ← 900×600 配图 1（→ LOCKS）
├── 配图-港股闭环.jpg                  ← 900×500 配图 2（→ PATHWAY）
└── upload_results.json                ← Step 8 输出（草稿 id + mmbiz URL）
```

## upload_results.json 示例

```json
{
  "draft_media_id": "kiuyle4KZHC7JKxpTQssMBA6dE_K0wyVH92gcWVuyF5uU_51cwECYHlLrWcCpjU_",
  "title": "20 亿美元买了一个寂寞",
  "author": "刘生",
  "cover": "/tmp/lanlong_cover.jpg",
  "mmbiz_urls": [
    "http://mmbiz.qpic.cn/mmbiz_jpg/.../locks.jpg",
    "http://mmbiz.qpic.cn/sz_mmbiz_jpg/.../pathway.jpg"
  ],
  "html_path": "/tmp/article.html",
  "published_at": "2026-06-14T13:15:42",
  "draft_url": "https://mp.weixin.qq.com/cgi-bin/appmsg?action=list&type=10"
}
```

## 失败模式速查

| 现象 | 原因 | 解决 |
|------|------|------|
| `mmbiz Gate 失败` | HTML 里没真含 mmbiz URL | 检查占位符是否被替换；grep -c mmbiz HTML 应 ≥ 1 |
| `author size out of limit` | 作者 > 4 字符 | 改成 ≤4 字（如"刘生"、"卡兹克"） |
| `title size out of limit` | 标题 > 16 字符 | 调用 `safe_title_shorten.py` 截短 |
| `digest 超 54 字节` | 摘要太长 | 缩到 18 个中文字以内 |
| `sandbox 脱敏 APPSECRET` | 在 `execute_code` 里写 inline Python | 改走 `publish_lanlong.py`（subprocess）避开 |
| 草稿链接打不开 | media_id 错位 | 重新跑 Step 8，检查 `upload_results.json` |

## 沙箱安全铁律

- **永远走 `publish_lanlong.py`**（subprocess 调 `publish_zhili.py`），不要在 `execute_code` 内联 Python
- **永远不要 print 任何 token**——`upload_results.json` 也不写 token，只写 media_id
- **永远不复制凭证到脚本**——`publish_zhili.py` 内置 `load_config()` 从 `references/config.md` 读

## 与 zhili-publish 的边界

| 这件事 | 走 zhililong | 走 zhili-publish |
|--------|--------------|------------------|
| 写 4000-5500 字长文 | ✅ 主职 | ❌ |
| 自动生成 900×540 封面图 | ✅ `cover_pil.py` | ❌ |
| AI 智能生成封面（SenseNova） | ❌ | ✅ `--cover-prompt` |
| 上传图片到 mmbiz | ✅ `publish_lanlong.py` 内部 | ✅ `upload_article_image` |
| 创建草稿 | ✅ `publish_lanlong.py` 内部 | ✅ `create_draft` |
| 短评（<800 字）发布 | ❌ | ❌ 用 zhilicomments-publish |

**铁律**：本 skill 的 Step 8 调 zhili-publish 的 `publish_zhili.py` 是**单方向**调用，**不反向依赖**。下次 zhililong 改代码不会破坏 zhili-publish，反之亦然。
