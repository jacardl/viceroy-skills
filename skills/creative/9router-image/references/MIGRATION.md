# 9Router Image Gen — 移植指南

## 目标

在任意 Hermes 安装中，通过 9Router 本地网关启用图像生成能力（`image_generate` 工具）。

---

## 步骤 1：确认 9Router 已安装并运行

```bash
# 9Router 默认监听本地端口 20128
curl -s http://127.0.0.1:20128/v1/models | python3 -m json.tool | head -5

# 若连接拒绝：启动 9Router
# 9router serve   # 或对应命令，参见 9Router 文档
```

---

## 步骤 2：写入插件文件

复制 `references/9router-plugin/` 下的两个文件到目标 Hermes 安装：

```
# 目标路径（相对于 hermes-agent repo 根目录）：
plugins/image_gen/9router/__init__.py
plugins/image_gen/9router/plugin.yaml
```

**可选**，直接在目标机器重建文件——参考 `references/9router-plugin/__init__.py` 源码。

---

## 步骤 3：写入 config.yaml

编辑 `~/.hermes/config.yaml`，加入：

```yaml
providers:
  9router:
    api: http://127.0.0.1:20128/v1
    api_key: sk-your-9router-key

image_gen:
  provider: 9router
  model: cx/gpt-5.5-image
```

`api_key` 是注册 9Router 时拿到的 key，**不是** cx / qwen 的 key。

---

## 步骤 4：重启 Hermes（或重载配置）

```bash
# 重启 Hermes 使插件生效
hermes restart
```

---

## 步骤 5：验证

```bash
# 方式 A：通过 Hermes 工具
# 在 Hermes 对话中：
image_generate(prompt="a red rose")

# 方式 B：直接 curl（验证 9Router 连通性）
bash references/scripts/9router-list-models.sh
# 预期：返回 cx/gpt-5.5-image 等模型
```

---

## 架构说明（可跳读）

9Router 是一个**本地 AI 网关**，同时支持 text 和 image 两种模型端点：

| 端点 | 用途 | 可用模型 |
|---|---|---|
| `/v1/chat/completions` | 文本对话 | qwen、minimax 等 |
| `/v1/images/generations` | 图像生成 | cx/gpt-5.5-image 等 |

9Router 根据请求中的 `model` 字段**前缀**路由到不同的上游 provider：

| model 前缀 | 路由到 | 说明 |
|---|---|---|
| `cx/` | 9Router 内置 cx provider | ✅ 可生图 |
| `image`（无前缀） | 默认 OpenAI provider | ❌ 无 credentials |
| `qwen/` | qwen provider | ❌ 该 provider 未配 key |
| `image` | qwen-image-2.0 provider | ❌ 该 provider 不支持生图端点 |

因此 **必须用 `cx/gpt-5.5-image`**（或其他 `cx/` 前缀模型）。

---

## 已知限制

- 推理时间约 99s，超时阈值硬编码为 120s
- portrait 尺寸（1024×1792）prompt 宜精简避免超时
- 不支持 image-to-image / 编辑（仅 text-to-image）
- cx 模型的 key 由 9Router 服务端管理，无需在 Hermes config 中配置
