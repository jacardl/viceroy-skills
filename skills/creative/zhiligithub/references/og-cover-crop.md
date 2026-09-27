# OG 图封面裁剪配方（2026-08-19 实测）

从 GitHub 下载 OG 图后，需要裁剪为 900×383（2.35:1）才能用作微信封面。

## 标准裁剪代码

```python
from PIL import Image

og_path = '/tmp/og.jpg'
out_path = '/tmp/cover_crop.jpg'
target_w, target_h = 900, 383

img = Image.open(og_path)
w, h = img.size
ratio = target_w / target_h
current_ratio = w / h

if current_ratio > ratio:
    new_w = int(h * ratio)
    left = (w - new_w) // 2
    img_crop = img.crop((left, 0, left + new_w, h))
else:
    new_h = int(w / ratio)
    top = (h - new_h) // 2
    img_crop = img.crop((0, top, w, top + new_h))

img_crop = img_crop.resize((target_w, target_h), Image.LANCZOS)
img_crop.save(out_path, quality=95)
```

## 验证步骤

```bash
# 下载 OG 图
curl -sL "https://opengraph.githubassets.com/1/{owner}/{repo}" -o /tmp/og.jpg

# 验证是真实图片（不是 HTML 重定向）
file /tmp/og.jpg          # 必须是 PNG/JPEG/GIF，不是 HTML
wc -c < /tmp/og.jpg      # 真实图片通常 > 10KB

# 裁剪后验证
python3 -c "from PIL import Image; img=Image.open('/tmp/cover_crop.jpg'); print(img.size)"
# 必须输出 (900, 383)
```

## 注意

- `cover_pil.py` 从零生成样式化封面（深蓝背景+白字），不是裁剪 OG 图
- 微信封面要求 2.35:1 比例，900×383 是标准尺寸
- push.py 会自动调用 zhili-illustration 生成封面图；传 `--cover` 时使用传入的封面文件
