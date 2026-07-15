#!/usr/bin/env python3
"""
zhililong · 概念类文章 PIL 配图模板（mmbiz Gate 必备）

为什么需要这个：
  概念类长文（如增广贤文冰鉴等行业研究/金句解读）没有项目截图/视频截图，
  publish_zhili 的 mmbiz Gate 强制要求 HTML 含 mmbiz 字面量。
  PIL 自制概念图是最快方案：纯离线、2 秒出图、≥600px 宽。

用法（3 步，5 分钟出图）：
  1. cp scripts/zhililong_concept_image_template.py /tmp/make_xxx_concept.py
  2. 改 cards 列表（每张卡片 = 4 元组：标签/原句/编号/底色）
  3. python3 /tmp/make_xxx_concept.py → 拿到 .jpg 路径

实战案例（2026-06-18 增广贤文）：
  6 张卡片 = 3 大规律 + 3 句底牌，900×600，~80KB
  配色：深蓝/紫/酒红/橄榄/墨绿/深青，每节一个冷色系
  卡片格式：左侧大编号 + 右侧双行（原句 + 白话解读）
"""
import os
from PIL import Image, ImageDraw, ImageFont

# macOS / Linux 字体候选（按优先级）
FONT_CANDIDATES = [
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
]


def find_font(size, bold=False):
    for p in FONT_CANDIDATES:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


def draw_text_cn(draw, xy, text, size=18, color=(255, 255, 255)):
    font = find_font(size)
    draw.text(xy, text, font=font, fill=color)


def make_concept_image(
    out_path,
    title,
    subtitle,
    cards,           # [(label, sub, num, color), ...]  6 张卡片
    notes,           # [6 个白话解读]
    author="直隶按察使 · 刘生",
    width=900,
    height=600,
):
    """生成 N 卡片概念图（N = len(cards)，自动算布局）"""
    n = len(cards)
    cols = 2 if n <= 6 else 3
    rows = (n + cols - 1) // cols

    img = Image.new("RGB", (width, height), (245, 240, 230))  # 米黄底色
    draw = ImageDraw.Draw(img)

    # 顶部标题条
    draw.rectangle([(0, 0), (width, 70)], fill=(58, 32, 16))
    draw_text_cn(draw, (24, 22), title, 28, (245, 220, 180))
    if subtitle:
        draw_text_cn(draw, (24, 52), subtitle, 14, (210, 195, 165))

    # 卡片布局
    margin = 40
    gap_x, gap_y = 20, 16
    available_w = width - 2 * margin - (cols - 1) * gap_x
    available_h = height - 70 - 32 - margin - (rows - 1) * gap_y  # 减标题条 + 落款
    box_w = available_w // cols
    box_h = available_h // rows

    for i, (label, sub, num, color) in enumerate(cards):
        row, col = divmod(i, cols)
        x = margin + col * (box_w + gap_x)
        y = 90 + row * (box_h + gap_y)
        # 卡片底
        draw.rectangle([(x, y), (x + box_w, y + box_h)], fill=color)
        # 左侧大编号
        draw_text_cn(draw, (x + 18, y + 24), num, 56, (255, 255, 255))
        # 标签
        draw_text_cn(draw, (x + 130, y + 22), label, 22, (255, 240, 200))
        # 副标（原句）
        draw_text_cn(draw, (x + 130, y + 60), sub, 26, (255, 255, 255))
        # 底部白话解读
        if i < len(notes):
            draw_text_cn(draw, (x + 130, y + 102), notes[i], 13, (220, 220, 230))

    # 底部落款
    draw.rectangle([(0, height - 32), (width, height)], fill=(58, 32, 16))
    draw_text_cn(draw, (24, height - 26), author, 14, (210, 195, 165))

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    img.save(out_path, "JPEG", quality=92, optimize=True)
    print(f"✅ 配图已生成: {out_path} ({width}×{height}, {os.path.getsize(out_path):,} bytes)")


# ============ 默认模板：6 卡片 3+3 模式 ============
# 用法：直接 python3 跑这个脚本，会用默认示例出图；
#       实际任务时改 cards/notes 即可。
if __name__ == "__main__":
    cards = [
        ("第一规律", "原句 1",      "01", (40, 75, 110)),
        ("第二规律", "原句 2",      "02", (75, 50, 95)),
        ("第三规律", "原句 3",      "03", (110, 40, 70)),
        ("底牌 1",   "原句 4",      "04", (95, 70, 30)),
        ("底牌 2",   "原句 5",      "05", (60, 90, 60)),
        ("底牌 3",   "原句 6",      "06", (40, 70, 90)),
    ]
    notes = [
        "白话解读 1",
        "白话解读 2",
        "白话解读 3",
        "白话解读 4",
        "白话解读 5",
        "白话解读 6",
    ]
    make_concept_image(
        out_path="/tmp/concept_xxx.jpg",
        title="你的标题",
        subtitle="你的副标题（可选）",
        cards=cards,
        notes=notes,
    )
