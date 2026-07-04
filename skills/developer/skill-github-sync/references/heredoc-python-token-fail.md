# 坑 N+1（2026-07-03）：heredoc 写 Python → TOKEN 字符串被外层 bash 吞掉

## 症状

在 `terminal` 里用 heredoc 写 Python 脚本：

```bash
python3 << 'PYEOF'
import urllib.request, json
TOKEN=open('...')
# ...
PYEOF
```

报错：`SyntaxError: invalid syntax` 或 `unterminated string literal`，且报错位置指向 `TOKEN=*** 这一行。

## 根本原因

Hermes 的 `terminal` 工具在执行命令前会经过一个**外层 bash wrapper**。当 heredoc 里有 `TOKEN=*** 这样的字符串（哪怕是 `#` 注释行的部分），wrapper 会先做变量展开：

1. Wrapper 看到 `TOKEN=*** → 认为是 shell 变量赋值
2. `***` 中的 `*` 被 glob 展开 → 变成非法字符或空值
3. 实际传给 bash 的内容已损坏

**同样的问题在 Python 的 `TOKEN=*** = "..."` 一行赋值里也会出现**（赋值操作符 `=` 被识别为 shell 赋值语法）。

## 可靠解法：先写文件，再执行

```bash
# 1. 用 write_file 把脚本写到 /tmp/
# 2. 执行
python3 /tmp/sync_script.py
```

write_file 工具不经过 shell，不做变量展开，脚本原样写入文件。

## 禁止做法

| 方式 | 结果 |
|------|------|
| `terminal` heredoc `<< 'EOF'` | ❌ 失败 |
| `terminal` inline `python3 - << 'EOF'` | ❌ 失败 |
| `execute_code` 里写 Python | ⚠️ 受限（工具沙箱），不适合需要网络 IO + GitHub token 的场景 |
| `write_file` → `terminal python3` | ✅ 正确 |

## 验证模板

写完脚本后，直接执行确认：

```bash
python3 /tmp/sync_script.py
```

退出码 0 + 无 stderr 报错 = 成功。

## 实战案例（2026-07-03 zhilicomments 三端同步）

- 三份本地 zhilicomments：`openclaw`（17,801B）、`hermes`（33,365B）、云端（17,801B）
- 第一次尝试：bash heredoc → 5 次 SyntaxError（每次修复后又报新错）
- 切换方案：write_file + terminal 执行 → 一次成功
- 结果：openclaw + hermes 均同步到云端版本（31,829B），字节数一致
