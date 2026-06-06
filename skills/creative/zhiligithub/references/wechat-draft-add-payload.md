# WeChat draft/add Payload 完整规范

> 来源：2026-06-03 实战踩坑。会话中 44003 报错"empty news data"误导排查 2 次才找到根因。

## 1. 错误信息与根因对照表

| 错误码 | 错误信息 | 根因 | 修复 |
|---|---|---|---|
| **44003** | `empty news data` | **payload 用了扁平结构 `{title, content, ...}`**，不是 `{"articles": [{...}]}` | 把整个 article 对象包进 `articles` 数组 |
| 44003 | `empty news data` | content 字段为空字符串或 None | 检查 `len(content) > 0`，且不要传 `""` |
| 44003 | `empty news data` | access_token 失效（看起来"内容空"但其实是认证失败） | 重新调 `cgi-bin/token` 获取 |
| 40007 | `invalid media_id` | thumb_media_id 用了 `media/upload?type=thumb` 接口的返回值 | 改用 `material/add_material?type=thumb` 的 media_id |
| 45003 | `title size out of limit` | 标题 > 60 字节 | 缩到 ≤22 字节（约 7-8 个中文字） |
| 45003 | `digest size out of limit` | 摘要 > 54 字节 | 缩到 ≤54 字节（约 18 个中文字）|
| 40001 | `invalid credential` | access_token 过期或 AppSecret 错 | 重新获取 token；AppSecret 从 `references/config.md` 读（真实值保存在 `~/.openclaw/secrets/zhili-credentials.md`，**绝不能**进 GitHub） |

## 2. 正确 payload 结构（✅ 唯一可用）

```python
import json
import urllib.request

payload = {
    "articles": [{
        "title": title,                    # ≤60 字节（≤22 中文字）
        "author": author,                  # ≤2 个中文字
        "digest": digest,                  # ≤54 字节（≤18 中文字）
        "content": content,                # HTML 字符串，必须含 mmbiz URL
        "thumb_media_id": thumb_media_id,  # 来自 material/add_material?type=thumb
        "need_open_comment": 1,            # 0/1，是否开启评论
        "only_fans_can_comment": 0,        # 0/1，是否仅粉丝可评论
        "original": 1,                     # 0/1，是否原创（原创文章要设 1）
    }]
}

body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
req = urllib.request.Request(
    f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={TOKEN}",
    data=body, method="POST"
)
req.add_header("Content-Type", "application/json")  # ⚠️ 不带 charset=utf-8

with urllib.request.urlopen(req, timeout=30) as resp:
    result = json.loads(resp.read().decode("utf-8"))
    if "media_id" in result:
        print(f"✅ 草稿创建成功: {result['media_id']}")
    else:
        print(f"❌ 失败: {result}")
```

## 3. 常见错误 payload（❌ 不要用）

```python
# ❌ 错误 1：扁平结构（最常见）
payload = {
    "title": title,
    "content": content,
    "thumb_media_id": thumb_media_id,
    # ... 缺 articles 数组 → 44003 empty news data
}

# ❌ 错误 2：articles 数组里直接放字符串
payload = {
    "articles": ["article content here"]  # 必须是对象数组
}

# ❌ 错误 3：articles 包错字段
payload = {
    "articles": [{
        "title": title,
        "content": content,
        # 漏了 author / digest / thumb_media_id
    }]
}
# 这种情况可能 200 OK 但草稿不完整，必须全字段填
```

## 4. 验证脚本（推荐在写 payload 后跑一遍）

```python
def validate_draft_payload(payload: dict) -> list[str]:
    """返回错误列表，空列表 = 通过"""
    errors = []
    if "articles" not in payload:
        errors.append("❌ 缺 articles 顶层字段（44003 empty news data 的根因）")
    elif not isinstance(payload["articles"], list):
        errors.append("❌ articles 必须是数组")
    elif len(payload["articles"]) == 0:
        errors.append("❌ articles 数组为空")
    else:
        a = payload["articles"][0]
        required = ["title", "author", "digest", "content", "thumb_media_id"]
        for f in required:
            if f not in a or not a[f]:
                errors.append(f"❌ 缺字段或为空: {f}")
        # 字节限制
        if len(a.get("title", "").encode("utf-8")) > 60:
            errors.append(f"❌ 标题超 60 字节")
        if len(a.get("digest", "").encode("utf-8")) > 54:
            errors.append(f"❌ 摘要超 54 字节")
        if len(a.get("author", "")) > 2:
            errors.append(f"❌ 作者超 2 字符")
    return errors
```

## 5. 调试 44003 时的排查顺序

如果 `draft/add` 返回 44003，按这个顺序查（不要乱试）：

1. **payload 结构**：先 print 整个 payload，**确认 `articles` 数组在最外层**
2. **content 字段**：确认 `len(content) > 0` 且是字符串
3. **access_token**：调 `cgi-bin/draft/count` 验证 token 有效
4. **thumb_media_id**：调 `cgi-bin/material/get_material` 验证 media_id 存在
5. **JSON 编码**：确认用了 `ensure_ascii=False` + `Content-Type: application/json`（不带 charset）

如果 1-5 都 OK 还 44003，几乎肯定是**结构问题**——`articles` 数组被丢掉或被命名错了。

## 6. 完整发布流程（带预检）

```python
# Step 1: 验证 payload
errors = validate_draft_payload(payload)
if errors:
    print("❌ Payload 验证失败:")
    for e in errors:
        print(f"  {e}")
    sys.exit(1)

# Step 2: 验证 HTML 含 mmbiz（脚本 Gate）
if "mmbiz" not in payload["articles"][0]["content"]:
    print("❌ HTML 正文必须含 mmbiz 图片（无图会被 publish_zhili.py Gate 拦截）")
    sys.exit(1)

# Step 3: 验证 HTML 无空行
if re.search(r'\n\s*\n', payload["articles"][0]["content"]):
    print("⚠️ HTML 含空行，先用 cleanup_html.py 清理")

# Step 4: 发请求
# (见上文正确 payload 代码)
```

## 7. publish_zhili.py 已经是正确实现

`scripts/publish_zhili.py` 的 `create_draft()` 函数已经用了正确的 `{"articles": [{...}]}` 结构。**直接调用这个函数，不要手写 draft/add 请求**，除非需要绕过某些限制。

调用方式：

```python
import sys
sys.path.insert(0, '/root/.hermes/skills/creative/zhiligithub/scripts')
import publish_zhili as pz

token = pz.get_access_token(appid, appsecret)
thumb_id = pz.upload_thumb_material(token, '/tmp/cover.jpg')
result = pz.create_draft(token, title, author, digest, content, thumb_id)
# result == {"media_id": "...", "item": [...]} 表示成功
```
