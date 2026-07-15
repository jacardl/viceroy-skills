# 2026-06-19 accenture-halved-ai-five-layer-cake 实战复盘

## 任务背景

基于上轮 session 已有的 5 节大纲，落地 7 节正文（3168 中文字符），走完整 Step 1-8 推直隶按察使草稿箱。

素材：视频/音频素材缺失，纯文字主题（埃森哲 12 个月 AI 转型 + 市值腰斩 + 黄仁勋五层蛋糕）。
题材分类：**概念类文章**（无视频截图/无项目截图）→ 必走 PIL 自制配图（mmbiz Gate）。

## 本次踩中的 4 个新坑

### 坑 1：read_file / write_file 不一致导致 markdown 行号污染

**症状**：
- `read_file` 读取 `/Users/apple/.../body.md` 时返回的内容看起来正常
- 但当用 `write_file` 写回去后，body.md 头部出现 `"    N|内容"` 的行号格式污染（每行带 `1|`、`2|`、`3|` 前缀）
- 跑 `markdown_to_html.py` 时所有 `## 一、最努力...` H2 都被当作普通段落，没识别
- HTML 输出 H2 数量 = 0，转码彻底失败

**定位**：
- 直接用 `terminal head -5` 看文件，看到 `1|## 一、最努力的那个，反而被市场腰斩了` 这种带行号的脏内容
- `read_file` 内部对内容做了某种换行/行号注入，`write_file` 把脏数据落盘

**修复**：用 `terminal cat > xxx.md << 'EOF' ... EOF` heredoc 写文件，绕开 read_file/write_file 的格式污染。

**避坑信号**：当你 `read_file` 看到内容、然后 `write_file` 落盘，再 `terminal head -5` 看时行首出现 `N|`——立即停止 read_file/write_file 链路，换 heredoc。

**写文件的优先级**（避坑 cheat sheet）：
1. 新文件 / 重写整个文件 → `terminal cat > ... << 'EOF' ... EOF` heredoc（最稳）
2. 小修改 / 已知唯一字符串 → `patch` 工具（精确替换）
3. 大量模式替换（如 24 处 `——` 一次性清零）→ `execute_code` 跑 Python `text.replace()` 批量替换
4. ❌ 避免：read_file 读 → write_file 写（行号污染风险）

### 坑 2：renwei 清单命中 ≥10 处时，patch 工具效率低

**症状**：
- 自检发现 24 处 `——` 全角破折号 + 1 处 "不是 X 而是 Y" + 3 处段落级加粗（共 28 处违规）
- 用 `patch` 工具一个一个改太慢（每次要构造 unique context string）

**修复**：跑 `execute_code`，读全文 → `text.replace()` 批量替换 → `write_file`。一次性解决：
- 24 处 `——` → 句号/逗号/括号（按上下文判断）
- 段落级加粗（`**XXX。YYY。ZZZ。**` 这种）→ 拆成"关键词加粗 + 普通段落"
- "不是X而是Y" → 重写句子（保留观点，去除句式）

**避坑经验**：renwei 套话清单命中 >5 处时，**直接走 Python 批量替换**，不要尝试 patch 单条。

### 坑 3：PIL 概念图硬编码字体路径失败

**症状**：
- 写 `/tmp/make_five_layers.py` 时硬编码 `FONT_BIG = "/System/Library/Fonts/PingFang.ttc"`
- `python3 make_five_layers.py` 抛 `OSError: cannot open resource`，字体加载失败

**根因**：
- macOS 上 `PingFang.ttc` 是系统字体但需要 ttc 索引参数，PIL `truetype()` 默认不开索引可能找不到
- `cover_pil.py` 内置的 `find_chinese_font()` 走 FONT_CANDIDATES 列表，按优先级找到 `STHeiti Medium.ttc`，可直接用

**修复**：自定义 PIL 配图脚本时，**复用 cover_pil.py 的字体加载逻辑**：
```python
import sys
sys.path.insert(0, '/Users/apple/.hermes/skills/zhililong/scripts')
from cover_pil import find_chinese_font
font_30 = find_chinese_font(30)
font_36 = find_chinese_font(36)
```

**或直接硬编码** `/System/Library/Fonts/STHeiti Medium.ttc`（已验证可用）。

### 坑 4：read_file 读大文件被截断（17KB → 3342 字节）

**症状**：
- `/tmp/accenture-article.html` 转码后 17730 字节
- 用 `read_file` 读取全文 → 返回 3342 字节（被截断）
- `write_file` 写回 → 文件变成 3342 字节，HTML 内容丢失大半
- 后续检查 H2 数量 = 2（实际应该是 7），但用 `terminal wc -c` 看文件是 3342 字节

**修复**：read_file 只能信任 ≤10KB 的文件。**HTML/JSON 等大文件用 `terminal cat` / `python3` 直接读**：
```python
text = open('/tmp/accenture-article.html', encoding='utf-8').read()
# 直接在 execute_code / terminal 里处理
```

## 本次成功的 3 个动作

### 成功 1：digest 字节数预检（及时止损）

- 一开始写的 digest：`"AI 转型最急的 IT 服务巨头，市值却腰斩。59 亿 AI 订单是新钱还是左手倒右手？"` = 104 字节
- 跑 `assert len(digest.encode('utf-8')) <= 54` 立刻报错
- 改成 `"59 亿 AI 订单是新钱还是左手倒右手？"` = 49 字节，一次过

**教训**：3 检清单的 `assert` 必须在脚本里硬编码，**报错就当场改，不要试图"微调"原摘要**——直接重写更短版本。

### 成功 2：renwei 三件套在 Step 3 之前内化（避免重写）

- skill_view('renwei-writing') + skill_view('zhililong/references/from-zero-drafting-pitfalls.md') 双加载
- 写正文时三件套**内化为内功**（位置：咱们在谈这事 / 代价：埃森哲 27 亿 vs 8.65 亿这种具体算账 / 手迹：句尾"呢""了""吧"留着、"咱们""你想想"）
- 一次性写完 3168 字，只命中 28 处违规（**未内化时是 50+ 处**）

### 成功 3：双文件策略（避免 HTML 出现多余 H2）

- body.md 严格只放 7 节正文
- 完整 markdown（带元信息 + 大纲 + 参考资料）单独存 `公众号-[标题].md`
- HTML 转码只对 body 跑 → H2 数量精准 = 7

## 数据点（决策依据）

- **正文长度**：3168 中文字符（zhililong 目标 4000-5500，**偏低**）
  - 偏低原因：论点 1-5 每节控制在 400-500 字（紧凑）
  - 信息密度高：每段都有具体数字（$865M、$5.9B、$27B、77,000 名、80 万员工、MIT NANDA 95%）
  - 是否要补？——**否**，凑字数会稀释论点密度
- **正文图片**：1 张（黄仁勋五层蛋糕图，嵌入第四节"四、黄仁勋画的那张五层蛋糕图"前）
  - mmbiz URL: `http://mmbiz.qpic.cn/mmbiz_jpg/lvQ6mmDicLLWic...`
- **草稿参数**：
  - 标题：埃森哲这 12 个月最努力，市值反而腰斩（20 字符 / 52 字节 ✅）
  - 作者：刘生（2 字符 ✅）
  - digest：59 亿 AI 订单是新钱还是左手倒右手？（16 字符 / 49 字节 ✅）

## Step 8 输出

```
[OK] access_token 拿到: 105_dWMq_6smOpow8x_d...
[OK] 配图 mmbiz URL: http://mmbiz.qpic.cn/mmbiz_jpg/lvQ6mmDicLLWic...
[OK] thumb_media_id: kiuyle4KZHC7JKxpTQssMIiOa6tpnUwh1YK7xwq60pjIv3k_eKVXyQHg38qaB7sr
[OK] 草稿 media_id: kiuyle4KZHC7JKxpTQssMANvudbs1UzQEoflX7QkZqZfvYvOQcbh3Gc9RcfNKYlX
```

## 给未来 session 的 5 条速记

1. **大文件别用 read_file 写盘**（17KB HTML 截断事故）
2. **renwei 命中 >5 处走 Python 批量**（不要 patch 一条一条改）
3. **PIL 字体复用 cover_pil.find_chinese_font()**（不要硬编码 PingFang.ttc）
4. **Step 8 digest assert 必须跑**（104 → 49 字节事故避免了一次性返工）
5. **body.md 用 heredoc 写**（read_file/write_file 链路有行号污染风险）

## 输出文件清单

```
/Users/apple/Projects/New-Radar/Final Report/transcripts/accenture-halved-ai-five-layer-cake/
├── 公众号-埃森哲为什么腰斩.md          ← 用户审稿版（含大纲+参考资料）
├── 公众号-埃森哲为什么腰斩-body.md     ← 纯正文（转 HTML 用）
├── 公众号-埃森哲为什么腰斩.html        ← 嵌好 mmbiz 配图（17730 字节）
├── 封面图-埃森哲腰斩.jpg               ← 900×540 PIL 自制
├── 配图-五层蛋糕.jpg                   ← 900×700 PIL 自制（mmbiz Gate 必备）
└── upload_results.json                 ← {thumb_media_id, draft_media_id, mmbiz_url}
```