# zhili-illustration + zhililong 配图工作流（2026-07-08 实战沉淀）

## 核心要求：markdown 必须用 `##` 标记章节

`markdown_to_html.py` 转码器**只识别 `##` 语法**来生成 H2 标签：

```
## 一场劳动纠纷如何走到港交所桌前   ← ✅ 生成 <h2>
一场劳动纠纷如何走到港交所桌前       ← ❌ 不生成 <h2>
```

`publish_lanlong.py` 的 `extract_shot_list()` 依赖 H2 标签来：
1. 确定配图数量（最多 5 张）
2. 定位每个配图的注入位置（每个 H2 后面一张）
3. 生成配图 prompt（提取 H2 后的第一段作 context）

**如果 markdown 没有 `##`，转出来的 HTML 有 0 个 H2，配图流程全面失败。**

### 诊断方法

```python
import re
with open("article.html") as f:
    html = f.read()
h2s = re.findall(r'<h2[^>]*>(.*?)</h2>', html, re.DOTALL)
print(f"H2 数量: {len(h2s)}")  # 期望值：正文章节数（通常 4-6 个）
```

### 修复步骤

如果发现 markdown 章节是纯文本（无 `##`）：

```python
import re

headings = [
    "一场劳动纠纷如何走到港交所桌前",
    "对IPO的冲击不在钱，而在不确定性",
    "小红书不能只等风波过去",
    "所有想上市的公司，都该看看这封信",
]

with open("article.md") as f:
    md = f.read()

for h in headings:
    pattern = rf'(?<=\n)\n?({re.escape(h)})(?=\n)'
    md = re.sub(pattern, r'\n## \1', md)

with open("article_fixed.md", "w") as f:
    f.write(md)
```

然后对 `article_fixed.md` 跑 `markdown_to_html.py`。

---

## 两种配图路径

### 路径 A：脚本完整流程（推荐）

HTML 中**无** img 标签 → 让 `publish_lanlong.py` 跑完整流程：

```bash
python3 scripts/publish_lanlong.py \
  --html /tmp/article.html \
  --cover /tmp/cover.png \
  --title "文章标题" \
  --author "刘生" \
  --digest "摘要" \
  --delete-first <old_draft_id>
```

脚本内部自动：提取 H2 → 生成配图 → 上传 mmbiz → 注入 HTML → 上传封面 → 创建草稿。

### 路径 B：预置 img 标签（本次实战路径）

HTML 中**已有** `<img src="http://mmbiz.qpic.cn/...">` CDN URL：

1. 手动注入配图到 HTML（H2 前后各一张，或固定位置）
2. 调用脚本时加 `--skip-illustration --skip-cover`：
   ```bash
   python3 scripts/publish_lanlong.py \
     --html /tmp/article_with_imgs.html \
     --cover /tmp/cover.png \
     --title "文章标题" \
     --author "刘生" \
     --digest "摘要" \
     --delete-first <old_draft_id> \
     --skip-illustration \
     --skip-cover
   ```
3. 脚本检测到 HTML 有 mmbiz img → 跳过 shot 提取/上传/注入（2026-07-08 patch 后）
4. 封面走 `material/add_material` → thumb_media_id → `draft/add`

**脚本 2026-07-08 patch 效果**：`--skip-illustration` 时若 HTML 已有 mmbiz img，自动清空 shots 列表，跳过 `upload_illustrations()` 和 `inject_into_html()`，避免对 URL 字符串执行文件上传报错。

---

## 封面上传关键：必须用 `material/add_material`（永久素材）

**根因（2026-07-08 实战确认）**：草稿创建时传入的 `thumb_media_id` 字段，**必须来自 `material/add_material`（永久素材）**，不能用 `media/upload`（临时素材）。临时素材 ID 会导致 `draft/add` 返回 **errcode 40007 invalid media_id**。

正确流程：
```python
# 封面用 material/add_material 上传 → 返回 media_id
boundary = "----PythonFormBoundary7MA4YWxkTrZu0gW"
with open("cover.png", "rb") as f:
    img_data = f.read()
body = (
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="media"; filename="cover.png"\r\n'
    f"Content-Type: image/png\r\n\r\n"
).encode("utf-8") + img_data + f"\r\n--{boundary}--\r\n".encode("utf-8")

req = urllib.request.Request(
    f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image",
    data=body, method="POST",
    headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
)
result = json.loads(urllib.request.urlopen(req).read())
thumb_media_id = result["media_id"]  # ✅ 永久素材，可用于 draft/add

# draft/add payload
payload = {"articles": [{"thumb_media_id": thumb_media_id, ...}]}
```

**不要用** `media/upload`（临时素材）和 `media/uploadimg`（返回 url 而非 media_id）作为草稿封面的来源。

---

## 草稿重建而非局部更新

微信草稿 API 不支持"替换正文中的某张图片"。如果需要更新配图：
1. 重建完整 HTML（含新 img 标签）
2. `draft/delete` 旧草稿
3. `draft/add` 新草稿

不要尝试对已有草稿做局部 patch。
