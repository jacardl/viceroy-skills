# zhililong 一键发布快速上手（Step 7 + Step 8）

> **适用场景**：用户说"写完直接发到草稿箱"/"一键发布到直隶按察使"时，按本文件 3 步走完全程。
> **不适用**：只想产出 markdown（不发布）→ 只跑 Step 1-6，跳过本文件。

## 最小可执行流程（4 命令）

```bash
# 假设你已经产出 body.md（7 节正文，无大纲无参考资料）

# ============ Step 7: 封面图（走 zhili-illustration）=============
python3 ~/.hermes/skills/creative/xiaohu-ip-studio/scripts/run_mmx.py \
  --prompt-file /tmp/cover_prompt.md --out /tmp/cover_16x9.png
# PIL 裁剪到 900×383
python3 -c "
from PIL import Image; img = Image.open('/tmp/cover_16x9.png')
w,h = img.size; target = 900/383
if w/h > target: new_w = int(h*target); left=(w-new_w)//2; img=img.crop((left,0,left+new_w,h))
else: new_h=int(w/target); top=(h-new_h)//2; img=img.crop((0,top,w,top+new_h))
img.resize((900,383), Image.LANCZOS).save('/tmp/cover_final.png','PNG')
"

# ============ Step 6: HTML 转码 ============
python3 /root/.hermes/skills/creative/zhililong/scripts/markdown_to_html.py \
  /tmp/article-body.md /tmp/article.html
# 验证：grep -c '^$' /tmp/article.html 应为 0

# ============ 配图生成（手动，zhili-illustration）==============
# 生成 5 张配图 → 上传到微信素材 → 拿到 media_id → 注入 HTML（见"配图工作流"章节）

# ============ Step 8: 一键发布（HTML 已含 img 标签，直接推送）======
python3 /root/.hermes/skills/creative/zhililong/scripts/publish_lanlong.py \
  --title "文章标题" \
  --author "刘生" \
  --digest "文章摘要（≤54字节）" \
  --html /tmp/article_with_imgs.html \
  --cover /tmp/cover_final.png
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

## 配图工作流（重要！）

`publish_lanlong.py --skip-illustration` 会跳过**配图生成 AND HTML 注入**。如果跳过配图后发现草稿没有图，没有任何局部更新机制，只能重建完整 HTML + 重新推送。

**正确流程（配图在前，推送在后）**：

```
1. 生成图片（zhili-illustration，手动调用 xiaohu-ip-studio）
2. 上传到微信素材获取 media_id（uploadimg API，返回 mmbiz://xxx）
3. 手动注入 img 标签到 HTML（每张图对应一个 H2 章节之后的第一个 </p> 位置）
4. 调用 publish_lanlong.py 时【不要】传 --skip-illustration
   → 脚本会跳过配图生成但【不会】跳过 HTML 封面上传 + 创建草稿
```

**手动注入 img 标签**（Python 示例）：
```python
media_ids = {"01": "t5YJ4C8cRSErGljGN...", "02": "t5YJ4C8cRSErGljGN..."}
for num, mid in media_ids.items():
    img_html = f'<div style="text-align:center;margin:32px 0;"><img src="mmbiz://{mid}" style="width:100%;max-width:660px;border-radius:8px;" /></div>'
    marker = f'<p...>VIE架构能否讲得圆</p>'   # H2 章节关键词
    pos = html.find(marker) + len(marker)
    end_pos = html.find('</p>', pos) + len('</p>')
    html = html[:end_pos] + img_html + html[end_pos:]
```

**补发草稿（草稿已有但缺图）**：
```bash
# 1. 重建含图的 HTML
# 2. 删除旧草稿（--delete-first），再推新草稿
python3 scripts/publish_lanlong.py \
  --title "文章标题" --author "刘生" --digest "摘要" \
  --html /path/to/article_with_imgs.html \
  --cover /path/to/cover_final.png \
  --delete-first kiuyle4KZHC7JKxp... \  # 旧草稿 media_id
  --skip-illustration   # 跳过封面重生成（已有封面）
```

## 失败模式速查

| 现象 | 原因 | 解决 |
|------|------|------|
| `errcode 40007 invalid media_id`（草稿推送） | cover 图的 media_id 类型错误 | **必须用 `type=thumb` 上传封面**，拿到的 media_id 才能作为 thumb_media_id；`type=image` 拿到的 media_id 推草稿会报 40007 |
| `errcode 40006 invalid media size` | 封面图 > 64KB | PIL 压缩到 ≤64KB 再上传（`quality=85` 通常够）；不要用 PNG（太大），压成 JPEG |
| 草稿推送成功但无配图 | 用 --skip-illustration 且没有提前注入 img 标签 | 重建 HTML + --delete-first 重新推送 |
| `mmbiz Gate 失败` | HTML 里没真含 mmbiz URL | grep mmbiz HTML 应 ≥ 1；没图则补注后再推送 |
| `author size out of limit` | 作者 > 4 字符 | 改成 ≤4 字（如"刘生"、"卡兹克"） |
| `title size out of limit` | 标题 > 16 字符 | 调用 `safe_title_shorten.py` 截短 |
| `digest 超 54 字节` | 摘要太长 | 缩到 18 个中文字以内 |
| `sandbox 脱敏 APPSECRET` | 在 `execute_code` 里写 inline Python | 改走 `publish_lanlong.py`（subprocess）避开 |
| 草稿链接打不开 | media_id 错位 | 重新跑 Step 8，检查 `upload_results.json` |
| 配图媒体ID无效（预览黑图） | media_id 过期或类型错误 | 重新上传 img，用新 media_id 替换 HTML 中旧值，再推 |

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
