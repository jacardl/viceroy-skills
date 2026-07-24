#!/usr/bin/env python3
"""
zhililong · 微信草稿推送脚本（含 zhili-illustration 集成）

2026-06-28 集成 zhili-illustration：
  - 配图：自动提取 H2 小节（最多 5 张），生成 + 注入 HTML + 上传 mmbiz
  - 封面：xiaohu-ip-studio 生成 16:9 → PIL 裁剪 900×383（2.35:1）
  - 全流程 5 步：配图生成 → HTML 注入 → 封面上传 → 创建草稿 → 删除旧草稿

用法:
  # 标准发布（HTML 在 /tmp/zhili_article.html，封面在 /tmp/zhili_cover.png）
  python3 publish_lanlong.py --html /tmp/article.html --cover /tmp/cover.png \
    --title "文章标题" --author "刘生" --digest "文章摘要"

  # 跳过配图（直接推送，无插图）
  python3 publish_lanlong.py --html /tmp/article.html --cover /tmp/cover.png \
    --title "..." --author "刘生" --digest "..." \
    --skip-illustration

  # 跳过封面生成（用已有封面）
  python3 publish_lanlong.py --html /tmp/article.html --cover /tmp/cover.png \
    --title "..." --author "刘生" --digest "..." \
    --skip-cover

  # 重推（先删旧草稿）
  python3 publish_lanlong.py --html /tmp/article.html --cover /tmp/cover.png \
    --title "..." --author "刘生" --digest "..." \
    --delete-first kiuyle4KZHC7JKxpTQssMDHBE_fD05y2cqQjXeLko...
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
from datetime import datetime

# ============ 配置（按需修改）============
APPID = "wx38a91c353554588a"
APP_SECRET_PATH = os.path.expanduser("~/.hermes/keys/wx_appsecret.txt")
DEFAULT_COVER_PATH = "/tmp/zhili_cover.png"
DEFAULT_HTML_PATH = "/tmp/zhili_article.html"
ZHILILONG_ILLUSTRATION_DIR = "/tmp/zhililong_illustrations"
RUN_MMX = os.path.expanduser("~/.hermes/skills/creative/xiaohu-ip-studio/scripts/run_mmx.py")
TARGET_W, TARGET_H = 900, 383  # 2.35:1 封面裁剪目标
MAX_ILLUSTRATIONS = 5  # 长文最多 5 张配图

ILLUSTRATION_IP = "问号人"
ILLUSTRATION_STYLE = "手绘线稿·淡彩"


# ============ zhili-illustration：配图提取（2026-06-28）============

def _extract_h2_sections(html: str) -> list:
    """提取 HTML 中所有 <h2> 标题文本，作为配图锚点。"""
    h2s = re.findall(r"<h2[^>]*>(.*?)</h2>", html, re.DOTALL)
    results = []
    for h in h2s:
        text = re.sub(r"<[^>]+>", "", h).strip()
        if text:
            results.append(text)
    return results


def _build_illo_prompt(html: str, section_title: str, idx: int, total: int) -> str:
    """为单个配图生成 prompt 文件。"""
    paras = re.findall(r"<p[^>]*>(.*?)</p>", html, re.DOTALL)
    paras_plain = [re.sub(r"<[^>]+>", "", p).strip() for p in paras if p.strip()]

    # 取该 H2 之后的第一个段落作为 context
    h2_pos = html.find(f"<h2")
    pos = 0
    for i, m in enumerate(re.finditer(r"<h2[^>]*>", html)):
        inner = re.sub(r"<[^>]+>", "", html[m.start():html.find("</h2>", m.start())]).strip()
        if inner == section_title:
            pos = html.find("</h2>", m.start())
            break

    next_p = re.search(r"</h2>\s*<p[^>]*>(.*?)</p>", html[pos:pos+1000], re.DOTALL)
    context = ""
    if next_p:
        context = re.sub(r"<[^>]+>", "", next_p.group(1)).strip()
    if not context and paras_plain:
        context = paras_plain[min(idx, len(paras_plain)-1)]

    purpose = f"放在「{section_title[:20]}」章节之后，配图说明该小节核心观点"
    content = f"""[Task]
为文章章节生成配图，IP 角色：{ILLUSTRATION_IP}（极简线条符号人），画风：{ILLUSTRATION_STYLE}。

[Content]
- 用途：{purpose}
- 章节标题：{section_title}
- 核心意思：{context[:200]}
- 必现内容点：{ILLUSTRATION_IP} 角色、场景氛围
- 建议中文标注词：（无文字，纯符号表达）

[Visual Requirements]
- 比例：4:3
- 角色占比：小·嵌入（~15%）
- 不要任何文字（标签/标题/注释都不要）
- 纯符号表达，禁止 emoji
"""
    path = f"/tmp/lanlong_illo_prompt_{idx}.md"
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def extract_shot_list(html: str) -> list:
    """根据 HTML 中 H2 章节提取 shot list（最多 5 张）。"""
    sections = _extract_h2_sections(html)
    shots = []
    for i, sec in enumerate(sections[:MAX_ILLUSTRATIONS]):
        out_path = os.path.join(ZHILILONG_ILLUSTRATION_DIR, f"img_{i+1:02d}.png")
        prompt_file = _build_illo_prompt(html, sec, i, len(sections))
        shots.append({
            "name": f"img_{i+1:02d}",
            "section": sec[:30],
            "prompt_file": prompt_file,
            "out_path": out_path,
        })
    return shots


def generate_illustrations(shots: list) -> list:
    """调用 run_mmx.py 生成每张配图。"""
    os.makedirs(ZHILILONG_ILLUSTRATION_DIR, exist_ok=True)

    for idx, shot in enumerate(shots):
        print(f"[配图] 生成第 {idx+1}/{len(shots)} 张：{shot['section']}...")
        cmd = [
            sys.executable, RUN_MMX,
            "--prompt-file", shot["prompt_file"],
            "--out", shot["out_path"],
        ]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print(f"      ⚠️  {shot['name']} 失败: {r.stderr[:200]}")
        else:
            print(f"      ✓ {shot['name']} 生成成功 → {shot['out_path']}")

    return shots


def _find_injection_pos(html: str, section_title: str) -> int:
    """在 HTML 中找到指定章节 <h2> 之后的第一个 </p> 位置。"""
    # 找该 H2 的结束位置
    pattern = re.compile(r"<h2[^>]*>.*?" + re.escape(section_title) + r".*?</h2>", re.DOTALL)
    m = pattern.search(html)
    if not m:
        return html.find("</p>")
    end_h2 = m.end()
    # 找 H2 之后的第一个 </p>
    pos = html.find("</p>", end_h2)
    return pos if pos != -1 else end_h2


def inject_into_html(html: str, shots: list, mmbiz_map: dict) -> str:
    """将配图注入 HTML（每个 H2 之后一张）。"""
    for shot in shots:
        local_path = shot["out_path"]
        mmbiz = mmbiz_map.get(local_path)
        if not mmbiz or not os.path.exists(local_path):
            print(f"      ⚠️  跳过 {shot['name']}（文件或 mmbiz 缺失）")
            continue

        pos = _find_injection_pos(html, shot["section"])
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


# ============ zhili-illustration：封面生成（2026-06-28）============

def generate_cover(html: str, title: str, out_path: str = DEFAULT_COVER_PATH) -> str:
    """用 xiaohu-ip-studio 生成封面图：16:9 → 裁剪为 900×383。"""
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    title_clean = re.sub(r"<[^>]+>", "", title).strip()
    if not title_clean:
        title_clean = "科技新闻"

    cover_prompt_file = "/tmp/lanlong_cover_prompt.md"
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

    tmp_16x9 = "/tmp/lanlong_cover_16x9.png"
    print(f"[封面] 生成 16:9 底图（{tmp_16x9}）...")
    cmd = [sys.executable, RUN_MMX, "--prompt-file", cover_prompt_file, "--out", tmp_16x9]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"⚠️  封面生成失败: {r.stderr[:300]}")
        return out_path

    # PIL 裁剪：16:9 → 2.35:1
    try:
        from PIL import Image
        img = Image.open(tmp_16x9)
        w, h = img.size
        target_ratio = TARGET_W / TARGET_H
        cur_ratio = w / h

        if cur_ratio > target_ratio:
            new_w = int(h * target_ratio)
            left = (w - new_w) // 2
            img = img.crop((left, 0, left + new_w, h))
        else:
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


# ============ WeChat API 直接调用（不走 publish_zhili.py）============

def get_access_token() -> str:
    """POST /cgi-bin/stable_token"""
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
    """material/add_material?type=image"""
    url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image"
    boundary = "----PythonFormBoundary7MA4YWxkTrZu0gW"
    with open(cover_path, "rb") as f:
        img_data = f.read()
    ext = os.path.splitext(cover_path)[1].lstrip(".") or "png"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="media"; filename="cover.{ext}"\r\n'
        f"Content-Type: image/{ext}\r\n\r\n"
    ).encode("utf-8") + img_data + f"\r\n--{boundary}--\r\n".encode("utf-8")
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


def create_draft(token: str, html: str, media_id: str, title: str, author: str, digest: str) -> str:
    """draft/add"""
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
    """draft/delete"""
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
    parser = argparse.ArgumentParser(description="zhililong · 公众号草稿推送（含 zhili-illustration）")
    parser.add_argument("--title", required=True, help="文章标题")
    parser.add_argument("--author", default="刘生", help="作者署名")
    parser.add_argument("--digest", required=True, help="摘要（≤54 字节）")
    parser.add_argument("--html", default=DEFAULT_HTML_PATH, help="正文 HTML 文件路径")
    parser.add_argument("--cover", default=DEFAULT_COVER_PATH, help="封面图路径")
    parser.add_argument("--delete-first", default="", help="先删除指定 draft_id，再推新草稿")
    parser.add_argument("--skip-illustration", action="store_true", help="跳过配图生成（直接推送，无插图）")
    parser.add_argument("--skip-cover", action="store_true", help="跳过封面生成，使用 --cover 指定的已有封面图")
    args = parser.parse_args()

    # ============ Step 1: 校验输入 ============
    if not os.path.exists(args.html):
        print(f"❌ HTML 文件不存在: {args.html}")
        sys.exit(1)

    with open(args.html, encoding="utf-8") as f:
        html = f.read()

    # ============ Step 2: zhili-illustration 生成配图 ============
    shots = []
    cover_path = args.cover

    if not args.skip_illustration:
        print("\n[配图] 提取 shot list...")
        shots = extract_shot_list(html)
        print(f"      ✓ {len(shots)} 张配图：{[s['name'] for s in shots]}")

        print("\n[配图] 生成配图（mmx-cli）...")
        generate_illustrations(shots)
    else:
        print("\n[配图] 跳过（--skip-illustration）")
        # 2026-07-08 fix: 检查 HTML 是否已有 mmbiz img 标签（有则说明 img 已预注入，不需要走 shot 提取/上传/注入流程）
        existing_imgs = re.findall(r'<img[^>]+src="(http://mmbiz\.qpic\.cn[^"]+)"', html)
        if existing_imgs:
            print(f"      ℹ️  HTML 已有 {len(existing_imgs)} 张 mmbiz 图片，跳过 shot 提取和注入")
            shots = []  # 强制清空，确保后续 upload_illustrations/inject_into_html 不执行

    # ============ Step 3: zhili-illustration 生成封面 ============
    # Bugfix 2026-07-08：--skip-cover 时优先用 --cover 指定的已有文件，不调用 generate_cover
    if args.skip_cover:
        if not os.path.exists(args.cover):
            print(f"❌ 封面不存在: {args.cover}")
            sys.exit(1)
        print(f"\n[封面] 跳过（--skip-cover，使用已有：{args.cover}）")
        cover_path = args.cover
    else:
        print("\n[封面] 用 zhili-illustration 生成封面图...")
        cover_path = generate_cover(html, args.title, args.cover)  # 生成到 --cover 指定路径，不走 DEFAULT_COVER_PATH

    # ============ Step 4: 获取 token ============
    print("\n[4/5] 获取 access_token...")
    token = get_access_token()
    print(f"      ✓ token 长度: {len(token)}")

    # ============ Step 5: 配图上传 + 注入 HTML ============
    if shots:
        print("\n[配图上传] 上传配图到微信素材...")
        mmbiz_map = upload_illustrations(shots, token)
        print(f"      ✓ {len(mmbiz_map)} 张配图已上传")

        if mmbiz_map:
            print("\n[配图注入] 注入 HTML...")
            html = inject_into_html(html, shots, mmbiz_map)
            print("      ✓ HTML 配图注入完成")
    else:
        print("\n[配图注入] 跳过（无配图）")

    # ============ Step 6: 封面上传 + 创建草稿 ============
    if args.delete_first:
        print(f"\n[删除旧草稿] {args.delete_first[:20]}...")
        result = delete_draft(token, args.delete_first)
        print(f"      ✓ {result}")

    print("\n[封面上传 + 创建草稿]")
    cover_id = upload_cover(token, cover_path)
    print(f"      ✓ cover media_id: {cover_id}")

    draft_id = create_draft(token, html, cover_id, args.title, args.author, args.digest)
    print(f"      ✓ draft_id: {draft_id}")

    # ============ 回写结果 ============
    output_json = os.path.join(os.path.dirname(args.html) or "/tmp", "upload_results.json")
    result_data = {
        "draft_media_id": draft_id,
        "title": args.title,
        "author": args.author,
        "cover": cover_path,
        "illustration_count": len(shots),
        "html_path": args.html,
        "published_at": datetime.now().isoformat(),
        "draft_url": "https://mp.weixin.qq.com/cgi-bin/appmsg?action=list&type=10",
    }
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)
    print(f"✅ 结果已回写: {output_json}")

    print("")
    print("=" * 60)
    print("🎉 草稿推送成功")
    print(f"   草稿 media_id : {draft_id}")
    print(f"   标题          : {args.title}")
    print(f"   作者          : {args.author}")
    print(f"   配图数        : {len(shots)} 张")
    print("=" * 60)
    print("📌 接下来：登录微信公众平台 → 内容管理 → 草稿箱 → 编辑 → 群发")


if __name__ == "__main__":
    main()
