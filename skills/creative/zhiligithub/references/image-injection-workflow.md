# 图片注入工作流补充（2026-07-15）

> 补充 practical-writing-workflow.md，聚焦无占位符时的完整流程。

## 核心教训

render 输出 `图片占位=0` 时，末尾的 `⚠️ 发布前需将 <img src="PLACEHOLDER"> 替换为 mmbiz URL` 警告**不适用**。这是路径 A 的提示，路径 B 无占位符，直接忽略该警告即可。

## 无占位符项目完整流程（2026-07-15 OpenCut 实测）

### Step 1：找图

1. 先查 GitHub API `GET /repos/{owner}/{repo}/contents/` 是否有图片
2. 再查 README 是否引用外部图片
3. 都无 → 用 GitHub OG 图：`curl -L "https://opengraph.githubassets.com/1/{owner}/{repo}" -o /tmp/og.png`
   - OG 图尺寸 1200×600，16:9 比例
   - PIL 裁剪：`Image.open('og.png').crop((0, top, w, top+h))` 取中间偏上部分

### Step 2：上传

封面 → `material/add_material?type=image` → 返回 `media_id`（用于草稿 `thumb_media_id`）  
内容图 → `media/uploadimg` → 返回 `url`（mmbiz 公开 URL，直接写入 HTML）

```python
import urllib.request, json

appid = 'wx38a91c353554588a'
appsecret = open('/root/.hermes/keys/wx_appsecret.txt').read().strip()

# access token
url = f'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={appid}&secret={appsecret}'
with urllib.request.urlopen(url, timeout=10) as resp:
    token = json.loads(resp.read())['access_token']

# 内容图（uploadimg → mmbiz URL）
boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
img_data = open('/tmp/content.jpg', 'rb').read()
body = f'--{boundary}\r\nContent-Disposition: form-data; name="media"; filename="content.jpg"\r\nContent-Type: image/jpeg\r\n\r\n'.encode() + img_data + f'\r\n--{boundary}--'.encode()
req = urllib.request.Request(
    f'https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={token}&type=image',
    data=body,
    headers={'Content-Type': f'multipart/form-data; boundary={boundary}'}
)
with urllib.request.urlopen(req, timeout=30) as resp:
    mmbiz_url = json.loads(resp.read())['url']

# 封面（add_material → media_id）
封面_data = open('/tmp/cover.jpg', 'rb').read()
封面_body = f'--{boundary}\r\nContent-Disposition: form-data; name="media"; filename="cover.jpg"\r\nContent-Type: image/jpeg\r\n\r\n'.encode() + 封面_data + f'\r\n--{boundary}--'.encode()
封面_req = urllib.request.Request(
    f'https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image',
    data=封面_body,
    headers={'Content-Type': f'multipart/form-data; boundary={boundary}'}
)
with urllib.request.urlopen(封面_req, timeout=30) as resp:
    cover_result = json.loads(resp.read())
    cover_media_id = cover_result['media_id']
```

### Step 3：注入 HTML

注入点在「二、项目介绍」末尾（正文第一张图）或「三、架构设计」开头。

```python
with open('/tmp/article.html') as f:
    html = f.read()

mmbiz_url = 'http://mmbiz.qpic.cn/sz_mmbiz_jpg/...'  # 上一步获取
img_tag = f'<img src="{mmbiz_url}" style="width:100%;max-width:680px;border-radius:4px;margin:16px 0;" />'
caption = '<p style="font-size:13px;color:#7c6f64;font-style:italic;margin:0 0 20px 0;text-align:center;">▲ 图注</p>'

# 从渲染后的 HTML 中找精确 marker（不用 markdown 原句）
target = '正在从零重写</strong>。</p><h2 style="font-size:20px;font-weight:bold;color:#1B365D;border-left:4px solid #00d4aa;padding-left:12px;margin:28px 0 12px 0;">三、架构设计</h2>'
replacement = f'正在从零重写</strong>。</p>{img_tag}{caption}<h2 style="font-size:20px;font-weight:bold;color:#1B365D;border-left:4px solid #00d4aa;padding-left:12px;margin:28px 0 12px 0;">三、架构设计</h2>'

html = html.replace(target, replacement)

# 同时注入 title
html = html.replace(
    '<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>',
    '<head><meta charset="utf-8"><title>文章标题</title><meta name="viewport" content="width=device-width,initial-scale=1"></head>'
)

with open('/tmp/article.html', 'w') as f:
    f.write(html)
```

### Step 4：push

```bash
cd /tmp && python3 /root/.hermes/skills/creative/zhiligithub/scripts/push.py \
  --html /tmp/article.html \
  --cover /tmp/cover.jpg \
  --skip-illustration
```
