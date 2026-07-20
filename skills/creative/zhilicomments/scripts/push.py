#!/usr/bin/env python3
"""
zhilicomments · 微信草稿推送脚本
2026-06-19 实战首版。绕过 publish_zhili.py 的三个坑：
  1. 用 POST /cgi-bin/stable_token（不是 GET /cgi-bin/token）
  2. 不强制要求 mmbiz 图片（zhilicomments 短评不需要）
  3. 从 ~/.hermes/keys/wx_appsecret.txt 读真值（config.md 是 REDACTED 占位符）

2026-06-28 集成 zhili-illustration：
  - preflight 之后自动生成 2 张配图（开头钩子 + 结尾）
  - 配图注入 HTML → 上传微信素材 → mmbiz 替换本地路径
  - 封面图也由 zhili-illustration 生成（16:9 → 裁剪为 900×383）

Usage:
    # 标准发布（HTML 在 /tmp/zhili_article.html，封面在 /tmp/zhili_cover.png）
    python3 push.py --html /tmp/zhili_article.html --cover /tmp/zhili_cover.png

    # 自定义文件路径（--html 必须，显式传参）
    python3 push.py --html /path/to/article.html --cover /path/to/cover.png

    # 跳过配图（直接推送，无插图）
    python3 push.py --html /path/to/article.html --skip-illustration
"""
import argparse
import json
import os
import re
import shutil
import ssl
import subprocess
import sys
import urllib.request


# ============ 配置（按需修改）============
APPID = "wx38a91c353554588a"
APP_SECRET_PATH = os.path.expanduser("~/.hermes/keys/wx_appsecret.txt")
TITLE = "Anthropic 的设计提示词被人扒出来开源了，还顺手教 AI 识别AI味儿"
AUTHOR = "刘生"
DIGEST = "Anthropic 设计提示词被反向工程开源，14项技能里藏着AI味儿检测器"
HTML_PATH = "/tmp/zhili_article.html"
COVER_PATH = "/tmp/zhili_cover.png"
DEFAULT_COVER_PATH = "/tmp/zhili_cover.png"


# ============ zhili-illustration 集成（2026-06-28）============

ILLUSTRATION_IP = "问号人"
ILLUSTRATION_STYLE = "手绘线稿·淡彩"
ILLUSTRATION_DIR = "/tmp/zhili_illustrations"
RUN_MMX = os.path.expanduser("~/.hermes/skills/creative/xiaohu-ip-studio/scripts/run_mmx.py")

# zhilicomments 短评固定 2 张配图：开头钩子 + 结尾
SHOT_LIST = [
    {
        "name": "img_01",
        "position_keyword": None,  # 开头钩子：第一个 <h2> 之后
        "shot_type": "情绪锚点图",
        "aspect_ratio": "4:3",
        "max_width": "660px",
    },
    {
        "name": "img_02",
        "position_keyword": None,  # 结尾钩子：最后一段之后
        "shot_type": "情绪锚点图",
        "aspect_ratio": "4:3",
        "max_width": "660px",
    },
]


def _build_prompt_file(html: str, shot: dict, idx: int) -> str:
    """生成单张配图的 prompt 文件（/tmp/illo_prompt.md）。"""
    # 提取对应段落内容作为 context
    paras = re.findall(r"<p[^>]*>(.*?)</p>", html, re.DOTALL)
    paras_plain = [re.sub(r"<[^>]+>", "", p).strip() for p in paras if p.strip()]
    first_para = paras_plain[0] if paras_plain else ""
    last_para = paras_plain[-1] if paras_plain else ""

    if idx == 0:
        context = first_para[:200]
        purpose = "放在文章开头段落之后，营造情绪氛围"
        must_include = "问号人（极简符号人），手绘线稿·淡彩风格"
    else:
        context = last_para[:200]
        purpose = "放在文章结尾，呼应核心观点"
        must_include = "问号人（极简符号人），手绘线稿·淡彩风格"

    content = f"""[Task]
为文章段落生成配图，IP 角色：{ILLUSTRATION_IP}（极简线条符号人），画风：{ILLUSTRATION_STYLE}。

[Content]
- 用途：{purpose}
- 核心意思：{context}
- 必现内容点：{ILLUSTRATION_IP} 角色、场景氛围
- 建议中文标注词：（无文字，纯符号表达）

[Visual Requirements]
- 比例：{shot["aspect_ratio"]}
- 角色占比：小·嵌入（~15%）
- 不要任何文字（标签/标题/注释都不要）
- 纯符号表达，禁止 emoji
"""
    path = "/tmp/illo_prompt.md"
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def extract_shot_list(html: str) -> list:
    """根据 HTML 内容生成 shot list（zhilicomments 固定 2 张）。"""
    shots = []
    for i, shot in enumerate(SHOT_LIST):
        prompt_file = _build_prompt_file(html, shot, i)
        out_path = os.path.join(ILLUSTRATION_DIR, f"{shot['name']}.png")
        shots.append({
            **shot,
            "prompt_file": prompt_file,
            "out_path": out_path,
        })
    return shots


def generate_illustrations(shots: list) -> list:
    """调用 run_mmx.py 生成每张配图。"""
    os.makedirs(ILLUSTRATION_DIR, exist_ok=True)

    # 先只生第 1 张确认风格
    print(f"\n[配图] 生成第 1 张基准图（{shots[0]['out_path']}）...")
    cmd = [
        sys.executable, RUN_MMX,
        "--prompt-file", shots[0]["prompt_file"],
        "--out", shots[0]["out_path"],
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"⚠️  run_mmx 第 1 张失败: {r.stderr[:300]}")
        # 不退出，继续尝试第 2 张
    else:
        print(f"      ✓ 第 1 张生成成功")

    # 批量生成其余图片
    for shot in shots[1:]:
        print(f"[配图] 生成 {shot['name']}（{shot['out_path']}）...")
        cmd = [
            sys.executable, RUN_MMX,
            "--prompt-file", shot["prompt_file"],
            "--out", shot["out_path"],
        ]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print(f"      ⚠️  {shot['name']} 失败: {r.stderr[:200]}")
        else:
            print(f"      ✓ {shot['name']} 生成成功")
    return shots


def _find_injection_pos(html: str, keyword: str | None, is_last: bool) -> int:
    """在 HTML 中定位配图注入位置。keyword=None 时：
    - is_last=False → 第一个 <h2> 之后（开头钩子）
    - is_last=True  → 最后一个 </p> 之后（结尾）
    """
    if is_last:
        # 找最后一个 </p>
        pos = html.rfind("</p>")
        if pos == -1:
            pos = len(html)
        return pos

    # 开头钩子：找第一个 <h2
    h2_pos = html.find("<h2")
    if h2_pos != -1:
        # 找这个 h2 之后的第一个 </p>
        end_p = html.find("</p>", h2_pos)
        if end_p != -1:
            return end_p

    # fallback：第一个 </p> 之后
    first_p = html.find("</p>")
    return first_p if first_p != -1 else 300


def inject_into_html(html: str, shots: list, mmbiz_map: dict) -> str:
    """将配图注入 HTML，返回新的 HTML。"""
    for shot in shots:
        local_path = shot["out_path"]
        mmbiz = mmbiz_map.get(local_path)
        if not mmbiz or not os.path.exists(local_path):
            print(f"      ⚠️  跳过 {shot['name']}（文件或 mmbiz 缺失）")
            continue

        pos = _find_injection_pos(html, shot["position_keyword"], shot["name"] == "img_02")

        img_tag = (
            f'<div style="text-align:center;margin:32px 0;">\n'
            f'  <img src="{mmbiz}" style="width:100%;max-width:{shot["max_width"]};border-radius:8px;" />\n'
            f'</div>'
        )
        html = html[:pos + 4] + "\n" + img_tag + "\n" + html[pos + 4:]

    return html


def upload_illustrations(shots: list, token: str) -> dict:
    """上传配图到微信素材，返回 {local_path: mmbiz_url}。"""
    mmbiz_map = {}
    for shot in shots:
        path = shot["out_path"]
        if not os.path.exists(path):
            print(f"      ⚠️  {shot['name']} 文件不存在，跳过上传")
            continue
        print(f"[配图上传] {shot['name']} → {path}")
        url = f"https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={token}&type=image"
        with open(path, "rb") as f:
            img_data = f.read()

        boundary = "----PythonFormBoundary7MA4YWxkTrZu0gW"
        ext = os.path.splitext(path)[1].lstrip(".") or "png"
        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="media"; filename="{shot["name"]}.{ext}"\r\n'
            f"Content-Type: image/{ext}\r\n\r\n"
        ).encode("utf-8") + img_data + f"\r\n--{boundary}--\r\n".encode("utf-8")

        req = urllib.request.Request(
            url, data=body, method="POST",
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                result = json.loads(r.read())
            mmbiz = result.get("url", "")
            if mmbiz:
                mmbiz_map[path] = mmbiz
                print(f"      ✓ mmbiz: {mmbiz[:40]}...")
            else:
                print(f"      ⚠️  上传返回无 url: {result}")
        except Exception as e:
            print(f"      ⚠️  上传失败: {e}")

    return mmbiz_map


# ============ 封面生成（zhili-illustration，2026-06-28）============

TARGET_W, TARGET_H = 900, 383  # 2.35:1


def generate_cover(html: str, title: str, out_path: str = COVER_PATH) -> str:
    """用 xiaohu-ip-studio 生成封面图：16:9 → 裁剪为 900×383。

    封面 prompt：从标题提取核心视觉概念，深色背景 + 情绪氛围。
    生成 16:9 → PIL 裁剪中间部分到 2.35:1。
    """
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    # 从标题提取封面概念
    title_clean = re.sub(r"<[^>]+>", "", title).strip()
    if not title_clean:
        title_clean = "科技新闻"

    # 生成 16:9 底图
    cover_prompt_file = "/tmp/cover_prompt.md"
    cover_prompt = f"""[Task]
为微信公众号文章生成封面图。IP 角色：{ILLUSTRATION_IP}（极简线条符号人），画风：{ILLUSTRATION_STYLE}。

[Content]
- 用途：微信公众号文章封面
- 文章标题：{title_clean}
- 封面氛围：科技感、深色背景、高对比度、情绪张力
- 必现内容点：{ILLUSTRATION_IP} 角色、标题相关的视觉隐喻
- 不要文字（标题已经在公众号平台显示，封面不需要任何文字）

[Visual Requirements]
- 比例：16:9
- 背景：深色系（深蓝/深紫/深灰），营造科技感和阅读氛围
- 角色占比：中·醒目（~25%），{ILLUSTRATION_IP} 作为视觉焦点
- 不要任何文字（标签/标题/注释都不要）
- 纯符号表达，禁止 emoji
"""
    with open(cover_prompt_file, "w", encoding="utf-8") as f:
        f.write(cover_prompt)

    tmp_16x9 = "/tmp/cover_16x9.png"
    print(f"[封面] 生成 16:9 底图（{tmp_16x9}）...")
    cmd = [sys.executable, RUN_MMX, "--prompt-file", cover_prompt_file, "--out", tmp_16x9]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"⚠️  封面生成失败: {r.stderr[:300]}")
        return out_path  # 回退，不阻断流程

    # PIL 裁剪：16:9 → 2.35:1（从中间裁宽边）
    try:
        from PIL import Image
        img = Image.open(tmp_16x9)
        w, h = img.size
        target_ratio = TARGET_W / TARGET_H  # ~2.35
        cur_ratio = w / h

        if cur_ratio > target_ratio:
            # 图太宽：裁左右
            new_w = int(h * target_ratio)
            left = (w - new_w) // 2
            img = img.crop((left, 0, left + new_w, h))
        else:
            # 图太高：裁上下
            new_h = int(w / target_ratio)
            top = (h - new_h) // 2
            img = img.crop((0, top, w, top + new_h))

        img = img.resize((TARGET_W, TARGET_H), Image.LANCZOS)
        img.save(out_path, "PNG")
        print(f"[封面] ✓ {TARGET_W}×{TARGET_H} → {out_path}")
    except ImportError:
        # 没 PIL，直接 resize
        from PIL import Image
        img = Image.open(tmp_16x9).resize((TARGET_W, TARGET_H), Image.LANCZOS)
        img.save(out_path, "PNG")
        print(f"[封面] ✓ resize → {out_path}")
    except Exception as e:
        print(f"⚠️  封面裁剪失败: {e}，回退到原始 16:9")
        shutil.copy(tmp_16x9, out_path)

    return out_path


# ============ 工具函数 ============

def calc_bytes(s: str) -> int:
    """WeChat 草稿 digest 字节：CJK=3 bytes，ASCII=1 byte"""
    return sum(3 if ord(c) > 127 else 1 for c in s)


def get_access_token() -> str:
    """POST /cgi-bin/stable_token（不能用 GET /cgi-bin/token）"""
    with open(APP_SECRET_PATH) as f:
        secret = f.read().strip()
    url = "https://api.weixin.qq.com/cgi-bin/stable_token"
    data = json.dumps({
        "grant_type": "client_credential",
        "appid": APPID,
        "secret": secret,
    }).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, method="POST",
        headers={"Content-Type": "application/json"},
    )
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
        result = json.loads(r.read())
    if "access_token" not in result:
        print(f"❌ access_token 失败: {result}")
        sys.exit(1)
    return result["access_token"]


def upload_cover(token: str, cover_path: str) -> str:
    """material/add_material?type=image（不能用 type=thumb，否则 draft/add 报 40007）"""
    url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image"
    boundary = "----PythonFormBoundary7MA4YWxkTrZu0gW"
    with open(cover_path, "rb") as f:
        img = f.read()
    ext = os.path.splitext(cover_path)[1].lstrip(".") or "png"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="media"; filename="cover.{ext}"\r\n'
        f"Content-Type: image/{ext}\r\n\r\n"
    ).encode("utf-8") + img + f"\r\n--{boundary}--\r\n".encode("utf-8")
    req = urllib.request.Request(
        url, data=body, method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        result = json.loads(r.read())
    if "media_id" not in result:
        print(f"❌ 封面上传失败: {result}")
        sys.exit(1)
    return result["media_id"]


def create_draft(token: str, html: str, media_id: str, title: str, digest: str) -> str:
    """
    draft/add 关键点：
      1. payload 必须用 {"articles": [{...}]} 数组包裹（漏数组 → 44003 empty news data）
      2. ensure_ascii=False + UTF-8 原文
      3. Content-Type: application/json（不带 charset=utf-8）
    """
    payload = {"articles": [{
        "title": title,
        "author": AUTHOR,
        "digest": digest,
        "content": html,
        "thumb_media_id": media_id,
        "need_open_comment": 1,
        "only_fans_can_comment": 0,
        "original": 1,
    }]}
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        result = json.loads(r.read())
    if "media_id" not in result:
        print(f"❌ 草稿创建失败: {result}")
        sys.exit(1)
    return result["media_id"]


def delete_draft(token: str, draft_id: str) -> dict:
    """draft/delete — 重发时先调这个删掉旧草稿"""
    url = f"https://api.weixin.qq.com/cgi-bin/draft/delete?access_token={token}"
    data = json.dumps({"media_id": draft_id}).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


# ============ 入口 ============

def main():
    parser = argparse.ArgumentParser(description="zhilicomments · 公众号草稿推送")
    parser.add_argument("--html", default=HTML_PATH, help="HTML 文件路径")
    parser.add_argument("--cover", default=COVER_PATH, help="封面图路径")
    parser.add_argument("--delete-first", default="", help="先删除指定 draft_id，再推新草稿")
    parser.add_argument("--skip-illustration", action="store_true", help="跳过配图生成（直接推送，无插图）")
    parser.add_argument("--skip-cover", action="store_true", help="跳过封面生成，使用 --cover 指定的已有封面图")
    args = parser.parse_args()

    # 读 HTML 并动态提取标题 + digest
    import re
    with open(args.html, encoding="utf-8") as f:
        html = f.read()
    cjk = sum(1 for c in html if "\u4e00" <= c <= "\u9fff")
    print(f"HTML 中文字数: {cjk} (要求 1000-1500)")
    assert 1000 <= cjk <= 1500, "❌ 字数超区间"

    title_match = re.search(r"<title>(.*?)</title>", html)
    live_title = title_match.group(1).strip() if title_match else TITLE
    p_matches = re.findall(r"<p[^>]*>(.*?)</p>", html, re.DOTALL)
    first_p_text = re.sub(r"<[^>]+>", "", p_matches[0]).strip() if p_matches else DIGEST
    live_digest = (first_p_text[:40].strip() or DIGEST)
    # digest 限 54 字节（CJK=3B，ASCII=1B），18字 CJK 约 54B，留余量截到 18 字
    live_digest = live_digest[:18]

    # 预检
    print(f"标题: {live_title} ({len(live_title)} 字符)")
    print(f"作者: 刘生")
    print(f"digest: {live_digest}")
    db = calc_bytes(live_digest)
    print(f"digest 字节: {db} (限 54)")
    assert db <= 54, f"❌ digest 超 54 字节"

    if not os.path.exists(args.cover):
        print(f"❌ 封面图不存在: {args.cover}")
        sys.exit(1)

    # ========== zhili-illustration 流程 ==========
    # 步骤 1：preflight 之后立即生成图片（不需要 token）
    shots = []
    cover_path = args.cover
    if not args.skip_illustration:
        print("\n[配图] 提取 shot list...")
        shots = extract_shot_list(html)
        print(f"      ✓ {len(shots)} 张配图：{[s['name'] for s in shots]}")

        print("\n[配图] 生成配图（mmx-cli）...")
        generate_illustrations(shots)

    # 封面生成（zhili-illustration）
    if not args.skip_cover:
        print("\n[封面] 用 zhili-illustration 生成封面图...")
        cover_path = generate_cover(html, live_title or TITLE, COVER_PATH)
    else:
        print(f"\n[封面] 跳过（使用已有封面：{args.cover}）")
        cover_path = args.cover
    # ========== 配图生成结束 ==========

    print("\n[1/4] 获取 access_token...")
    token = get_access_token()
    print(f"      ✓ token 长度: {len(token)}")

    if args.delete_first:
        print(f"\n[2/4] 删除旧草稿 {args.delete_first[:20]}...")
        result = delete_draft(token, args.delete_first)
        print(f"      ✓ {result}")
        step_cover_label = "[3/4] 封面上传 + 重推草稿..."
    else:
        step_cover_label = "[3/4] 封面上传 + 创建草稿..."

    # ========== 步骤 2/4：配图上传 + 注入 HTML ==========
    step_illo_label = "[2/4] 配图上传 + 注入 HTML..."
    if shots:
        print(f"\n{step_illo_label}")
        mmbiz_map = upload_illustrations(shots, token)
        print(f"      ✓ {len(mmbiz_map)} 张配图已上传")
        if mmbiz_map:
            print("\n[配图] 注入 HTML...")
            html = inject_into_html(html, shots, mmbiz_map)
            print("      ✓ HTML 配图注入完成")
    else:
        print(f"\n{step_illo_label}（跳过，无配图）")

    # ========== 步骤 3/4：封面上传 + 创建草稿 ==========
    print(f"\n{step_cover_label}")
    cover_id = upload_cover(token, cover_path)
    print(f"      ✓ cover media_id: {cover_id}")
    draft_id = create_draft(token, html, cover_id, live_title, live_digest)
    print(f"      ✓ draft_id: {draft_id}")

    print(f"\n========== 发布完成 ==========")
    print(f"标题: {live_title}")
    print(f"草稿 media_id: {draft_id}")
    print(f"配图: {len(shots)} 张" if shots else "配图: 无")
    print(f"请到微信公众平台后台编辑并发布")


if __name__ == "__main__":
    main()