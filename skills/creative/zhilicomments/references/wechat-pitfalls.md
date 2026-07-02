# 微信 API 实操踩坑（2026-06-10 / 2026-06-11 实战沉淀）

## 凭证来源（2026-06-11 修正）

- **真实 APPSECRET** 在 `zhili-publish/references/config.md`，佳哥维护
- 同步到本 skill `references/config.md`（publish_zhili.py 优先读本 skill 的 config.md）
- 脱敏版备份为 `references/config.md.bak-redacted-20260611`
- ⚠️ **严禁**把真实 APPSECRET 明文写入对话/飞书/日志
- 云端 SKILL.md 第 326 行示例里的 `~/.hermes/keys/wx_appsecret.txt` 路径是**过时的**——本 skill 不再使用

## access_token：必须 POST stable_token

```python
# ✅ 正确：POST stable_token
url = "https://api.weixin.qq.com/cgi-bin/stable_token"
data = json.dumps({"grant_type": "client_credential", "appid": APPID, "secret": SECRET}).encode()
# ❌ 错误：GET /cgi-bin/token → 素材接口报 40001
```

## 封面图：必须用 type=image

```python
# ✅ type=image → media_id 可用于 thumb_media_id
url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image"

# ❌ type=thumb → draft/add 时报 40007 invalid media_id
```

## draft/add：JSON 编码必须 ensure_ascii=False

```python
# ✅ UTF-8 原文 + Content-Type: application/json（无 charset）
payload = json.dumps({...}, ensure_ascii=False).encode('utf-8')
req.add_header('Content-Type', 'application/json')  # 不要带 charset=utf-8

# ❌ ensure_ascii=True（默认）→ 中文变 \uXXXX → 微信预览渲染器显示乱码
```

## digest 字节计算（54 字节上限）

```python
def calc_bytes(s: str) -> int:
    return sum(3 if ord(c) > 127 else 1 for c in s)

# 纯中文 25-30 字符 = 75-90 字节 → 超限
# 中英混排反而省字节（"Anthropic 昨晚发布 Claude Fable 5" = 54 字节）
```

## content 字段里的 mmbiz URL 必须用本次上传的

如果在 HTML 里用 `src="http://mmbiz.qpic.cn/..."`，必须确认是这次 `material/add_material` 返回的 url，否则会 40007 或显示错图。

## 完整上传+草稿最小骨架

```python
import urllib.request, json, ssl, os, re

# 1. 取凭证
APPID = 'wx38a91c353554588a'
with open(os.path.expanduser("~/.hermes/skills/social-media/.agents/skills/zhilicomments/references/config.md")) as f:
    cfg = f.read()
app_secret = re.search(r"APPSECRET[:\s=]+([a-zA-Z0-9_-]+)", cfg).group(1)

# 2. POST stable_token
req = urllib.request.Request(
    "https://api.weixin.qq.com/cgi-bin/stable_token",
    data=json.dumps({"grant_type": "client_credential", "appid": APPID, "secret": app_secret}).encode(),
    headers={"Content-Type": "application/json"}, method="POST")
with urllib.request.urlopen(req, timeout=10) as r:
    token = json.loads(r.read())["access_token"]

# 3. 上传封面（type=image）
boundary = '----PF123456'
with open('/tmp/cover.jpg', 'rb') as f:
    img = f.read()
body = (f'--{boundary}\r\nContent-Disposition: form-data; name="media"; filename="cover.jpg"\r\n'
        f'Content-Type: image/jpeg\r\n\r\n').encode() + img + f'\r\n--{boundary}--\r\n'.encode()
req = urllib.request.Request(
    f'https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image',
    data=body, method='POST')
req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
ctx = ssl.create_default_context()
ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
with urllib.request.urlopen(req, timeout=30, context=ctx) as r:
    media_id = json.loads(r.read())["media_id"]

# 4. 创建草稿
html = open('/tmp/article.html').read()
req = urllib.request.Request(
    f'https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}',
    data=json.dumps({"articles": [{
        "title": "标题", "author": "刘生", "digest": "摘要", "content": html,
        "thumb_media_id": media_id, "need_open_comment": 1, "only_fans_can_comment": 0
    }]}, ensure_ascii=False).encode('utf-8'),
    headers={"Content-Type": "application/json"}, method='POST')
with urllib.request.urlopen(req, timeout=10) as r:
    result = json.loads(r.read())
    print(result["media_id"])  # 草稿 media_id（不是封面那个）
```

## execute_code sandbox 提醒

- 每次 `execute_code` 是独立 sandbox，`os`/`re`/自定义变量**不跨调用保留**
- 必须在每个脚本里 import 需要的库（不能假设已 import）
- 文件读写、URL 抓取都走 sandbox 内的 `terminal`/`write_file` 接口，不要依赖全局 `os.chdir`
