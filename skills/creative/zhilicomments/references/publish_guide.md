# 独立小扎 · 草稿发布参考

## 凭证
```
APPID: wx38a91c353554588a
APPSECRET: [已配置]
CATEGORY_ID: 100
```

## 典型发布流程

```python
import json, urllib.request

# 1. 获取 access_token
with open('/tmp/token.json') as f:
    token = json.load(f)['access_token']

# 2. 上传封面（type=thumb，返回 media_id）
# curl -F "media=@/tmp/cover.jpg" "https://api.weixin.qq.com/cgi-bin/material/add_material?access_token=${TOKEN}&type=thumb"

# 3. 创建草稿
payload = {
    "articles": [{
        "title": "标题",
        "author": "刘生",
        "digest": "摘要",
        "content": "<div>...</div>",
        "thumb_media_id": "media_id",
        "need_open_comment": 1,
        "only_fans_can_comment": 0
    }]
}
url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')
with urllib.request.urlopen(req) as resp:
    result = json.loads(resp.read())
    print(result.get('media_id'))
```

## 常见错误

| errcode | 说明 | 修复 |
|---------|------|------|
| 40007 | media_id 无效 | 必须用 `type=thumb`，不能用 `type=image` |
| 40164 | IP 不在白名单 | 将服务器出口 IP 添加到微信公众平台 → 设置与开发 → 基本配置 → IP白名单 |

## 删除旧草稿
```bash
curl -X POST "https://api.weixin.qq.com/cgi-bin/draft/delete?access_token=${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"media_id":"旧草稿media_id"}'
```