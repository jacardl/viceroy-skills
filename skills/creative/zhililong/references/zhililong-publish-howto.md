# zhililong 发布到草稿箱的实战步骤（2026-07-08 更新）

> ⚠️ **2026-07-08 重大更正**：`publish_lanlong.py` 是 zhililong 的**唯一**发布入口。
> ~~`publish_pipeline.py`~~ 已废弃，**不要**混用两套脚本。

## 发布入口：`publish_lanlong.py`（自包含）

路径：`~/.hermes/skills/creative/zhililong/scripts/publish_lanlong.py`

**全流程 5 步**：
1. zhili-illustration 提取 shot list（每个 H2 → 一张配图）→ 调用 mmx-cli 生成
2. 配图上传 mmbiz（`media/uploadimg`，返回 CDN URL）→ 注入 HTML
3. 封面生成（zhili-illustration，16:9 → 900×383）
4. 封面上传（`material/add_material?type=image`）→ 创建草稿
5. 回写 upload_results.json

## 正确工作流

### 方式 A：脚本全流程处理（推荐）

```bash
python3 ~/.hermes/skills/creative/zhililong/scripts/publish_lanlong.py \
  --title "文章标题" \
  --author "刘生" \
  --digest "摘要（≤54字节）" \
  --html /tmp/article.html
```

### 方式 B：预生成配图 + 手动注入 CDN

当需要精细控制配图 prompt 时：

```bash
# Step 1：手动生成配图
python3 ~/.hermes/skills/creative/xiaohu-ip-studio/scripts/run_mmx.py \
  --prompt-file /tmp/illo_01.md --out /tmp/img_01.png

# Step 2：上传到微信素材（必须用 media/uploadimg，返回 CDN URL）
TOKEN=$(curl -s "https://api.weixin.qq.com/cgi-bin/stable_token" \
  -X POST -H "Content-Type: application/json" \
  -d "{\"grant_type\":\"client_credential\",\"appid\":\"wx38a91c353554588a\",\"secret\":$(cat ~/.hermes/keys/wx_appsecret.txt)}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl -X POST "https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token=$TOKEN" \
  -F "media=@/tmp/img_01.png"
# 返回 {"url": "http://mmbiz.qpic.cn/..."}  ← CDN URL，必须用这个

# Step 3：把 CDN URL 注入 HTML（H2 之后的 </p> 处）
# <div style="text-align:center;margin:32px 0;"><img src="http://mmbiz.qpic.cn/..." /></div>

# Step 4：调用脚本（不要加 --skip-illustration！）
python3 ~/.hermes/skills/creative/zhililong/scripts/publish_lanlong.py \
  --title "..." --author "刘生" --digest "..." \
  --html /tmp/article_with_cdn_imgs.html
```

## --skip-illustration 正确用法

`--skip-illustration` 的语义是"**整篇文章不需要任何配图**"，不是"跳过配图生成步骤"。

| 场景 | --skip-illustration |
|------|------|
| 文章确实没有配图 | ✅ 加 |
| 有配图但想手动生成 | ❌ 不加 |
| 有配图且已预注入 CDN URL | ❌ 不加（脚本会保留 `mmbiz.qpic.cn` URL） |

**踩坑（2026-07-08）**：预注入 CDN img 后加 `--skip-illustration` → `inject_into_html` 读原始 HTML（无 img）→ 预注入内容丢失。

## WeChat 草稿箱图片格式

| 接口 | 返回格式 | 草稿箱能否渲染 |
|------|---------|--------------|
| `media/uploadimg` | `url`: `http://mmbiz.qpic.cn/...` | ✅ 可以 |
| `media/upload` | `media_id`: `mmbiz://xxxx` | ❌ 不识别 |

## 失败速查

| 症状 | 根因 | 修复 |
|------|------|------|
| 草稿箱看不到配图 | `mmbiz://media_id` 格式 | 必须用 `media/uploadimg` |
| 预注入配图丢失 | 加了 `--skip-illustration` | 不加该 flag |
| Token 41004 | sandbox 替换 APPSECRET | 脚本内部读 `wx_appsecret.txt` |
| 44003 empty news data | payload 缺数组包裹 | 已修复 |
| 45003 author out of limit | 作者名超 2 中文字 | 固定传"刘生" |

## 沉淀记录

- **2026-06-20**：第一次走通，publish_pipeline.py 方案（已废弃）
- **2026-07-08**：切换到 `publish_lanlong.py`；草稿箱不显示配图根因：`media/upload` media_id 格式 vs `media/uploadimg` CDN URL；预注入配图丢失根因：`--skip-illustration`
