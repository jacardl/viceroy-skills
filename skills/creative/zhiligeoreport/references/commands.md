# 命令清单

## 端到端

```bash
# 一行命令：render + inline + split + push
uv run python3 -m geo_report.cli publish-weekly \
  --parts 3 --per-section-cap 12 --cover /tmp/zhili_cover.jpg

# 只渲染不推（--skip-push）
uv run python3 -m geo_report.cli publish-weekly \
  --parts 3 --per-section-cap 12 --skip-push
```

## 分步

```bash
cd /Users/apple/Downloads/User/geo-report

# Step 1: 抓信源
uv run python3 -m geo_report.cli fetch-all

# Step 2: 渲染 HTML（带 4 项验证门禁）
uv run python3 scripts/13_render_only.py

# Step 3: inline 化（WeChat 兼容）
uv run python3 scripts/16_inline_css.py data/reports/liusheng_geo_<DATE>.html

# Step 4: 按字节拆篇（≤64KB/篇）
uv run python3 scripts/15_split_zhili.py \
  data/reports/liusheng_geo_<DATE>_inline.html \
  --parts 3 --per-section-cap 12

# Step 5: 推草稿箱（3 篇）
for f in /tmp/zhili_part{1,2,3}.html; do
  python3 /Users/apple/.hermes/skills/zhiligithub/scripts/push.py \
    --html "$f" --cover /tmp/zhili_cover.jpg \
    --skip-illustration --skip-cover
done
```

## 状态查询

```bash
# 数据库状态
uv run python3 -m geo_report.cli db-status

# 整体健康度
uv run python3 -m geo_report.cli status

# 分析（不渲染）
uv run python3 -m geo_report.cli analyze

# 单次渲染（无抓取）
uv run python3 -m geo_report.cli report-render
```

## 草稿箱管理（操作）

```bash
# 删旧草稿（push.py 的 --delete-first 参数）
python3 /Users/apple/.hermes/skills/zhiligithub/scripts/push.py \
  --html <HTML> --cover <COVER> \
  --delete-first <old_media_id>
```

## 自检（操作）

```python
import re
html = open('data/reports/liusheng_geo_<DATE>_inline.html').read()
chars = sum(1 for c in html if '\u4e00' <= c <= '\u9fff')
assert chars >= 18000, f"中文字 {chars} 太少"
assert not re.search(r'<style', html), "还有 <style> 块"
sections = re.findall(r'class="section-h2"[^>]*>([^<]+)', html)
assert len(sections) == 2, f"板块数 {len(sections)} ≠ 2"
```