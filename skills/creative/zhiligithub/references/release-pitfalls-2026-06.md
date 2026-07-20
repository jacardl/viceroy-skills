# 发布实战踩坑备忘（2026-06-13 mattermost 长文）

> 这次完整跑通了一次 zhiligithub 端到端发布，记录几个**SKILL.md 没写但下次会用到的**实战细节。

## 1. 字节控制实测值（与 SKILL.md 表对齐）

| 字段 | 上限 | 实战值 | 通过/失败 |
|------|------|--------|-----------|
| 标题 | 60 字节 | 57 字节（"Mattermost v11.8.0：11 年没死，因为只在改安全"） | ✅ |
| 作者 | 8 字节 | "刘生" = 6 字节（"刘"=3 + "生"=3） | ✅ |
| digest | 54 字节 | 52 字节（"11 年、37K stars 的开源 IM，Slack 替代品里"） | ✅ |

**核心公式**（zhilicomments 已沉淀，zhiligithub 同步）：
```python
def calc_bytes(s: str) -> int:
    return sum(3 if ord(c) > 127 else 1 for c in s)
```

**安全预算策略**：
- 标题 ≤50 字节最稳（≈ 16-18 个中文字）
- digest 纯中文 25-30 字符就到上限；中英混排可塞更多英文省字节
- 写完必跑 `calc_bytes()`，超 54 字节（digest）自动截断

## 2. 封面图 PIL 离线生成的「字体死结」与解法

**死结**：默认 fallback 路径下，PIL `load_default()` 中文显示为方块，封面图废了。

**正确字体路径**（已实测可用）：
```python
CJK_BOLD = '/usr/share/fonts/google-noto-cjk/NotoSansCJK-Bold.ttc'
CJK_REG  = '/usr/share/fonts/google-noto-cjk/NotoSansCJK-Regular.ttc'
```

`fc-list :lang=zh` 可列出系统所有中文字体；如果系统换掉，先 `fc-list` 再选路径。

**封面图布局模板**（900×900 通用）：
- 顶部 110px 墨蓝条（#1B365D）+ 白字标签 + 灰字日期
- 中央大数字 + 汉字副标题
- 主体英文/中文项目名
- 副标题 2 行（多关键词）
- 底部 90px 墨蓝条 + 总结口号

## 3. 内容图（GitHub OG）的 PNG→JPEG 转换

**问题**：WeChat `uploadimg` 只接受 JPEG，PNG 报 40137 格式错误。

**修复**（务必先转）：
```python
from PIL import Image
img = Image.open('/tmp/mm-og.png').convert('RGB')  # 1200x600 → RGB
img.save('/tmp/mm-og.jpg', 'JPEG', quality=90)
```

PIL 用 `convert('RGB')` 处理 PNG alpha 通道，避免保存 JPEG 时报 alpha 错。

## 4. 占位替换的「不双 style」技巧（与 SKILL.md 已有踩坑对齐）

**做法 A（推荐）**：HTML 占位只写 `id`，替换时再补 style
```html
<img src="PLACEHOLDER_OG" id="og-img" />
```
```python
html = html.replace(
    '<img src="PLACEHOLDER_OG" id="og-img" />',
    f'<img src="{og_url}" id="og-img" style="width:100%;max-width:680px;border-radius:4px;margin:16px 0;" />'
)
```

**为什么**：如果占位和替换都带 `style`，容易出双 `style` 属性 bug。SKILL.md「图片占位 style 重复陷阱」已记载。

## 5. 端到端时间估算

- 下载 OG 图：< 5 秒
- PIL 生成封面图：< 2 秒
- 获取 token：< 2 秒
- 上传封面（type=image）：< 3 秒
- PNG→JPEG 转换：< 1 秒
- 上传内容图（uploadimg）：< 3 秒
- 占位替换：< 1 秒
- 创建草稿：< 3 秒
- **总耗时：约 20 秒**（token 已是 cached 的情况下）

如果 token 第一次获取：多 1-2 秒。

## 6. 草稿返回 payload 关键字段

```json
{
  "media_id": "kiuyle4KZH...",
  "item": [
    {
      "index": 0,
      "ad_count": 2    // ← 平台自动注入的广告位数量（个人订阅号）
    }
  ]
}
```

`ad_count` 是返回字段，不是错误。说明草稿创建成功，平台会自动加 2 个广告位（个人订阅号场景）。

## 7. digest 截断的 fallback 公式

```python
while calc_bytes(digest) > 54:
    digest = digest[:-1]
```

**实操建议**：先写完完整摘要，**然后**检查字节，超了再截断到 54 字节内（保持语义完整）。

## 8. 用户工作流确认

**「写完文章不自动发布」是默认工作流**（SKILL.md「⚠️ 新项目首次调研」章节已沉淀）：
- 默认：写完 → 输出到对话 → 询问是否发布
- 用户明确说「继续/发布」→ 才走完整 API 流程

这次会话走的就是这个流程：先输出文章 + 询问 → 用户说「继续」→ 才开始 token + upload + draft。
