# preflight CSS 误报项（zhilicomments 专用）

preflight.py 的第 6/7 项（CSS 对齐检查）是按 zhiligithub 规则编写的。zhilicomments 会误报以下项，**不阻塞推送**：

## 误报项清单

| 检查项 | preflight 期望 | zhilicomments 实际 | 是否阻塞 |
|--------|---------------|---------------------|---------|
| H2 ≥ 3 | 3+ 个 H2 标签 | 不分章节，不用 H2 | ❌ 非阻塞 |
| 容器宽度 680px | div 含 width:680px | 无容器 div | ❌ 非阻塞 |
| 容器内边距 | div 含 padding | 无容器 div | ❌ 非阻塞 |
| H2 基础样式 | H2 墨蓝色左边框 | 无 H2 | ❌ 非阻塞 |
| 墨蓝色 | color:#1B365D | 正文是 #2c2c2c | ❌ 非阻塞 |

## 判断规则

**preflight 第 1-5 项全过 + 仅第 6/7 项 CSS 失败 → 可直接推送。**

不需要修复任何 CSS 项。H2 相关检查（数量、样式）对 zhilicomments 完全不适用。
