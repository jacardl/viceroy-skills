# 微信发布错码速查（zhiliGitHub 专用，2026-06-04 实战沉淀）

发布微信草稿时遇到的错码速查表。按"出现频率"排序，每个错码给出现象、根因、解决方案。

> **重要免责**：`draft/get` API 永远返回 `\uXXXX`（因为 API 内部 JSON 编码），**不能作为判断中文是否正常显示的标准**——必须由佳哥本人在 mp.weixin.qq.com 草稿箱**视觉验证**。

---

## 🔴 致命错（必须修复才能发布）

### errcode 40001 — invalid credential / access_token invalid

- **现象**：`uploadimg` / `add_material` / `draft/add` 任意一个接口报 40001
- **根因**：access_token 过期（7200s）或**跨操作复用**
- **解决方案**：
  - **每步单独** `POST /cgi-bin/stable_token` 拿新 token（**不要跨操作复用**）
  - 验证：`if "media_id" in resp.json()`（不能用 `errcode == 0`）
- **绝对不能用** GET `/cgi-bin/token`（会报 40001）
- **实战场景**（2026-06-04 headroom）：第一次创建草稿用旧 token → 40001 → 重新拿 token + 立即用 → 成功

### errcode 40007 — invalid media_id（thumb_media_id 一次性绑定陷阱）

- **现象**：`draft/add` 报 40007
- **根因**（三个常见原因）：
  1. **thumb_media_id 跨草稿复用**（每篇草稿必须重新上传封面）
  2. 上传用了 `type=thumb` 而非 `type=image`（旧版本残留错误）
  3. 上传后过了 3 天，永久素材被清理
- **解决方案**：
  - 上传后**立即用**，不要缓存
  - 用 `material/add_material?type=image`（**不是** `type=thumb`，**不是** `media/upload`）
  - 每篇草稿独立上传封面
- **实测验证**（2026-06-04 headroom）：传 `type=image` 拿到的 `media_id` 直接作 `thumb_media_id` 成功创建草稿

### errcode 44003 — empty news data（payload 结构错，错误信息极具误导性）

- **现象**：`draft/add` 报 44003 + 错误信息 "empty news data"
- **根因**：payload 用了扁平结构 `{title, content, ...}` 而非包成 `articles` 数组
- **解决方案**：
  ```python
  # ❌ 错（2026-06-03 踩坑）
  payload = {"title": "...", "content": "...", "author": "..."}
  
  # ✅ 对
  payload = {"articles": [{"title": "...", "content": "...", "author": "..."}]}
  ```
- **错误信息极具误导性**——其实是结构错不是内容空

### errcode 45003 — title size out of limit

- **现象**：`draft/add` 报 45003
- **根因**：标题 > 60 字节
- **解决方案**：
  - 标题 ≤ 60 字节（UTF-8 中文 = 3 字节/字，约 ≤20 个中文字）
  - 推荐 14-22 字节（约 5-7 个中文字）
  - **策略**：先写 18-22 字节测试通过再逐步加长

### errcode 45004 — digest size out of limit

- **现象**：`draft/add` 报 45004
- **根因**：digest > 54 字节（隐式限制，API 不直接返回）
- **解决方案**：
  - digest ≤ 54 字节（约 18 个中文字）
  - 写完必查：`len(digest.encode('utf-8'))`

### errcode 45110 — author size out of limit

- **现象**：`draft/add` 报 45110
- **根因**：author 字段 > 2 字符
- **解决方案**：
  - 固定填 `刘生`（2 字符，2026-05-30 确认）
  - 留空也可（不报 45110），但填 `刘生` 更稳

### errcode 40125 — invalid appsecret

- **现象**：`stable_token` 报 40125
- **根因**：AppSecret 无效（被重置 / 配置错）
- **解决方案**：
  - **不能重试**，需用户提供新 AppSecret
  - 检查 `~/.hermes/keys/wx_appsecret.txt` 文件内容是否正确

### errcode 48001 — api unauthorized（freepublish 权限不足）

- **现象**：`/cgi-bin/freepublish/submit` 报 48001
- **根因**：个人订阅号没有 `freepublish`（直接发布）权限
- **解决方案**：
  - **走草稿箱**，由佳哥手动从 mp.weixin.qq.com 发布
  - 不要尝试 `freepublish` 任何子接口

---

## 🟡 字符编码错（草稿箱显示问题）

### 中文显示为 `\uXXXX` 字面量

- **现象**：草稿箱前端正文显示 `\u5361\u5179\u514b` 而非"卡兹克"
- **根因**：`json.dumps()` 默认 `ensure_ascii=True` 把中文转义成 `\uXXXX`
- **解决方案**：
  ```python
  # ✅ 正确（2026-05-30 三阶段排查确认）
  data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
  # Content-Type: application/json（不带 charset=utf-8）
  
  # ❌ 错误方案 1（默认）
  data = json.dumps(payload).encode("utf-8")  # ensure_ascii=True 默认
  
  # ❌ 错误方案 2
  data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
  # 然后 Content-Type: application/json; charset=utf-8
  # → WeChat JSON 管线无法解码
  ```
- **核心**：WeChat 自己推断 UTF-8，**不要**在 HTTP 头里声明编码
- **再次免责**：`draft/get` API 永远返回 `\uXXXX` 字面量——必须 mp.weixin.qq.com 视觉验证

### Content-Type 带 `charset=utf-8`

- **现象**：WeChat JSON 管线无法解码，行为不定（有时 40001，有时静默成功但显示乱码）
- **解决方案**：
  ```python
  req.add_header("Content-Type", "application/json")  # 不带 charset
  ```

---

## 🟠 上传相关错

### errcode 41005 — media data missing（urllib.request multipart 报）

- **现象**：用 urllib.request 上传图片返回 41005
- **根因**：multipart 格式有 bug（罕见，Python 3.11+ 已修）
- **解决方案**：
  ```bash
  # 改用 curl subprocess
  curl -s -F 'media=@img.jpg' \
    "https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token=TOKEN&type=image"
  ```

### errcode 40137 — invalid file type（uploadimg）

- **现象**：uploadimg 报 40137
- **根因**：上传了 PNG（uploadimg **只接受 JPEG**）
- **解决方案**：
  ```python
  from PIL import Image
  img = Image.open("/tmp/cover.png").convert("RGB")
  img.save("/tmp/cover.jpg", "JPEG", quality=90)
  # 然后上传 /tmp/cover.jpg
  ```
- **注意对比**：
  - `add_material?type=image`（封面）→ **接受** PNG
  - `media/uploadimg`（内容图）→ **只接受** JPEG

### PIL `image file is truncated` 错

- **现象**：`Image.open()` 报 `OSError: image file is truncated`
- **根因**：源文件损坏（GitHub user-attachments 下载不完整）
- **解决方案**：
  ```bash
  # 重新下载，加 max-time 和 retry
  curl -s -L "https://github.com/user-attachments/assets/XXX" \
    -o /tmp/img.png --max-time 30 --retry 3
  ```
  或换其他图片源（OG 图 / AI 生成）

---

## 👁️ 视觉验证铁律（最重要）

**mp.weixin.qq.com 草稿箱需要登录 cookie 才能验证显示效果**。所有"草稿箱显示问题"必须由佳哥本人在浏览器视觉确认：

- [ ] 标题中文正常（**不是** `\uXXXX`）
- [ ] 5 个 H2 章节标题（开头 + 5 编号段）中文正常
- [ ] 4-5 个代码块文字可见（**不是**黑底黑字）
- [ ] 文末作者=`刘生`（**不是**"卡兹克"）
- [ ] 全文无 branding 残留（卡兹克 / zhiliGitHub / 本文由 / 一键三连 / 扫码 / wzglyay / 自动发布）
- [ ] 封面图正常显示（800×400 或 900×383）

**`draft/get` API 永远返回 `\uXXXX`**（因为 API 内部 JSON 编码），**不能作为判断标准**。

---

## 🚫 草稿删除禁令（2026-05-27 最高优先级）

> ⚠️ **哪怕是 bug 草稿，不要在 mp.weixin.qq.com 草稿箱手动删**。

错误操作链：bug 草稿 → 手动删 → 后悔 → 没法重发 → 损失 1 个选题

正确操作链：bug 草稿 → 本地备份 → 反向方案（重建 / 用 `ensure_ascii=True` 重发）→ 验证 OK → 才删

---

## 📊 错码速查表（按数字排序）

| errcode | 含义 | 频率 | 一行解 |
|---------|------|------|--------|
| 0 | 成功 | — | `if "media_id" in resp.json()` 判断 |
| 40001 | access_token invalid | 高 | 重新拿 token，每步单独拿 |
| 40007 | invalid media_id | 高 | 重新上传封面，用 `type=image` |
| 40125 | invalid appsecret | 低 | 不能重试，找佳哥要新凭证 |
| 40137 | invalid file type (uploadimg) | 中 | PNG 转 JPEG 再上传 |
| 41005 | media data missing | 低 | urllib 改 curl subprocess |
| 44003 | empty news data | 中 | payload 包成 `articles: [{...}]` |
| 45003 | title size out of limit | 高 | 缩短到 ≤ 22 字节（zhiliGitHub） |
| 45004 | digest size out of limit | 中 | 缩短到 ≤ 54 字节 |
| 45110 | author size out of limit | 低 | 填 `刘生`（2 字符） |
| 48001 | api unauthorized | 中 | 走草稿箱，不用 freepublish |

---

## 🔧 API 端点速查

| 用途 | 端点 | 关键字段 |
|------|------|----------|
| 拿 token | `POST /cgi-bin/stable_token` | `{"grant_type":"client_credential","appid":...,"secret":...}` |
| 上传封面 | `POST /cgi-bin/material/add_material?type=image` | multipart: `media` 字段 |
| 上传内容图 | `POST /cgi-bin/media/uploadimg?type=image` | multipart: `media` 字段（**只接受 JPEG**） |
| 创建草稿 | `POST /cgi-bin/draft/add` | `{"articles":[{title, author, digest, content, thumb_media_id}]}` |
| 查询草稿 | `POST /cgi-bin/draft/batchget` | `{"offset":0, "count":10, "no_content":1}` |
| 直接发布 | `POST /cgi-bin/freepublish/submit` | ❌ 个人订阅号无权限 |

**所有 POST 必须**：
- `Content-Type: application/json`（**不带** charset）
- `json.dumps(..., ensure_ascii=False).encode("utf-8")`
