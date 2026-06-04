"""
WeChat draft/add payload 验证器

用法：
    from validate_draft_payload import validate_draft_payload
    errors = validate_draft_payload(payload)
    if errors:
        for e in errors: print(e)
        sys.exit(1)

或者命令行：
    python3 validate_draft_payload.py /path/to/payload.json

预防 44003 "empty news data" 错误（最常见根因：articles 数组结构丢失）。

详细背景见 references/wechat-draft-add-payload.md
"""

import json
import sys
from pathlib import Path


def validate_draft_payload(payload: dict) -> list:
    """返回错误列表，空列表 = 通过"""
    errors = []

    if not isinstance(payload, dict):
        return [f"❌ payload 必须是 dict，实际是 {type(payload).__name__}"]

    # === 顶层结构 ===
    if "articles" not in payload:
        errors.append("❌ 缺 articles 顶层字段 → 44003 empty news data")
    elif not isinstance(payload["articles"], list):
        errors.append(f"❌ articles 必须是 list，实际是 {type(payload['articles']).__name__}")
    elif len(payload["articles"]) == 0:
        errors.append("❌ articles 数组为空")
    elif len(payload["articles"]) > 1:
        errors.append(f"⚠️ articles 含 {len(payload['articles'])} 篇，draft/add 单次只发 1 篇（多篇用 draft/add batch 接口）")
    else:
        a = payload["articles"][0]
        if not isinstance(a, dict):
            errors.append(f"❌ articles[0] 必须是 dict，实际是 {type(a).__name__}")
        else:
            errors.extend(_validate_article(a))

    return errors


def _validate_article(a: dict) -> list:
    """验证单篇文章对象"""
    errors = []

    # 必填字段
    required = ["title", "author", "digest", "content", "thumb_media_id"]
    for f in required:
        if f not in a or not a[f]:
            errors.append(f"❌ 缺字段或为空: {f}")

    # 字节限制
    if "title" in a and a["title"]:
        b = len(a["title"].encode("utf-8"))
        if b > 60:
            errors.append(f"❌ 标题超 60 字节（实际 {b} 字节）→ 45003")
    if "digest" in a and a["digest"]:
        b = len(a["digest"].encode("utf-8"))
        if b > 54:
            errors.append(f"❌ 摘要超 54 字节（实际 {b} 字节）→ 45003")
    if "author" in a and a["author"]:
        if len(a["author"]) > 8:
            # 注意：作者限制是 2 个中文字，但 unicode 字符是 1 个；按 WeChat 实测是 ≤2 个中文字 ≈ 8 字节
            errors.append(f"⚠️ 作者可能超限（实际 {len(a['author'])} 字符）→ author size out of limit")
    if "content" in a and a["content"]:
        c = a["content"]
        if "mmbiz" not in c:
            errors.append("❌ HTML 不含 mmbiz 图片（publish_zhili.py Gate 会拒绝）")
        # 检查空行
        import re
        if re.search(r'\n\s*\n', c):
            errors.append("⚠️ HTML 含连续空行，建议先跑 cleanup_html.py")
        # 检查 markdown 残留
        if re.search(r'\*\*[^*]+\*\*', c):
            # 可能是 <strong> 里的，但粗略检查
            md_residual = [m for m in re.finditer(r'\*\*[^*]+\*\*', c)
                           if "<strong" not in c[max(0, m.start()-200):m.start()]]
            if md_residual:
                errors.append(f"⚠️ 可能含 Markdown ** 残留（{len(md_residual)} 处）")

    return errors


def main():
    if len(sys.argv) != 2:
        print("用法: python3 validate_draft_payload.py <payload.json>")
        print("或作为模块 import: from validate_draft_payload import validate_draft_payload")
        sys.exit(1)

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"❌ 文件不存在: {path}")
        sys.exit(1)

    try:
        with open(path) as f:
            payload = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ JSON 解析失败: {e}")
        sys.exit(1)

    errors = validate_draft_payload(payload)
    if errors:
        print("❌ Payload 验证失败:")
        for e in errors:
            print(f"  {e}")
        sys.exit(1)
    else:
        print("✅ Payload 验证通过")
        sys.exit(0)


if __name__ == "__main__":
    main()
