---
name: zhililong
related_skills: [zhili-illustration]
description: |
  直隶按察使公众号长文输出技能。基于素材（视频/音频/文字稿）产出 4000-5500 字的中文公众号长文。
  触发：用户说"写一篇公众号长文"/"写一篇 4000-5000 字"、粘贴视频链接+"写长文"、已有 transcript_clean.txt+"扩写"。
  不适用：短评（zhilicomments）、教程（khazix-writer）、GitHub 项目介绍（zhiligithub）。
---

# 直隶按察使 · 长文输出（zhililong）

## 字数判断

| 输入 | 字数 |
|------|------|
| < 30 分钟视频 | 4000-5000 字 |
| 30-60 分钟视频 | 4500-5500 字 |
| 用户指定 | 以用户为准（低于 4000 字建议不写） |

**中文字符计数**：`re.findall(r'[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]', text)` 含 CJK 标点。

> ⚠️ CSS / stop-slop / renwei / pre-submit 清单 → `zhili-shared/references/zhili-style.md`。

---

## 完整工作流（9 步）

```
Step 1：素材接收 + 真实性核对
Step 2：列 5 节骨架（先列骨架再写内容）
Step 3：renwei 改稿（zhili-style.md 第3节）
Step 4：markdown 落稿（必须用 ## 章节语法）
Step 5：HTML 转码（scripts/markdown_to_html.py）
Step 6：renwei 自检全文（zhili-style.md 第4节）
Step 7：配图（zhili-illustration）
Step 8：一键推送草稿（scripts/publish_lanlong.py）
```

---

## Step 1：素材接收 + 真实性核对

必做：
- 读取 `transcript_clean.txt`（或视频链接的转写）
- 校对 ASR 常见错（"冰箭"→"冰鉴"、"向犹新生"→"向死而生"）
- 提取**具体人物名、具体场景、具体数字、具体金句**（带书名号引用）

**反模式**：用"古人说"/"有研究表明"等泛指。**每段至少 1 个可查证的具体素材**。

---

## Step 2：5 节结构骨架

**先列骨架，再写内容**。每节预估字数，控制篇幅：

```
一、[论点 1 — 反常识切入，300-500 字]
二、[论点 2 — 具体方法论 1，800-1000 字]
三、[论点 3 — 具体方法论 2，800-1000 字]
四、[论点 4 — 具体方法论 3，800-1000 字]
五、[论点 5 — 具体方法论 4 或整合，800-1000 字]
[反转段 — 颠覆前面某个认知，300-500 字]
[行动段 — 给读者一个今天就能做的事，200-300 字]
```

**结构硬约束**：
- 论点 1 必须用**反常识切入**（"你以为 X，其实是 Y"，**不要写成"不是 X 而是 Y"句式**）
- 5 个论点必须**层层递进**或**互为补充**，不能并列
- 反转段必须**真的反转**
- 行动段必须**今天就能做**（"今天回家观察一下你爸"而不是"用心观察身边的人"）

---

## Step 3：renwei 改稿

> ⚠️ renwei 是 zhililong 写出"佳哥体"的**唯一通道**。没有内化就下笔，5000 字长文一定掉进 AI 套话陷阱。

**三原则**（写每段前自问）：
1. **位置**：开头 3 句话能不能让读者看出"作者在什么场景下说话"？
2. **代价**：每段至少 1 个具体数字 / 1 个具体场景 / 1 个身体感觉？
3. **手迹**：句尾"呢""吧""了"保留了吗？

完整套话清单（11 项，≥3 项命中 → 打回重写）→ `zhili-shared/references/zhili-style.md` 第 3 节。

---

## Step 4：markdown 落稿

### ⚠️ 章节标记必须用 `##` 语法

✅ 正确：`## 一`、`## 二`、`## 三`、`## 反转`、`## 行动`
❌ 错误：文章正文中写 `一`、`二`、`三` 作为纯文本

**原因**：`markdown_to_html.py` 将 `## xxx` 转换为 `<h2>`，纯文本 `一` 会被转换为 `<p>`，导致 `publish_lanlong.py` 的 `extract_shot_list()` 返回 0 shots，配图注入失败。

### markdown 规范

- 标题：`# [标题]`
- 章节：`## [论点]`
- 引用：`> [原话]`
- 强调：**仅关键词**，每节最多 1 处
- 底部：参考资料 + 不涉玄学声明（如题材是玄学/命理类）

### 双文件模式（必须）

> ⚠️ `markdown_to_html.py` 会把所有 `##` 都当 H2 处理——包括大纲和参考资料。

拆分两份 markdown：
- `公众号-[标题]-body.md`：仅含 7 节正文（**转 HTML 用**）
- `公众号-[标题].md`：`body.md` + 头部元信息 + 大纲 + 尾部参考资料（**用户审稿用**）

```python
import re
md = open(full_md, encoding="utf-8").read()
body = re.sub(r"## 大纲\n[\s\S]*?(?=## 一、)", "", md)  # 删大纲
body = re.sub(r"\n## 参考资料[\s\S]*$", "", body)           # 删参考资料
open(body_md, "w", encoding="utf-8").write(body)
```

只对 body 跑转码：`python3 scripts/markdown_to_html.py body.md out.html`

---

## Step 5：HTML 转码

**转换规则**：

| markdown | HTML |
|----------|------|
| `# 标题` | （不写入 HTML，标题传给 draft/add 的 title 字段） |
| `## 章节` | `<h2 style="...">`（样式A H2 规范，见 zhili-style.md） |
| `**重点**` | `<strong style="color:#e63946;">重点</strong>` |
| `> 引用` | `<blockquote style="...">` |
| 普通段落 | `<p style="margin:0 0 16px 0;line-height:1.6;">` |

**HTML 拼接规范**：
```python
blocks = [
    '<p style="...">第一段</p>',
    '<p style="...">第二段</p>',
]
html_content = ''.join(blocks)  # 零分隔符
```

**验证**：
```bash
grep -c '^$' /tmp/article.html   # 应为 0
grep -n '\*\*' /tmp/article.html  # 应为空
```

---

## Step 6：renwei 自检全文

> ⚠️ 从零写 5000 字 vs 用户给原文让 AI 改：前者清单**扫全文**，后者只扫动过的句子。

必跑：`python3 scripts/post_edit_check.py /tmp/article-body.md`

检查项（详见 `references/post-edit-checklist.md`）：
- [ ] 「不是 X 而是 Y」：0 处
- [ ] 排比三连：0 处
- [ ] 破折号 `——`：0 处
- [ ] AI 套话：0 处
- [ ] 字数：4000-5500

**命中率 ≥ 3 → 先打回重写，不要一边改一边扫**。

---

## Step 7：配图

封面图（zhili-illustration）：
- 尺寸 900×540（微信编辑器推荐）
- 走 `zhililong/scripts/cover_pil.py` 或 xiaohu-ip-studio 生成底图

正文配图（zhili-illustration）：
- 读取 HTML，按 `## H2` 章节提取 shot list（最多 5 张）
- 调用 `xiaohu-ip-studio` + `mmx-cli` 生成图片
- 按 `zhili-illustration/references/html-image-injection.md` 规范注入 HTML

---

## Step 8：一键推送草稿

```bash
python3 scripts/publish_lanlong.py \
  --title "文章标题" \
  --author "刘生" \
  --digest "文章摘要（≤54字节）" \
  --html /tmp/article.html \
  --cover /tmp/cover.png

# 快速重推
python3 scripts/publish_lanlong.py ... --skip-illustration --skip-cover

# 重推（先删旧草稿）
python3 scripts/publish_lanlong.py ... --delete-first <old_draft_id>
```

**全流程 5 步**：配图生成 → 配图上传 mmbiz → 注入 HTML → 封面上传 → 创建草稿

### ⚠️ WeChat API 关键教训

| 症状 | 根因 | 解决 |
|------|------|------|
| `errcode 40007` + `invalid media_id` | `thumb_media_id` 来自 `media/upload`（临时素材） | 改用 `material/add_material?type=image` |
| 草稿图片显示 400 | mmbiz URL 截断，缺 `?from=appmsg` 后缀 | 用完整 mmbiz URL（157-163字符） |
| `errcode 40007` + `media_id missing` | `ensure_ascii=True` 导致中文被 `\uXXXX` 转义 | `json.dumps(payload, ensure_ascii=False).encode("utf-8")` |

---

## Step 9：交付格式

每次产出必须给：

```markdown
# [文章标题]

**字数**：[N] 中文字符（含标点 [M]）
**结构**：[5 节 + 1 反转 + 1 行动]
**自检**：✅ [通过项]

## 大纲
1. ...

**markdown 路径**：`/path/to/公众号-[标题].md`
**HTML 路径**：`/tmp/[标题].html`
**草稿 media_id**：（仅当 Step 8 执行后出现）
```

---

## 凭证配置

凭证在 `references/config.md`，不输出到对话。

## 已知限制

| 功能 | 状态 | 解决 |
|------|------|------|
| execute_code sandbox 破坏含中文 URL 的 HTML | sandbox 替换含敏感词的整行字符串 | 用 terminal Python 而非 execute_code |
| `publish_lanlong.py` 内置所有 WeChat API 细节 | — | 优先用脚本，不要手搓 inline Python |
