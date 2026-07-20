# 草稿出错 → 删除 → 重新发布（2026-06-12 实战补）

> 适用场景：草稿已经发到微信（`draft/add` 返回 `media_id`），事后发现内容 bug
> （图片占位 style 重复、branding 残留、JSON 编码问题、字数超限等），需要重发。

## 核心约束

**不要清空草稿箱**（用户硬性规则，2026-05-21 确认）。只能针对那一条坏草稿做删除 + 重建。

## 操作流程

1. **记录坏草稿的 `media_id`**（`draft/add` 返回值）
2. **调用 `draft/delete` 删除**
3. **修复 HTML / Markdown 源**
4. **重新走完整发布流程**（access_token → 封面 → 内容图 → 替换占位 → 草稿）

## 代码模板

```python
import json, ssl, urllib.request

APPID = "wx38a91c353554588a"
with open(os.path.expanduser("~/.hermes/keys/wx_appsecret.txt")) as f:
    APPSECRET = f.read().strip()
BAD_MEDIA_ID = "..."  # 从上次 draft/add 返回值复制

# 1. 拿 token
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APPID}&secret={APPSECRET}"
with urllib.request.urlopen(url, timeout=30, context=ctx) as r:
    token = json.loads(r.read())["access_token"]

# 2. 删草稿
url = f"https://api.weixin.qq.com/cgi-bin/draft/delete?access_token={token}"
req = urllib.request.Request(
    url,
    data=json.dumps({"media_id": BAD_MEDIA_ID}, ensure_ascii=False).encode("utf-8"),
    headers={"Content-Type": "application/json"},
)
with urllib.request.urlopen(req, timeout=30, context=ctx) as r:
    print(json.loads(r.read()))  # {'errcode': 0, 'errmsg': 'ok'} = 成功
```

## 容易踩的坑

- **token 失效**：删除和重建之间如果间隔超过 2 小时，token 会过期（WeChat access_token
  有效期 7200s），需要重新拿。`publish_zhili.py` 不会自动重连。
- **删除是不可逆操作**：先确认 `BAD_MEDIA_ID` 真的不是你想要的草稿
  （如果用户在草稿箱里手动改过内容，删了就找不回来）
- **重传 thumb/content image 是允许的**：不需要复用上次的 `thumb_media_id`，
  重新调用 `material/add_material` 即可（不会占配额）
- **占位 HTML 复用陷阱**：上次跑 publish.py 时 `/tmp/.../article.html` 已经被改过
  （`PLACEHOLDER` 已被替换成上次的 mmbiz URL），第二次跑会找不到占位。
  一定要**重新 `build_html.py` 一次**，从带 `PLACEHOLDER` 的干净 HTML 开始

## 验证

删除成功时返回：
```json
{"errcode": 0, "errmsg": "ok"}
```

删除失败时：
- `errcode: 40007` → `media_id` 错了或已失效
- `errcode: 40001` → access_token 失效，重新拿
- `errcode: 45009` → 调用频率超限，等几秒重试
