---
name: zhilicomments
description: >
  微信公众号短评论发布技能，专为「独立小扎喝不醉每天都在天上飞」公众号定制。
  适用：一事一议的短观点、热评reaction、资讯点评（2000-3000字，1-2张图）。
  触发条件：用户说「评论」「热评」「观点」「点评」「说两句」。
---

# 独立小扎 · 短评论发布技能

## 与 zhili-publish 的区别

| | zhili-publish | zhilicomments |
|--|---------------|---------------|
| 字数 | 1500-2500字 | 2000-3000字 |
| 结构 | Evolver 六段式 | 轻量三段式 |
| 配图 | 项目截图+封面 | 1-2张评论配图 |
| 用途 | 项目介绍/教程 | 热评/观点/Reaction |

## 内容格式（轻量三段式）

### 写作引擎：khazix-writer

> ⚠️ 短评论内容由 **khazix-writer** skill 生成，调用方式：
> 1. `skill_view(name='khazix-writer')` 加载完整写作指南
> 2. 按照 khazix-writer 的【第四步：四层自检体系】执行写作和质检
> 3. 文章类型：现象解读型为主（观察现象 → 层层分析 → 文化升维）
> 4. 字数必须达到 2000-3000 字
> 5. 开头必须从具体事件切入，禁止宏大叙事
> 6. 结尾不求 Star/转发，纯观点金句收
卡兹克短评论的核心特征：
- 2000-3000字左右（长文是 2000-4000字，短评也是这个区间但更精炼）
- 一句话断裂成段制造节奏感
- 观点鲜明，有立场不做理中客
- 结尾用反问或金句收，不求 Star/转发

### 一、事件/现象（300-400字）
从具体事件切入，2-3句背景交代，让读者知道发生了什么。开头要有画面感，能让读者立刻进入场景。

### 二、核心观点（1500-2000字）
- 一句话亮出核心观点（加粗）
- 2-3个支撑点，每个点用具体数据/案例支撑
- 允许一个段落长达200-300字，不要怕写长段落
- 每段要有扣主线句，保持阅读节奏
- 结尾文化升维：从具体事件连接到更大的文化/哲学/历史参照物

### 三、金句收尾（50字以内）
用反问或金句收尾，不需要号召行动，纯观点落笔。

## HTML 格式规范（强制标准）

发布任何短评时，必须遵守以下 CSS 规格：

| 属性 | 值 |
|------|-----|
| 行高 | `1.8` |
| 两侧间距 | `0 12px` |
| 大标题 h2 | `font-size:20px;font-weight:bold;color:#1a1a2e` |
| 正文字号 | `font-size:17px` |
| 对齐方式 | **`text-align:left`（所有元素）** |
| 关键词高亮 | `<strong style="color:#e63946;">` |
| 引用块 | `border-left:4px solid #e63946;padding:12px 16px;background:#f8f8f8;margin:16px 0` |
| 分隔线 | `<hr style="border:none;border-top:1px solid #eee;margin:24px 0">` |
| 容器 | `max-width:678px;margin:0 auto;padding:0 12px;font-size:17px;line-height:1.8;color:#333;text-align:left;` |

### 丰富 CSS 渲染示例

```html
<!-- 核心容器 -->
<div style="max-width:678px;margin:0 auto;padding:0 12px;font-size:17px;line-height:1.8;color:#333;text-align:left;">

  <!-- 章节标题 -->
  <h2 style="font-size:20px;font-weight:bold;color:#1a1a2e;margin:32px 0 16px 0;text-align:left;border-left:4px solid #e63946;padding-left:12px;">一、事件</h2>

  <!-- 段落 -->
  <p style="margin:0 0 20px 0;text-align:left;">正文内容...</p>

  <!-- 引用块 -->
  <p style="border-left:4px solid #e63946;padding:12px 16px;background:#f8f8f8;margin:20px 0;font-style:normal;color:#555;text-align:left;">「引用内容」</p>

  <!-- 关键词加粗高亮 -->
  <p style="margin:0 0 20px 0;text-align:left;"><strong style="color:#e63946;">核心观点：</strong>展开描述...</p>

  <!-- 分隔线 -->
  <hr style="border:none;border-top:1px solid #eee;margin:28px 0;">

  <!-- 一句话金句 -->
  <p style="margin:0 0 16px 0;font-size:18px;font-weight:bold;text-align:left;color:#1a1a2e;">金句收尾。</p>
</div>
```

> ⚠️ **所有 block 元素（p/h2/hr）必须单独一行，不能有换行符分隔**
> ⚠️ 禁用词（严禁出现）：`说白了`、`意味着什么`、`本质上`、`双引号`、`冒号`、`破折号`

### 标题要求
- 字数 ≥10字
- 卡兹克风格：观点鲜明，有情绪张力

## 发布流程

```
获取内容 → 生成/下载配图 → 上传封面 → 写HTML → 创建草稿 → 完成
```

### 第一步：获取内容
用户提供：
- 评论对象（链接/标题/截图）
- 核心观点（一句话）
- 支撑素材（可选）

### 第二步：配图（可选）
短评论可以无图，但如果配图：
1. 用 PIL 生成信息图（900×383 或 900×900）：`/tmp/cover.jpg`
2. 上传获取 `media_id`：

```bash
# 必须用 type=thumb，返回的 media_id 才能用于 draft/add
curl -F "media=@/tmp/cover.jpg" \
  "https://api.weixin.qq.com/cgi-bin/material/add_material?access_token=${TOKEN}&type=thumb"
```

返回字段中的 `media_id` 即为 `thumb_media_id`。

> ⚠️ **不能用 `type=image`**：用 `type=image` 上传返回的 media_id 在 `draft/add` 时会报 `40007 invalid media_id`。必须 `type=thumb`。
返回字段中的 `media_id` 即为 `thumb_media_id`。

> ⚠️ **不能用 `type=image`**：用 `type=image` 上传返回的 media_id 在 `draft/add` 时会报 `40007 invalid media_id`。必须 `type=thumb`。

### 第三步：写 HTML

> ⚠️ 全文禁止使用 `ul`/`li` 列表结构。改为用 `•` 符号替代，每个要点独立 `<p>` 段落。
> ⚠️ 所有 block 元素（p/h2/hr）必须单独一行，不能有换行符分隔。

```html
<div style="max-width:678px;margin:0 auto;padding:0 12px;font-size:17px;line-height:1.8;color:#333;text-align:left;">
  <h2 style="font-size:20px;font-weight:bold;color:#1a1a2e;margin:32px 0 16px 0;text-align:left;border-left:4px solid #e63946;padding-left:12px;">一、事件</h2>
  <p style="margin:0 0 20px 0;text-align:left;">描述内容...</p>
  <h2 style="font-size:20px;font-weight:bold;color:#1a1a2e;margin:32px 0 16px 0;text-align:left;border-left:4px solid #e63946;padding-left:12px;">二、观点</h2>
  <p style="margin:0 0 20px 0;text-align:left;"><strong style="color:#e63946;">核心观点。</strong>展开描述...</p>
  <p style="border-left:4px solid #e63946;padding:12px 16px;background:#f8f8f8;margin:20px 0;font-style:normal;color:#555;text-align:left;">引用块内容...</p>
  <hr style="border:none;border-top:1px solid #eee;margin:28px 0;">
  <p style="margin:0 0 16px 0;font-size:18px;font-weight:bold;text-align:left;color:#1a1a2e;">金句收尾。</p>
</div>
```

### 第四步：创建草稿

调用微信 API：
```bash
# 获取 access_token
curl "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=${APPID}&secret=${APPSECRET}"

# 上传封面（type=thumb）
curl -F "media=@/tmp/cover.jpg" "https://api.weixin.qq.com/cgi-bin/material/add_material?access_token=${TOKEN}&type=thumb"

# 创建草稿
curl -X POST "https://api.weixin.qq.com/cgi-bin/draft/add?access_token=${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "articles": [{
      "title": "标题",
      "author": "刘生",
      "digest": "摘要",
      "content": "<div>...</div>",
      "thumb_media_id": "media_id",
      "need_open_comment": 1,
      "only_fans_can_comment": 0
    }]
  }'
```

## 凭证配置

从 `references/config.md` 读取：APPID、APPSECRET、CATEGORY_ID。
从 `references/publish_guide.md` 读取完整发布流程和常见错误排查。

## 封面图规格

- 尺寸：900×383（信息图比例）或 900×900（方图）
- 风格：深色背景 + 高对比文字，观点鲜明
- 可用 PIL 纯代码生成

## 注意事项

- 标题 ≥10字，卡兹克风格
- 正文配图可选
- 观点要有立场，不做理中客
- 结尾不求 Star/项目地址，纯观点文
- **禁用词（严禁出现）**：`说白了`、`意味着什么`、`本质上`、`双引号`、`冒号`、`破折号`
- 所有文字 **`text-align:left`**，无例外
