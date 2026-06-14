#!/usr/bin/env python3
"""
zhililong · 一键发布封装（Step 8）

把「长文 HTML + 封面图 + 配图」一键推到直隶按察使公众号草稿箱。
不重新造轮子，**全部走 zhili-publish/scripts/publish_zhili.py**。

设计:
- 入参：标题、作者、摘要、HTML 路径、封面图路径（可选）
- 处理：把 HTML 中占位符 LOCKS_PLACEHOLDER / PATHWAY_PLACEHOLDER 替换为 mmbiz URL
        （如果 --content-image 提供）
- 调用：subprocess.run(["python3", publish_zhili.py, ...]) 走完整 zhili-publish 流程
- 输出：草稿 media_id → 写到同目录 upload_results.json

用法:
  python3 publish_lanlong.py \
    --title "20 亿美元买了一个寂寞" \
    --author "刘生" \
    --digest "Meta 与 Manus 的 20 亿美元收购被强制拆开，5 节深度拆解。" \
    --html /tmp/manus_article.html \
    --cover /tmp/manus_cover.jpg

  # 一步：占位符替换 + 配图 mmbiz 上传（自动调 zhili-publish 的 upload_article_image）
  python3 publish_lanlong.py \
    --title "..." --author "刘生" --digest "..." \
    --html /tmp/article.html --cover /tmp/cover.jpg \
    --image-locks /tmp/locks.jpg --image-pathway /tmp/pathway.jpg

凭证路径: 复用 zhili-publish 的 config.md（无需二次配置）
"""
import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime

# 锁定 publish_zhili.py 的位置（zhililong 与 zhili-publish 是兄弟 skill）
PUBLISH_ZHILI = os.path.expanduser(
    "~/.hermes/skills/social-media/.agents/skills/zhili-publish/scripts/publish_zhili.py"
)
ZHILI_PUBLISH_DIR = os.path.dirname(PUBLISH_ZHILI)


def upload_image_to_mmbiz(image_path: str) -> str:
    """
    走 zhili-publish 内部函数上传配图，拿 mmbiz 公网 URL。
    复用 publish_zhili.py 的 upload_article_image + get_access_token。
    凭证由 zhili-publish 内部 load_config() 处理。
    """
    if not os.path.exists(image_path):
        print(f"ERROR: 配图不存在: {image_path}", file=sys.stderr)
        sys.exit(1)

    sys.path.insert(0, ZHILI_PUBLISH_DIR)
    try:
        # 动态导入（避免 sandbox 脱敏 APPSECRET——走 zhili-publish 内部函数已处理）
        from publish_zhili import load_config, get_access_token, upload_article_image
    except ImportError as e:
        print(f"ERROR: 无法导入 zhili-publish.publish_zhili: {e}", file=sys.stderr)
        print(f"请确认 zhili-publish 位于: {ZHILI_PUBLISH_DIR}", file=sys.stderr)
        sys.exit(1)

    config = load_config()
    token = get_access_token(config["APPID"], config["APPSECRET"])
    url = upload_article_image(token, image_path)
    if not url:
        print(f"ERROR: 配图上传失败: {image_path}", file=sys.stderr)
        sys.exit(1)
    return url


def replace_placeholders(html: str, mapping: dict) -> str:
    """
    把 HTML 中 LOCKS_PLACEHOLDER / PATHWAY_PLACEHOLDER 等占位符
    替换为 mmbiz URL。

    mapping: {"LOCKS_PLACEHOLDER": "http://mmbiz.qpic.cn/xxx", ...}
    """
    for placeholder, url in mapping.items():
        html = html.replace(placeholder, url)
    return html


def call_publish_zhili(title, author, digest, html, cover_path):
    """调用 zhili-publish 一手发布脚本"""
    if not os.path.exists(PUBLISH_ZHILI):
        print(f"ERROR: publish_zhili.py 不存在: {PUBLISH_ZHILI}", file=sys.stderr)
        sys.exit(1)

    # 4 位置参数 + --cover-path
    cmd = [
        sys.executable, PUBLISH_ZHILI,
        title, author, digest, html,
        "--cover-path", cover_path,
    ]
    print(f"========== 调用 zhili-publish ==========")
    print(" ".join(repr(c) for c in cmd[:5]) + " [...]")
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    print(result.stdout)
    if result.stderr:
        print("[zhili-publish stderr]:", result.stderr, file=sys.stderr)

    # 解析草稿 media_id
    m = re.search(r"草稿 media_id:\s*(\S+)", result.stdout)
    if not m:
        print("ERROR: 未能从 zhili-publish 输出解析到草稿 media_id", file=sys.stderr)
        sys.exit(1)
    return m.group(1)


def main():
    parser = argparse.ArgumentParser(description="zhililong · 一键发布到草稿箱")
    parser.add_argument("--title", required=True, help="文章标题")
    parser.add_argument("--author", required=True, help="作者署名")
    parser.add_argument("--digest", required=True, help="摘要（≤54 字节）")
    parser.add_argument("--html", required=True, help="正文 HTML 文件路径")
    parser.add_argument("--cover", required=True, help="封面图路径（900×540 .jpg）")
    parser.add_argument("--image-locks", default="", help="LOCKS 占位符配图路径")
    parser.add_argument("--image-pathway", default="", help="PATHWAY 占位符配图路径")
    parser.add_argument("--output-json", default="", help="回写结果 JSON 路径（默认同 html 目录）")
    args = parser.parse_args()

    # ============ Step 1: 校验输入 ============
    if not os.path.exists(args.html):
        print(f"ERROR: HTML 文件不存在: {args.html}", file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(args.cover):
        print(f"ERROR: 封面图不存在: {args.cover}", file=sys.stderr)
        sys.exit(1)

    html_content = open(args.html, encoding="utf-8").read()

    # ============ Step 2: 配图上传（占位符替换）============
    mmbiz_urls = []
    mapping = {}
    if args.image_locks:
        url = upload_image_to_mmbiz(args.image_locks)
        mapping["LOCKS_PLACEHOLDER"] = url
        mmbiz_urls.append(url)
    if args.image_pathway:
        url = upload_image_to_mmbiz(args.image_pathway)
        mapping["PATHWAY_PLACEHOLDER"] = url
        mmbiz_urls.append(url)

    if mapping:
        html_content = replace_placeholders(html_content, mapping)
        print(f"✅ 已替换 {len(mapping)} 个占位符")

    # ============ Step 3: 写到临时 HTML（避免长字符串命令行溢出）============
    tmp_html = f"/tmp/lanlong_article_{os.getpid()}.html"
    with open(tmp_html, "w", encoding="utf-8") as f:
        f.write(html_content)

    # ============ Step 4: 调用 zhili-publish ============
    media_id = call_publish_zhili(
        title=args.title,
        author=args.author,
        digest=args.digest,
        html=tmp_html,
        cover_path=args.cover,
    )

    # ============ Step 5: 回写结果 ============
    output_json = args.output_json or os.path.join(
        os.path.dirname(args.html), "upload_results.json"
    )
    result = {
        "draft_media_id": media_id,
        "title": args.title,
        "author": args.author,
        "cover": args.cover,
        "mmbiz_urls": mmbiz_urls,
        "html_path": args.html,
        "published_at": datetime.now().isoformat(),
        "draft_url": "https://mp.weixin.qq.com/cgi-bin/appmsg?action=list&type=10",
    }
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"✅ 结果已回写: {output_json}")

    # ============ Step 6: 用户提示 ============
    print("")
    print("=" * 60)
    print("🎉 草稿推送成功")
    print(f"   草稿 media_id : {media_id}")
    print(f"   标题          : {args.title}")
    print(f"   作者          : {args.author}")
    print(f"   配图数        : {len(mmbiz_urls)} 张")
    print("=" * 60)
    print("📌 接下来：登录微信公众平台 → 内容管理 → 草稿箱 → 编辑 → 群发")


if __name__ == "__main__":
    main()
