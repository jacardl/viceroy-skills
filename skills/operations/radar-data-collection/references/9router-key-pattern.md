# 9Router Key — 从 SQLite 动态读取

## 关键规则

**不要在代码里硬编码 key 的 mask 形式**。常见错误：
```python
NINE_ROUTER_KEY = "sk-0d6...a7da"   # ← 截断 mask，13 字符，所有 /v1/search 返回 401
```
collect.py 的旧 hardcoded 值就是这个，导致 search 类采集 401 失败。

## 正确读取方式

```python
import sqlite3
db_path = os.path.expanduser("~/.9router/db/data.sqlite")
conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute("SELECT key FROM apiKeys LIMIT 1")
NINE_ROUTER_KEY = cur.fetchone()[0]  # sqlite3 默认返回 str，直接用
conn.close()
```

⚠️ `conn.text_factory = bytes` 是**错误**做法——加了它返回 bytes 而非 str，Bearer 拼接会出错。

## 验证 key 有效性

```python
import urllib.request, json

req = urllib.request.Request(
    "http://localhost:20128/v1/search",
    data=json.dumps({"model": "tavily", "query": "test", "max_results": 1}).encode(),
    headers={"Content-Type": "application/json", "Authorization": f"Bearer {NINE_ROUTER_KEY}"},
    method="POST"
)
with urllib.request.urlopen(req, timeout=10) as resp:
    print(json.loads(resp.read()).get("results", []))
```

## Key 格式

- 长度：35 字符
- 前缀：`sk-0d`
- 示例：`sk-0d68daa6645450e7-bc1xz4-8ac6a7da`
- 表：`apiKeys`，列：`key`
