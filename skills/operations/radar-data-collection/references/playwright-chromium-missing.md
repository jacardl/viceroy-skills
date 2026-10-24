# Playwright chromium 缺失场景 (2026-10-15 实测)

## 触发条件

**方式 A（Trending 不可用）**：`gh_collect.py` 内部 Playwright `p.chromium.launch()` 失败（`agent-reach-venv314` 环境有 playwright 包但无 chromium 可执行文件）。

**方式 B（HP 源本身不可用）**：`ungh.cc/repos/<owner>/<repo>` 返回 HTTP 403/404，或 `raw.githubusercontent.com` 无法访问。2026-10-17 实测：`ruanyf/weekly` 在 `ungh.cc/repos/ruanyf/weekly` 返回 403 Forbidden。

## 现象

```
[gh_collect] Playwright error: Traceback (most recent call last):
  File ".../playwright/sync_ap" ...
  browser = p.chromium.launch(args=['--no-sandbox', '--disable-dev-shm-usage'])
[gh_collect] WARN: Playwright returned no trending repos (will rely on HP sources only)
[gh_collect] Inserted 1 repos (HP=1, trending=0)
```

- HP 源（`ruanyf/weekly`）**不受影响**，正常写入
- Trending 采集静默失败，不重试，不抛异常
- 最终 DB 中 github 条目 = HP 源条目数（本例 1 条）

## 与「GitHub 彻底失败」的区别

| 场景 | gh_collect.py exit | github 条目 | 原因 |
|------|-------------------|-------------|------|
| Playwright 缺 chromium | 0（成功） | 1（HP only） | 防火墙/无头浏览器不可用 |
| gh_collect.py 路径错误 | 0（成功） | 0 | collect.py 内部路径错，不写数据 |
| GitHub API 彻底失败 | 非 0 | 0 | 网络或认证问题 |

## 判定规则

- github=0 且 gh_collect.py exit=0 → 检查是否有 HP 源写入（可能 Playwright 失败）
- github=0 且 gh_collect.py exit≠0 → 真正失败，按 PATCH-2026-08-10-001 告警
- github≥1 → 无论数量多少都视为部分成功，不触发 GitHub 告警

## 当前 workaround

无 Playwright 环境下只能依赖 HP 源，Trending 无法采集。可考虑：
1. `pip install playwright && playwright install chromium`（需网络访问）
2. 接受 HP-only 模式，不阻塞日报推送

## 真实根因：Python 3.14 greenlet C 扩展 ABI 不匹配（2026-10-17 实测）

**症状**：`Playwright error:` 后面 traceback 在 `playwright/sync_api/__init__.py` 第 26 行 `import playwright.sync_api._generated` 阶段就崩，**根本没到 chromium 启动**。表面像 chromium 缺失，实际是 Python 3.14 ABI 问题。

**完整堆栈**（手工验证）：
```
File "/Users/apple/.agent-reach-venv314/lib/python3.14/site-packages/playwright/_impl/_greenlets.py", line 17
  import greenlet
File "/Users/apple/.agent-reach-venv314/lib/python3.14/site-packages/greenlet/__init__.py", line 26
  from ._greenlet import _C_API
ModuleNotFoundError: No module named 'greenlet._greenlet'
```

**为什么 traceback 在 cron 报告里被截断**：`gh_collect.py` 把 traceback 嵌进 `[gh_collect] Playwright error: {traceback}` 一次性 print，但 cron 终端 buffer + stdout pipe 截断到 ~6 行（停在 `playwright/sync_ap` 路径中间），真实根因藏在截断里。手工 `head`/`sed -n '5,30p'` 看也只能看到同一段。

**完整诊断命令**（绕过脚本，直接在目标 venv import 拿全栈）：

```bash
/Users/apple/.agent-reach-venv314/bin/python3 -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(args=['--no-sandbox','--disable-dev-shm-usage'])
"
```

**修复**（拿匹配 Python 3.14 的 C 扩展 wheel）：

```bash
/Users/apple/.agent-reach-venv314/bin/pip install --upgrade --force-reinstall greenlet playwright
```

**修后验证**（端到端）：

```bash
/Users/apple/.agent-reach-venv314/bin/python3 ~/.shared-agent-skills/operations/radar-data-collection/scripts/gh_collect.py $(TZ=Asia/Shanghai date '+%Y-%m-%d')
```

应输出 `Inserted N repos (HP=1, trending=M)`，M > 0 表示 trending 恢复。

**HP 源只有 1 条 (ruanyf/weekly) 不够 ≥10 目标**，trending 必须恢复才能满足日报 GH 验证标准（参见 SKILL.md「验证标准」节）。

## 排查 SOP 升级（2026-10-17）

1. **不要被"chromium 缺失"表象误导**。Playwright 链路不通时先 `python3 -c "from playwright.sync_api import sync_playwright"` 直跑 import，看是 import 阶段崩（greenlet / cffi / typing_extensions 等依赖）还是 launch 阶段崩（chromium 真的缺）。
2. **不要只信 gh_collect.py 输出的 traceback**。脚本的 `[gh_collect] Playwright error:` 后面 traceback 多半被截，**重跑直接 import 拿全栈**才能定位。
3. **修完后端到端验证**：脚本能跑 + DB `github` 有数据 + push.py 06:00 推送 MSG3 正常显示，缺一不可。