# push.py 封面路径与生成时机

## 已知行为

push.py 的 `--cover` 参数接受自定义路径，但覆盖生成逻辑如下：

1. 如果指定路径的文件存在 → 使用该文件
2. 如果文件不存在 → 内部调用 mmx 生成新封面（需要网络）

因此，如果网络不可用或 mmx 超时，传入 `--cover /tmp/cover.png` 会触发"封面图不存在"警告，然后尝试生成。

## 工作区

如果网络不稳定，在推送前先检查 cover 文件是否存在：

```python
import os
if not os.path.exists('/tmp/cover.png'):
    # 使用 PIL 生成备用封面
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new('RGB', (900, 383), color='#1B365D')
    draw = ImageDraw.Draw(img)
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
    except:
        font_large = ImageFont.load_default()
    draw.text((450 - 200, 150), "标题", fill='white', font=font_large)
    img.save('/tmp/cover.png')
```

## --skip-illustration 行为

`--skip-illustration` 只跳过**内容配图**（img_01, img_02），封面仍由 push.py 生成。不存在"跳过封面"的参数。

如果需要完全控制封面，应先生成 `/tmp/cover.png`（或任意路径），然后 `--cover <该路径>` 传入。
