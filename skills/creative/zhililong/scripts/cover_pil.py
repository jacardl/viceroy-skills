#!/usr/bin/env python3
"""
zhililong · PIL 封面图自动生成器

不依赖 AI 图像生成 API（避免 mmx/sensenova 不稳定），用 PIL 在 2 秒内
画一张 900×540 的公众号封面图（微信编辑器推荐尺寸）。

用法:
  python3 cover_pil.py --title "20 亿美元买了一个寂寞" --output /tmp/cover.jpg
  python3 cover_pil.py --title "Manus 拆伙" --output /tmp/cover.jpg --subtitle "中美 AI 资本博弈"

设计:
- 背景：左→右 深蓝 → 暗紫 渐变（与「直隶按察使」色调统一）
- 主标题：白色 60px 粗体，居中
- 副标题（可选）：半透明白 28px
- 角标：「直隶按察使」左上角
- 装饰：右下角斜向 30% 透明几何块

回退:
- 标题过长 → 自动等比缩字号
- 缺中文字体 → 走 DejaVuSans（提示用户安装思源宋体/Noto Serif CJK）
"""
import argparse
import os
import sys

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("ERROR: 缺少 Pillow。安装: pip install Pillow", file=sys.stderr)
    sys.exit(1)


# 中文字体候选路径（macOS / Linux / 常见安装位置，按优先级）
FONT_CANDIDATES = [
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/STHeiti Light.ttc",
    "/Library/Fonts/Songti.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/usr/share/fonts/truetype/arphic/uming.ttc",
    "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc",
]


def find_chinese_font(size: int):
    """找到第一个可用的中文字体。无则回退到默认"""
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    # 回退：DejaVuSans（不支持中文但不会崩，图片仍能生成）
    return ImageFont.truetype("/System/Library/Fonts/Supplemental/DejaVuSans-Bold.ttf", size) \
        if os.path.exists("/System/Library/Fonts/Supplemental/DejaVuSans-Bold.ttf") \
        else ImageFont.load_default()


def draw_gradient_bg(img: Image.Image, color_a=(20, 30, 70), color_b=(60, 20, 80)):
    """横向线性渐变：左 color_a → 右 color_b"""
    draw = ImageDraw.Draw(img)
    w, h = img.size
    for x in range(w):
        ratio = x / max(w - 1, 1)
        r = int(color_a[0] + (color_b[0] - color_a[0]) * ratio)
        g = int(color_a[1] + (color_b[1] - color_a[1]) * ratio)
        b = int(color_a[2] + (color_b[2] - color_a[2]) * ratio)
        draw.line([(x, 0), (x, h)], fill=(r, g, b))


def draw_corner_badge(img: Image.Image, text="直隶按察使", pos=(40, 30), size=28, color=(255, 255, 255, 220)):
    """左上角白色品牌标"""
    draw = ImageDraw.Draw(img)
    font = find_chinese_font(size)
    draw.text(pos, text, font=font, fill=color)


def draw_title(img: Image.Image, title: str, subtitle: str = ""):
    """主标题（自动调字号）"""
    draw = ImageDraw.Draw(img)
    w, h = img.size
    # 字号根据标题长度动态调整
    char_count = len(title)
    if char_count <= 8:
        font_size = 78
    elif char_count <= 12:
        font_size = 64
    elif char_count <= 16:
        font_size = 52
    else:
        font_size = 44
    font = find_chinese_font(font_size)
    # 居中
    bbox = draw.textbbox((0, 0), title, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = (w - tw) // 2
    ty = (h - th) // 2 - (40 if subtitle else 0)
    # 阴影
    draw.text((tx + 3, ty + 3), title, font=font, fill=(0, 0, 0, 100))
    draw.text((tx, ty), title, font=font, fill=(255, 255, 255, 255))

    if subtitle:
        sub_font = find_chinese_font(28)
        sbbox = draw.textbbox((0, 0), subtitle, font=sub_font)
        stw, sth = sbbox[2] - sbbox[0], sbbox[3] - sbbox[1]
        sx = (w - stw) // 2
        sy = ty + th + 30
        draw.text((sx, sy), subtitle, font=sub_font, fill=(255, 255, 255, 200))


def draw_decoration(img: Image.Image):
    """右下角几何装饰"""
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    w, h = img.size
    # 半透明斜向条纹
    for i in range(8):
        x0 = w - 200 + i * 30
        odraw.polygon(
            [(x0, h), (x0 + 80, h), (x0 + 30, h - 100)],
            fill=(255, 255, 255, 30),
        )
    img.paste(overlay, (0, 0), overlay)


def main():
    parser = argparse.ArgumentParser(description="zhililong 封面图生成器（PIL，无 AI 依赖）")
    parser.add_argument("--title", required=True, help="文章标题（≤16 字最佳）")
    parser.add_argument("--subtitle", default="", help="副标题（可选）")
    parser.add_argument("--output", required=True, help="输出图片路径（建议 .jpg）")
    parser.add_argument("--width", type=int, default=900, help="宽度（默认 900）")
    parser.add_argument("--height", type=int, default=540, help="高度（默认 540）")
    args = parser.parse_args()

    img = Image.new("RGB", (args.width, args.height), (20, 30, 70))
    draw_gradient_bg(img)
    draw_decoration(img)
    draw_corner_badge(img)
    draw_title(img, args.title, args.subtitle)

    # 输出（确保父目录）
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    if args.output.lower().endswith(".png"):
        img.save(args.output, "PNG", optimize=True)
    else:
        img.save(args.output, "JPEG", quality=92, optimize=True)

    size = os.path.getsize(args.output)
    print(f"✅ 封面图已生成: {args.output} ({args.width}×{args.height}, {size:,} bytes)")


if __name__ == "__main__":
    main()
