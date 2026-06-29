---
name: zhili-illustration
description: >
  为「直隶按察使」公众号长文统一配图。读取 HTML → 提取 shot list → mmx image generate 生图 → 上传微信素材 → 注入 HTML。
  触发条件：用户说「配图」「生成插图」「zhili-illustration」「给文章配图」。
triggers:
  - 配图
  - 生成插图
  - zhili-illustration
  - 给文章配图
  - 文章插图
---

# zhili-illustration · 直隶按察使公众号配图技能

## 核心链路

```
HTML → 提取 shot list → mmx image generate ×N
                                  ↓
                              下载图片
                                  ↓
                          微信素材上传 → mmbiz URL
                                  ↓
                          注入 HTML → HTML-FINAL
```

## 步骤详解

### Step 1 · 提取 Shot List

从 HTML 读取所有 H2 章节，每个 H2 对应一张配图。

```python
from bs4 import BeautifulSoup

def extract_shots(html_path):
    with open(html_path, encoding='utf-8') as f:
        html = f.read()
    soup = BeautifulSoup(html, 'html.parser')
    shots = []
    for h2 in soup.find_all('h2'):
        title = h2.get_text(strip=True)
        if title:
            shots.append(title)
    return shots
```

**Shot 即章节标题**，不需要另外写 prompt。mmx 会根据标题语义生成契合图片。

### Step 2 · 生成图片（mmx image generate）

每张图用 `mmx image generate`，比例 `16:9`，输出到统一目录。

```bash
# 单张
mmx image generate \
  --prompt "Open source autonomous driving dashboard, futuristic HUD, self-driving car interface, dark blue theme" \
  --aspect-ratio 16:9 \
  --out-dir /tmp/zhili-illustration/ \
  --out-prefix "shot-01" \
  --quiet

# 并发生图（可用 & / xargs -P）
for i in "${!shots[@]}"; do
  n=$((i+1))
  mmx image generate \
    --prompt "Caption for: ${shots[$i]}" \
    --aspect-ratio 16:9 \
    --out-dir /tmp/zhili-illustration/ \
    --out-prefix "shot-$(printf '%02d' $n)" \
    --quiet \
    &
done
wait
```

**Prompt 优化策略**：
- 科技/AI 类 → `futuristic, dark theme, neon accents`
- 开源/协作 → `open source, community, code interface`
- 人物/传记 → `clean editorial, portrait style`
- 产品/工具 → `minimalist product shot, clean background`
- 自动适配 HTML 内容关键词

### Step 3 · 上传微信素材

用 `publish_zhili.py` 内部函数，避免硬编码凭证。

```python
import sys, os
sys.path.insert(0, os.path.expanduser(
    "~/.hermes/skills/social-media/.agents/skills/zhili-publish/scripts/"
))
from publish_zhili import load_config, get_access_token, upload_article_image

def upload_to_mmbiz(image_path):
    config = load_config()
    token = get_access_token(config["APPID"], config["APPSECRET"])
    return upload_article_image(token, image_path)

mmbiz_urls = {}
for i, shot in enumerate(shots, 1):
    local = f"/tmp/zhili-illustration/shot-{i:02d}.png"
    url = upload_to_mmbiz(local)
    mmbiz_urls[i] = url
```

### Step 4 · 注入 HTML

统计 HTML 中「图片」占位符数量，逐一替换为 mmbiz URL。

```python
def inject_mmbiz(html, mmbiz_urls):
    for i, url in mmbiz_urls.items():
        placeholder = f'<img src="图片{i}">'
        replacement = f'<img src="{url}">'
        html = html.replace(placeholder, replacement, 1)
    return html

with open("article-final.html", "w", encoding="utf-8") as f:
    f.write(final_html)
```

## 输出文件

- `/tmp/zhili-illustration/shot-01.png` … `shot-NN.png` — 配图原图
- `{html_同目录}/xxx-final.html` — 已注入 mmbiz URL 的发布用 HTML

## 凭证说明

凭证由 `zhili-publish/scripts/publish_zhili.py` 的 `load_config()` 管理，
无需传入 APPID/APPSECRET。技能内部通过 `sys.path.insert` 复用。

## 封面图（单独处理）

封面图不走本技能。用 `zhiliGitHub`/`zhililong` 的封面图流程：
`zhiliGitHub/scripts/cover_pil.py`（PIL 渐变）或 `mmx image generate` 生成后
单独用 `material/add_material` 上传。

## 已知限制

- mmx image generate 推理约 30-60s/张，并发过多可能触发 rate limit（MiniMax RPM）
- 微信素材 API 要求图片格式为 jpg/png，大小 ≤ 2MB
- HTML 中占位符必须为 `<img src="图片N">` 格式（N 从 1 开始连续）
