#!/usr/bin/env python3
"""
PIL 封面图生成器 — zhiliGitHub 草稿专用
零外部 API 依赖，确定性高，风格统一（#1B365D 墨蓝背景 + 白色主标题 + #c9553d 砖红副标题）

首次实战: 2026-06-04 headroom 9.5k 草稿 (800×400 PNG, 23KB)
字体: NotoSansCJK-Bold (路径自动 fallback)

Usage:
    python3 cover_pil.py "标题" "副标题" "tagline" /tmp/cover.png [width] [height]
    python3 cover_pil.py "9.5k星Headroom" "把LLM输入压掉60-95%" "开源·MCP·可逆压缩" /tmp/cover.png

Requirements: pip install Pillow
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont


# 调色板（按 zhiliGitHub 样式A 锁定，2026-06-04 实战）
BG = (27, 54, 93)          # #1B365D 墨蓝背景
FG = (255, 255, 255)       # #FFFFFF 白色主标题
ACCENT = (201, 85, 61)     # #c9553d 砖红副标题
TEAL = (0, 212, 170)       # #00d4aa 青色装饰
SUB = (245, 244, 237)      # #f5f4ed 羊皮纸 tagline

# CJK 字体 fallback 链（按系统实际路径调整）
FONT_PATHS = [
    "/usr/share/fonts/google-noto-cjk/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    "/usr/share/fonts/truetype/arphic/uming.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # 英文 fallback
    "/Library/Fonts/PingFang.ttc",  # macOS
    "C:/Windows/Fonts/msyhbd.ttc",  # Windows
]


def find_font():
    for p in FONT_PATHS:
        if os.path.exists(p):
            return p
    raise RuntimeError(
        f"找不到 CJK 字体，尝试过: {FONT_PATHS}\n"
        "请安装 noto-cjk: apt install fonts-noto-cjk  (Debian/Ubuntu)\n"
        "或: yum install google-noto-sans-cjk-fonts  (CentOS/RHEL)"
    )


def wrap_text(draw, text, font, max_width):
    """按字符粗切自动换行（中英混合安全）"""
    lines = []
    cur = ""
    for ch in text:
        test = cur + ch
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] > max_width and cur:
            lines.append(cur)
            cur = ch
        else:
            cur = test
    if cur:
        lines.append(cur)
    return lines


def generate_cover(
    title: str,
    subtitle: str = "",
    tagline: str = "",
    output_path: str = "/tmp/cover.png",
    width: int = 800,
    height: int = 400,
) -> str:
    """生成 zhiliGitHub 风格封面图

    Args:
        title: 主标题（必填）
        subtitle: 副标题（可选）
        tagline: 底部小字（可选）
        output_path: 输出路径
        width: 宽度（默认 800）
        height: 高度（默认 400，比例 2:1）

    Returns:
        output_path
    """
    font_path = find_font()
    img = Image.new("RGB", (width, height), BG)
    d = ImageDraw.Draw(img)

    # 装饰：左下角小色块（#00d4aa + #c9553d 标志性元素）
    d.rectangle([0, height - 8, 80, height], fill=ACCENT)
    d.rectangle([0, height - 16, 40, height - 8], fill=TEAL)

    # 主标题（最大字号 56，自动换行最多 2 行）
    title_font = ImageFont.truetype(font_path, 56)
    title_lines = wrap_text(d, title, title_font, width - 80)[:2]

    # 垂直居中算法：先算总高度，再起点
    line_h = 64
    if subtitle:
        sub_h = 36
    else:
        sub_h = 0
    if tagline:
        tag_h = 22
    else:
        tag_h = 0

    total_h = line_h * len(title_lines) + sub_h + tag_h + (40 if subtitle else 0) + (50 if tagline else 0)
    y = (height - total_h) // 2

    # 渲染主标题
    for line in title_lines:
        bbox = d.textbbox((0, 0), line, font=title_font)
        tw = bbox[2] - bbox[0]
        d.text(((width - tw) // 2, y), line, fill=FG, font=title_font)
        y += line_h

    # 渲染副标题
    if subtitle:
        y += 20
        sub_font = ImageFont.truetype(font_path, 28)
        bbox = d.textbbox((0, 0), subtitle, font=sub_font)
        sw = bbox[2] - bbox[0]
        d.text(((width - sw) // 2, y), subtitle, fill=ACCENT, font=sub_font)
        y += sub_h

    # 渲染 tagline
    if tagline:
        tag_font = ImageFont.truetype(font_path, 16)
        bbox = d.textbbox((0, 0), tagline, font=tag_font)
        tw_ = bbox[2] - bbox[0]
        d.text(((width - tw_) // 2, height - 50), tagline, fill=SUB, font=tag_font)

    img.save(output_path, "PNG", quality=95)
    size = os.path.getsize(output_path)
    print(f"✓ 封面已生成: {output_path} ({width}×{height}, {size} bytes, 字体={os.path.basename(font_path)})")
    return output_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 cover_pil.py '标题' ['副标题' ['tagline' [/tmp/cover.png [width [height]]]]]")
        print()
        print("Example:")
        print('  python3 cover_pil.py "9.5k星Headroom" "把LLM输入压掉60-95%" "开源·MCP·可逆压缩" /tmp/cover.png')
        sys.exit(1)

    title = sys.argv[1]
    subtitle = sys.argv[2] if len(sys.argv) > 2 else ""
    tagline = sys.argv[3] if len(sys.argv) > 3 else ""
    output = sys.argv[4] if len(sys.argv) > 4 else "/tmp/cover.png"
    width = int(sys.argv[5]) if len(sys.argv) > 5 else 800
    height = int(sys.argv[6]) if len(sys.argv) > 6 else 400

    generate_cover(title, subtitle, tagline, output, width, height)
