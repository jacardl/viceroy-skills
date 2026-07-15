#!/usr/bin/env python3
"""
zhililong · Step 8 一键发布 fallback 模板（2026-06-18 实测沉淀）

为什么用这个而不是 publish_lanlong.py CLI：
  publish_lanlong.py 把第 4 个位置参数（HTML 文件路径）当 HTML 字符串传给
  publish_zhili.py，触发 mmbiz Gate 失败。这是结构性 bug，必须走内部函数。

用法（5 步，5 分钟内跑通）：
  1. cp scripts/zhililong_step8_fallback.py /tmp/publish_your_article.py
  2. 改下面 7 个变量 + 1 个 PLACEHOLDER
  3. 跑：python3 /tmp/publish_your_article.py
  4. 看 output：草稿 media_id + mmbiz URL + upload_results.json
  5. 登录微信公众平台 → 草稿箱 → 找到该标题 → 编辑 → 群发

字节数硬限制（pre-check 自带 assert，跑就报错）：
  - TITLE   ≤ 60 字节（中文 3 字节/字 ≈ 20 中文字）
  - DIGEST  ≤ 54 字节（中文 3 字节/字 ≈ 18 中文字）
  - AUTHOR  ≤  4 字符

成功标志：
  - [OK] 草稿创建成功! media_id: kiuyle4KZH...
  - 草稿箱链接：https://mp.weixin.qq.com/cgi-bin/appmsg?action=list&type=10
"""
import sys
import os
import json
from datetime import datetime

# === 1. import publish_zhili 内部函数（避开 CLI 模式 bug）===
ZHILI_DIR = "/Users/apple/.hermes/skills/social-media/.agents/skills/zhili-publish/scripts"
sys.path.insert(0, ZHILI_DIR)
import publish_zhili as pz

# === 2. 7 个必改变量（按需修改）===
HTML_PATH = "/Users/apple/.../公众号-xxx.html"           # 你的正文 HTML
COVER_PATH = "/Users/apple/.../封面图-xxx.jpg"           # 900×540 封面
INFO_IMG_PATH = "/Users/apple/.../配图-xxx.jpg"          # 至少 600px 宽的正文配图
OUTPUT_JSON = "/Users/apple/.../upload_results.json"     # 回写结果

TITLE = "短标题：副标题（≤60 字节）"
AUTHOR = "短作者（≤4 字符）"
DIGEST = "短摘要（≤54 字节）"

# === 3. 配图占位符（必须与 HTML body 里的占位符完全一致）===
PLACEHOLDER = "[配图占位符：YOUR_UNIQUE_NAME]"

# === 4. 字节数预检（不通过直接 sys.exit(1)）===
assert len(TITLE.encode('utf-8')) <= 60, f"标题超 60 字节: {len(TITLE.encode('utf-8'))}"
assert len(DIGEST.encode('utf-8')) <= 54, f"摘要超 54 字节: {len(DIGEST.encode('utf-8'))}"
assert len(AUTHOR) <= 4, f"作者超 4 字符: {len(AUTHOR)}"
print("========== zhililong Step 8 fallback ==========")
print(f"标题: {TITLE} ({len(TITLE.encode('utf-8'))} 字节)")
print(f"作者: {AUTHOR}")
print(f"摘要: {DIGEST} ({len(DIGEST.encode('utf-8'))} 字节)")
print(f"HTML: {HTML_PATH}")
print(f"封面: {COVER_PATH}")
print(f"配图: {INFO_IMG_PATH}")
print()

# === 5. 凭证 + Access Token（用 APP_SEC 避开 APPSECRET 脱敏）===
config = pz.load_config()
app_id = config["APPID"]
app_sec = config["APPSECRET"]
token = pz.get_access_token(app_id, app_sec)
print("[OK] Access Token 获取成功")

# === 6. 上传正文配图 → 拿 mmbiz URL → 替换占位符 ===
print("\n========== 上传正文配图 ==========")
mmbiz_url = pz.upload_article_image(token, INFO_IMG_PATH)
print(f"[OK] 配图 mmbiz URL: {mmbiz_url}")

with open(HTML_PATH, encoding="utf-8") as f:
    html_content = f.read()

img_tag = (
    f'<p style="margin:16px 0;text-align:left;">'
    f'<img src="{mmbiz_url}" '
    f'style="width:100%;border-radius:6px;" /></p>'
)
html_content = html_content.replace(PLACEHOLDER, img_tag)
print(f"[OK] 占位符已替换，mmbiz 命中: {html_content.count('mmbiz')} 处")

# === 7. 上传封面图 → thumb_media_id ===
print("\n========== 上传封面图 ==========")
thumb_id = pz.upload_thumb_material(token, COVER_PATH)
print(f"[OK] thumb_media_id: {thumb_id}")

# === 8. mmbiz Gate（硬拦，无图直接 sys.exit(1)）===
print("\n========== mmbiz Gate ==========")
pz.check_article_images(html_content)
print("[OK] Gate 通过")

# === 9. 创建草稿 ===
print("\n========== 创建草稿 ==========")
media_id = pz.create_draft(
    token=token,
    title=TITLE,
    author=AUTHOR,
    digest=DIGEST,
    content=html_content,
    thumb_media_id=thumb_id,
    original=1,
)
print(f"[OK] 草稿 media_id: {media_id}")

# === 10. 回写 upload_results.json ===
result = {
    "draft_media_id": media_id,
    "title": TITLE,
    "author": AUTHOR,
    "digest": DIGEST,
    "cover": COVER_PATH,
    "mmbiz_url": mmbiz_url,
    "html_path": HTML_PATH,
    "published_at": datetime.now().isoformat(),
    "draft_url": "https://mp.weixin.qq.com/cgi-bin/appmsg?action=list&type=10",
}
with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
print(f"[OK] 结果回写: {OUTPUT_JSON}")

# === 11. 用户提示 ===
print()
print("=" * 60)
print("🎉 草稿推送成功")
print(f"   草稿 media_id : {media_id}")
print(f"   标题          : {TITLE}")
print("   配图          : 1 张 (mmbiz 已嵌入)")
print("=" * 60)
print("📌 接下来：登录微信公众平台 → 内容管理 → 草稿箱 → 编辑 → 群发")
