---
name: zhili-illustration
description: >
  直隶按察使公众号统一配图技能。供 zhilicomments / zhiligithub / zhililong / zhiligeo
  等写作技能调用，为文章正文生成 IP 角色配图并插入 HTML。
  底层引擎：xiaohu-ip-studio（问号人等 31 个 IP + mmx-cli 后端）。
  触发：写作技能在 HTML 完成之后自动调用本技能，无需用户另行触发。
version: 0.1.0
source: https://github.com/xiaohuailabs/xiaohu-ip-studio
---

# 直隶按察使 · 统一配图技能（zhili-illustration）

> 本技能是 xiaohu-ip-studio 的直隶按察使定制封装，供各写作技能在 HTML 完成后调用。
> **不要单独触发**，由 zhilicomments / zhiligithub / zhililong / zhiligeo 等写作技能在各自流程的第 N 步自动引入。

## 工作流总览

```
写作技能完成 HTML 草稿
    ↓
① 提取 shot list（每节一张配图方案）
    ↓
② 生成图片（调用 xiaohu-ip-studio + mmx-cli）
    ↓
③ 注入 HTML（img 标签插入对应段落）
    ↓
④ 上传微信素材（获取 media_id）
    ↓
写作技能继续：推送草稿箱
```

## 第一步：提取 shot list

读取文章 HTML 或 markdown，按小节粒度列出配图方案：

| 小节 | 内容信号 | 图类型 | 核心意思（灵魂话） | IP 角色 | 比例 |
|------|---------|--------|-----------------|--------|------|
| 开头钩子 | 故事场景 | 情绪锚点图 | 要有共鸣感 | 问号人 | 4:3 |
| XX 段 | 机制解释 | 解释图 | 一看就懂 | 问号人 | 4:3 |
| XX 段 | 数据对比 | 信息图 | 数字说话 | 问号人 | 3:4 |
| ... | ... | ... | ... | ... | ... |

**图类型三轨**：
- **情绪锚点图**：故事开场/有情感张力的段落 → 手绘线稿·淡彩
- **解释图**：机制/流程/对比/关系 → 极简线条风格
- **信息图**：数据/步骤/矩阵 → 纯墨线·无彩 or Notion 风格

**IP 选问号人**（符号成精 meme，极简线条）：适合几乎所有技术/商业文章场景。
如需其他 IP，参考 `~/.hermes/skills/creative/xiaohu-ip-studio/ip-library.html`。

> ⚠️ Shot list 提取完成后，**必须等用户确认 IP 和风格**再生成图片。这是用户的品味节点，不能跳过。

## 第二步：生成图片

**后端：MiniMax mmx-cli**（无需 config.yaml，系统已登录）：

```bash
# 用 xiaohu-ip-studio 的 run_mmx.py
python3 ~/.hermes/skills/creative/xiaohu-ip-studio/scripts/run_mmx.py \
  --prompt-file /tmp/illo_prompt.md \
  --out /tmp/illustrations/
```

**Prompt 文件格式**（`/tmp/illo_prompt.md`）：
```
[Task]
为文章段落生成配图，IP 角色：问号人（极简线条符号人），画风：手绘线稿·淡彩。

[Content]
- 用途：放在文章「XXX」段落之后
- 核心意思：XXXXXXXX（一句话灵魂）
- 必现内容点：XX、XX、XX
- 建议中文标注词：XX、XX

[Visual Requirements]
- 比例：4:3
- 角色占比：小·嵌入（~15%）
- 不要任何文字（标签/标题/注释都不要）
- 纯符号表达，禁止 emoji
```

**生图节奏**：
1. 先只生 **1 张基准图**，确认风格 OK 再批量
2. 批量生成，每张独立 prompt
3. 保存到 `/tmp/illustrations/img_01.png`、`img_02.png`...

## 第三步：注入 HTML

配图插入文章正文对应段落之后：

```html
<!-- img_01 · 开头钩子情绪锚点 -->
<div style="text-align:center;margin:32px 0;">
  <img src="mmbiz://xxx" style="width:100%;max-width:660px;border-radius:8px;" />
</div>
```

> ⚠️ 微信草稿箱 HTML 用 `mmbiz://` 协议引用已上传素材的 media_id。
> 暂用本地路径调试，上传步骤见第四步。

## 第四步：上传微信素材（img 标签转 media_id）

每个配图必须上传微信素材获取 `media_id`，再替换 HTML 中的路径：

```bash
# 上传图片素材（示例）
curl -X POST "https://api.weixin.qq.com/cgi-bin/media/upload?access_token=TOKEN&type=image" \
  -F "media=@/tmp/illustrations/img_01.png"

# 返回 {"media_id":"xxx","url":"mmbiz://..."}
# 将 HTML 中 <img src="..." /> 替换为 <img src="mmbiz://xxx" />
```

上传后返回的 `url` 字段即为 `mmbiz://` 协议的 media_id，直接写入 HTML 即可在公众号预览/发布。

## 微信封面图规范（独立流程）

封面图**不走 xiaohu-ip-studio**，直接用以下规格：

| 参数 | 值 |
|------|-----|
| 尺寸 | 900×383（2.35:1） |
| 格式 | JPG/PNG |
| 文件名 | `/tmp/zhili_cover.png` |
| 上传 type | `image`（不是 `thumb`） |

## 参考文件

| 文件 | 用途 |
|------|-----|
| `~/.hermes/skills/creative/xiaohu-ip-studio/SKILL.md` | 完整配图方法论（shot list / 三轨 / 深层提炼） |
| `~/.hermes/skills/creative/xiaohu-ip-studio/scripts/run_mmx.py` | mmx-cli 后端封装 |
| `~/.hermes/skills/creative/xiaohu-ip-studio/references/geo-sample-prompts.md` | GEO 文章配图 prompt 样本 |
| `references/html-image-injection.md` | HTML img 标签注入规范 |
