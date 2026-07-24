---
name: zhiliGEO
description: "写直隶按察使公众号 GEO 垂直系列文章"
metadata: { "openclaw": { "emoji": "📍" } }
---

# 直隶按察使 GEO 垂直写作

**触发**：写一篇 GEO 文章 / GEO 系列 / GEO 选题 / GEO 稿

**不是** SEO 教程，是**品牌在 AI 搜索时代如何被准确理解**的实战故事。

## 参考文件（写前必读）
- `references/geo-article-sample.md` — 范文原文，含骨架 + 写法要点
- `references/geo-knowledge.md` — GEO 知识背景
- `references/style-guide.md` — 风格规范 + HTML 模板

## 品牌参数
| 参数 | 值 |
|------|-----|
| 公众号名 | 直隶按察使 |
| 作者 | 刘生 |
| 样式 | Georgia, Noto Serif SC / #f5f4ed 背景 / 强调色 #c9553d |
| 分隔符 | `· · ·` |

## 发布流程
1. 写完 HTML → 自检：作者=刘生 / 无 emoji / 无 bullet / 无企业全名 / 分隔符≤3次 / 标题16–24字
2. **配图**：调用 `zhili-illustration` 技能（生成封面图 → 上传微信素材获取 media_id）
3. 调用 `zhili-publish` 推送草稿箱
4. 飞书汇报：标题 + 字数 + 封面图建议

## 选题方向
1. SEO vs GEO 本质区别
2. 品牌在 AI 搜索里的可见度
3. 国内 vs 海外 GEO 规则差异
4. GEO 进入招标市场
5. GEO 三个常见误区
6. AI 搜索时代的品牌信息基础设施
7. 具体品牌 GEO 实战案例（脱敏处理）
