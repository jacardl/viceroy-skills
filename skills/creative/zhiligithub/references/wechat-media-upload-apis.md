# WeChat 配图上传：两个 API 的区别

## 背景

`cgi-bin/media/upload` 和 `cgi-bin/media/uploadimg` 是微信公众平台两个不同的素材上传接口，返回格式完全不同。

## 对比

| 字段 | `media/upload` (永久素材) | `media/uploadimg` (图文内图片) |
|------|--------------------------|-------------------------------|
| 用途 | 永久素材库 / 封面图 | 图文正文中插入的图片 |
| type 参数 | `image` | `image` |
| 返回字段 | `media_id` | `url` |
| URL 格式 | media_id 不能直接拼 mmbiz URL | 直接返回完整 mmbiz URL，含 `/0?from=appmsg` 后缀 |
| 有效期 | 永久 | 永久 |
| 草稿箱兼容性 | thumb_media_id 用这个 | 正文配图用这个 |

## 正确的 mmbiz URL 格式

微信返回的图文图片 URL 形如：

```
http://mmbiz.qpic.cn/mmbiz_png/{部分ID}/{MEDIA_ID}/0?from=appmsg
```

**直接用 `media_id` 拼接 `mmbiz.qpic.cn` 的方式不可用**，会返回 400。

## push.py 实际调用的是哪个

`push.py` 的 `upload_illustrations()` 函数调用的是 `cgi-bin/media/uploadimg`，所以从 push.py 流程走是直接拿到可用 URL 的。

手动上传时（如本 session 用 curl 测试），必须用 `uploadimg` 接口才能拿到直接可注入 HTML 的 mmbiz URL。

## Cover 图与 push.py 的覆盖问题

`push.py` 在处理配图时：

1. 先读取 `--cover` 参数指定的文件
2. 然后自动生成一张封面（调用 zhili-illustration）
3. 上传后者作为草稿封面

**结果**：手动指定的 `--cover` 会被静默覆盖。要跳过自动封面生成，用 `--skip-cover` 参数。

如果需要使用特定封面图作为草稿封面，应该先生成图并确认文件名，然后查证 push.py 是否真的用了 `--skip-cover` 而非依赖参数传递。

## 验证命令

```bash
# 获取 token
TOKEN=$(curl -s "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=${APPID}&secret=${APPSECRET}" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# uploadimg（返回可用 URL）
curl -s "https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token=${TOKEN}&type=image" -F "media=@/tmp/cover.png"

# upload（返回 media_id，不能直接拼 mmbiz URL）
curl -s "https://api.weixin.qq.com/cgi-bin/media/upload?access_token=${TOKEN}&type=image" -F "media=@/tmp/cover.png"
```
