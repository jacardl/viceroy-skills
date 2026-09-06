#!/usr/bin/env python3
"""
zhiligithub · 微信草稿推送脚本

2026-06-28 集成 zhili-illustration：
  - 配图：自动提取 H2 小节（最多 5 张），生成 + 注入 HTML + 上传 mmbiz
  - 封面：xiaohu-ip-studio 生成 16:9 → PIL 裁剪 900×383（2.35:1）
  - 全流程 4 步：配图生成 → HTML 注入 → 封面上传 → 创建草稿

Usage:
    # 标准发布（HTML 在 /tmp/zhili_article.html）
    python3 push.py

    # 自定义路径
    python3 push.py --html /path/to/article.html --cover /path/to/cover.png

    # 跳过配图（快速重推已有图）
    python3 push.py --skip-illustration

    # 跳过封面（用已有封面）
    python3 push.py --skip-cover

    # 删除旧草稿再发
    python3 push.py --delete-first <draft_id>
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
HTML_PATH = "/tmp/zhili_article.html"
COVER_PATH = "/tmp/zhili_cover.png"
DEFAULT_COVER_PATH = "/tmp/zhili_cover.png"


# ============ zhili-illustration 集成（2026-06-28）============

ILLUSTRATION_IP = "问号人"
ILLUSTRATION_STYLE = "手绘线稿·淡彩"
ILLUSTRATION_DIR = "/tmp/zhili_illustrations"
RUN_MMX = os.path.expanduser("~/.hermes/skills/creative/xiaohu-ip-studio/scripts/run_mmx.py")

# zhiligithub 长文最多 5 张配图（每个 H2 小节一张）
MAX_SHOTS = 5


def _build_prompt_file(html: str, h2_title: str, section_content: str, idx: int) -> str:
    """生成单张配图的 prompt 文件。"""
    # 取该小节的核心意思（段落前100字）
    paras = re.findall(r"<p[^>]*>(.*?)</p>", section_content, re.DOTALL)
    paras_plain = [re.sub(r"<[^>]+>", "", p).strip() for p in paras if p.strip()]
    snippet = " ".join(paras_plain[:3])[:150].strip()

    content = f"""[Task]
为文章段落生成配图，IP 角色：{ILLUSTRATION_IP}（极简线条符号人），画风：{ILLUSTRATION_STYLE}。

[Content]
- 章节：「{h2_title}」
- 用途：放在文章「{h2_title}」小节之后
- 核心意思：{snippet}
- 必现内容点：{ILLUSTRATION_IP} 角色、章节相关的视觉隐喻
- 不要文字（标签/标题/注释都不要）

[Visual Requirements]
- 比例：4:3
- 角色占比：小·嵌入（~15%）
- 不要任何文字，纯符号表达，禁止 emoji
"""
    path = "/tmp/illo_prompt.md"
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def extract_shot_list(html: str) -> list:
    """从 HTML 提取 shot list：每个 H2 小节一张配图（最多 MAX_SHOTS）。"""
    # 找所有 H2
    h2_pattern = re.compile(r'<h2[^>]*>(.*?)</h2>', re.DOTALL)
    h2_matches = list(h2_pattern.finditer(html))

    if not h2_matches:
        print("[WARN] HTML 中无 H2，配图数量降为 0")
        return []

    shots = []
    for idx, m in enumerate(h2_matches[:MAX_SHOTS]):
        h2_title = re.sub(r"<[^>]+>", "", m.group(1)).strip()

        # 取该 H2 到下一个 H2（或末尾）之间的内容
        start = m.end()
        end = h2_matches[idx + 1].start() if idx + 1 < len(h2_matches) else len(html)
        section_html = html[start:end]

        prompt_file = _build_prompt_file(html, h2_title, section_html, idx)
        out_path = os.path.join(ILLUSTRATION_DIR, f"img_{idx + 1:02d}.png")
        shots.append({
            "name": f"img_{idx + 1:02d}",
            "h2_title": h2_title,
            "prompt_file": prompt_file,
            "out_path": out_path,
        })

    return shots


def generate_illustrations(shots: list) -> list:
    """调用 run_mmx.py 生成每张配图。"""
    os.makedirs(ILLUSTRATION_DIR, exist_ok=True)

    # 先生第 1 张确认风格
    if shots:
        print(f"\n[配图] 生成第 1 张基准图（{shots[0]['out_path']}）...")
        cmd = [
            sys.executable, RUN_MMX,
            "--prompt-file", shots[0]["prompt_file"],
            "--out", shots[0]["out_path"],
        ]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print(f"⚠️  run_mmx 第 1 张失败: {r.stderr[:300]}")
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


def _find_injection_pos(html: str, after_h2_idx: int) -> int:
    """找第 N 个 H2 之后的第一个 </p> 位置。"""
    h2_pattern = re.compile(r'<h2[^>]*>.*?</h2>', re.DOTALL)
    h2_matches = list(h2_pattern.finditer(html))

    if after_h2_idx >= len(h2_matches):
        # fallback：最后一个 </p>
        pos = html.rfind("</p>")
        return pos if pos != -1 else len(html)

    # 该 H2 之后第一个 </p>
    h2_end = h2_matches[after_h2_idx].end()
    end_p = html.find("</p>", h2_end)
    return end_p if end_p != -1 else (h2_end + 100)


def inject_into_html(html: str, shots: list, mmbiz_map: dict) -> str:
    """将配图注入 HTML，每个 H2 小节之后一张。"""
    for shot in shots:
        local_path = shot["out_path"]
        mmbiz = mmbiz_map.get(local_path)
        if not mmbiz or not os.path.exists(local_path):
            print(f"      ⚠️  跳过 {shot['name']}（文件或 mmbiz 缺失）")
            continue

        # 根据 name 提取序号（img_01 → idx 0）
        try:
            idx = int(re.search(r"img_(\d+)", shot["name"]).group(1)) - 1
        except Exception:
            idx = 0

        pos = _find_injection_pos(html, idx)

        img_tag = (
            f'<div style="text-align:center;margin:32px 0;">\n'
            f'  <img src="{mmbiz}" style="width:100%;max-width:660px;border-radius:8px;" />\n'
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


# ============ 封面生成（zhili-illustration）============

TARGET_W, TARGET_H = 900, 383  # 2.35:1


def generate_cover(html: str, title: str, out_path: str = COVER_PATH) -> str:
    """用 xiaohu-ip-studio 生成封面图：16:9 → 裁剪为 900×383。

    封面 prompt：从标题提取核心视觉概念，深色背景 + 情绪氛围。
    生成 16:9 → PIL 裁剪中间部分到 2.35:1。
    """
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    title_clean = re.sub(r"<[^>]+>", "", title).strip()
    if not title_clean:
        title_clean = "GitHub 黑马项目"

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
    """POST /cgi-bin/stable_token（不能用旧 GET /cgi-bin/token）"""
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
    if not os.path.exists(cover_path):
        print(f"❌ 封面图不存在: {cover_path}")
        sys.exit(1)
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


def create_draft(token: str, html: str, media_id: str, title: str, digest: str, author: str = "刘生") -> str:
    """创建草稿：payload 必须 {"articles": [{...}]}，ensure_ascii=False"""
    payload = {"articles": [{
        "title": title,
        "author": author,
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
    """draft/delete — 重发时先删旧草稿"""
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
    parser = argparse.ArgumentParser(description="zhiligithub · 公众号草稿推送")
    parser.add_argument("--html", default=HTML_PATH, help="HTML 文件路径")
    parser.add_argument("--cover", default=COVER_PATH, help="封面图路径")
    parser.add_argument("--delete-first", default="", help="先删除指定 draft_id，再推新草稿")
    parser.add_argument("--skip-illustration", action="store_true", help="跳过配图生成（直接推送）")
    parser.add_argument("--skip-cover", action="store_true", help="跳过封面生成，使用 --cover 指定的已有封面")
    args = parser.parse_args()

    # 读 HTML，动态提取标题 + digest
    with open(args.html, encoding="utf-8") as f:
        html = f.read()

    cjk = sum(1 for c in html if "\u4e00" <= c <= "\u9fff")
    print(f"HTML 中文字数: {cjk} (要求 1500-2000)")

    # 提取标题
    title_match = re.search(r"<title>(.*?)</title>", html)
    live_title = title_match.group(1).strip() if title_match else "GitHub 黑马项目"

    # 提取第一段作为 digest
    p_matches = re.findall(r"<p[^>]*>(.*?)</p>", html, re.DOTALL)
    first_p_text = re.sub(r"<[^>]+>", "", p_matches[0]).strip() if p_matches else ""
    live_digest = (first_p_text[:40].strip() or live_title[:40])
    # digest 限 54 字节，18 字 CJK 约 54B
    live_digest = live_digest[:18]

    print(f"标题: {live_title} ({len(live_title)} 字符)")
    print(f"作者: 刘生")
    print(f"digest: {live_digest} ({calc_bytes(live_digest)} 字节，限 54)")

    assert calc_bytes(live_digest) <= 54, "❌ digest 超 54 字节"

    if not os.path.exists(args.html):
        print(f"❌ HTML 不存在: {args.html}")
        sys.exit(1)

    cover_path = args.cover

    # ========== zhili-illustration 流程 ==========

    # 步骤 1：配图生成
    shots = []
    if not args.skip_illustration:
        print("\n[配图] 提取 shot list...")
        shots = extract_shot_list(html)
        print(f"      ✓ {len(shots)} 张配图：{[s['name'] for s in shots]}")

        if shots:
            print("\n[配图] 生成配图（mmx-cli）...")
            generate_illustrations(shots)

    # 步骤 2：封面生成（zhili-illustration）
    if not args.skip_cover:
        print("\n[封面] 用 zhili-illustration 生成封面图...")
        cover_path = generate_cover(html, live_title, COVER_PATH)
    else:
        print(f"\n[封面] 跳过（使用已有封面：{args.cover}）")
        if not os.path.exists(args.cover):
            print(f"❌ 封面图不存在: {args.cover}")
            sys.exit(1)
        cover_path = args.cover

    # ========== token + 配图上传 ==========
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
