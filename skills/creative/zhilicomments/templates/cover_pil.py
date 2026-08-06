#!/usr/bin/env python3
"""
zhilicomments · 封面图生成模板

用法：复制本文件 → 改顶部 4 个常量 → python3 cover.py
产物：/tmp/zhili_cover.png（push.py 默认读取路径）

目标尺寸：900×383 px（push.py 从 16:9 底图裁剪至此比例）
风格：深墨蓝底 + 青色装饰条 + 白色大标题 + 红棕色副标题 + 黄底引言
"""
from PIL import Image, ImageDraw, ImageFont
import os

# ============ 必改 4 项 ============
TITLE_LINE_1 = "几小时"          # 主标题第 1 行（白色大字）
TITLE_LINE_2 = "攻破 NSA"        # 副标题（红棕色）
QUOTE_LINE_1 = "NSA 局长亲口说"  # 引言第 1 行
QUOTE_LINE_2 = "AI 几小时内攻破几乎所有机密系统"  # 引言第 2 行（黄底高亮感）
TAG = "直隶按察使 · 短评"        # 顶部小标
SIG = "刘生  /  2026.06.22"     # 底部署名

# ============ 视觉常量（按需调）============
W, H = 900, 383
BG = '#1B365D'           # 深墨蓝底
ACCENT = '#00d4aa'       # 青色装饰条
TEXT_MAIN = '#f5f4ed'    # 浅米白
TEXT_RED = '#c9553d'     # 红棕色
TEXT_YELLOW = '#fff3b0'  # 黄底高亮
TEXT_MUTED = '#7c6f64'   # 弱化署名色
OUT = '/tmp/zhili_cover.png'

# ============ 字体（系统优先 wqy，否则降级）============
FONT_PATHS = [
    '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
    '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc',
    '/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc',
    '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
]
FONT_PATH = next((p for p in FONT_PATHS if os.path.exists(p)), None)

def font(size):
    return ImageFont.truetype(FONT_PATH, size) if FONT_PATH else ImageFont.load_default()

# ============ 绘制 ============
img = Image.new('RGB', (W, H), color=BG)
draw = ImageDraw.Draw(img)

# 顶部 tag
draw.text((50, 50), TAG, fill=ACCENT, font=font(22))
# 装饰条
draw.rectangle([(50, 90), (130, 96)], fill=ACCENT)

# 主标题（第 1 行）
draw.text((50, 130), TITLE_LINE_1, fill=TEXT_MAIN, font=font(96))
# 副标题（第 2 行）
draw.text((50, 240), TITLE_LINE_2, fill=TEXT_RED, font=font(96))

# 引言
draw.text((50, 360), QUOTE_LINE_1, fill=TEXT_MAIN, font=font(28))
draw.text((50, 395), QUOTE_LINE_2, fill=TEXT_YELLOW, font=font(28))

# 署名
draw.text((50, 450), SIG, fill=TEXT_MUTED, font=font(20))

img.save(OUT, 'PNG', optimize=True)
print(f'✓ 封面已生成: {OUT}  ({W}x{H}, {os.path.getsize(OUT)/1024:.1f} KB)')
